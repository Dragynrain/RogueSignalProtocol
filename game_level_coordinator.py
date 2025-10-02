#!/usr/bin/env python3
"""
Game Level Coordinator
Handles level generation, progression, and placement of game elements.
Extracted from game_engine.py for better separation of concerns.
"""

import logging
import random
import traceback
from typing import List, Dict, Any

from game_config import GameConfig, GameBalance
from game_entities import Position, PositionValidator
from game_inventory import CodeHack, ExploitItem, StoryFragment
from game_data import GameData, GameUpgrades
from game_characters import Enemy, EnemyMovement
from game_save import SaveGameManager


class GameLevelCoordinator:
    """Coordinates level generation and progression."""

    def __init__(self, game_engine):
        """Initialize with reference to game engine."""
        self.game_engine = game_engine

    def generate_procedural_level(self):
        """Generate a procedural level using the new LevelGenerator system."""
        # Clear all map data and enemies first
        self._clear_map()

        # Get network configuration for current level from game state manager
        config = self.game_engine.game_state.get_current_network_config()

        try:
            # Play appropriate background music for the level (loops infinitely)
            if self.game_engine.level == 1:
                self.game_engine.sound_manager.play_music("level1_stealth.mp3", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME)
            elif self.game_engine.level == 2:
                self.game_engine.sound_manager.play_music("level2_infiltration.mp3", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME)
            elif self.game_engine.level == 3:
                self.game_engine.sound_manager.play_music("level3_core.mp3", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME)

            # Use the new LevelGenerator system
            self.game_engine.level_generator.generate_level(self.game_engine.level, self.game_engine.game_state.dungeon_seed)

            # Generate additional game elements not handled by LevelGenerator
            self._create_border_walls()
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
            # - Detection: Reset to 0 (doesn't carry over)
            # - Admin spawned state: Reset (new network, fresh start)
            self.game_engine.player.detection = 0
            self.game_engine.admin_spawned = False

            self.game_engine.message_log.add_message(f"{config['name']} loaded")

        finally:
            # Restore random seed
            random.seed()

    def progress_to_next_level(self):
        """Progress to the next level."""
        # Don't progress if game is already over
        if self.game_engine.game_over:
            return

        self.game_engine.level += 1
        if self.game_engine.level > 3:
            self.game_engine.sound_manager.play_music("victory.ogg", loops=1)
            self.game_engine.message_log.add_message_typed("BREAKTHROUGH TO THE INTERNET!", 'green')
            self.game_engine.message_log.add_message("You've escaped into the vast digital realm...")
            self.game_engine.message_log.add_message("The entire world wide web awaits exploration!")
            self.game_engine.message_log.add_message(f"Stats: Turns:{self.game_engine.turn} Det:{int(self.game_engine.player.detection)}%")
            self.game_engine.game_over = True
            # Delete save on game completion (no continuing after winning)
            SaveGameManager.delete_save()
            self.game_engine.message_log.add_message("Mission complete - save data purged")
        else:
            try:
                self.generate_procedural_level()
                # Auto-save after successful level generation
                self.game_engine.auto_save()
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                line_no = tb[-1].lineno if tb else "?"
                self.game_engine.message_log.add_message(f"Network error: {str(e)[:15]} (line {line_no})")
                self.game_engine.level -= 1

    def _clear_map(self):
        """Clear all map data."""
        self.game_engine.game_map.walls.clear()
        self.game_engine.game_map.shadows.clear()
        self.game_engine.game_map.cooling_nodes.clear()
        self.game_engine.game_map.cpu_recovery_nodes.clear()
        self.game_engine.game_map.ghost_nodes.clear()
        self.game_engine.game_map.code_hacks.clear()
        self.game_engine.game_map.exploit_pickups.clear()
        self.game_engine.game_map.permanent_upgrades.clear()
        self.game_engine.game_map.story_fragments.clear()
        self.game_engine.game_map.explored_tiles.clear()
        self.game_engine.game_map.last_known_enemy_positions.clear()
        self.game_engine.game_state.revealed_special_nodes.clear()
        self.game_engine.enemy_manager.enemies.clear()
        # Invalidate transparency cache for FOV calculations
        self.game_engine.game_map.invalidate_transparency_cache()

    def _create_border_walls(self):
        """Create walls around the map border."""
        for x in range(GameConfig.MAP_WIDTH):
            self.game_engine.game_map.walls.add((x, 0))
            self.game_engine.game_map.walls.add((x, GameConfig.MAP_HEIGHT - 1))
        for y in range(GameConfig.MAP_HEIGHT):
            self.game_engine.game_map.walls.add((0, y))
            self.game_engine.game_map.walls.add((GameConfig.MAP_WIDTH - 1, y))
        # Invalidate transparency cache after walls are modified
        self.game_engine.game_map.invalidate_transparency_cache()

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
                    return test_pos

        # Final fallback (should never be needed)
        return Position(6, 6)

    def _place_code_hacks(self):
        """Place codes throughout the level."""
        # Code effects should already be initialized at game start
        # If somehow empty, this is an error - don't place patches
        if not self.game_engine.code_hack_effects:
            logging.error("Code effects not initialized - skipping patch placement")
            return

        patch_count = 12 + self.game_engine.level * 4  # Much more codes (was 6 + level * 2)
        placed_patches = 0
        attempts = 0

        while placed_patches < patch_count and attempts < 150:
            attempts += 1
            x = random.randint(3, GameConfig.MAP_WIDTH - 3)
            y = random.randint(3, GameConfig.MAP_HEIGHT - 3)
            position = Position(x, y)

            if self._is_valid_patch_placement(position):
                color = random.choice(list(self.game_engine.code_hack_effects.keys()))
                effect, desc = self.game_engine.code_hack_effects[color]
                patch = CodeHack(color_name=color, effect=effect, name=f"{color.title()} Code", description=desc)

                # Check if player has already discovered this color effect
                # by looking at existing inventory items
                patch.discovered = self._is_code_color_discovered(color)

                self.game_engine.game_map.code_hacks[(x, y)] = patch
                placed_patches += 1

    def _is_code_color_discovered(self, color: str) -> bool:
        """Check if player has already discovered what this code color does."""
        # Check the global discovered effects for this game session
        return color in self.game_engine.discovered_code_effects

    def _place_exploit_pickups(self):
        """Place random exploit pickups throughout the level."""
        exploit_count = 5 + self.game_engine.level * 2  # Much more exploits (was 2 + max(0, level - 1))
        placed_exploits = 0
        attempts = 0

        # Get list of available exploits (excluding ones player starts with)
        available_exploits = list(GameData.EXPLOITS.keys())

        while placed_exploits < exploit_count and attempts < 100:
            attempts += 1
            x = random.randint(5, GameConfig.MAP_WIDTH - 5)
            y = random.randint(5, GameConfig.MAP_HEIGHT - 5)
            position = Position(x, y)

            if self._is_valid_patch_placement(position):  # Reuse code placement validation
                # Choose random exploit
                exploit_key = random.choice(available_exploits)
                exploit_def = GameData.EXPLOITS[exploit_key]
                exploit_item = ExploitItem(exploit_key, exploit_def)
                self.game_engine.game_map.exploit_pickups[(x, y)] = exploit_item
                placed_exploits += 1

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

        while placed_upgrades < upgrade_count and attempts < 100:
            attempts += 1
            x = random.randint(8, GameConfig.MAP_WIDTH - 8)
            y = random.randint(8, GameConfig.MAP_HEIGHT - 8)
            position = Position(x, y)

            # Use stricter placement rules for rare upgrades
            if (self._is_valid_patch_placement(position) and
                abs(x - 5) > 10 and abs(y - 5) > 10):  # Not near starting position

                upgrade_key = random.choice(available_upgrades)
                self.game_engine.game_map.permanent_upgrades[(x, y)] = upgrade_key
                placed_upgrades += 1

                # Remove from available to prevent duplicates on same level
                available_upgrades.remove(upgrade_key)
                if not available_upgrades:
                    break

    def _place_enemies(self, enemy_count: int):
        """Place enemies throughout the level with increased density."""
        enemy_types = ['scanner', 'patrol', 'bot', 'firewall', 'hunter', 'virus', 'inhibitor']
        # Adjust weights for challenging gameplay
        enemy_weights = [4, 3, 2, 2, 2, 1, 2]  # More scanners and firewalls for detection challenge, virus is rare

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
                    enemy.type_data.movement = chosen_movement

                    # Generate patrol route if virus got LINEAR movement
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