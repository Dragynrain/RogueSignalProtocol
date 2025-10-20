#!/usr/bin/env python3
"""
Turn processing manager coordinating game state updates and enemy AI.

This module handles per-turn game logic in structured phases:

Turn processing order:
1. Player status effects (speed boost, virus damage, temp effects)
2. Special tile effects (cooling nodes, CPU recovery, ghost nodes, item pickups)
3. Memory system updates (FOV, explored tiles, enemy ghost positions)
4. Enemy AI phases (awareness -> movement -> attacks)
5. Trace level increases and admin spawn checks

Enemy AI phases (CRITICAL ORDER):
- Phase 1: Awareness - Update states (UNAWARE/ALERT/HOSTILE), communication
- Phase 2: Movement - All enemies move based on current state
- Phase 3: Attacks - Adjacent enemies attack (move OR attack, not both)

Key systems:
- FOV using TCOD shadowcasting for exploration and vision
- Enemy state machine (UNAWARE -> ALERT -> HOSTILE) with 1-turn alert timer
- Ghost position tracking (last known enemy locations)
- Trace level warnings at 75% and 90% thresholds
- Permadeath save deletion on death
"""

import os
import tcod
import tcod.constants
import random
import math
import logging
from typing import List, Optional

from game_config import GameConfig, GameBalance
from data_loading import DataLoader
from game_entities import Position, Colors, EnemyState, EnemyMovement
from game_inventory import StoryFragment
from game_data import GameUpgrades
from game_save import SaveGameManager


class GameTurnManager:
    """
    Manages complete turn processing with phased enemy AI and game effects.

    Orchestrates all per-turn updates in a specific order to ensure consistent
    behavior and prevent timing issues. Enemy AI is split into three phases to
    prevent movement-attack conflicts and ensure proper communication.

    Key responsibilities:
    - Player status effect updates (speed, virus, temporary effects)
    - Special tile processing (nodes, pickups, story fragments)
    - FOV/memory system updates (TCOD shadowcasting, ghost positions)
    - Enemy AI coordination (three-phase: awareness -> movement -> attacks)
    - Trace level management and admin spawning
    - Permadeath enforcement (save deletion on death)

    Phase separation rationale:
    Separating awareness/movement/attacks prevents enemies from moving twice,
    ensures proper communication propagation, and makes AI behavior predictable.

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
            self.game_engine.player.trace_level = min(100, self.game_engine.player.trace_level + background_increase)

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
            transparency = self.game_engine.game_map._get_transparency_map()
            fov = tcod.map.compute_fov(
                transparency=transparency,
                pov=(self.game_engine.player.y, self.game_engine.player.x),
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

    def _update_enemies(self):
        """
        Update all enemy states and actions in structured three-phase system.

        Phase 1: Awareness and Communication
        - All enemies check visibility and update states (UNAWARE/ALERT/HOSTILE)
        - Alert/hostile enemies communicate with nearby enemies

        Phase 2: Movement
        - All enemies move based on their current state
        - Enemies adjacent to player skip movement (save attack for phase 3)

        Phase 3: Attacks
        - Enemies adjacent to player attack (move OR attack, not both)
        - Track attacks for inventory warning dialogue

        Why phased?
        - Prevents double-movement (enemy moving during awareness then during movement)
        - Ensures communication propagates before movement
        - Makes AI behavior deterministic and testable
        """
        # Reset movement flags at start of enemy turn
        for enemy in self.game_engine.enemies:
            enemy.has_moved_this_turn = False

        # PHASE 1: Awareness and Communication
        # All enemies detect player, update states, and communicate with nearby enemies
        self._update_enemy_awareness()

        # PHASE 2: Movement
        # All enemies move based on their current awareness state
        self._move_enemies()

        # PHASE 3: Attacks
        # All enemies attack if they are in range (move OR attack, not both)
        self._process_enemy_attacks()

    def _update_enemy_awareness(self):
        """
        PHASE 1: Update enemy awareness states and handle communication.

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
            can_see = enemy.can_see_player(self.game_engine.player, self.game_engine.game_map)

            # Admin Avatar has perfect tracking
            if enemy.type == 'admin':
                if enemy.state != EnemyState.HOSTILE:
                    enemy.state = EnemyState.HOSTILE
                    self.game_engine.message_log.add_message(f"{enemy.type_data.name} detected you!")
                enemy.last_seen_player = Position(self.game_engine.player.x, self.game_engine.player.y)
            else:
                self._update_enemy_state(enemy, can_see)

    def _update_enemy_state(self, enemy, can_see_player):
        """Update enemy state based on player visibility."""
        player_pos = Position(self.game_engine.player.x, self.game_engine.player.y)

        if can_see_player:
            # Enemy sees player - escalate state
            if enemy.state == EnemyState.UNAWARE:
                enemy.state = EnemyState.ALERT
                enemy.invalidate_move_queue()  # State changed, recalculate path
                enemy.alert_timer = 1  # Give 1 turn grace period before becoming HOSTILE
                enemy.last_seen_player = player_pos
                self.game_engine.message_log.add_message(f"{enemy.type_data.name} investigating")
                self.game_engine.sound_manager.play_sound("enemy_alert")

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
                    enemy.invalidate_move_queue()  # State changed, recalculate path
                    self._restore_patrol(enemy)
                    self.game_engine.message_log.add_message(f"{enemy.type_data.name} lost interest")

            elif enemy.state == EnemyState.HOSTILE:
                if random.random() < 0.15:
                    if enemy.type == 'admin':
                        enemy.state = EnemyState.ALERT
                        enemy.invalidate_move_queue()  # State changed
                        enemy.alert_timer = 0
                    else:
                        enemy.state = EnemyState.UNAWARE
                        enemy.invalidate_move_queue()  # State changed
                        enemy.last_seen_player = None
                        self._restore_patrol(enemy)
                        self.game_engine.message_log.add_message(f"{enemy.type_data.name} lost track")

    def _transition_to_hostile(self, enemy):
        """Transition enemy to hostile state."""
        self._restore_patrol(enemy)  # Store original patrol index
        enemy.state = EnemyState.HOSTILE
        enemy.invalidate_move_queue()  # State changed, recalculate path
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
                break

    def _alert_nearby_enemies(self, alerting_enemy):
        """Alert nearby enemies when one becomes hostile."""
        alert_range = GameConfig.NEARBY_ENEMY_ALERT_RADIUS  # Use config value
        alerted_count = 0
        alerted_enemies = []

        for enemy in self.game_engine.enemies:
            if enemy is alerting_enemy or enemy.state == EnemyState.HOSTILE:
                continue

            distance = enemy.position.distance_to(alerting_enemy.position)
            if distance <= alert_range:
                # Store patrol information for PATROL enemies before becoming hostile
                movement_type = enemy.get_movement_type()
                if movement_type == EnemyMovement.PATROL and enemy.patrol_points:
                    enemy.original_patrol_index = enemy.patrol_index
                # All enemies within alert range immediately go HOSTILE and get player location
                enemy.state = EnemyState.HOSTILE
                enemy.invalidate_move_queue()  # State changed, recalculate path
                enemy.alert_timer = 0
                enemy.last_seen_player = Position(self.game_engine.player.x, self.game_engine.player.y)
                alerted_count += 1
                alerted_enemies.append(enemy)

        # Don't move alerted enemies immediately - they will move in the movement phase
        # This ensures proper phase separation: awareness -> movement -> attacks

        if alerted_count > 0:
            self.game_engine.message_log.add_message(f"{alerted_count} enemies alerted nearby!")
            self.game_engine.sound_manager.play_sound("enemies_alerted", priority=6)

    def _move_enemies(self):
        """PHASE 2: Move all enemies according to their current awareness state."""
        for enemy in self.game_engine.enemies:
            # Only move enemies that haven't moved this turn
            if not getattr(enemy, 'has_moved_this_turn', False):
                # If enemy can attack player, don't move (save the attack for next phase)
                if enemy.can_attack_player(self.game_engine.player):
                    enemy.has_moved_this_turn = False  # Mark as not moved so it can attack
                else:
                    # Enemy can't attack, so try to move
                    did_move = enemy.move(self.game_engine.game_map, self.game_engine.player, self.game_engine)
                    enemy.has_moved_this_turn = did_move

    def _process_enemy_attacks(self):
        """PHASE 3: Process attacks from enemies adjacent to player."""
        # Track attacks this turn for inventory warning (only show once per turn)
        player_attacked_in_inventory = False
        total_damage_taken = 0
        attacking_enemy_count = 0

        for enemy in self.game_engine.enemies[:]:
            # Only attack if enemy hasn't moved this turn (move OR attack, not both)
            if enemy.can_attack_player(self.game_engine.player) and not getattr(enemy, 'has_moved_this_turn', False):
                self.game_engine.sound_manager.play_sound("enemy_attack")
                damage = enemy.attack_player(self.game_engine.player)

                # Track if player was attacked while in inventory
                # Count ALL attacks (damage, virus, inhibitor) not just direct damage
                total_damage_taken += damage
                attacking_enemy_count += 1
                if self.game_engine.show_inventory:
                    player_attacked_in_inventory = True

                if enemy.type == 'virus':
                    virus_turns = self.game_engine.player.temporary_effects.get('virus_turns', 0)
                    self.game_engine.message_log.add_message(f"{enemy.type_data.name} applies virus damage ({virus_turns} turns)")
                    self.game_engine.sound_manager.play_sound("virus_infection")
                elif enemy.type == 'inhibitor':
                    # Inhibitor applies movement slow
                    slow_turns = self.game_engine.player.temporary_effects.get('movement_slowed_turns', 0)
                    if slow_turns > 0:
                        self.game_engine.message_log.add_message(f"{enemy.type_data.name} applies movement slow ({slow_turns} turns)")
                    else:
                        self.game_engine.message_log.add_message(f"{enemy.type_data.name} disrupts speed boost")
                elif damage > 0:
                    self.game_engine.message_log.add_message(f"{enemy.type_data.name} attacks: {damage} CPU damage")
                if self.game_engine.player.cpu <= 0:
                    self.game_engine.sound_manager.play_sound("player_death", priority=10)
                    self.game_engine.message_log.add_message_typed("CRITICAL SYSTEM FAILURE!", Colors.RED)
                    self.game_engine.sound_manager.play_sound("critical_system_failure", priority=10)
                    self.game_engine.sound_manager.stop_music(fade_out_ms=500)  # Stop level music on death
                    # Delete save on death (permadeath)
                    self._delete_save_on_death()
                    self.game_engine.game_over = True
                    # Show death dialogue
                    from game_dialogue_system import create_death_dialogue
                    self.game_engine.dialogue_state.show(create_death_dialogue())
                    return  # Exit immediately - no more enemy processing after player death

        # Show inventory attack warning if player was attacked while inventory was open
        if player_attacked_in_inventory:
            from game_dialogue_system import create_inventory_attack_dialogue
            self.game_engine.dialogue_state.show(create_inventory_attack_dialogue())

        # Movement flags are reset at the start of _update_enemies()

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
            self.game_engine.message_log.add_message("*** ADMIN AVATAR SPAWNED! ***")
            self.game_engine.sound_manager.play_sound("admin_spawn", priority=8)

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
        return Position(40, 40)

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