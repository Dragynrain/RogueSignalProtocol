#!/usr/bin/env python3
"""
Turn processing manager for game session.

Handles turn-by-turn game logic including:
- Player turn effects (virus damage, status effects)
- Special tile processing (nodes, items, upgrades)
- Memory system updates (FOV, explored tiles, ghost positions)
- Enemy AI coordination (awareness, movement, attacks)
- Admin avatar spawning
- Trace level management

Extracted from GameSession to improve modularity and maintainability.
"""

import logging
import math
import random

from game_config import GameBalance, GameConfig
from game_data import GameUpgrades
from game_entities import Colors, EnemyMovement, EnemyState, Position


class GameTurnManager:
    """
    Manages turn processing for game sessions.

    Coordinates turn execution including player effects, enemy AI,
    special tile processing, and memory system updates.

    Attributes:
        game_engine: GameEngine instance for accessing all game systems
    """

    def __init__(self, game_engine):
        """
        Initialize turn manager with game engine reference.

        Args:
            game_engine: GameEngine instance providing access to all game systems
        """
        self.game_engine = game_engine
        self._enemies_alerted_played_this_turn = False  # Prevent sound stacking
        # A20: Track last blind spot position for consume-on-leave behavior
        self._last_blind_spot_position: Position | None = None

    def reset_blind_spot_tracking(self) -> None:
        """
        Reset A20 blind spot position tracking for a new level.

        Must be called when transitioning to a new level to prevent
        incorrectly consuming blind spots from the previous level.
        """
        self._last_blind_spot_position = None

    def process_turn(self):
        """
        Process one complete game turn in structured phases.

        Turn order:
        1. Grant speed boost moves (if active and exhausted)
        2. Process player turn effects (virus damage, status effects)
        3. Process special tiles (nodes, items, upgrades, fragments)
        4. Update memory system (FOV, explored tiles, ghost positions)
        5. Update enemies (three-phase: awareness -> movement -> attacks)
        6. Check admin spawn (if trace >= 100%)
        7. Apply passive trace increase (based on level config)

        Note: Speed boost grants 2 moves per enemy turn. This is processed
        at the start of each turn to ensure consistent move counting.
        """
        # Skip turn processing if game is over (player dead or won)
        # This prevents enemies from acting on a dead player
        if self.game_engine.game_over:
            return

        # Reset flags at start of turn
        self._enemies_alerted_played_this_turn = False

        # Grant speed boost moves at start of turn
        if (
            self.game_engine.player.temporary_effects["speed_boost_turns"] > 0
            and self.game_engine.player.speed_moves_remaining == 0
        ):
            self.game_engine.player.speed_moves_remaining = 2  # Grant 2 moves per enemy turn

        # Process turn using the dedicated turn processor
        old_cpu = self.game_engine.player.cpu
        self.game_engine.turn_processor.process_turn(self.game_engine.player)

        # Handle sound effects for virus damage
        if (
            old_cpu > self.game_engine.player.cpu
            and self.game_engine.player.has_active_effect("virus_turns")
        ):
            self.game_engine.sound_manager.play_sound("virus_damage")
            # Check for death from virus using centralized handler
            self.game_engine.death_handler.check_death("virus")

        # Process special tiles
        self._process_special_tiles()

        # Update enemies
        self._update_enemies()

        # Update memory system
        self._update_memory_system()

        # Check for admin spawn
        self._check_admin_spawn()

        # NOTE: Passive trace level increase is handled in TurnProcessor._process_trace_increase()
        # which applies ascension modifiers (A3 trace gain multiplier)

        # Occasional atmospheric flavor text (10% chance, reduced from 15% to avoid spam)
        atmo_msg = self.game_engine.narrative_manager.trigger_random_atmospheric(chance=0.10)
        if atmo_msg:
            self.game_engine.message_log.add_message(atmo_msg)

        # Final death check - catches any deaths not handled at their source
        # The death handler is idempotent, so this is safe even if already called
        # Using "unknown" as fallback cause - if this gets logged, it means a damage
        # source failed to call check_death() properly (indicates a bug to investigate)
        if self.game_engine.player.cpu <= 0 and not self.game_engine.death_handler.is_handled:
            logging.warning(
                "Death caught by fallback check - a damage source may be missing check_death() call"
            )
        self.game_engine.death_handler.check_death("unknown")

    def _update_memory_system(self):
        """Update the hybrid fog of war memory system using TCOD FOV."""
        vision_range = self.game_engine.player.get_vision_range()

        # Use TCOD FOV for more accurate vision calculations
        if self.game_engine.player.can_see_through_walls():
            # Enhanced vision - simple distance check
            for dx in range(-vision_range, vision_range + 1):
                for dy in range(-vision_range, vision_range + 1):
                    if dx * dx + dy * dy <= vision_range * vision_range:
                        x = self.game_engine.player.x + dx
                        y = self.game_engine.player.y + dy
                        world_pos = Position(x, y)
                        if world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                            self.game_engine.game_map.explored_tiles.add((x, y))
        else:
            # Use VisibilityManager for cached FOV calculation
            visible_tiles = self.game_engine.visibility_manager.get_player_visible_tiles(
                self.game_engine.player, self.game_engine.turn
            )

            # Mark all visible tiles as explored
            for x, y in visible_tiles:
                self.game_engine.game_map.explored_tiles.add((x, y))

        # Update last known enemy positions
        for enemy in self.game_engine.enemies:
            if self.game_engine.player.can_see_enemy(enemy, self.game_engine.game_map):
                self.game_engine.game_map.last_known_enemy_positions[enemy.id] = (
                    enemy.position,
                    self.game_engine.turn,
                )

        # Clean up ghost positions where player can see the area but enemy is not there
        self._cleanup_ghost_positions()

    def _cleanup_ghost_positions(self):
        """Remove ghost enemy positions when player can see the area but enemy is not there."""
        vision_range = self.game_engine.player.get_vision_range()
        gm = self.game_engine.game_map

        positions_to_remove = [
            enemy_id
            for enemy_id, (ghost_pos, _) in gm.last_known_enemy_positions.items()
            if gm.can_see_position(self.game_engine.player.position, ghost_pos, vision_range)
            and not any(
                e.id == enemy_id and e.position.distance_to(ghost_pos) == 0
                for e in self.game_engine.enemies
            )
        ]

        for enemy_id in positions_to_remove:
            del gm.last_known_enemy_positions[enemy_id]

    def _process_special_tiles(self):
        """Process effects of special tiles at player position."""
        player_pos = (self.game_engine.player.x, self.game_engine.player.y)
        gm = self.game_engine.game_map
        pp = self.game_engine.player.position

        # Check if player is on any special node and if it's a new position
        is_on_node = gm.is_cooling_node(pp) or gm.is_cpu_recovery_node(pp) or gm.is_ghost_node(pp)
        should_play_sound = is_on_node and self.game_engine.last_node_position != player_pos

        # Update last node position and track discoveries
        if is_on_node:
            self.game_engine.last_node_position = player_pos

            # Mark special nodes as discovered when first stepped on
            # (revealed_special_nodes is initialized in GameStateManager.__init__)
            if self.game_engine.game_map.is_cooling_node(self.game_engine.player.position):
                self.game_engine.game_state.revealed_special_nodes[player_pos] = "cooling"
            elif self.game_engine.game_map.is_cpu_recovery_node(self.game_engine.player.position):
                self.game_engine.game_state.revealed_special_nodes[player_pos] = "cpu"
            elif self.game_engine.game_map.is_ghost_node(self.game_engine.player.position):
                self.game_engine.game_state.revealed_special_nodes[player_pos] = "ghost"
        else:
            self.game_engine.last_node_position = None

        # Cooling node (with A13+ capacity support)
        if self.game_engine.game_map.is_cooling_node(self.game_engine.player.position):
            node = self.game_engine.game_map.cooling_nodes.get(player_pos)
            if node and not node.depleted:
                wanted_reduction = 20
                # Calculate actual benefit needed (don't waste capacity)
                actual_benefit = min(wanted_reduction, self.game_engine.player.heat)
                if actual_benefit > 0:
                    restored = node.use(actual_benefit)
                    old_heat = self.game_engine.player.heat
                    self.game_engine.player.heat = max(0, self.game_engine.player.heat - restored)
                    if old_heat > self.game_engine.player.heat and should_play_sound:
                        self.game_engine.sound_manager.play_sound("node_activate")
                    # Track restoration node usage for floor_is_lava achievement
                    if restored > 0:
                        from game_metrics import track

                        track("restoration_nodes_used")

        # CPU recovery node (with A13+ capacity support)
        if self.game_engine.game_map.is_cpu_recovery_node(self.game_engine.player.position):
            node = self.game_engine.game_map.cpu_recovery_nodes.get(player_pos)
            if node and not node.depleted:
                wanted_recovery = GameBalance.CPU_RECOVERY_AMOUNT
                # Calculate actual benefit needed (don't waste capacity)
                actual_benefit = min(
                    wanted_recovery,
                    self.game_engine.player.max_cpu - self.game_engine.player.cpu,
                )
                if actual_benefit > 0:
                    restored = node.use(actual_benefit)
                    # Cap CPU to max_cpu to prevent overflow
                    self.game_engine.player.cpu = min(
                        self.game_engine.player.max_cpu,
                        self.game_engine.player.cpu + restored,
                    )
                    if restored > 0 and should_play_sound:
                        self.game_engine.sound_manager.play_sound("node_activate")
                    # Track restoration node usage for floor_is_lava achievement
                    if restored > 0:
                        from game_metrics import track

                        track("restoration_nodes_used")

        # Ghost node (trace level reduction with A13+ capacity support)
        if self.game_engine.game_map.is_ghost_node(self.game_engine.player.position):
            node = self.game_engine.game_map.ghost_nodes.get(player_pos)
            if node and not node.depleted:
                wanted_reduction = 20
                # Calculate actual benefit needed (don't waste capacity)
                actual_benefit = min(wanted_reduction, self.game_engine.player.trace_level)
                if actual_benefit > 0:
                    restored = node.use(int(actual_benefit))
                    old_trace = self.game_engine.player.trace_level
                    self.game_engine.player.trace_level = max(
                        0, self.game_engine.player.trace_level - restored
                    )
                    actual_reduction = old_trace - self.game_engine.player.trace_level

                    # Only play sound when first stepping on the node or when there's actual reduction
                    if should_play_sound or actual_reduction > 0:
                        if should_play_sound:
                            self.game_engine.sound_manager.play_sound("node_activate")
                    # Track restoration node usage for floor_is_lava achievement
                    if restored > 0:
                        from game_metrics import track

                        track("restoration_nodes_used")

        # Code hack
        if player_pos in self.game_engine.game_map.code_hacks:
            patch = self.game_engine.game_map.code_hacks[player_pos]
            self.game_engine.sound_manager.play_sound("item_pickup_code")
            self.game_engine.player.inventory_manager.add_item(patch)
            self.game_engine.message_log.add_message(f"Found {patch.name}")
            logging.info(
                f"[PICKUP] Code Hack: {patch.name} at ({player_pos[0]},{player_pos[1]}) on Level {self.game_engine.level}"
            )
            del self.game_engine.game_map.code_hacks[player_pos]

        # Exploit pickup
        if player_pos in self.game_engine.game_map.exploit_pickups:
            exploit_item = self.game_engine.game_map.exploit_pickups[player_pos]
            self.game_engine.sound_manager.play_sound("item_pickup_exploit")
            self.game_engine.player.inventory_manager.add_item(exploit_item)
            self.game_engine.message_log.add_message(f"Found {exploit_item.name}")
            logging.info(
                f"[PICKUP] Exploit: {exploit_item.name} ({exploit_item.exploit_key}) at ({player_pos[0]},{player_pos[1]}) on Level {self.game_engine.level}"
            )
            del self.game_engine.game_map.exploit_pickups[player_pos]

        # Permanent upgrade pickup (auto-equip)
        if player_pos in self.game_engine.game_map.permanent_upgrades:
            upgrade_key = self.game_engine.game_map.permanent_upgrades[player_pos]
            if upgrade_key in GameUpgrades.UPGRADES:
                upgrade = GameUpgrades.UPGRADES[upgrade_key]
                if self.game_engine.player.apply_permanent_upgrade(upgrade_key):
                    self.game_engine.sound_manager.play_sound("item_pickup_upgrade")
                    self.game_engine.message_log.add_message(f"Integrated {upgrade.name}!")
                    self.game_engine.message_log.add_message(upgrade.description)
                    logging.info(
                        f"[PICKUP] Permanent Upgrade: {upgrade.name} ({upgrade_key}) at ({player_pos[0]},{player_pos[1]}) on Level {self.game_engine.level}"
                    )
                    del self.game_engine.game_map.permanent_upgrades[player_pos]
                    # Track upgrade discovery for Explorer achievement
                    from game_metrics import get_current_session

                    session = get_current_session()
                    if session:
                        session.special_nodes_discovered.add("upgrade")

        # Story fragment pickup
        if player_pos in self.game_engine.game_map.story_fragments:
            story_fragment = self.game_engine.game_map.story_fragments[player_pos]
            # Discover the fragment and save progress
            if self.game_engine.story_fragment_manager.discover_fragment(
                story_fragment.fragment_index
            ):
                self.game_engine.sound_manager.play_sound("item_pickup_story")
                self.game_engine.message_log.add_message("Data fragment recovered!")
                logging.info(
                    f"[PICKUP] Story Fragment #{story_fragment.fragment_index} at ({player_pos[0]},{player_pos[1]}) on Level {self.game_engine.level}"
                )

                # Open lore viewer in reading mode for the newly discovered fragment
                discovered_fragments = (
                    self.game_engine.story_fragment_manager.get_discovered_fragments()
                )
                # Find the index of this fragment in the discovered list
                for i, (frag_idx, _) in enumerate(discovered_fragments):
                    if frag_idx == story_fragment.fragment_index:
                        self.game_engine.lore_viewer_selection = i
                        break

                # Only open lore viewer if renderer is available (not in headless tests)
                if (
                    hasattr(self.game_engine, "input_handler")
                    and self.game_engine.input_handler
                    and self.game_engine.input_handler.renderer
                ):
                    self.game_engine.show_lore_viewer = True
                    self.game_engine.lore_viewer_mode = "reading"
                # Track story discovery for Explorer achievement
                from game_metrics import get_current_session

                session = get_current_session()
                if session:
                    session.special_nodes_discovered.add("story")

                # Remove fragment from map only after successful discovery
                del self.game_engine.game_map.story_fragments[player_pos]
            else:
                # Invalid fragment index - remove from map but log error
                logging.error(
                    f"[PICKUP] Invalid Story Fragment #{story_fragment.fragment_index} at "
                    f"({player_pos[0]},{player_pos[1]}) - fragment removed from map"
                )
                del self.game_engine.game_map.story_fragments[player_pos]

        # Environmental narrative: First blind spot entry
        player_in_blind_spot = self.game_engine.game_map.is_blind_spot(pp)
        if player_in_blind_spot:
            blind_spot_msg = self.game_engine.narrative_manager.trigger_first_blind_spot()
            if blind_spot_msg:
                self.game_engine.message_log.add_message(blind_spot_msg)

            # Track turns in blind spots for Shadow Dancer achievement
            from game_metrics import get_current_session

            session = get_current_session()
            if session:
                session.turns_in_blind_spots += 1

        # A20+: Consume blind spot when player LEAVES it (not when entering)
        # Player can stay as long as they want, but once they move away it vanishes
        if self.game_engine.ascension_modifiers.blind_spots_consumable:
            # Check if player left a tracked blind spot
            if self._last_blind_spot_position is not None and self._last_blind_spot_position != pp:
                # Player moved away from blind spot - consume it
                self.game_engine.game_map.consume_blind_spot(self._last_blind_spot_position)
                self._last_blind_spot_position = None

            # Track current blind spot position
            if player_in_blind_spot:
                self._last_blind_spot_position = pp
            else:
                self._last_blind_spot_position = None

        # Environmental narrative: Low CPU warning
        cpu_percent = self.game_engine.player.cpu / self.game_engine.player.max_cpu
        if cpu_percent < 0.30 and random.random() < 0.10:  # 10% chance per turn when below 30%
            low_cpu_msg = self.game_engine.narrative_manager.trigger_low_cpu()
            if low_cpu_msg:
                self.game_engine.message_log.add_message(low_cpu_msg)

    def _update_enemies(self):
        """
        Update all enemy states and actions in single-pass system.

        For each enemy:
        1. Update awareness state and communicate alerts
        2. Decide action: if adjacent to player, attack; otherwise move
        3. Execute action (ensuring move OR attack, not both)

        This simplification removes the three-phase approach while preserving
        the "move OR attack" constraint essential for game balance.
        """
        # First pass: Update awareness for all enemies
        # This must be separate to ensure alert propagation before movement
        self._update_all_enemy_awareness()

        # Second pass: Process each enemy's action (move OR attack)
        # Track attacks for inventory warning dialogue
        player_attacked_in_inventory = False
        total_damage_taken = 0
        attacking_enemy_count = 0

        for enemy in self.game_engine.enemies[:]:
            # Check if enemy can attack player
            can_attack = enemy.can_attack_player(self.game_engine.player)

            if can_attack:
                # Enemy is adjacent - attack instead of moving
                # Play appropriate sound based on enemy type
                if enemy.type == "virus":
                    self.game_engine.sound_manager.play_sound("virus_infection")
                else:
                    self.game_engine.sound_manager.play_sound("enemy_attack")
                damage = enemy.attack_player(self.game_engine.player, game_engine=self.game_engine)

                # Add damage message to log (always, not just when inventory is open)
                if damage > 0:
                    cpu_remaining = max(0, self.game_engine.player.cpu)
                    self.game_engine.message_log.add_message(
                        f"{enemy.type_data.name} attacked for {damage} CPU damage! ({cpu_remaining} remaining)",
                        Colors.RED,
                    )
                elif enemy.type == "virus":
                    virus_turns = self.game_engine.player.temporary_effects.get("virus_turns", 0)
                    self.game_engine.message_log.add_message(
                        f"{enemy.type_data.name} infected you! (Virus: {virus_turns} turns)",
                        Colors.YELLOW,
                    )
                elif enemy.type == "inhibitor":
                    self.game_engine.message_log.add_message(
                        f"{enemy.type_data.name} inhibited your movement!", Colors.YELLOW
                    )

                # Track attacks for inventory warning
                if damage >= 0 or (
                    hasattr(enemy.type_data, "effects")
                    and (
                        "virus" in enemy.type_data.effects or "inhibitor" in enemy.type_data.effects
                    )
                ):
                    attacking_enemy_count += 1
                    if damage > 0:
                        total_damage_taken += damage

                    if self.game_engine.show_inventory:
                        player_attacked_in_inventory = True

                        if total_damage_taken > 0:
                            if attacking_enemy_count > 1:
                                warning_msg = f"{attacking_enemy_count} enemies attacked for {total_damage_taken} damage! Close inventory to defend."
                            else:
                                warning_msg = (
                                    f"Attacked for {damage} damage! Close inventory to defend."
                                )
                            self.game_engine.message_log.add_message(warning_msg, Colors.RED)
                        else:
                            self.game_engine.message_log.add_message(
                                "Enemy attacked with status effect! Close inventory to defend.",
                                Colors.YELLOW,
                            )

            else:
                # Enemy is not adjacent - move toward player
                enemy.move(self.game_engine.game_map, self.game_engine.player, self.game_engine)

        # Show inventory attack warning dialogue if player was attacked while in inventory
        if player_attacked_in_inventory:
            from game_dialogue_system import create_inventory_attack_dialogue

            # Get input mapper for dynamic button hints
            input_mapper = self.game_engine.get_input_mapper()

            dialogue = create_inventory_attack_dialogue(input_mapper)
            self.game_engine.dialogue_state.show(dialogue)

    def _update_all_enemy_awareness(self):
        """
        Update awareness states and handle communication for all enemies.

        This is kept separate from movement/attack to ensure alert propagation
        happens before any enemy moves.

        State machine per enemy:
        - UNAWARE + sees player -> ALERT (1 turn grace period)
        - ALERT + sees player (timer expires) -> HOSTILE (alerts nearby enemies)
        - ALERT + loses sight -> UNAWARE (after grace period)
        - HOSTILE + loses sight -> 15% chance to return to UNAWARE

        Communication:
        - Hostile enemies alert all enemies within NEARBY_ENEMY_ALERT_RADIUS
        - Alerted enemies immediately become HOSTILE with player's last position

        Note: Skip updates on first turn after loading to preserve saved states.
        """
        # Skip enemy state updates on the first turn after loading to preserve saved states
        if (
            hasattr(self.game_engine.game_state, "just_loaded")
            and self.game_engine.game_state.just_loaded
        ):
            self.game_engine.game_state.just_loaded = False
            return

        for enemy in self.game_engine.enemies[:]:
            # Blinded enemies can't see anything (but keep moving)
            if enemy.blinded_turns > 0:
                can_see = False
            else:
                can_see = enemy.can_see_player(self.game_engine.player, self.game_engine.game_map)

            # Admin Avatar has perfect tracking (but can still be blinded)
            if enemy.type == "admin":
                if enemy.blinded_turns <= 0:  # Only track if not blinded
                    player_pos = Position(self.game_engine.player.x, self.game_engine.player.y)
                    if enemy.state != EnemyState.HOSTILE:
                        # Use make_hostile for consistent state transition (clears move queue)
                        enemy.make_hostile(player_pos)
                        self.game_engine.message_log.add_message(
                            f"{enemy.type_data.name} detected you!"
                        )
                    else:
                        # Already hostile - just update last seen position
                        enemy.last_seen_player = player_pos
            else:
                self._update_enemy_state(enemy, can_see)

    def _update_enemy_state(self, enemy, can_see_player):
        """Update enemy state based on player visibility."""
        player_pos = Position(self.game_engine.player.x, self.game_engine.player.y)

        # Track old state for invalidation
        old_state = enemy.state

        if can_see_player:
            # Enemy sees player - escalate state
            if enemy.state == EnemyState.UNAWARE:
                enemy.state = EnemyState.ALERT
                enemy.alert_timer = 1  # Give 1 turn grace period before becoming HOSTILE
                enemy.last_seen_player = player_pos
                self.game_engine.message_log.add_message(f"{enemy.type_data.name} investigating")
                self.game_engine.sound_manager.play_sound("enemy_alert")

                # Track detection for Ghost Protocol achievement
                # Also reset stealth streak for Silent Assassin
                from game_metrics import get_current_session

                session = get_current_session()
                if session:
                    session.ever_detected = True
                    session.current_stealth_streak = 0  # Detection breaks the streak

            elif enemy.state == EnemyState.ALERT:
                enemy.last_seen_player = player_pos
                enemy.alert_timer -= 1  # Decrement timer each turn they see player
                if enemy.alert_timer <= 0:
                    self._transition_to_hostile(enemy)

            elif enemy.state == EnemyState.HOSTILE:
                enemy.last_seen_player = player_pos
                self._increase_trace(
                    GameBalance.ENEMY_TRACE_CONTINUOUS_HOSTILE, "trace_continuous_hostile"
                )
                self._alert_nearby_enemies(enemy)
        else:
            # Enemy lost sight - de-escalate state
            if enemy.state == EnemyState.ALERT:
                enemy.alert_timer -= 1
                if enemy.alert_timer <= 0:
                    enemy.state = EnemyState.UNAWARE
                    self._restore_patrol(enemy)
                    self.game_engine.message_log.add_message(
                        f"{enemy.type_data.name} lost interest"
                    )

            elif enemy.state == EnemyState.HOSTILE:
                if random.random() < 0.15:
                    if enemy.type == "admin":
                        enemy.state = EnemyState.ALERT
                        enemy.alert_timer = 0
                    else:
                        enemy.state = EnemyState.UNAWARE
                        enemy.last_seen_player = None
                        self._restore_patrol(enemy)
                        self.game_engine.message_log.add_message(
                            f"{enemy.type_data.name} lost track"
                        )

        # INVALIDATION TRIGGER #1: State change
        if enemy.state != old_state:
            enemy.move_queue.clear()  # New state = new plan

    def _transition_to_hostile(self, enemy):
        """Transition enemy to hostile state with proper state management."""
        # Use make_hostile helper for consistent state transitions
        # (handles patrol index storage, state change, move queue invalidation)
        player_pos = Position(self.game_engine.player.x, self.game_engine.player.y)
        enemy.make_hostile(player_pos)

        self._increase_trace(GameBalance.ENEMY_TRACE_ALERT_TO_HOSTILE, "trace_alert_to_hostile")
        self.game_engine.message_log.add_message(f"{enemy.type_data.name} detected you!")
        self.game_engine.sound_manager.play_sound("enemy_hostile")
        self._alert_nearby_enemies(enemy)

    def _increase_trace(self, default_value, config_key):
        """Increase player trace level, with A7+ hostile trace bonus."""
        network_configs = GameConfig.NETWORK_CONFIGS()
        level_config = network_configs[self.game_engine.level]
        trace_increase = level_config[config_key]

        # A7+: Add hostile trace bonus from ascension modifiers
        trace_increase += self.game_engine.ascension_modifiers.hostile_trace_bonus

        old_trace = self.game_engine.player.trace_level
        self.game_engine.player.trace_level = min(
            100, self.game_engine.player.trace_level + trace_increase
        )

        # Track metrics if trace actually increased
        if self.game_engine.player.trace_level > old_trace:
            from game_metrics import track, track_highest_trace

            track("trace_increases")
            track_highest_trace(self.game_engine.player.trace_level)

        self._check_trace_threshold_warnings(old_trace, self.game_engine.player.trace_level)

    def _restore_patrol(self, enemy):
        """Restore patrol enemy to their original patrol waypoint when losing interest.

        When a PATROL enemy transitions from HOSTILE/ALERT back to UNAWARE,
        restore their patrol_index to the original value stored when they
        first became hostile (via make_hostile()).
        """
        movement_type = enemy.get_movement_type()
        if movement_type == EnemyMovement.PATROL and enemy.patrol_points:
            # Restore to original patrol waypoint (stored when became hostile)
            enemy.patrol_index = enemy.original_patrol_index

    def _check_trace_threshold_warnings(self, old_trace: float, new_trace: float):
        """Check and play warning sounds for trace level threshold crossings."""
        thresholds = [
            (25, "Trace signature detected - network monitoring active", Colors.INFO),
            (50, "Elevated trace level - detection risk increasing", Colors.WARNING),
            (75, "WARNING: High trace level!", Colors.YELLOW),
            (90, "CRITICAL: Admin spawn imminent!", Colors.RED),
        ]
        for threshold, msg, color in thresholds:
            if old_trace < threshold <= new_trace:
                # Only play sound for 75+ thresholds (avoid spam)
                if threshold >= 75:
                    self.game_engine.sound_manager.play_sound("trace_threshold")
                self.game_engine.message_log.add_message(msg, color)
                # Add environmental narrative for high trace
                if threshold >= 75:
                    env_msg = self.game_engine.narrative_manager.trigger_high_trace()
                    if env_msg:
                        self.game_engine.message_log.add_message(env_msg)
                break

    def _alert_nearby_enemies(self, alerting_enemy):
        """Alert nearby enemies when one becomes hostile, with A15+ override."""
        # Stunned enemies cannot alert others
        if alerting_enemy.disabled_turns > 0:
            return

        # A15+: Use alert range override if set, otherwise use config default
        mods = self.game_engine.ascension_modifiers
        if mods.alert_range_override is not None:
            alert_range = mods.alert_range_override
        else:
            alert_range = GameConfig.NEARBY_ENEMY_ALERT_RADIUS
        alerted_count = 0

        for enemy in self.game_engine.enemies:
            if enemy is alerting_enemy or enemy.state == EnemyState.HOSTILE:
                continue

            # Use grid distance for gameplay mechanics (diagonals = 1)
            distance = enemy.position.grid_distance_to(alerting_enemy.position)
            if distance <= alert_range:
                # Use consolidated hostile transition
                enemy.make_hostile(self.game_engine.player.position)
                enemy.alert_timer = 0  # Reset alert timer specifically for alert chain
                alerted_count += 1

        # Don't move alerted enemies immediately - they will move in the movement phase
        # This ensures proper phase separation: awareness -> movement -> attacks

        if alerted_count > 0:
            enemy_word = "enemy" if alerted_count == 1 else "enemies"
            self.game_engine.message_log.add_message(
                f"{alerted_count} {enemy_word} alerted nearby!"
            )
            # Only play sound once per turn to prevent stacking
            if not self._enemies_alerted_played_this_turn:
                self.game_engine.sound_manager.play_sound("enemies_alerted", priority=6)
                self._enemies_alerted_played_this_turn = True

    def _check_admin_spawn(self):
        """Check if admin avatar should spawn."""
        if (
            self.game_engine.player.trace_level >= GameConfig.MAX_TRACE_LEVEL
            and not self.game_engine.admin_spawned
            and not any(e.type == "admin" for e in self.game_engine.enemies)
        ):
            self._spawn_admin_avatar()

    def _spawn_admin_avatar(self):
        """Spawn the admin avatar enemy."""
        if self.game_engine.admin_spawned:
            return

        spawn_position = self._find_admin_spawn_position()
        if spawn_position:
            admin = self.game_engine.enemy_manager.spawn_enemy(spawn_position, "admin")
            admin.state = EnemyState.HOSTILE
            admin.last_seen_player = Position(self.game_engine.player.x, self.game_engine.player.y)
            self.game_engine.admin_spawned = True

            # Track metrics
            from game_metrics import track

            track("admin_spawns")

            logging.warning("=" * 80)
            logging.warning(
                f"[ADMIN SPAWN] Admin Avatar spawned at ({spawn_position.x},{spawn_position.y})"
            )
            logging.warning(f"Level: {self.game_engine.level}, Turn: {self.game_engine.turn}")
            logging.warning(
                f"Player Trace: {self.game_engine.player.trace_level:.1f}% (triggered at 100%)"
            )
            logging.warning(
                f"Player position: ({self.game_engine.player.x},{self.game_engine.player.y})"
            )
            logging.warning("=" * 80)

            self.game_engine.message_log.add_message("*** ADMIN AVATAR SPAWNED! ***")
            self.game_engine.sound_manager.play_sound("admin_spawn", priority=8)
            # Add environmental narrative for admin spawn
            env_msg = self.game_engine.narrative_manager.trigger_admin_spawn()
            if env_msg:
                self.game_engine.message_log.add_message(env_msg)

    def _find_admin_spawn_position(self) -> Position | None:
        """Find a suitable spawn position for admin avatar near player and visible."""
        player_vision = self.game_engine.player.get_vision_range()

        # Try to spawn within player's vision range (5-10 tiles away for dramatic effect)
        for _ in range(100):
            # Generate position within player's vision range but not too close
            distance = random.randint(5, min(10, player_vision))
            angle = random.uniform(0, 2 * math.pi)  # Random angle in radians

            spawn_x = int(self.game_engine.player.x + distance * math.cos(angle))
            spawn_y = int(self.game_engine.player.y + distance * math.sin(angle))
            position = Position(spawn_x, spawn_y)

            if (
                self.game_engine.game_map.is_valid_position(position)
                and position.distance_to(self.game_engine.player.position)
                >= 5  # Not too close to player
                and position.distance_to(self.game_engine.player.position)
                <= player_vision  # Within sight
                and self.game_engine.game_map.has_line_of_sight(
                    self.game_engine.player.position, position
                )  # Actually visible
                and not self.game_engine._get_enemy_at(position)
                and (spawn_x, spawn_y) not in self.game_engine.game_map.code_hacks
                and (spawn_x, spawn_y) not in self.game_engine.game_map.cooling_nodes
                and (spawn_x, spawn_y) not in self.game_engine.game_map.cpu_recovery_nodes
            ):
                return position

        # Fallback: try positions just within vision range if ideal spots don't work
        for _ in range(50):
            distance = player_vision - 1  # Just within vision
            angle = random.uniform(0, 2 * math.pi)

            x = int(self.game_engine.player.x + distance * math.cos(angle))
            y = int(self.game_engine.player.y + distance * math.sin(angle))
            position = Position(x, y)

            if self.game_engine.game_map.is_valid_position(
                position
            ) and not self.game_engine._get_enemy_at(position):
                return position

        # Last resort fallback position
        fallback = Position(GameConfig.MAP_WIDTH - 10, GameConfig.MAP_HEIGHT - 10)
        if self.game_engine.game_map.is_valid_position(fallback):
            return fallback

        # Check hard-coded fallback before returning
        last_resort = Position(40, 40)
        if self.game_engine.game_map.is_valid_position(last_resort):
            return last_resort

        # No valid position found - admin won't spawn
        return None

