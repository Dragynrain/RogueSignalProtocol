#!/usr/bin/env python3
"""
Game Save/Load Manager - Extracted from game_engine.py
Handles all save and load operations for better separation of concerns.
"""

import logging
import random
import traceback
from typing import Dict, Any, Optional, List

from game_config import GameConfig
from game_entities import Position, Colors, parse_coordinate_string, EnemyState
from game_characters import Enemy
from game_save import SaveGameManager


class GameSaveLoadManager:
    """
    Manages save and load operations for the game engine.
    Extracted to improve separation of concerns and reduce GameEngine complexity.
    """

    def __init__(self, game_engine):
        """Initialize with reference to game engine."""
        self.game_engine = game_engine

    def load_game_state(self) -> bool:
        """Load complete game state from save file."""
        save_data = SaveGameManager.load_game()
        if not save_data:
            return False

        try:
            self._restore_core_game_state(save_data)
            self._restore_player_state(save_data["player"])
            self._restore_game_effects(save_data)
            self._sync_code_discovered_status()
            self._restore_ui_state(save_data)

            # Generate level layout for map structure
            self.game_engine.level_generator.generate_level(
                self.game_engine.game_state.level,
                self.game_engine.game_state.dungeon_seed
            )

            # Restore map items and enemies
            self._restore_map_items(save_data["map_state"])
            self._restore_enemies(save_data["enemies"])

            # Restore Enemy class counter
            if "enemy_next_id" in save_data:
                Enemy._next_id = save_data["enemy_next_id"]

            self.game_engine.message_log.add_message("Game loaded successfully!", Colors.GREEN)
            return True

        except Exception as e:
            error_msg = f"Failed to restore game state: {e}"
            print(error_msg)
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            return False

    def _restore_core_game_state(self, save_data: Dict[str, Any]) -> None:
        """Restore core game state from save data."""
        game_state = self.game_engine.game_state
        game_state.level = save_data.get("level", 1)
        game_state.turn = save_data.get("turn", 0)
        game_state.game_over = save_data.get("game_over", False)
        game_state.admin_spawned = save_data.get("admin_spawned", False)
        game_state.dungeon_seed = save_data.get("dungeon_seed", random.randint(1, GameConfig.DUNGEON_SEED_RANGE))
        game_state.just_loaded = True  # Set flag to prevent immediate enemy state updates

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
            'data_mimic_turns': 0,
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

        game_state = self.game_engine.game_state
        game_state.threat_scan_turns = effects_data.get("threat_scan_turns", 0)
        game_state.noise_locations = [
            Position(loc["x"], loc["y"]) for loc in effects_data.get("noise_locations", [])
        ]

        # Restore distraction points with error handling
        game_state.distraction_points = {}
        for pos_str, turns in effects_data.get("distraction_points", {}).items():
            position = parse_coordinate_string(pos_str)
            if position:  # Skip malformed coordinate data
                game_state.distraction_points[position] = turns

        # Restore revealed special nodes
        game_state.revealed_special_nodes = {}
        for pos_str, node_type in effects_data.get("revealed_special_nodes", {}).items():
            pos_parts = pos_str.split(',')
            if len(pos_parts) == 2:
                try:
                    x, y = int(pos_parts[0]), int(pos_parts[1])
                    game_state.revealed_special_nodes[(x, y)] = node_type
                except ValueError:
                    pass  # Skip malformed coordinate data

        # Restore code effects (backward compatibility)
        self.game_engine.code_hack_effects = save_data.get("code_hack_effects", {})
        self.game_engine.discovered_code_effects = save_data.get("discovered_code_effects", {})

    def _restore_ui_state(self, save_data: Dict[str, Any]) -> None:
        """Restore UI state from save data."""
        ui_state = save_data.get("ui_state", {})
        engine = self.game_engine

        engine.show_inventory = ui_state.get("show_inventory", False)
        engine.show_help = ui_state.get("show_help", False)
        engine.show_gateway_confirmation = ui_state.get("show_gateway_confirmation", False)
        engine.show_story_fragment = ui_state.get("show_story_fragment")
        engine.last_node_position = ui_state.get("last_node_position")
        if engine.last_node_position:
            engine.last_node_position = tuple(engine.last_node_position)
        engine.show_lore_viewer = ui_state.get("show_lore_viewer", False)
        engine.lore_viewer_selection = ui_state.get("lore_viewer_selection", 0)
        engine.lore_viewer_mode = ui_state.get("lore_viewer_mode", "list")
        engine.inventory_selection = ui_state.get("inventory_selection", 0)

        # Targeting system
        engine.targeting_mode = ui_state.get("targeting_mode", False)
        engine.targeting_exploit = ui_state.get("targeting_exploit")
        cursor_pos = ui_state.get("cursor_position", [0, 0])
        engine.cursor_position = Position(cursor_pos[0], cursor_pos[1])

        # Overclocking system
        engine.overclock_confirmation = ui_state.get("overclock_confirmation", False)
        engine.overclock_exploit = ui_state.get("overclock_exploit")

    def _restore_map_items(self, map_state: Dict[str, Any]) -> None:
        """Restore map items from save data."""
        game_map = self.game_engine.game_map

        # Restore gateways
        gateway_data = map_state.get("gateways", [])
        game_map.gateways = {Position(gw["x"], gw["y"]) for gw in gateway_data}

        # Restore data nodes
        node_data = map_state.get("data_nodes", [])
        game_map.data_nodes = {Position(node["x"], node["y"]) for node in node_data}

    def _restore_enemies(self, enemies_data: List[Dict[str, Any]]) -> None:
        """Restore enemies from save data."""
        from game_characters import Enemy

        enemy_manager = self.game_engine.enemy_manager
        enemy_manager.enemies.clear()

        for enemy_data in enemies_data:
            try:
                position = Position(enemy_data["x"], enemy_data["y"])
                enemy = Enemy(position, enemy_data["type"])

                # Restore enemy state
                enemy.cpu = enemy_data.get("cpu", enemy.type_data.cpu)
                enemy.max_cpu = enemy_data.get("max_cpu", enemy.type_data.cpu)
                enemy.state = EnemyState(enemy_data.get("state", EnemyState.UNAWARE.value))
                enemy.alert_timer = enemy_data.get("alert_timer", 0)
                enemy.disabled_turns = enemy_data.get("disabled_turns", 0)
                enemy.move_cooldown = enemy_data.get("move_cooldown", 0)

                # Restore movement data
                if "last_seen_player" in enemy_data and enemy_data["last_seen_player"]:
                    lsp = enemy_data["last_seen_player"]
                    enemy.last_seen_player = Position(lsp["x"], lsp["y"])

                # Restore patrol points
                patrol_data = enemy_data.get("patrol_points", [])
                enemy.patrol_points = [Position(p["x"], p["y"]) for p in patrol_data]
                enemy.patrol_index = enemy_data.get("patrol_index", 0)

                # Restore movement queue
                move_queue_data = enemy_data.get("move_queue", [])
                enemy.move_queue = [Position(p["x"], p["y"]) for p in move_queue_data]

                # Restore queue target
                queue_target_data = enemy_data.get("queue_target")
                if queue_target_data:
                    enemy._queue_target = Position(queue_target_data["x"], queue_target_data["y"])

                enemy_manager.enemies.append(enemy)

            except Exception as e:
                error_msg = f"Failed to restore enemy: {e}"
                print(error_msg)
                logging.warning(error_msg)

    def _deserialize_inventory(self, inventory_data: List[Dict[str, Any]]) -> List:
        """Deserialize inventory items from save data."""
        from game_inventory import InventoryItem, CodeHack, ExploitItem, StoryFragment

        items = []
        for item_data in inventory_data:
            try:
                item_type = item_data.get("type", "item")

                if item_type == "code_hack":
                    item = CodeHack(
                        color_name=item_data["color"],
                        effect=item_data["effect"],
                        name=item_data["name"],
                        description=item_data["description"],
                        quantity=item_data.get("quantity", 1)
                    )
                    # Restore discovered status
                    item.discovered = item_data.get("discovered", False)
                elif item_type == "exploit":
                    from game_data import GameData
                    exploit_key = item_data["exploit_key"]
                    if exploit_key in GameData.EXPLOITS:
                        exploit_def = GameData.EXPLOITS[exploit_key]
                        item = ExploitItem(exploit_key, exploit_def)
                    else:
                        # Skip invalid exploit - log warning
                        logging.warning(f"Skipping invalid exploit during load: {exploit_key}")
                        continue
                elif item_type == "story_fragment":
                    fragment_index = item_data.get("fragment_index", 0)
                    item = StoryFragment(fragment_index)
                else:
                    item = InventoryItem(
                        name=item_data["name"],
                        item_type=item_type,
                        description=item_data.get("description", "")
                    )

                items.append(item)

            except Exception as e:
                error_msg = f"Failed to deserialize inventory item: {e}"
                print(error_msg)
                logging.warning(error_msg)

        return items

    def _sync_code_discovered_status(self) -> None:
        """Sync discovered code hack status with inventory."""
        player = self.game_engine.player

        for item in player.inventory_manager.items:
            if hasattr(item, 'effect_text') and item.effect_text in self.game_engine.code_hack_effects:
                discovered_name = self.game_engine.code_hack_effects[item.effect_text][0]
                if discovered_name not in self.game_engine.discovered_code_effects:
                    self.game_engine.discovered_code_effects[discovered_name] = item.effect_text