#!/usr/bin/env python3
"""
Game state persistence manager for save/load operations.

Handles complete game state serialization and restoration including:
- Save game to JSON file
- Load game from JSON file
- Player state (stats, inventory, effects)
- Map state (items, enemies, explored tiles)
- Game effects (code discoveries, distraction points)
- Session metrics and achievements

Extracted from GameSession to improve modularity and maintainability.
"""

import logging
import random
import traceback
from typing import Any

from game_characters import Enemy
from game_config import GameConfig
from game_data import GameData
from game_entities import Colors, Position, parse_coordinate_string
from game_inventory import CodeHack, ExploitItem, StoryFragment
from game_save import SaveGameManager


class GameStatePersistence:
    """
    Manages game state persistence for save/load operations.

    Coordinates complete game state serialization and restoration
    including player state, map state, enemies, and session metrics.

    Attributes:
        game_engine: GameEngine instance for accessing all game systems
    """

    def __init__(self, game_engine):
        """
        Initialize persistence manager with game engine reference.

        Args:
            game_engine: GameEngine instance providing access to all game systems
        """
        self.game_engine = game_engine

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
            # Sync code hack discovered status with global discovered effects
            from game_inventory import sync_code_discovered_status

            sync_code_discovered_status(
                self.game_engine.player.inventory_manager.items,
                self.game_engine.discovered_code_effects,
            )
            self._restore_ui_state(save_data)

            # Generate level layout for map structure
            logging.info(
                f"Load: Generating level {self.game_engine.game_state.level} with seed={self.game_engine.game_state.dungeon_seed}"
            )
            self.game_engine.level_generator.generate_level(
                self.game_engine.game_state.level, self.game_engine.game_state.dungeon_seed
            )
            logging.info(
                f"Load: Level generation complete, player at ({self.game_engine.player.x}, {self.game_engine.player.y})"
            )

            # Validate player position after map generation
            # If player position is invalid, the save is incompatible (likely due to map generation changes)
            player_pos = Position(self.game_engine.player.x, self.game_engine.player.y)
            if self.game_engine.game_map.is_wall(player_pos):
                logging.error(
                    f"Load: SAVE INCOMPATIBLE - Player position {player_pos} is in a wall!"
                )
                logging.error(
                    "Load: This likely means the save is from an older version with different map generation."
                )
                logging.error("Load: Refusing to load - game will start fresh.")
                self.game_engine.message_log.add_message_typed(
                    "Save file incompatible with current version!", Colors.RED
                )
                self.game_engine.message_log.add_message("Starting new game...")
                return False

            # Restore map items and enemies
            self._restore_map_items(save_data["map_state"])
            self._restore_enemies(save_data["enemies"])

            # Restore Enemy class counter
            if "enemy_next_id" in save_data:
                Enemy.set_next_id_counter(save_data["enemy_next_id"])

            # Set just_loaded flag to prevent enemy awareness updates on first turn
            # This ensures enemies don't get a "free" turn to spot the player
            self.game_engine.game_state.just_loaded = True

            self.game_engine.message_log.add_message_typed(
                "Game loaded successfully!", Colors.GREEN
            )
            return True

        except (KeyError, TypeError, ValueError, AttributeError) as e:
            # Common save data errors - corrupted or incompatible save
            logging.error(f"Failed to restore game state (data error): {e}")
            logging.debug(traceback.format_exc())
            return False
        except Exception as e:
            # Unexpected errors - log full traceback for debugging
            logging.error(f"Failed to restore game state (unexpected): {e}")
            logging.error(traceback.format_exc())
            return False

    def _restore_game_state(self, save_data: dict[str, Any]) -> None:
        """Restore core game state from save data."""
        self.game_engine.game_state.level = save_data.get("level", 1)
        self.game_engine.game_state.turn = save_data.get("turn", 0)
        self.game_engine.game_state.game_over = save_data.get("game_over", False)
        self.game_engine.game_state.admin_spawned = save_data.get("admin_spawned", False)

        # Restore ascension level and recalculate modifiers
        saved_ascension = save_data.get("ascension_level", 0)
        self.game_engine.ascension_level = saved_ascension
        from game_ascension import calculate_ascension_modifiers

        self.game_engine.ascension_modifiers = calculate_ascension_modifiers(saved_ascension)

        # Log seed restoration for debugging
        saved_seed = save_data.get("dungeon_seed")
        if saved_seed is None:
            logging.warning("Load: No dungeon_seed in save file! Generating new random seed.")
            self.game_engine.game_state.dungeon_seed = random.randint(
                1, GameConfig.DUNGEON_SEED_RANGE
            )
        else:
            self.game_engine.game_state.dungeon_seed = saved_seed
            logging.info(f"Load: Restored dungeon_seed={saved_seed}")

    def _restore_player_state(self, player_data: dict[str, Any]) -> None:
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
        player.temporary_effects = player_data.get(
            "temporary_effects",
            {
                "speed_boost_turns": 0,
                "movement_slowed_turns": 0,
                "enhanced_vision_turns": 0,
                "exploit_efficiency_turns": 0,
                "traffic_masquerade_turns": 0,
                "virus_turns": 0,
            },
        )

        # Restore inventory with defaults
        player.inventory_manager.equipped_exploits = player_data.get("equipped_exploits", [])
        player.inventory_manager.max_equipped_exploits = player_data.get("max_equipped_exploits", 5)
        inventory_items = player_data.get("inventory_items", [])
        player.inventory_manager.items = self._deserialize_inventory(inventory_items)

        # Re-apply ascension modifiers to player
        # A10: Player vision override
        if self.game_engine.ascension_modifiers.player_vision_override is not None:
            player.ascension_vision_override = (
                self.game_engine.ascension_modifiers.player_vision_override
            )
        # A14: Starting RAM is already restored from save (ram_total above)

    def _restore_game_effects(self, save_data: dict[str, Any]) -> None:
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

        # Restore revealed special nodes (from Network Scan exploit)
        self.game_engine.game_state.revealed_special_nodes = {}
        for pos_str, node_type in effects_data.get("revealed_special_nodes", {}).items():
            position = parse_coordinate_string(pos_str)
            if position:
                self.game_engine.game_state.revealed_special_nodes[(position.x, position.y)] = (
                    node_type
                )

        # Restore code effects (backward compatibility)
        self.game_engine.code_hack_effects = save_data.get("code_hack_effects", {})
        self.game_engine.discovered_code_effects = save_data.get("discovered_code_effects", {})

        # Restore overclocking state
        self.game_engine.overclock_confirmation = save_data.get("overclock_confirmation", False)
        self.game_engine.overclock_exploit = save_data.get("overclock_exploit", None)

    def _restore_metrics(self, save_data: dict[str, Any]) -> None:
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

    def _restore_ui_state(self, save_data: dict[str, Any]) -> None:
        """Restore UI state from save data."""
        ui_state = save_data.get("ui_state", {})
        self.game_engine.inventory_selection = ui_state.get("inventory_selection", 0)
        self.game_engine.lore_viewer_selection = ui_state.get("lore_viewer_selection", 0)

    def _deserialize_inventory(self, items_data: list[dict]) -> list:
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
                    quantity=item_data.get("quantity", 1),
                )
                item.discovered = item_data.get("discovered", False)
                items.append(item)
            elif item_data["type"] == "exploit":
                if item_data["exploit_key"] in GameData.EXPLOITS:
                    exploit_def = GameData.EXPLOITS[item_data["exploit_key"]]
                    item = ExploitItem(item_data["exploit_key"], exploit_def)
                    items.append(item)
                else:
                    # Exploit was removed or renamed - log for debugging
                    logging.warning(
                        f"Saved exploit '{item_data['exploit_key']}' not found in game data, skipping"
                    )
            elif item_data["type"] == "story_fragment":
                item = StoryFragment(item_data["fragment_index"])
                items.append(item)

        return items

    def _restore_map_items(self, map_data: dict) -> None:
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
                quantity=patch_data["quantity"],
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
                try:
                    enemy_id = int(enemy_id_str)
                except ValueError:
                    logging.warning(f"Invalid enemy_id in save: {enemy_id_str}, skipping")
                    continue
                position = Position(pos_data["x"], pos_data["y"])
                turn_seen = pos_data["turn"]
                game_map.last_known_enemy_positions[enemy_id] = (position, turn_seen)

        # A20: Restore used blind spots
        if "used_blind_spots" in map_data:
            game_map.used_blind_spots.clear()
            for tile_str in map_data["used_blind_spots"]:
                position = parse_coordinate_string(tile_str)
                if position:
                    # Remove from active blind spots (they were consumed)
                    pos_tuple = (position.x, position.y)
                    if pos_tuple in game_map.blind_spots:
                        game_map.blind_spots.remove(pos_tuple)
                    game_map.used_blind_spots.add(pos_tuple)

        # A13+: Restore node capacity state
        if "node_capacity" in map_data:
            node_capacity = map_data["node_capacity"]
            self._restore_node_capacity(
                node_capacity.get("cooling", {}), game_map.cooling_nodes
            )
            self._restore_node_capacity(
                node_capacity.get("cpu", {}), game_map.cpu_recovery_nodes
            )
            self._restore_node_capacity(
                node_capacity.get("ghost", {}), game_map.ghost_nodes
            )

    def _restore_node_capacity(
        self, capacity_data: dict[str, int], node_collection: dict
    ) -> None:
        """
        Restore used_capacity for nodes from save data.

        Args:
            capacity_data: Dict of "x,y" -> used_capacity from save
            node_collection: The game_map node dict (cooling_nodes, cpu_recovery_nodes, etc.)
        """
        for pos_str, used_capacity in capacity_data.items():
            position = parse_coordinate_string(pos_str)
            if position and (position.x, position.y) in node_collection:
                node_collection[(position.x, position.y)].used_capacity = used_capacity

    def _restore_enemies(self, enemies_data: list[dict]) -> None:
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

            enemy.state = (
                EnemyState(enemy_data["state"])
                if isinstance(enemy_data["state"], str)
                else enemy_data["state"]
            )
            enemy.move_cooldown = enemy_data["move_cooldown"]
            enemy.disabled_turns = enemy_data["disabled_turns"]
            enemy.blinded_turns = enemy_data.get("blinded_turns", 0)
            enemy.alert_timer = enemy_data["alert_timer"]
            enemy.patrol_index = enemy_data["patrol_index"]
            enemy.last_target = (
                Position(enemy_data["last_target"]["x"], enemy_data["last_target"]["y"])
                if enemy_data.get("last_target")
                else None
            )

            if enemy_data.get("last_seen_player"):
                enemy.last_seen_player = Position(
                    enemy_data["last_seen_player"]["x"], enemy_data["last_seen_player"]["y"]
                )

            if "patrol_points" in enemy_data:
                enemy.patrol_points = [
                    Position(point["x"], point["y"]) for point in enemy_data["patrol_points"]
                ]

            # Restore movement queue
            if "move_queue" in enemy_data:
                enemy.move_queue = [
                    Position(point["x"], point["y"]) for point in enemy_data["move_queue"]
                ]

            # Restore patrol restoration state (for hostile enemies returning to patrol)
            enemy.original_patrol_index = enemy_data.get("original_patrol_index", 0)

            # Restore original movement type (for virus mimic behavior)
            if "original_movement_type" in enemy_data:
                from game_entities import EnemyMovement

                enemy.original_movement_type = EnemyMovement(
                    enemy_data["original_movement_type"]
                )

            # Re-apply ascension modifiers for vision and damage (A4 damage, A1/A5 vision)
            # We DON'T want HP bonus to be re-applied since we restore from saved state
            # Instead, save the cpu/max_cpu, apply modifiers, then restore saved values
            saved_cpu = enemy.cpu
            saved_max_cpu = enemy_data.get("max_cpu", enemy.max_cpu)
            enemy.apply_ascension_modifiers(self.game_engine.ascension_modifiers)
            # Restore exact saved HP state - this preserves the ascension level from save time
            enemy.cpu = saved_cpu
            enemy.max_cpu = saved_max_cpu

            self.game_engine.enemy_manager.enemies.append(enemy)
