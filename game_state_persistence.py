#!/usr/bin/env python3
"""
Game State Persistence
Handles all save/load operations for the game state.
Extracted from game_engine.py for better separation of concerns.
"""

import logging
import traceback
import random
from typing import Dict, Any, List, Optional, Tuple

from game_config import GameConfig
from game_entities import Position, Colors, parse_coordinate_string
from game_save import SaveGameManager
from game_inventory import CodeHack, ExploitItem, StoryFragment
from game_data import GameData
from game_characters import Enemy


class GameStatePersistence:
    """Handles saving and loading game state data."""

    def __init__(self, game_engine):
        """Initialize with reference to game engine."""
        self.game_engine = game_engine

    def load_from_save(self) -> bool:
        """Load game state from save file."""
        save_data = SaveGameManager.load_game()
        if not save_data:
            return False

        try:
            self._restore_game_state(save_data)
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
        self.game_engine.game_state.dungeon_seed = save_data.get("dungeon_seed", random.randint(1, GameConfig.DUNGEON_SEED_RANGE))

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
        player.detection = player_data.get("detection", 0)
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

    def _sync_code_discovered_status(self) -> None:
        """Sync discovered status of inventory code hacks with global discovered effects."""
        for item in self.game_engine.player.inventory_manager.items:
            if isinstance(item, CodeHack):
                # Update discovered status based on global discovered effects
                item.discovered = item.color_name in self.game_engine.discovered_code_effects

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
            enemy.state = enemy_data["state"]
            enemy.move_cooldown = enemy_data["move_cooldown"]
            enemy.disabled_turns = enemy_data["disabled_turns"]
            enemy.alert_timer = enemy_data["alert_timer"]
            enemy.patrol_index = enemy_data["patrol_index"]
            enemy.patrol_stuck_counter = enemy_data.get("patrol_stuck_counter", 0)
            enemy.movement_queue = [Position(pos["x"], pos["y"]) for pos in enemy_data.get("movement_queue", [])]
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

            self.game_engine.enemy_manager.enemies.append(enemy)