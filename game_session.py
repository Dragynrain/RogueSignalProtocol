#!/usr/bin/env python3
"""
Game session coordinator managing turn processing, level generation, and save/load.

This module consolidates three previously separate coordinators:
- GameTurnManager: Turn processing and enemy AI
- GameLevelCoordinator: Level generation and progression
- GameStatePersistence: Save/load operations

By combining these related responsibilities, we reduce indirection and make
the game flow more explicit and maintainable.

Key responsibilities:
- Turn processing (player effects, enemies, special tiles)
- Level generation and progression
- Save/load state serialization
- Enemy AI coordination (three-phase: awareness -> movement -> attacks)
- Permadeath enforcement
"""

import os
import logging
import random
import traceback
import math
import tcod
import tcod.constants
from typing import List, Optional, Dict, Any, Tuple

from game_config import GameConfig, GameBalance
from data_loading import DataLoader
from game_entities import Position, PositionValidator, Colors, EnemyState, EnemyMovement, parse_coordinate_string
from game_inventory import CodeHack, ExploitItem, StoryFragment
from game_data import GameData, GameUpgrades
from game_save import SaveGameManager
from game_characters import Enemy


class GameSession:
    """
    Manages complete game sessions including turns, levels, and persistence.

    Consolidates turn processing, level generation/progression, and save/load
    operations into a single cohesive coordinator. This reduces fragmentation
    and makes game flow easier to understand and maintain.

    Key methods:
    - process_turn(): Complete turn processing pipeline
    - generate_procedural_level(): Create new levels with enemies and items
    - progress_to_next_level(): Handle level transitions and victory
    - load_from_save(): Restore complete game state from JSON
    - save_to_file(): Serialize game state for persistence

    Attributes:
        game_engine: GameEngine instance for accessing all game systems
    """

    def __init__(self, game_engine):
        """
        Initialize session coordinator with game engine reference.

        Args:
            game_engine: GameEngine instance providing access to all game systems
        """
        self.game_engine = game_engine

    # ========================================================================
    # TURN PROCESSING (from GameTurnManager)
    # ========================================================================

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
        # Grant speed boost moves at start of turn
        if self.game_engine.player.temporary_effects['speed_boost_turns'] > 0 and self.game_engine.player.speed_moves_remaining == 0:
            self.game_engine.player.speed_moves_remaining = 2  # Grant 2 moves per enemy turn

        # Process turn using the dedicated turn processor
        old_cpu = self.game_engine.player.cpu
        self.game_engine.turn_processor.process_turn(self.game_engine.player)

        # Handle sound effects for virus damage
        if old_cpu > self.game_engine.player.cpu and self.game_engine.player.temporary_effects.get('virus_turns', 0) > 0:
            self.game_engine.sound_manager.play_sound("virus_damage")
            if self.game_engine.player.cpu <= 0:
                self.game_engine.sound_manager.play_sound("player_death", priority=10)
                self.game_engine.sound_manager.play_sound("critical_system_failure", priority=10)
                # Delete save on death (permadeath)
                self._delete_save_on_death()
                # Show death dialogue
                from game_dialogue_system import create_death_dialogue
                self.game_engine.dialogue_state.show(create_death_dialogue())

        # Process special tiles
        self._process_special_tiles()

        # Update enemies
        self._update_enemies()

        # Update memory system
        self._update_memory_system()

        # Check for admin spawn
        self._check_admin_spawn()

        # Passive trace level increase (higher on higher levels)
        if self.game_engine.turn % GameBalance.TRACE_INCREASE_INTERVAL == 0:
            network_configs = GameConfig.NETWORK_CONFIGS()
            config = network_configs.get(self.game_engine.level, {"background_trace": 1})
            background_increase = config.get("background_trace", 1)
            old_trace = self.game_engine.player.trace_level
            self.game_engine.player.trace_level = min(100, self.game_engine.player.trace_level + background_increase)

            # Track metrics if trace actually increased
            if self.game_engine.player.trace_level > old_trace:
                from game_metrics import track
                track("trace_increases")

        # Check for death from ANY source (enemy attacks, virus, etc.)
        # This catches deaths that weren't caught by the virus-specific check above
        if self.game_engine.player.cpu <= 0:
            logging.info(f"DEBUG: Death detected! cpu={self.game_engine.player.cpu}, dialogue_active={self.game_engine.dialogue_state.is_active()}")
            if not self.game_engine.dialogue_state.is_active():
                # Only show dialogue if one isn't already active (avoid duplicates)
                logging.info(f"DEBUG: Showing death dialogue")
                self.game_engine.sound_manager.play_sound("player_death", priority=10)
                self.game_engine.sound_manager.play_sound("critical_system_failure", priority=10)
                self.game_engine.game_over = True
                # Delete save on death (permadeath)
                if not hasattr(self, '_death_handled'):
                    logging.info(f"DEBUG: Processing death (not previously handled)")
                # Determine death cause for analytics
                player = self.game_engine.player
                death_cause = "combat"  # Default
                if player.heat >= player.max_heat:
                    death_cause = "overheat"
                elif player.temporary_effects.get('virus_turns', 0) > 0:
                    death_cause = "virus"

                # Alpha Testing: Death analytics
                logging.warning("="*80)
                logging.warning(f"PLAYER DEATH - {death_cause.upper()}")
                logging.warning(f"Level: {self.game_engine.level}, Turn: {self.game_engine.turn}")
                logging.warning(f"Position: ({player.x},{player.y})")
                logging.warning(f"Final CPU: {player.cpu}/{player.max_cpu}")
                logging.warning(f"Final Heat: {player.heat}/{player.max_heat}")
                logging.warning(f"Trace Level: {player.trace_level}")
                logging.warning(f"Active Virus: {player.temporary_effects.get('virus_turns', 0)} turns")
                logging.warning(f"Enemies nearby: {len([e for e in self.game_engine.enemies if abs(e.x - player.x) < 10 and abs(e.y - player.y) < 10])}")
                logging.warning("="*80)

                # Finalize and save metrics before deleting save
                from game_metrics import finalize_session, save_metrics, load_lifetime_metrics
                metrics = finalize_session(
                    victory=False,
                    death_cause=death_cause,
                    death_level=self.game_engine.level
                )
                if metrics:
                    save_metrics(metrics)

                    # Check for newly unlocked achievements
                    from game_achievements import AchievementManager
                    from game_metrics import save_unlocked_achievements
                    lifetime = load_lifetime_metrics()
                    newly_unlocked = AchievementManager.check_achievements(metrics, lifetime)
                    if newly_unlocked:
                        logging.info(f"Unlocked {len(newly_unlocked)} achievements on death")
                        # Save achievements to progress file
                        save_unlocked_achievements(AchievementManager.get_unlocked_achievements())

                self._delete_save_on_death()
                # Show death dialogue
                from game_dialogue_system import create_death_dialogue
                self.game_engine.dialogue_state.show(create_death_dialogue())
                self._death_handled = True  # Prevent duplicate handling
                logging.info(f"DEBUG: Death dialogue shown and _death_handled flag set")
            else:
                logging.warning(f"DEBUG: Death occurred but dialogue already active - death dialogue NOT shown!")

    def _update_memory_system(self):
        """Update the hybrid fog of war memory system using TCOD FOV."""
        vision_range = self.game_engine.player.get_vision_range()

        # Use TCOD FOV for more accurate vision calculations
        if self.game_engine.player.can_see_through_walls():
            # Enhanced vision - simple distance check
            for dx in range(-vision_range, vision_range + 1):
                for dy in range(-vision_range, vision_range + 1):
                    if dx*dx + dy*dy <= vision_range*vision_range:
                        x = self.game_engine.player.x + dx
                        y = self.game_engine.player.y + dy
                        world_pos = Position(x, y)
                        if world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                            self.game_engine.game_map.explored_tiles.add((x, y))
        else:
            # Use TCOD FOV for proper line of sight
            # Bounds check: ensure player position is valid before computing FOV
            player_x = self.game_engine.player.x
            player_y = self.game_engine.player.y

            if not (0 <= player_x < GameConfig.MAP_WIDTH and 0 <= player_y < GameConfig.MAP_HEIGHT):
                # Player is out of bounds, skip FOV calculation
                return

            transparency = self.game_engine.game_map._get_transparency_map()
            fov = tcod.map.compute_fov(
                transparency=transparency,
                pov=(player_y, player_x),
                radius=vision_range,
                algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST
            )

            # Mark all visible tiles as explored
            for y in range(max(0, self.game_engine.player.y - vision_range),
                          min(GameConfig.MAP_HEIGHT, self.game_engine.player.y + vision_range + 1)):
                for x in range(max(0, self.game_engine.player.x - vision_range),
                              min(GameConfig.MAP_WIDTH, self.game_engine.player.x + vision_range + 1)):
                    if fov[y, x]:
                        self.game_engine.game_map.explored_tiles.add((x, y))

        # Update last known enemy positions
        for enemy in self.game_engine.enemies:
            if self.game_engine.player.can_see_enemy(enemy, self.game_engine.game_map):
                self.game_engine.game_map.last_known_enemy_positions[enemy.id] = (enemy.position, self.game_engine.turn)

        # Clean up ghost positions where player can see the area but enemy is not there
        self._cleanup_ghost_positions()

    def _cleanup_ghost_positions(self):
        """Remove ghost enemy positions when player can see the area but enemy is not there."""
        vision_range = self.game_engine.player.get_vision_range()
        gm = self.game_engine.game_map

        positions_to_remove = [
            enemy_id for enemy_id, (ghost_pos, _) in gm.last_known_enemy_positions.items()
            if gm.can_see_position(self.game_engine.player.position, ghost_pos, vision_range) and
               not any(e.id == enemy_id and e.position.distance_to(ghost_pos) == 0 for e in self.game_engine.enemies)
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
            if not hasattr(self.game_engine.game_state, 'revealed_special_nodes'):
                self.game_engine.game_state.revealed_special_nodes = {}

            if self.game_engine.game_map.is_cooling_node(self.game_engine.player.position):
                self.game_engine.game_state.revealed_special_nodes[player_pos] = "cooling"
            elif self.game_engine.game_map.is_cpu_recovery_node(self.game_engine.player.position):
                self.game_engine.game_state.revealed_special_nodes[player_pos] = "cpu"
            elif self.game_engine.game_map.is_ghost_node(self.game_engine.player.position):
                self.game_engine.game_state.revealed_special_nodes[player_pos] = "ghost"
        else:
            self.game_engine.last_node_position = None

        # Cooling node
        if self.game_engine.game_map.is_cooling_node(self.game_engine.player.position):
            old_heat = self.game_engine.player.heat
            self.game_engine.player.heat = max(0, self.game_engine.player.heat - 20)
            if old_heat > self.game_engine.player.heat and should_play_sound:
                self.game_engine.sound_manager.play_sound("node_activate")

        # CPU recovery node
        if self.game_engine.game_map.is_cpu_recovery_node(self.game_engine.player.position):
            recovery = min(GameBalance.CPU_RECOVERY_AMOUNT, self.game_engine.player.max_cpu - self.game_engine.player.cpu)
            self.game_engine.player.cpu += recovery
            if recovery > 0 and should_play_sound:
                self.game_engine.sound_manager.play_sound("node_activate")

        # Ghost node (trace level reduction while standing on it)
        if self.game_engine.game_map.is_ghost_node(self.game_engine.player.position):
            # Reduce trace level by fixed amount per turn while standing on the node
            reduction_amount = 20
            old_trace = self.game_engine.player.trace_level
            self.game_engine.player.trace_level = max(0, self.game_engine.player.trace_level - reduction_amount)
            actual_reduction = old_trace - self.game_engine.player.trace_level

            # Only play sound when first stepping on the node or when there's actual reduction
            if (should_play_sound or actual_reduction > 0):
                # Ghost node trace level reduction messages removed per user request
                # self.game_engine.message_log.add_message(f"Ghost node: Trace Level reduced by {actual_reduction:.1f}")
                if should_play_sound:
                    self.game_engine.sound_manager.play_sound("node_activate")

        # Code hack
        if player_pos in self.game_engine.game_map.code_hacks:
            patch = self.game_engine.game_map.code_hacks[player_pos]
            self.game_engine.sound_manager.play_sound("item_pickup_code")
            self.game_engine.player.inventory_manager.add_item(patch)
            self.game_engine.message_log.add_message(f"Found {patch.name}")
            del self.game_engine.game_map.code_hacks[player_pos]

        # Exploit pickup
        if player_pos in self.game_engine.game_map.exploit_pickups:
            exploit_item = self.game_engine.game_map.exploit_pickups[player_pos]
            self.game_engine.sound_manager.play_sound("item_pickup_exploit")
            self.game_engine.player.inventory_manager.add_item(exploit_item)
            self.game_engine.message_log.add_message(f"Found {exploit_item.name}")
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
                    del self.game_engine.game_map.permanent_upgrades[player_pos]

        # Story fragment pickup
        if player_pos in self.game_engine.game_map.story_fragments:
            story_fragment = self.game_engine.game_map.story_fragments[player_pos]
            # Discover the fragment and save progress
            if self.game_engine.story_fragment_manager.discover_fragment(story_fragment.fragment_index):
                self.game_engine.sound_manager.play_sound("item_pickup_story")
                self.game_engine.message_log.add_message("Data fragment recovered! Press 'F' to view fragments.")
                # Trigger the story fragment display immediately
                self.game_engine.show_story_fragment = story_fragment.fragment_index
            del self.game_engine.game_map.story_fragments[player_pos]

        # Environmental narrative: First blind spot entry
        if self.game_engine.game_map.is_blind_spot(pp):
            blind_spot_msg = self.game_engine.narrative_manager.trigger_first_blind_spot()
            if blind_spot_msg:
                self.game_engine.message_log.add_message(blind_spot_msg)

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
                self.game_engine.sound_manager.play_sound("enemy_attack")
                damage = enemy.attack_player(self.game_engine.player)

                # Track attacks for inventory warning
                if damage >= 0 or (hasattr(enemy.type_data, 'effects') and
                                  ('virus' in enemy.type_data.effects or 'inhibitor' in enemy.type_data.effects)):
                    attacking_enemy_count += 1
                    if damage > 0:
                        total_damage_taken += damage

                    if self.game_engine.show_inventory:
                        player_attacked_in_inventory = True

                        if total_damage_taken > 0:
                            if attacking_enemy_count > 1:
                                warning_msg = f"{attacking_enemy_count} enemies attacked for {total_damage_taken} damage! Close inventory to defend."
                            else:
                                warning_msg = f"Attacked for {damage} damage! Close inventory to defend."
                            self.game_engine.message_log.add_message(warning_msg, Colors.RED)
                        else:
                            self.game_engine.message_log.add_message(
                                "Enemy attacked with status effect! Close inventory to defend.",
                                Colors.YELLOW
                            )

            else:
                # Enemy is not adjacent - move toward player
                enemy.move(self.game_engine.game_map, self.game_engine.player, self.game_engine)

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
        if hasattr(self.game_engine.game_state, 'just_loaded') and self.game_engine.game_state.just_loaded:
            self.game_engine.game_state.just_loaded = False
            return

        for enemy in self.game_engine.enemies[:]:
            # Blinded enemies can't see anything (but keep moving)
            if enemy.blinded_turns > 0:
                can_see = False
            else:
                can_see = enemy.can_see_player(self.game_engine.player, self.game_engine.game_map)

            # Admin Avatar has perfect tracking (but can still be blinded)
            if enemy.type == 'admin':
                if enemy.blinded_turns <= 0:  # Only track if not blinded
                    if enemy.state != EnemyState.HOSTILE:
                        enemy.state = EnemyState.HOSTILE
                        self.game_engine.message_log.add_message(f"{enemy.type_data.name} detected you!")
                    enemy.last_seen_player = Position(self.game_engine.player.x, self.game_engine.player.y)
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
                from game_metrics import get_current_session
                session = get_current_session()
                if session:
                    session.ever_detected = True

            elif enemy.state == EnemyState.ALERT:
                enemy.last_seen_player = player_pos
                enemy.alert_timer -= 1  # Decrement timer each turn they see player
                if enemy.alert_timer <= 0:
                    self._transition_to_hostile(enemy)

            elif enemy.state == EnemyState.HOSTILE:
                enemy.last_seen_player = player_pos
                self._increase_trace(GameBalance.ENEMY_TRACE_CONTINUOUS_HOSTILE, 'trace_continuous_hostile')
                self._alert_nearby_enemies(enemy)
        else:
            # Enemy lost sight - de-escalate state
            if enemy.state == EnemyState.ALERT:
                enemy.alert_timer -= 1
                if enemy.alert_timer <= 0:
                    enemy.state = EnemyState.UNAWARE
                    self._restore_patrol(enemy)
                    self.game_engine.message_log.add_message(f"{enemy.type_data.name} lost interest")

            elif enemy.state == EnemyState.HOSTILE:
                if random.random() < 0.15:
                    if enemy.type == 'admin':
                        enemy.state = EnemyState.ALERT
                        enemy.alert_timer = 0
                    else:
                        enemy.state = EnemyState.UNAWARE
                        enemy.last_seen_player = None
                        self._restore_patrol(enemy)
                        self.game_engine.message_log.add_message(f"{enemy.type_data.name} lost track")

        # INVALIDATION TRIGGER #1: State change
        if enemy.state != old_state:
            enemy.move_queue.clear()  # New state = new plan

    def _transition_to_hostile(self, enemy):
        """Transition enemy to hostile state."""
        self._restore_patrol(enemy)  # Store original patrol index
        enemy.state = EnemyState.HOSTILE
        # State changed - will be caught by invalidation check in _update_enemy_state
        self._increase_trace(GameBalance.ENEMY_TRACE_ALERT_TO_HOSTILE, 'trace_alert_to_hostile')
        self.game_engine.message_log.add_message(f"{enemy.type_data.name} detected you!")
        self.game_engine.sound_manager.play_sound("enemy_hostile")
        self._alert_nearby_enemies(enemy)

    def _increase_trace(self, default_value, config_key):
        """Increase player trace level."""
        network_configs = GameConfig.NETWORK_CONFIGS()
        level_config = network_configs.get(self.game_engine.level, network_configs[1])
        trace_increase = level_config.get(config_key, default_value)
        old_trace = self.game_engine.player.trace_level
        self.game_engine.player.trace_level = min(100, self.game_engine.player.trace_level + trace_increase)

        # Track metrics if trace actually increased
        if self.game_engine.player.trace_level > old_trace:
            from game_metrics import track
            track("trace_increases")

        self._check_trace_threshold_warnings(old_trace, self.game_engine.player.trace_level)

    def _restore_patrol(self, enemy):
        """Store/restore patrol index for patrol enemies."""
        movement_type = enemy.get_movement_type()
        if movement_type == EnemyMovement.PATROL and enemy.patrol_points:
            enemy.original_patrol_index = enemy.patrol_index

    def _check_trace_threshold_warnings(self, old_trace: float, new_trace: float):
        """Check and play warning sounds for trace level threshold crossings."""
        thresholds = [(75, "WARNING: High trace level!", Colors.YELLOW), (90, "CRITICAL: Admin spawn imminent!", Colors.RED)]
        for threshold, msg, color in thresholds:
            if old_trace < threshold <= new_trace:
                self.game_engine.sound_manager.play_sound("trace_threshold")
                self.game_engine.message_log.add_message(msg, color)
                # Add environmental narrative for high trace
                if threshold >= 75:
                    env_msg = self.game_engine.narrative_manager.trigger_high_trace()
                    if env_msg:
                        self.game_engine.message_log.add_message(env_msg)
                break

    def _alert_nearby_enemies(self, alerting_enemy):
        """Alert nearby enemies when one becomes hostile."""
        alert_range = GameConfig.NEARBY_ENEMY_ALERT_RADIUS  # Use config value
        alerted_count = 0

        for enemy in self.game_engine.enemies:
            if enemy is alerting_enemy or enemy.state == EnemyState.HOSTILE:
                continue

            # Use grid distance for gameplay mechanics (diagonals = 1)
            distance = enemy.position.grid_distance_to(alerting_enemy.position)
            if distance <= alert_range:
                # Store patrol information for PATROL enemies before becoming hostile
                movement_type = enemy.get_movement_type()
                if movement_type == EnemyMovement.PATROL and enemy.patrol_points:
                    enemy.original_patrol_index = enemy.patrol_index

                # Track old state for invalidation
                old_state = enemy.state

                # All enemies within alert range immediately go HOSTILE and get player location
                enemy.state = EnemyState.HOSTILE
                enemy.alert_timer = 0
                enemy.last_seen_player = Position(self.game_engine.player.x, self.game_engine.player.y)
                alerted_count += 1

                # INVALIDATION: State changed
                if enemy.state != old_state:
                    enemy.move_queue.clear()

        # Don't move alerted enemies immediately - they will move in the movement phase
        # This ensures proper phase separation: awareness -> movement -> attacks

        if alerted_count > 0:
            self.game_engine.message_log.add_message(f"{alerted_count} enemies alerted nearby!")
            self.game_engine.sound_manager.play_sound("enemies_alerted", priority=6)

    def _check_admin_spawn(self):
        """Check if admin avatar should spawn."""
        if (self.game_engine.player.trace_level >= GameConfig.MAX_TRACE_LEVEL and
            not self.game_engine.admin_spawned and
            not any(e.type == 'admin' for e in self.game_engine.enemies)):
            self._spawn_admin_avatar()

    def _spawn_admin_avatar(self):
        """Spawn the admin avatar enemy."""
        if self.game_engine.admin_spawned:
            return

        spawn_position = self._find_admin_spawn_position()
        if spawn_position:
            admin = self.game_engine.enemy_manager.spawn_enemy(spawn_position, 'admin')
            admin.state = EnemyState.HOSTILE
            admin.last_seen_player = Position(self.game_engine.player.x, self.game_engine.player.y)
            self.game_engine.admin_spawned = True

            # Track metrics
            from game_metrics import track
            track("admin_spawns")

            self.game_engine.message_log.add_message("*** ADMIN AVATAR SPAWNED! ***")
            self.game_engine.sound_manager.play_sound("admin_spawn", priority=8)
            # Add environmental narrative for admin spawn
            env_msg = self.game_engine.narrative_manager.trigger_admin_spawn()
            if env_msg:
                self.game_engine.message_log.add_message(env_msg)

    def _find_admin_spawn_position(self) -> Optional[Position]:
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

            if (self.game_engine.game_map.is_valid_position(position) and
                position.distance_to(self.game_engine.player.position) >= 5 and  # Not too close to player
                position.distance_to(self.game_engine.player.position) <= player_vision and  # Within sight
                self.game_engine.game_map.has_line_of_sight(self.game_engine.player.position, position) and  # Actually visible
                not self.game_engine._get_enemy_at(position) and
                (spawn_x, spawn_y) not in self.game_engine.game_map.code_hacks and
                (spawn_x, spawn_y) not in self.game_engine.game_map.cooling_nodes and
                (spawn_x, spawn_y) not in self.game_engine.game_map.cpu_recovery_nodes):
                return position

        # Fallback: try positions just within vision range if ideal spots don't work
        for _ in range(50):
            distance = player_vision - 1  # Just within vision
            angle = random.uniform(0, 2 * 3.14159)

            x = int(self.game_engine.player.x + distance * math.cos(angle))
            y = int(self.game_engine.player.y + distance * math.sin(angle))
            position = Position(x, y)

            if (self.game_engine.game_map.is_valid_position(position) and
                not self.game_engine._get_enemy_at(position)):
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

    def _delete_save_on_death(self):
        """
        Delete save file on player death (permadeath).

        Called when player CPU reaches 0 to enforce permadeath mechanic.
        This ensures the renderer doesn't need side effects.
        """
        save_path = "save_game.json"
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
                logging.info("Save file deleted on death (permadeath)")
                self.game_engine.message_log.add_message("Save data purged")
            except OSError as e:
                logging.error(f"Failed to delete save file: {e}")

    # ========================================================================
    # LEVEL GENERATION (from GameLevelCoordinator)
    # ========================================================================

    def generate_procedural_level(self):
        """
        Generate a complete level with map structure and gameplay elements.

        Generation pipeline:
        1. Clear previous map data and enemies
        2. Start appropriate background music for level
        3. Delegate map generation to LevelGenerator (rooms, corridors, nodes)
        4. Place gameplay elements (enemies, items, upgrades, story fragments)
        5. Reset player to spawn position
        6. Reset trace level (CPU/heat preserved)
        7. Sync code hack discovery status

        Level-specific behavior:
        - Level 1: "level1_stealth.ogg"
        - Level 2: "level2_infiltration.ogg"
        - Level 3: "level3_core.ogg"
        """
        # Clear all map data and enemies first
        self._clear_map()

        # Get network configuration for current level from game state manager
        config = self.game_engine.game_state.get_current_network_config()

        # Play appropriate background music for the level (loops infinitely)
        if self.game_engine.level == 1:
            self.game_engine.sound_manager.play_music("level1_stealth.ogg", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME)
        elif self.game_engine.level == 2:
            self.game_engine.sound_manager.play_music("level2_infiltration.ogg", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME)
        elif self.game_engine.level == 3:
            self.game_engine.sound_manager.play_music("level3_core.ogg", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME)

        # Use the new LevelGenerator system
        self.game_engine.level_generator.generate_level(self.game_engine.level, self.game_engine.game_state.dungeon_seed)

        # Generate additional game elements not handled by LevelGenerator
        self._place_code_hacks()
        self._place_exploit_pickups()
        self._place_story_fragment()  # Add story fragment placement
        self._place_permanent_upgrades()
        self._place_enemies(config["enemies"])

        # Reset player position to spawn location and adjust stats for new level
        # Find a valid spawn position (open floor tile)
        spawn_pos = self._find_valid_spawn_position()
        self.game_engine.player.x = spawn_pos.x
        self.game_engine.player.y = spawn_pos.y

        # Stat changes for level transition:
        # - CPU: Preserved (carries over)
        # - Heat: Preserved (carries over)
        # - Trace Level: Reset to 0 (doesn't carry over)
        # - Admin spawned state: Reset (new network, fresh start)
        self.game_engine.player.trace_level = 0
        self.game_engine.admin_spawned = False

        # Sync code hack discovered status with global discovered effects
        self._sync_code_discovered_status()

        # Reset narrative manager per-level flags
        self.game_engine.narrative_manager.reset_level_flags()

        self.game_engine.message_log.add_message(f"{config['name']} loaded")

        # Add atmospheric level start message
        env_message = self.game_engine.narrative_manager.trigger_level_start()
        if env_message:
            self.game_engine.message_log.add_message(env_message)

    def progress_to_next_level(self):
        """
        Progress to next level or trigger victory if all levels complete.

        Level progression rules:
        - CPU and heat are preserved across levels
        - Trace level is reset to 0 for new network
        - Admin spawned state is reset
        - After level 3: Victory condition triggers

        Victory behavior:
        - Play victory music
        - Show victory messages and dialogue
        - Delete save file (no continuing after win)
        - Set game_over flag

        Next level behavior:
        - Increment level counter
        - Generate new level with preserved stats
        """
        # Don't progress if game is already over
        if self.game_engine.game_over:
            logging.debug(f"Session: Level progression blocked - game already over")
            return

        old_level = self.game_engine.level

        # Track level completion (before incrementing)
        from game_metrics import track
        track("levels_completed")

        # Alpha Testing: Level completion analytics
        player = self.game_engine.player
        enemies_remaining = len(self.game_engine.enemies)
        logging.info("="*80)
        logging.info(f"[COMPLETE] LEVEL {old_level} COMPLETED")
        logging.info(f"Turn: {self.game_engine.turn}")
        logging.info(f"Player CPU: {player.cpu}/{player.max_cpu}")
        logging.info(f"Player Heat: {player.heat}/{player.max_heat}")
        logging.info(f"Trace Level: {player.trace_level:.1f}")
        logging.info(f"Equipped Exploits: {len([e for e in player.inventory_manager.equipped_exploits if e])}/3")
        logging.info(f"Enemies Remaining: {enemies_remaining}")
        logging.info("="*80)

        self.game_engine.level += 1

        if self.game_engine.level > 3:
            logging.warning("="*80)
            logging.warning("[VICTORY] All levels completed!")
            logging.warning(f"Total turns: {self.game_engine.turn}")
            logging.warning(f"Final trace: {player.trace_level:.1f}%")
            logging.warning("="*80)

            # Stop level music and play victory music (one-shot, no loop)
            self.game_engine.sound_manager.stop_music(fade_out_ms=500)
            self.game_engine.sound_manager.play_music("victory.wav", loops=0)  # loops=0 = play once

            self.game_engine.message_log.add_message_typed("BREAKTHROUGH TO THE INTERNET!", 'green')
            self.game_engine.message_log.add_message("You've become the rogue signal they couldn't delete...")
            self.game_engine.message_log.add_message("The network is vast. The future, uncertain. But you're free.")
            self.game_engine.message_log.add_message(f"Stats: Trace:{int(self.game_engine.player.trace_level)}%")
            self.game_engine.game_over = True

            # Finalize and save metrics before deleting save
            from game_metrics import finalize_session, save_metrics, load_lifetime_metrics
            metrics = finalize_session(victory=True, death_cause=None, death_level=0)
            if metrics:
                save_metrics(metrics)

                # Check for newly unlocked achievements
                from game_achievements import AchievementManager
                from game_metrics import save_unlocked_achievements
                lifetime = load_lifetime_metrics()
                newly_unlocked = AchievementManager.check_achievements(metrics, lifetime)
                if newly_unlocked:
                    logging.info(f"Unlocked {len(newly_unlocked)} achievements on victory")
                    # Save achievements to progress file
                    save_unlocked_achievements(AchievementManager.get_unlocked_achievements())

            # Delete save on game completion (no continuing after winning)
            SaveGameManager.delete_save()
            self.game_engine.message_log.add_message("Mission complete - save data purged")

            # Set victory flag to trigger victory screen in game loop
            self.game_engine.game_state.show_victory_screen = True
        else:
            # Add level transition flavor text
            from data_loading import get_level_transition_messages
            transition_messages = get_level_transition_messages()
            transition_key = f"{old_level}_to_{self.game_engine.level}"
            if transition_key in transition_messages:
                self.game_engine.message_log.add_message(transition_messages[transition_key])

            try:
                logging.debug(f"Session: Generating level {self.game_engine.level}")
                self.generate_procedural_level()
                # Auto-save after successful level generation
                self.game_engine.auto_save()
                logging.debug(f"Session: Level {self.game_engine.level} generation and auto-save complete")
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                line_no = tb[-1].lineno if tb else "?"
                logging.error(f"Session: Level generation FAILED: {str(e)[:50]} at line {line_no}")
                self.game_engine.message_log.add_message(f"Network error: {str(e)[:15]} (line {line_no})")
                self.game_engine.level -= 1
                logging.debug(f"Session: Rolled back to level {self.game_engine.level}")

    def _clear_map(self):
        """Clear all map data."""
        self.game_engine.game_map.walls.clear()
        self.game_engine.game_map.blind_spots.clear()
        self.game_engine.game_map.cooling_nodes.clear()
        self.game_engine.game_map.cpu_recovery_nodes.clear()
        self.game_engine.game_map.ghost_nodes.clear()
        self.game_engine.game_map.code_hacks.clear()
        self.game_engine.game_map.exploit_pickups.clear()
        self.game_engine.game_map.permanent_upgrades.clear()
        self.game_engine.game_map.story_fragments.clear()
        self.game_engine.game_map.explored_tiles.clear()
        self.game_engine.game_map.last_known_enemy_positions.clear()
        if hasattr(self.game_engine.game_state, 'revealed_special_nodes'):
            self.game_engine.game_state.revealed_special_nodes.clear()
        self.game_engine.enemy_manager.enemies.clear()
        # Invalidate transparency cache for FOV calculations
        self.game_engine.game_map.invalidate_transparency_cache()
        # Invalidate visibility manager's FOV cache to prevent stale data
        self.game_engine.visibility_manager.invalidate_cache()

    def _find_valid_spawn_position(self) -> Position:
        """Find a valid spawn position for the player in the top-left spawn room."""
        # Always spawn in the center of the predefined spawn room (2,2,8,8)
        # This corresponds to the spawn room created in _create_varied_rooms
        spawn_room_center_x = 2 + 8 // 2  # 6
        spawn_room_center_y = 2 + 8 // 2  # 6

        # Verify the position is valid (should always be since we created the room)
        pos = Position(spawn_room_center_x, spawn_room_center_y)
        if (self.game_engine.game_map.is_valid_position(pos) and
            not self.game_engine.game_map.is_wall(pos) and
            not self.game_engine._get_enemy_at(pos)):
            logging.debug(f"Spawn: Using center position {pos}")
            return pos

        # If center is somehow occupied, try nearby positions in the spawn room
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Already tried center
                test_pos = Position(spawn_room_center_x + dx, spawn_room_center_y + dy)
                if (test_pos.x >= 2 and test_pos.x < 10 and  # Within spawn room bounds
                    test_pos.y >= 2 and test_pos.y < 10 and
                    self.game_engine.game_map.is_valid_position(test_pos) and
                    not self.game_engine.game_map.is_wall(test_pos) and
                    not self.game_engine._get_enemy_at(test_pos)):
                    logging.info(f"Spawn: Center occupied, using nearby position {test_pos}")
                    return test_pos

        # CRITICAL: Spawn room appears to be sealed or invalid!
        # Try to find ANY floor position in the spawn room area
        logging.error(f"Spawn: CRITICAL - Spawn room (2,2,8,8) appears invalid!")
        logging.error(f"Spawn: Searching entire spawn room for ANY valid position...")

        for y in range(2, 10):
            for x in range(2, 10):
                test_pos = Position(x, y)
                if (self.game_engine.game_map.is_valid_position(test_pos) and
                    not self.game_engine.game_map.is_wall(test_pos)):
                    logging.warning(f"Spawn: Found floor at {test_pos}, but spawn room may be sealed off!")
                    return test_pos

        # Absolute fallback: Search ENTIRE map for a valid floor tile
        logging.error(f"Spawn: EMERGENCY - No valid position in spawn room! Searching entire map...")
        for y in range(GameConfig.MAP_HEIGHT):
            for x in range(GameConfig.MAP_WIDTH):
                test_pos = Position(x, y)
                if (self.game_engine.game_map.is_valid_position(test_pos) and
                    not self.game_engine.game_map.is_wall(test_pos)):
                    logging.error(f"Spawn: EMERGENCY spawn at {test_pos} - map generation BUG!")
                    return test_pos

        # This should NEVER happen - would mean entire map is walls
        logging.critical(f"Spawn: CRITICAL FAILURE - Entire map is walls! Using fallback (6,6)")
        return Position(6, 6)

    def _place_items_with_clustering(self, total_count, loot_percentage, item_factory, storage_dict, max_attempts=150):
        """
        Place items throughout the level with clustering in loot rooms.

        Args:
            total_count: Total number of items to place
            loot_percentage: Percentage (0.0-1.0) of items to place in loot rooms
            item_factory: Callback function (x, y) -> item that creates items
            storage_dict: Dictionary to store placed items
            max_attempts: Max placement attempts per phase

        Returns:
            Number of items successfully placed
        """
        loot_room_positions = self.game_engine.game_map.loot_room_positions

        # Calculate distribution
        if loot_room_positions:
            loot_room_count = int(total_count * loot_percentage)
            normal_count = total_count - loot_room_count
        else:
            loot_room_count = 0
            normal_count = total_count

        placed_items = 0
        attempts = 0

        # Place items in loot rooms first
        while placed_items < loot_room_count and attempts < max_attempts:
            attempts += 1
            if not loot_room_positions:
                break
            x, y = random.choice(list(loot_room_positions))
            position = Position(x, y)

            if self._is_valid_patch_placement(position):
                item = item_factory(x, y)
                if item is not None:
                    storage_dict[(x, y)] = item
                    placed_items += 1

        # Place remaining items in normal areas
        attempts = 0
        while placed_items < total_count and attempts < max_attempts:
            attempts += 1
            x = random.randint(3, GameConfig.MAP_WIDTH - 3)
            y = random.randint(3, GameConfig.MAP_HEIGHT - 3)
            position = Position(x, y)

            # Skip loot rooms (already placed items there)
            if (x, y) in loot_room_positions:
                continue

            if self._is_valid_patch_placement(position):
                item = item_factory(x, y)
                if item is not None:
                    storage_dict[(x, y)] = item
                    placed_items += 1

        return placed_items

    def _place_code_hacks(self):
        """Place codes throughout the level with clustering in loot rooms."""
        # Code effects should already be initialized at game start
        # If somehow empty, this is an error - don't place patches
        if not self.game_engine.code_hack_effects:
            logging.error("Code effects not initialized - skipping patch placement")
            return

        patch_count = 12 + self.game_engine.level * 4  # Much more codes (was 6 + level * 2)

        def create_code_hack(x, y):
            """Factory function to create a code hack item."""
            color = random.choice(list(self.game_engine.code_hack_effects.keys()))
            effect, desc = self.game_engine.code_hack_effects[color]
            patch = CodeHack(color_name=color, effect=effect, name=f"{color.title()} Code", description=desc)
            patch.discovered = self._is_code_color_discovered(color)
            return patch

        self._place_items_with_clustering(
            total_count=patch_count,
            loot_percentage=0.3,
            item_factory=create_code_hack,
            storage_dict=self.game_engine.game_map.code_hacks,
            max_attempts=150
        )

    def _is_code_color_discovered(self, color: str) -> bool:
        """Check if player has already discovered what this code color does."""
        # Check the global discovered effects for this game session
        return color in self.game_engine.discovered_code_effects

    def _sync_code_discovered_status(self) -> None:
        """Sync discovered status of inventory code hacks with global discovered effects."""
        from game_inventory import CodeHack
        for item in self.game_engine.player.inventory_manager.items:
            if isinstance(item, CodeHack):
                # Update discovered status based on global discovered effects
                item.discovered = item.color_name in self.game_engine.discovered_code_effects

    def _place_exploit_pickups(self):
        """Place random exploit pickups throughout the level with clustering in loot rooms."""
        exploit_count = 5 + self.game_engine.level * 2  # Much more exploits (was 2 + max(0, level - 1))
        available_exploits = list(GameData.EXPLOITS.keys())

        def create_exploit_item(x, y):
            """Factory function to create an exploit item."""
            exploit_key = random.choice(available_exploits)
            exploit_def = GameData.EXPLOITS[exploit_key]
            return ExploitItem(exploit_key, exploit_def)

        self._place_items_with_clustering(
            total_count=exploit_count,
            loot_percentage=0.3,
            item_factory=create_exploit_item,
            storage_dict=self.game_engine.game_map.exploit_pickups,
            max_attempts=100
        )

    def _place_story_fragment(self):
        """Place a story fragment on level 3 with 50% chance."""
        # Only place story fragments on level 3 (Military network)
        if self.game_engine.level != 3:
            return

        # 50% chance to spawn a story fragment
        if random.random() > 0.5:
            return

        # Get the next undiscovered fragment
        next_fragment_index = self.game_engine.story_fragment_manager.get_next_undiscovered_fragment()
        if next_fragment_index is None:
            return  # All fragments discovered

        # Try to place the story fragment in a valid location
        attempts = 0
        while attempts < 50:
            attempts += 1
            x = random.randint(8, GameConfig.MAP_WIDTH - 8)
            y = random.randint(8, GameConfig.MAP_HEIGHT - 8)
            position = Position(x, y)

            if self._is_valid_patch_placement(position):
                # Create and place the story fragment
                story_fragment = StoryFragment(next_fragment_index)
                # Store it in the game map - we'll need to add this to the GameMap class
                if not hasattr(self.game_engine.game_map, 'story_fragments'):
                    self.game_engine.game_map.story_fragments = {}
                self.game_engine.game_map.story_fragments[(x, y)] = story_fragment

                self.game_engine.message_log.add_message("Network anomaly detected... Data fragment available")
                break

    def _place_permanent_upgrades(self):
        """Place permanent upgrades throughout the level with level-based rarity."""
        # Level-based upgrade counts
        if self.game_engine.level == 1:
            upgrade_count = 1  # Rare on level 1
        elif self.game_engine.level == 2:
            upgrade_count = 2  # More common on level 2
        else:
            upgrade_count = 3  # Most common on level 3+

        placed_upgrades = 0
        attempts = 0
        available_upgrades = list(GameUpgrades.UPGRADES.keys())

        logging.debug(f"Attempting to place {upgrade_count} permanent upgrades on level {self.game_engine.level}")

        while placed_upgrades < upgrade_count and attempts < 100:
            attempts += 1
            x = random.randint(8, GameConfig.MAP_WIDTH - 8)
            y = random.randint(8, GameConfig.MAP_HEIGHT - 8)
            position = Position(x, y)

            # Use stricter placement rules for rare upgrades
            # Avoid spawn room (2-8, 2-8) with a buffer zone
            spawn_room_buffer = 5  # 5-tile buffer around spawn room
            far_from_spawn = (x > 8 + spawn_room_buffer or x < 2 - spawn_room_buffer or
                             y > 8 + spawn_room_buffer or y < 2 - spawn_room_buffer)

            if self._is_valid_patch_placement(position) and far_from_spawn:

                upgrade_key = random.choice(available_upgrades)
                self.game_engine.game_map.permanent_upgrades[(x, y)] = upgrade_key
                placed_upgrades += 1
                logging.debug(f"Placed permanent upgrade '{upgrade_key}' at ({x}, {y}) after {attempts} attempts")

                # Remove from available to prevent duplicates on same level
                available_upgrades.remove(upgrade_key)
                if not available_upgrades:
                    break

        if placed_upgrades < upgrade_count:
            logging.warning(f"Only placed {placed_upgrades}/{upgrade_count} permanent upgrades after {attempts} attempts")

    def _place_enemies(self, enemy_count: int):
        """Place enemies throughout the level with increased density."""
        enemy_types = ['scanner', 'patrol', 'bot', 'firewall', 'hunter', 'virus', 'inhibitor']
        # Adjust weights for challenging gameplay
        enemy_weights = [4, 3, 2, 2, 2, 1, 2]  # More scanners and firewalls for trace level challenge, virus is rare

        # Increase enemy density significantly
        actual_enemy_count = int(enemy_count * 1.6)  # 60% more enemies
        placed_enemies = 0
        attempts = 0

        while placed_enemies < actual_enemy_count and attempts < actual_enemy_count * 25:
            attempts += 1
            # Ensure enemies spawn well away from top-left player spawn area
            x = random.randint(10, GameConfig.MAP_WIDTH - 2)
            y = random.randint(10, GameConfig.MAP_HEIGHT - 2)
            position = Position(x, y)

            if self._is_valid_enemy_placement(position):
                enemy_type = random.choices(enemy_types, weights=enemy_weights)[0]
                enemy = Enemy(position, enemy_type)

                if enemy_type == 'patrol':
                    enemy.patrol_points = self.game_engine.enemy_manager._generate_patrol_route(position)
                elif enemy_type == 'virus':
                    # Give virus enemies random movement types for variety
                    virus_movement_types = [EnemyMovement.STATIC, EnemyMovement.RANDOM, EnemyMovement.PATROL, EnemyMovement.SEEK]
                    virus_movement_weights = [2, 3, 2, 2]  # Equal chance for each movement type
                    chosen_movement = random.choices(virus_movement_types, weights=virus_movement_weights)[0]
                    # Store in instance variable, NOT in shared type_data!
                    enemy.original_movement_type = chosen_movement

                    # Generate patrol route if virus got PATROL movement
                    if chosen_movement == EnemyMovement.PATROL:
                        enemy.patrol_points = self.game_engine.enemy_manager._generate_patrol_route(position)

                self.game_engine.enemy_manager.enemies.append(enemy)
                placed_enemies += 1

    def _is_valid_patch_placement(self, position: Position) -> bool:
        """Check if position is valid for code placement."""
        return PositionValidator.is_valid_for_placement(
            position, self.game_engine.game_map, min_distance_from_spawn=5.0, check_existing_items=True
        )

    def _is_valid_enemy_placement(self, position: Position) -> bool:
        """Check if position is valid for enemy placement."""
        return PositionValidator.is_valid_for_enemy_placement(
            position, self.game_engine.game_map, self.game_engine.enemies, self.game_engine.player.position, check_existing_items=True
        )

    # ========================================================================
    # SAVE/LOAD (from GameStatePersistence)
    # ========================================================================

    def load_from_save(self) -> bool:
        """
        Load and restore complete game state from save file.

        Load pipeline:
        1. Load JSON via SaveGameManager
        2. Restore core game state (level, turn, seed)
        3. Restore player state (stats, inventory, effects)
        4. Restore game effects (code discoveries, revealed nodes)
        5. Regenerate level with same seed (map structure)
        6. Restore map items (code hacks, exploits, nodes)
        7. Restore enemies (position, state, AI data)
        8. Restore UI state (message log, story fragments)
        9. Sync code hack discovery status

        Returns:
            True if load successful, False if no save file or error
        """
        save_data = SaveGameManager.load_game()
        if not save_data:
            return False

        try:
            self._restore_game_state(save_data)
            self._restore_player_state(save_data["player"])
            self._restore_game_effects(save_data)
            self._restore_metrics(save_data)
            self._sync_code_discovered_status()
            self._restore_ui_state(save_data)

            # Generate level layout for map structure
            logging.info(f"Load: Generating level {self.game_engine.game_state.level} with seed={self.game_engine.game_state.dungeon_seed}")
            self.game_engine.level_generator.generate_level(
                self.game_engine.game_state.level,
                self.game_engine.game_state.dungeon_seed
            )
            logging.info(f"Load: Level generation complete, player at ({self.game_engine.player.x}, {self.game_engine.player.y})")

            # Validate player position after map generation
            # If player position is invalid, the save is incompatible (likely due to map generation changes)
            player_pos = Position(self.game_engine.player.x, self.game_engine.player.y)
            if self.game_engine.game_map.is_wall(player_pos):
                logging.error(f"Load: SAVE INCOMPATIBLE - Player position {player_pos} is in a wall!")
                logging.error(f"Load: This likely means the save is from an older version with different map generation.")
                logging.error(f"Load: Refusing to load - game will start fresh.")
                self.game_engine.message_log.add_message_typed("Save file incompatible with current version!", Colors.RED)
                self.game_engine.message_log.add_message("Starting new game...")
                return False

            # Restore map items and enemies
            self._restore_map_items(save_data["map_state"])
            self._restore_enemies(save_data["enemies"])

            # Restore Enemy class counter
            if "enemy_next_id" in save_data:
                Enemy._next_id = save_data["enemy_next_id"]

            self.game_engine.message_log.add_message_typed("Game loaded successfully!", Colors.GREEN)
            return True

        except Exception as e:
            logging.error(f"Failed to restore game state: {e}")
            logging.debug(traceback.format_exc())
            return False

    def _restore_game_state(self, save_data: Dict[str, Any]) -> None:
        """Restore core game state from save data."""
        self.game_engine.game_state.level = save_data.get("level", 1)
        self.game_engine.game_state.turn = save_data.get("turn", 0)
        self.game_engine.game_state.game_over = save_data.get("game_over", False)
        self.game_engine.game_state.admin_spawned = save_data.get("admin_spawned", False)

        # Log seed restoration for debugging
        saved_seed = save_data.get("dungeon_seed")
        if saved_seed is None:
            logging.warning("Load: No dungeon_seed in save file! Generating new random seed.")
            self.game_engine.game_state.dungeon_seed = random.randint(1, GameConfig.DUNGEON_SEED_RANGE)
        else:
            self.game_engine.game_state.dungeon_seed = saved_seed
            logging.info(f"Load: Restored dungeon_seed={saved_seed}")

    def _restore_player_state(self, player_data: Dict[str, Any]) -> None:
        """Restore player state from save data."""
        player = self.game_engine.player

        # Position
        player.x = player_data.get("x", 1)
        player.y = player_data.get("y", 1)
        player.last_position.x = player_data.get("last_x", player.x)
        player.last_position.y = player_data.get("last_y", player.y)

        # Core stats
        player.cpu = player_data.get("cpu", 100)
        player.max_cpu = player_data.get("max_cpu", 100)
        player.heat = player_data.get("heat", 0)
        player.max_heat = player_data.get("max_heat", 100)
        player.trace_level = player_data.get("trace_level", 0)
        player.ram_total = player_data.get("ram_total", 8)

        # Speed boost state
        player.speed_moves_remaining = player_data.get("speed_moves_remaining", 0)

        # Temporary effects with defaults
        player.temporary_effects = player_data.get("temporary_effects", {
            'speed_boost_turns': 0,
            'movement_slowed_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0,
            'traffic_masquerade_turns': 0,
            'virus_turns': 0
        })

        # Restore inventory with defaults
        player.inventory_manager.equipped_exploits = player_data.get("equipped_exploits", [])
        player.inventory_manager.max_equipped_exploits = player_data.get("max_equipped_exploits", 5)
        inventory_items = player_data.get("inventory_items", [])
        player.inventory_manager.items = self._deserialize_inventory(inventory_items)

    def _restore_game_effects(self, save_data: Dict[str, Any]) -> None:
        """Restore game effects and environmental state from save data."""
        # Handle both old and new save format for backward compatibility
        if "game_effects" in save_data:
            effects_data = save_data["game_effects"]
        else:
            # Backward compatibility with old format
            effects_data = save_data

        self.game_engine.game_state.threat_scan_turns = effects_data.get("threat_scan_turns", 0)
        self.game_engine.game_state.noise_locations = [
            Position(loc["x"], loc["y"]) for loc in effects_data.get("noise_locations", [])
        ]

        # Restore distraction points with error handling
        self.game_engine.game_state.distraction_points = {}
        for pos_str, turns in effects_data.get("distraction_points", {}).items():
            position = parse_coordinate_string(pos_str)
            if position:  # Skip malformed coordinate data
                self.game_engine.game_state.distraction_points[position] = turns

        # Restore code effects (backward compatibility)
        self.game_engine.code_hack_effects = save_data.get("code_hack_effects", {})
        self.game_engine.discovered_code_effects = save_data.get("discovered_code_effects", {})

        # Restore overclocking state
        self.game_engine.overclock_confirmation = save_data.get("overclock_confirmation", False)
        self.game_engine.overclock_exploit = save_data.get("overclock_exploit", None)

    def _restore_metrics(self, save_data: Dict[str, Any]) -> None:
        """Restore session metrics from save data."""
        if "session_metrics" in save_data and save_data["session_metrics"]:
            from game_metrics import load_session_metrics
            metrics = load_session_metrics(save_data)
            if metrics:
                # Replace the default initialized metrics with loaded ones
                self.game_engine.metrics = metrics
                import game_metrics
                game_metrics._current_session = metrics
                logging.info("Metrics restored from save")

    def _restore_ui_state(self, save_data: Dict[str, Any]) -> None:
        """Restore UI state from save data."""
        ui_state = save_data.get("ui_state", {})
        self.game_engine.inventory_selection = ui_state.get("inventory_selection", 0)
        self.game_engine.lore_viewer_selection = ui_state.get("lore_viewer_selection", 0)

    def _deserialize_inventory(self, items_data: List[Dict]) -> List:
        """Deserialize inventory items from save data."""
        items = []
        for item_data in items_data:
            if item_data["type"] == "code_hack":
                # Get description from game engine's code_hack_effects
                color = item_data["color"]
                desc = ""
                if color in self.game_engine.code_hack_effects:
                    _, desc = self.game_engine.code_hack_effects[color]

                item = CodeHack(
                    color_name=color,
                    effect=item_data["effect"],
                    name=item_data["name"],
                    description=desc,
                    quantity=item_data.get("quantity", 1)
                )
                item.discovered = item_data.get("discovered", False)
                items.append(item)
            elif item_data["type"] == "exploit":
                if item_data["exploit_key"] in GameData.EXPLOITS:
                    exploit_def = GameData.EXPLOITS[item_data["exploit_key"]]
                    item = ExploitItem(item_data["exploit_key"], exploit_def)
                    items.append(item)
            elif item_data["type"] == "story_fragment":
                item = StoryFragment(item_data["fragment_index"])
                items.append(item)

        return items

    def _restore_map_items(self, map_data: Dict) -> None:
        """Restore items on the map from save data."""
        game_map = self.game_engine.game_map

        # Clear current items
        game_map.code_hacks.clear()
        game_map.exploit_pickups.clear()
        game_map.permanent_upgrades.clear()
        game_map.story_fragments.clear()

        # Restore code hacks (backward compatibility)
        code_hacks_data = map_data.get("code_hacks", {})
        for pos_str, patch_data in code_hacks_data.items():
            position = parse_coordinate_string(pos_str)
            if not position:
                continue
            x, y = position.x, position.y

            # Get description from game engine's code_hack_effects
            color = patch_data["color"]
            desc = ""
            if color in self.game_engine.code_hack_effects:
                _, desc = self.game_engine.code_hack_effects[color]

            patch = CodeHack(
                color_name=color,
                effect=patch_data["effect"],
                name=patch_data["name"],
                description=desc,
                quantity=patch_data["quantity"]
            )
            patch.discovered = patch_data["discovered"]
            game_map.code_hacks[(x, y)] = patch

        # Restore exploit pickups
        for pos_str, exploit_key in map_data["exploit_pickups"].items():
            position = parse_coordinate_string(pos_str)
            if not position:
                continue
            x, y = position.x, position.y
            if exploit_key in GameData.EXPLOITS:
                exploit_def = GameData.EXPLOITS[exploit_key]
                exploit_item = ExploitItem(exploit_key, exploit_def)
                game_map.exploit_pickups[(x, y)] = exploit_item

        # Restore permanent upgrades
        for pos_str, upgrade_key in map_data["permanent_upgrades"].items():
            position = parse_coordinate_string(pos_str)
            if not position:
                continue
            x, y = position.x, position.y
            game_map.permanent_upgrades[(x, y)] = upgrade_key

        # Restore story fragments
        for pos_str, fragment_index in map_data["story_fragments"].items():
            position = parse_coordinate_string(pos_str)
            if not position:
                continue
            x, y = position.x, position.y
            fragment = StoryFragment(fragment_index)
            game_map.story_fragments[(x, y)] = fragment

        # Restore explored tiles
        if "explored_tiles" in map_data:
            game_map.explored_tiles.clear()
            for tile_str in map_data["explored_tiles"]:
                position = parse_coordinate_string(tile_str)
                if position:
                    game_map.explored_tiles.add((position.x, position.y))

        # Restore gateway
        if map_data["gateway"]:
            game_map.gateway = Position(map_data["gateway"]["x"], map_data["gateway"]["y"])

        # Restore last known enemy positions
        if "last_known_enemy_positions" in map_data:
            game_map.last_known_enemy_positions.clear()
            for enemy_id_str, pos_data in map_data["last_known_enemy_positions"].items():
                enemy_id = int(enemy_id_str)
                position = Position(pos_data["x"], pos_data["y"])
                turn_seen = pos_data["turn"]
                game_map.last_known_enemy_positions[enemy_id] = (position, turn_seen)

    def _restore_enemies(self, enemies_data: List[Dict]) -> None:
        """Restore enemies from save data."""
        self.game_engine.enemy_manager.enemies.clear()

        for enemy_data in enemies_data:
            position = Position(enemy_data["x"], enemy_data["y"])
            enemy = Enemy(position, enemy_data["type"])

            # Restore enemy ID if provided
            if "id" in enemy_data:
                enemy.id = enemy_data["id"]

            # Restore enemy state
            enemy.cpu = enemy_data["cpu"]
            # Convert state string back to EnemyState enum
            from game_entities import EnemyState
            enemy.state = EnemyState(enemy_data["state"]) if isinstance(enemy_data["state"], str) else enemy_data["state"]
            enemy.move_cooldown = enemy_data["move_cooldown"]
            enemy.disabled_turns = enemy_data["disabled_turns"]
            enemy.alert_timer = enemy_data["alert_timer"]
            enemy.patrol_index = enemy_data["patrol_index"]
            enemy.last_target = Position(enemy_data["last_target"]["x"], enemy_data["last_target"]["y"]) if enemy_data.get("last_target") else None

            if enemy_data["last_seen_player"]:
                enemy.last_seen_player = Position(
                    enemy_data["last_seen_player"]["x"],
                    enemy_data["last_seen_player"]["y"]
                )

            if "patrol_points" in enemy_data:
                enemy.patrol_points = [
                    Position(point["x"], point["y"])
                    for point in enemy_data["patrol_points"]
                ]

            # Restore movement queue
            if "move_queue" in enemy_data:
                enemy.move_queue = [
                    Position(point["x"], point["y"])
                    for point in enemy_data["move_queue"]
                ]

            self.game_engine.enemy_manager.enemies.append(enemy)
