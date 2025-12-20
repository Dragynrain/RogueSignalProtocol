#!/usr/bin/env python3
"""
Level generation and progression coordinator for game session.

Handles level-to-level gameplay including:
- Procedural level generation (map structure, enemies, items)
- Level progression and transitions
- Victory condition processing
- Item placement with loot room clustering
- Enemy spawning with distribution

Extracted from GameSession to improve modularity and maintainability.
"""

import logging
import random
import traceback

from game_characters import Enemy
from game_config import GameConfig
from game_data import GameData, GameUpgrades
from game_entities import EnemyMovement, Position, PositionValidator
from game_inventory import CodeHack, ExploitItem, StoryFragment
from game_save import SaveGameManager


class GameLevelCoordinator:
    """
    Manages level generation and progression for game sessions.

    Coordinates level generation pipeline including map structure,
    enemy spawning, item placement, and level transitions.

    Attributes:
        game_engine: GameEngine instance for accessing all game systems
    """

    def __init__(self, game_engine):
        """
        Initialize level coordinator with game engine reference.

        Args:
            game_engine: GameEngine instance providing access to all game systems
        """
        self.game_engine = game_engine

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
            self.game_engine.sound_manager.play_music(
                "level1_stealth.ogg", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME
            )
        elif self.game_engine.level == 2:
            self.game_engine.sound_manager.play_music(
                "level2_infiltration.ogg", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME
            )
        elif self.game_engine.level == 3:
            self.game_engine.sound_manager.play_music(
                "level3_core.ogg", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME
            )

        # Use the new LevelGenerator system
        self.game_engine.level_generator.generate_level(
            self.game_engine.level,
            self.game_engine.game_state.dungeon_seed,
            self.game_engine.ascension_modifiers,
        )

        # Generate additional game elements not handled by LevelGenerator
        # A11+: Apply code reduction per floor (min 3 codes)
        mods = self.game_engine.ascension_modifiers
        code_count = config["code_hacks"]
        if mods.code_reduction_per_floor > 0:
            code_count = max(mods.code_minimum, code_count - mods.code_reduction_per_floor)
        self._place_code_hacks(code_count)

        self._place_exploit_pickups(config["exploit_pickups"])
        self._place_story_fragment()  # Add story fragment placement

        # A18+: Apply upgrade reduction per floor (min 0 upgrades)
        upgrade_count = config["permanent_upgrades"]
        if mods.upgrade_reduction_per_floor > 0:
            upgrade_count = max(0, upgrade_count - mods.upgrade_reduction_per_floor)
        self._place_permanent_upgrades(upgrade_count)
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

        # Reset A20 blind spot tracking for new level
        # (prevents incorrectly consuming blind spots from previous level)
        self.game_engine.game_session.turn_manager._last_blind_spot_position = None

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
            logging.debug("Session: Level progression blocked - game already over")
            return

        old_level = self.game_engine.level

        # Track level completion (before incrementing)
        from game_metrics import get_current_session, track

        track("levels_completed")

        # Track gateway discovery for Explorer achievement
        session = get_current_session()
        if session:
            session.special_nodes_discovered.add("gateway")

        # Alpha Testing: Level completion analytics
        player = self.game_engine.player
        enemies_remaining = len(self.game_engine.enemies)
        logging.info("=" * 80)
        logging.info(f"[COMPLETE] LEVEL {old_level} COMPLETED")
        logging.info(f"Turn: {self.game_engine.turn}")
        logging.info(f"Player CPU: {player.cpu}/{player.max_cpu}")
        logging.info(f"Player Heat: {player.heat}/{player.max_heat}")
        logging.info(f"Trace Level: {player.trace_level:.1f}")
        logging.info(
            f"Equipped Exploits: {len([e for e in player.inventory_manager.equipped_exploits if e])}/3"
        )
        logging.info(f"Enemies Remaining: {enemies_remaining}")
        logging.info("=" * 80)

        self.game_engine.level += 1

        if self.game_engine.level > 3:
            logging.warning("=" * 80)
            logging.warning("[VICTORY] All levels completed!")
            logging.warning(f"Total turns: {self.game_engine.turn}")
            logging.warning(f"Final trace: {player.trace_level:.1f}%")
            logging.warning("=" * 80)

            # Stop level music and play victory music (one-shot, no loop)
            self.game_engine.sound_manager.stop_music(fade_out_ms=500)
            self.game_engine.sound_manager.play_music("victory.wav", loops=0)  # loops=0 = play once

            self.game_engine.message_log.add_message_typed("BREAKTHROUGH TO THE INTERNET!", "green")
            self.game_engine.message_log.add_message(
                "You've become the rogue signal they couldn't delete..."
            )
            self.game_engine.message_log.add_message(
                "The network is vast. The future, uncertain. But you're free."
            )
            self.game_engine.message_log.add_message(
                f"Stats: Trace:{int(self.game_engine.player.trace_level)}%"
            )
            self.game_engine.game_over = True

            # Finalize and save metrics before deleting save
            from game_metrics import finalize_session, load_lifetime_metrics, save_metrics

            metrics = finalize_session(
                victory=True,
                death_cause=None,
                death_level=0,
                final_cpu=self.game_engine.player.cpu,
            )
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

            # Unlock next ascension level and record victory
            from game_ascension import unlock_next_ascension

            current_ascension = self.game_engine.ascension_level
            highest_unlocked = self.game_engine.settings.get_highest_ascension_unlocked()
            new_highest = unlock_next_ascension(current_ascension, highest_unlocked)

            if new_highest > highest_unlocked:
                self.game_engine.settings.unlock_ascension(new_highest)
                # Auto-advance to newly unlocked level (per PLAN requirement)
                self.game_engine.settings.set_ascension_level(new_highest)
                # Track for unlock screen display after victory screen
                self.game_engine.game_state.newly_unlocked_ascension = new_highest
                logging.info(
                    f"Ascension unlocked: A{new_highest} (beat A{current_ascension}), auto-advanced"
                )

            self.game_engine.settings.record_ascension_victory(current_ascension)

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
                logging.debug(
                    f"Session: Level {self.game_engine.level} generation and auto-save complete"
                )
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                line_no = tb[-1].lineno if tb else "?"
                logging.error(f"Session: Level generation FAILED: {str(e)[:50]} at line {line_no}")
                self.game_engine.message_log.add_message(
                    f"Network error: {str(e)[:15]} (line {line_no})"
                )
                self.game_engine.level -= 1
                logging.debug(f"Session: Rolled back to level {self.game_engine.level}")

    def _clear_map(self):
        """Clear all map data."""
        self.game_engine.game_map.walls.clear()
        self.game_engine.game_map.blind_spots.clear()
        self.game_engine.game_map.used_blind_spots.clear()  # A20: clear consumed blind spots
        self.game_engine.game_map.cooling_nodes.clear()
        self.game_engine.game_map.cpu_recovery_nodes.clear()
        self.game_engine.game_map.ghost_nodes.clear()
        self.game_engine.game_map.code_hacks.clear()
        self.game_engine.game_map.exploit_pickups.clear()
        self.game_engine.game_map.permanent_upgrades.clear()
        self.game_engine.game_map.story_fragments.clear()
        self.game_engine.game_map.explored_tiles.clear()
        self.game_engine.game_map.last_known_enemy_positions.clear()
        if hasattr(self.game_engine.game_state, "revealed_special_nodes"):
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
        if (
            self.game_engine.game_map.is_valid_position(pos)
            and not self.game_engine.game_map.is_wall(pos)
            and not self.game_engine._get_enemy_at(pos)
        ):
            logging.debug(f"Spawn: Using center position {pos}")
            return pos

        # If center is somehow occupied, try nearby positions in the spawn room
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Already tried center
                test_pos = Position(spawn_room_center_x + dx, spawn_room_center_y + dy)
                if (
                    test_pos.x >= 2
                    and test_pos.x < 10  # Within spawn room bounds
                    and test_pos.y >= 2
                    and test_pos.y < 10
                    and self.game_engine.game_map.is_valid_position(test_pos)
                    and not self.game_engine.game_map.is_wall(test_pos)
                    and not self.game_engine._get_enemy_at(test_pos)
                ):
                    logging.info(f"Spawn: Center occupied, using nearby position {test_pos}")
                    return test_pos

        # CRITICAL: Spawn room appears to be sealed or invalid!
        # Try to find ANY floor position in the spawn room area
        logging.error("Spawn: CRITICAL - Spawn room (2,2,8,8) appears invalid!")
        logging.error("Spawn: Searching entire spawn room for ANY valid position...")

        for y in range(2, 10):
            for x in range(2, 10):
                test_pos = Position(x, y)
                if self.game_engine.game_map.is_valid_position(
                    test_pos
                ) and not self.game_engine.game_map.is_wall(test_pos):
                    logging.warning(
                        f"Spawn: Found floor at {test_pos}, but spawn room may be sealed off!"
                    )
                    return test_pos

        # Absolute fallback: Search ENTIRE map for a valid floor tile
        logging.error("Spawn: EMERGENCY - No valid position in spawn room! Searching entire map...")
        for y in range(GameConfig.MAP_HEIGHT):
            for x in range(GameConfig.MAP_WIDTH):
                test_pos = Position(x, y)
                if self.game_engine.game_map.is_valid_position(
                    test_pos
                ) and not self.game_engine.game_map.is_wall(test_pos):
                    logging.error(f"Spawn: EMERGENCY spawn at {test_pos} - map generation BUG!")
                    return test_pos

        # This should NEVER happen - would mean entire map is walls
        logging.critical("Spawn: CRITICAL FAILURE - Entire map is walls! Using fallback (6,6)")
        return Position(6, 6)

    def _place_items_with_clustering(
        self, total_count, loot_percentage, item_factory, storage_dict, max_attempts=150
    ):
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
        else:
            loot_room_count = 0

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

    def _place_code_hacks(self, patch_count: int):
        """Place codes throughout the level with clustering in loot rooms."""
        # Code effects should already be initialized at game start
        # If somehow empty, this is an error - don't place patches
        if not self.game_engine.code_hack_effects:
            logging.error("Code effects not initialized - skipping patch placement")
            return

        def create_code_hack(x, y):
            """Factory function to create a code hack item."""
            color = random.choice(list(self.game_engine.code_hack_effects.keys()))
            effect, desc = self.game_engine.code_hack_effects[color]
            patch = CodeHack(
                color_name=color, effect=effect, name=f"{color.title()} Code", description=desc
            )
            patch.discovered = self._is_code_color_discovered(color)
            return patch

        self._place_items_with_clustering(
            total_count=patch_count,
            loot_percentage=0.3,
            item_factory=create_code_hack,
            storage_dict=self.game_engine.game_map.code_hacks,
            max_attempts=150,
        )

        actual_count = len(self.game_engine.game_map.code_hacks)
        match_status = "MATCH" if actual_count == patch_count else "MISMATCH"
        logging.info(
            f"Item Placement: CODE HACKS - Expected: {patch_count}, Actual: {actual_count} [{match_status}]"
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

    def _place_exploit_pickups(self, exploit_count: int):
        """Place random exploit pickups throughout the level with clustering in loot rooms."""
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
            max_attempts=100,
        )

        actual_count = len(self.game_engine.game_map.exploit_pickups)
        match_status = "MATCH" if actual_count == exploit_count else "MISMATCH"
        logging.info(
            f"Item Placement: EXPLOIT PICKUPS - Expected: {exploit_count}, Actual: {actual_count} [{match_status}]"
        )

    def _place_story_fragment(self):
        """Place a story fragment on level 3 with chance based on ascension level.

        Base chance: 50% at A0, scaling up to 70% at A20 (+1% per ascension level).
        This rewards players who beat higher ascension levels with faster story unlocks.
        """
        # Only place story fragments on level 3 (Military network)
        if self.game_engine.level != 3:
            return

        # Base 50% chance, +1% per ascension level (max 70% at A20)
        ascension_bonus = self.game_engine.ascension_level * 0.01
        spawn_threshold = 0.5 + ascension_bonus  # Higher threshold = more spawns
        if random.random() > spawn_threshold:
            return

        # Get the next undiscovered fragment
        next_fragment_index = (
            self.game_engine.story_fragment_manager.get_next_undiscovered_fragment()
        )
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
                if not hasattr(self.game_engine.game_map, "story_fragments"):
                    self.game_engine.game_map.story_fragments = {}
                self.game_engine.game_map.story_fragments[(x, y)] = story_fragment

                self.game_engine.message_log.add_message(
                    "Network anomaly detected... Data fragment available"
                )
                break

    def _place_permanent_upgrades(self, upgrade_count: int):
        """Place permanent upgrades throughout the level using network config."""
        placed_upgrades = 0
        attempts = 0
        available_upgrades = list(GameUpgrades.UPGRADES.keys())

        logging.debug(
            f"Attempting to place {upgrade_count} permanent upgrades on level {self.game_engine.level}"
        )

        while placed_upgrades < upgrade_count and attempts < 100:
            attempts += 1
            x = random.randint(8, GameConfig.MAP_WIDTH - 8)
            y = random.randint(8, GameConfig.MAP_HEIGHT - 8)
            position = Position(x, y)

            # Use stricter placement rules for rare upgrades
            # Avoid spawn room (2-8, 2-8) with a buffer zone
            spawn_room_buffer = 5  # 5-tile buffer around spawn room
            far_from_spawn = (
                x > 8 + spawn_room_buffer
                or x < 2 - spawn_room_buffer
                or y > 8 + spawn_room_buffer
                or y < 2 - spawn_room_buffer
            )

            if self._is_valid_patch_placement(position) and far_from_spawn:

                upgrade_key = random.choice(available_upgrades)
                self.game_engine.game_map.permanent_upgrades[(x, y)] = upgrade_key
                placed_upgrades += 1
                logging.debug(
                    f"Placed permanent upgrade '{upgrade_key}' at ({x}, {y}) after {attempts} attempts"
                )

                # Remove from available to prevent duplicates on same level
                available_upgrades.remove(upgrade_key)
                if not available_upgrades:
                    break

        actual_count = len(self.game_engine.game_map.permanent_upgrades)
        if placed_upgrades < upgrade_count:
            logging.warning(
                f"Only placed {placed_upgrades}/{upgrade_count} permanent upgrades after {attempts} attempts"
            )

        match_status = "MATCH" if actual_count == upgrade_count else "MISMATCH"
        logging.info(
            f"Item Placement: PERMANENT UPGRADES - Expected: {upgrade_count}, Actual: {actual_count} [{match_status}]"
        )

    def _place_enemies(self, enemy_count: int):
        """Place enemies throughout the level according to config and ascension modifiers."""
        enemy_types = ["scanner", "patrol", "bot", "firewall", "hunter", "virus", "inhibitor"]

        # Get spawn weights from config (gameplay.enemy_spawn_weights)
        base_weights = GameConfig.get_enemy_spawn_weights()
        enemy_weights = [base_weights.get(t, 1) for t in enemy_types]

        # Apply A12+ spawn weight overrides from ascension modifiers
        mods = self.game_engine.ascension_modifiers
        if mods.spawn_weights is not None:
            enemy_weights = [mods.spawn_weights.get(t, base_weights.get(t, 1)) for t in enemy_types]

        # Apply A9+ enemy count bonus
        modified_count = enemy_count + mods.enemy_count_bonus

        placed_enemies = 0
        attempts = 0

        while (
            placed_enemies < modified_count
            and attempts < modified_count * GameConfig.ENEMY_PLACEMENT_ATTEMPTS_MULTIPLIER
        ):
            attempts += 1
            # Ensure enemies spawn well away from top-left player spawn area
            x = random.randint(10, GameConfig.MAP_WIDTH - 2)
            y = random.randint(10, GameConfig.MAP_HEIGHT - 2)
            position = Position(x, y)

            if self._is_valid_enemy_placement(position):
                enemy_type = random.choices(enemy_types, weights=enemy_weights)[0]
                enemy = Enemy(position, enemy_type)

                if enemy_type == "patrol":
                    enemy.patrol_points = self.game_engine.enemy_manager._generate_patrol_route(
                        position
                    )
                elif enemy_type == "virus":
                    # Give virus enemies random passive movement types for variety
                    # SEEK is NOT included - it's the movement type used when hostile, not a base type
                    virus_movement_types = [
                        EnemyMovement.STATIC,
                        EnemyMovement.RANDOM,
                        EnemyMovement.PATROL,
                    ]
                    chosen_movement = random.choice(virus_movement_types)
                    # Store in instance variable, NOT in shared type_data!
                    enemy.original_movement_type = chosen_movement

                    # Generate patrol route if virus got PATROL movement
                    if chosen_movement == EnemyMovement.PATROL:
                        enemy.patrol_points = self.game_engine.enemy_manager._generate_patrol_route(
                            position
                        )

                # Apply ascension modifiers to enemy stats (HP, vision, damage)
                enemy.apply_ascension_modifiers(mods)

                # Log first enemy of each type to verify modifiers applied
                if placed_enemies == 0:
                    logging.debug(
                        f"First enemy stats after A{self.game_engine.ascension_level} mods: "
                        f"{enemy.type} cpu={enemy.cpu} vision={enemy.vision_range} dmg_mult={enemy.damage_multiplier}"
                    )

                self.game_engine.enemy_manager.enemies.append(enemy)
                placed_enemies += 1

        actual_count = len(self.game_engine.enemy_manager.enemies)
        match_status = "MATCH" if actual_count == modified_count else "MISMATCH"
        logging.info(
            f"Item Placement: ENEMIES - Expected: {modified_count}, Actual: {actual_count} [{match_status}]"
        )

    def _is_valid_patch_placement(self, position: Position) -> bool:
        """Check if position is valid for code placement."""
        return PositionValidator.is_valid_for_placement(
            position,
            self.game_engine.game_map,
            min_distance_from_spawn=5.0,
            check_existing_items=True,
        )

    def _is_valid_enemy_placement(self, position: Position) -> bool:
        """Check if position is valid for enemy placement."""
        return PositionValidator.is_valid_for_enemy_placement(
            position,
            self.game_engine.game_map,
            self.game_engine.enemies,
            self.game_engine.player.position,
            check_existing_items=True,
        )
