#!/usr/bin/env python3
"""
Rogue Signal Protocol - Save Game Management

Complete game state serialization and deserialization system.
Handles JSON save/load with numpy type conversion and robust error handling.
Deletes save file on player death (per game design). Single save slot system.
"""

import json
import logging
import os
import time
from typing import TYPE_CHECKING, Any

# Import game modules
from rsp.core.config import GameConfig
from rsp.core.file_paths import get_data_directory
from rsp.core.version import VERSION
from rsp.entities.position import serialize_position_dict, tuple_to_coord_string

if TYPE_CHECKING:
    from rsp.core.engine import GameEngine


class SaveLoadError(Exception):
    """Raised when save file fails to load properly."""


class SaveGameManager:
    """Manages complete game save/load operations."""

    @classmethod
    def _get_save_file_path(cls) -> str:
        """Get the path to the save file (supports portable/AppData modes)."""
        return str(get_data_directory() / "saves" / "rogue_signal_save.json")

    @classmethod
    def save_exists(cls) -> bool:
        """Check if a save file exists."""
        return os.path.exists(cls._get_save_file_path())

    @staticmethod
    def _numpy_converter(obj):
        """Convert numpy types to native Python types for JSON serialization."""
        import numpy as np

        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    @classmethod
    def create_save_data(cls, game: "GameEngine") -> dict:
        """
        Create save data dictionary from game state.

        This method extracts the current game state into a dictionary that can be:
        - Written to a save file (via save_game)
        - Included in debug packages (via debug_export)
        - Used for any other serialization needs

        Args:
            game: The GameEngine instance to serialize

        Returns:
            Dictionary containing complete game state

        Raises:
            ValueError: If game or player state is invalid
        """
        if game is None:
            raise ValueError("Cannot create save data: game object is None")
        if game.player is None:
            raise ValueError("Cannot create save data: player object is None")

        # Gather all game state data
        save_data = {
            "version": VERSION,
            "timestamp": time.time(),
            # Game state
            "level": game.level,
            "turn": game.turn,
            "game_over": game.game_over,
            "admin_spawned": game.admin_spawned,
            "dungeon_seed": game.game_state.dungeon_seed,
            # Ascension state
            "ascension_level": game.ascension_level,
            # Player state
            "player": {
                "x": game.player.x,
                "y": game.player.y,
                "last_x": game.player.last_position.x,
                "last_y": game.player.last_position.y,
                "cpu": game.player.cpu,
                "max_cpu": game.player.max_cpu,
                "heat": game.player.heat,
                "max_heat": game.player.max_heat,
                "trace_level": game.player.trace_level,
                "ram_total": game.player.ram_total,
                "speed_moves_remaining": game.player.speed_moves_remaining,
                "temporary_effects": dict(game.player.temporary_effects),
                "equipped_exploits": game.player.inventory_manager.equipped_exploits.copy(),
                "max_equipped_exploits": game.player.inventory_manager.max_equipped_exploits,
                "inventory_items": cls._serialize_inventory(game.player.inventory_manager.items),
            },
            # Game effects and state
            "game_effects": {
                "threat_scan_turns": game.game_state.threat_scan_turns,
                "noise_locations": [
                    {"x": pos.x, "y": pos.y} for pos in game.game_state.noise_locations
                ],
                "distraction_points": {
                    pos.to_coord_string(): turns
                    for pos, turns in game.game_state.distraction_points.items()
                },
                "revealed_special_nodes": serialize_position_dict(
                    game.game_state.revealed_special_nodes
                ),
            },
            # Map state (items and special locations only - layout regenerated)
            "map_state": {
                "code_hacks": cls._serialize_code_hacks(game.game_map.code_hacks),
                "exploit_pickups": cls._serialize_exploit_pickups(game.game_map.exploit_pickups),
                "permanent_upgrades": serialize_position_dict(game.game_map.permanent_upgrades),
                "story_fragments": {
                    tuple_to_coord_string(pos): fragment.fragment_index
                    for pos, fragment in game.game_map.story_fragments.items()
                },
                "gateway": (
                    {"x": game.game_map.gateway.x, "y": game.game_map.gateway.y}
                    if game.game_map.gateway
                    else None
                ),
                "explored_tiles": [
                    tuple_to_coord_string(pos) for pos in game.game_map.explored_tiles
                ],
                "last_known_enemy_positions": {
                    str(enemy_id): {"x": pos.x, "y": pos.y, "turn": turn}
                    for enemy_id, (pos, turn) in game.game_map.last_known_enemy_positions.items()
                },
                # A20: Used blind spots
                "used_blind_spots": [
                    tuple_to_coord_string(pos) for pos in game.game_map.used_blind_spots
                ],
                # A13+: Node capacity state
                "node_capacity": {
                    "cooling": cls._serialize_node_capacity(game.game_map.cooling_nodes),
                    "cpu": cls._serialize_node_capacity(game.game_map.cpu_recovery_nodes),
                    "ghost": cls._serialize_node_capacity(game.game_map.ghost_nodes),
                },
            },
            # Enemies
            "enemies": cls._serialize_enemies(game.enemies),
            # Enemy ID counter passed from game engine (avoids importing Enemy class)
            "enemy_next_id": game.get_enemy_id_counter(),
            # Code hack effects for this run
            "code_hack_effects": game.code_hack_effects,
            "discovered_code_effects": game.discovered_code_effects,
            # Overclocking state
            "overclock_confirmation": getattr(game, "overclock_confirmation", False),
            "overclock_exploit": getattr(game, "overclock_exploit", None),
            # UI state (optional - for better user experience)
            "ui_state": {
                "inventory_selection": game.inventory_selection,
                "lore_viewer_selection": game.lore_viewer_selection,
            },
            # Session metrics tracking
            "session_metrics": cls._serialize_metrics(game),
        }

        return save_data

    @classmethod
    def save_game(cls, game: "GameEngine") -> bool:
        """Save complete game state to file with robust error handling.

        Returns False without saving in prologue mode (tutorial doesn't persist).
        """
        if game is None:
            logging.error("Cannot save: game object is None")
            return False

        if game.player is None:
            logging.error("Cannot save: player object is None")
            return False

        # Prevent saving in prologue mode - tutorial state doesn't persist
        if getattr(game, "prologue_mode", False):
            logging.debug("Save skipped: prologue mode")
            return False

        # Ensure saves directory exists
        os.makedirs(os.path.dirname(cls._get_save_file_path()), exist_ok=True)

        # Attempt save with retry logic
        for attempt in range(GameConfig.MAX_SAVE_ATTEMPTS):
            try:
                logging.info(
                    f"Save: Attempt {attempt+1}/{GameConfig.MAX_SAVE_ATTEMPTS}, level={game.level}, turn={game.turn}, player_pos=({game.player.x},{game.player.y}), seed={game.game_state.dungeon_seed}"
                )

                # Create save data using the shared method
                save_data = cls.create_save_data(game)

                # Write to temporary file first, then atomic rename for safety
                temp_file = cls._get_save_file_path() + ".tmp"
                try:
                    with open(temp_file, "w", encoding="utf-8") as f:
                        json.dump(
                            save_data, f, indent=2, ensure_ascii=False, default=cls._numpy_converter
                        )

                    # Atomic rename to prevent corruption
                    import shutil

                    shutil.move(temp_file, cls._get_save_file_path())

                    file_size = os.path.getsize(cls._get_save_file_path())
                    logging.info(
                        f"Save: Successful, file={cls._get_save_file_path()}, size={file_size} bytes, enemies={len(game.enemies)}"
                    )
                    return True
                finally:
                    # Clean up temp file if it exists
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except (OSError, FileNotFoundError) as e:
                            logging.debug(f"Temp file cleanup failed (non-critical): {e}")

            except PermissionError as e:
                # PermissionError is non-retryable - fail immediately
                logging.error(f"Permission denied during save (no retry): {e}")
                return False

            except OSError as e:
                # Other I/O errors are retryable
                logging.warning(f"Save attempt {attempt + 1} failed with I/O error: {e}")
                if attempt == GameConfig.MAX_SAVE_ATTEMPTS - 1:
                    logging.error("All save attempts failed")
                    return False
                time.sleep(0.1)  # Brief delay before retry

            except (ValueError, TypeError) as e:
                logging.error(f"Data serialization error (no retry): {e}")
                return False
            except Exception as e:
                import traceback

                logging.error(f"Unexpected save error: {e}")
                logging.error(traceback.format_exc())
                return False

        return False  # Should never reach here

    @classmethod
    def load_game(cls) -> dict[str, Any] | None:
        """Load complete game state from file."""
        if not cls.save_exists():
            return None

        try:
            # Read file content first to check for corruption
            with open(cls._get_save_file_path(), encoding="utf-8") as f:
                content = f.read().strip()

            # Check if file is empty or contains only whitespace
            if not content:
                logging.error("Save file is empty or corrupted")
                return None

            # Try to parse JSON with better error reporting
            try:
                save_data = json.loads(content)
                level = save_data.get("level", "?")
                turn = save_data.get("turn", "?")
                player_data = save_data.get("player", {})
                player_cpu = player_data.get("cpu", "?")
                enemy_count = len(save_data.get("enemies", []))
                logging.info(
                    f"Load: Successful, level={level}, turn={turn}, player_cpu={player_cpu}, enemies={enemy_count}"
                )
                return save_data
            except json.JSONDecodeError as e:
                logging.error(
                    f"Save file corrupted - JSON decode error at line {e.lineno}, column {e.colno}: {e.msg}"
                )
                logging.error(
                    f"Problematic content around error: {content[max(0, e.pos-50):e.pos+50]}"
                )
                return None

        except FileNotFoundError:
            logging.info("No save file found")
            return None
        except PermissionError as e:
            logging.error(f"Permission denied accessing save file: {e}")
            return None
        except Exception as e:
            import traceback

            logging.error(f"Failed to load game: {e}")
            logging.error(traceback.format_exc())
            return None

    @classmethod
    def delete_save(cls) -> bool:
        """Delete the save file."""
        try:
            if cls.save_exists():
                logging.debug(
                    f"Save: Deleting save file: {cls._get_save_file_path()} (reason: player death)"
                )
                os.remove(cls._get_save_file_path())
                logging.info("Save: File deleted successfully")
            return True
        except Exception as e:
            import traceback

            logging.error(f"Failed to delete save: {e}")
            logging.error(traceback.format_exc())
            return False

    @classmethod
    def get_save_timestamp(cls) -> str | None:
        """Get formatted timestamp of save file.

        Uses file modification time for performance - avoids loading entire save file
        just to display timestamp in menu (was causing 60 load_game() calls per second).
        """
        if not cls.save_exists():
            return None

        try:
            # Use file modification time directly (fast, no disk I/O beyond stat)
            import datetime

            stat_result = os.stat(cls._get_save_file_path())
            dt = datetime.datetime.fromtimestamp(stat_result.st_mtime)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            import traceback

            logging.warning(f"Could not get save timestamp: {e}")
            logging.warning(traceback.format_exc())
            return "Unknown"

    @classmethod
    def get_save_info(cls) -> dict[str, Any] | None:
        """Get basic save file info without full load.

        Returns dict with ascension_level and level (floor), or None if no save.
        Caches result to avoid repeated file reads during menu rendering.
        """
        if not cls.save_exists():
            return None

        # Use a simple cache to avoid repeated reads during menu rendering
        cache_attr = "_save_info_cache"
        if hasattr(cls, cache_attr):
            cached = getattr(cls, cache_attr)
            # Invalidate cache if file was modified
            try:
                current_mtime = os.stat(cls._get_save_file_path()).st_mtime
                if cached and cached.get("_mtime") == current_mtime:
                    return cached
            except OSError:
                pass

        try:
            with open(cls._get_save_file_path(), encoding="utf-8") as f:
                data = json.load(f)

            info = {
                "ascension_level": data.get("ascension_level", 0),
                "level": data.get("level", 1),
                "_mtime": os.stat(cls._get_save_file_path()).st_mtime,
            }
            setattr(cls, cache_attr, info)
            return info
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Expected errors - file missing or corrupted
            logging.debug(f"Could not get save info: {e}")
            return None
        except (OSError, PermissionError) as e:
            # Permission or filesystem issues - worth logging more visibly
            logging.warning(f"Filesystem error reading save info: {e}")
            return None

    @classmethod
    def _serialize_inventory(cls, items: list) -> list[dict[str, Any]]:
        """Serialize inventory items."""
        serialized = []
        for item in items:
            if not hasattr(item, "item_type"):
                continue

            item_data = {"type": item.item_type, "name": item.name, "description": item.description}

            if hasattr(item, "color_name"):  # CodeHack
                item_data.update(
                    {
                        "color": item.color_name,
                        "effect": item.effect,
                        "quantity": getattr(item, "quantity", 1),
                        "discovered": getattr(item, "discovered", False),
                    }
                )
            elif hasattr(item, "exploit_key"):  # ExploitItem
                item_data.update({"exploit_key": item.exploit_key, "ram_cost": item.ram_cost})
            elif hasattr(item, "fragment_index"):  # StoryFragment
                item_data["fragment_index"] = item.fragment_index

            serialized.append(item_data)

        return serialized

    @classmethod
    def _serialize_code_hacks(cls, patches: dict) -> dict[str, dict]:
        """Serialize codes."""
        return {
            tuple_to_coord_string(pos): {
                "color": p.color_name,
                "effect": p.effect,
                "name": p.name,
                "quantity": p.quantity,
                "discovered": p.discovered,
            }
            for pos, p in patches.items()
        }

    @classmethod
    def _serialize_exploit_pickups(cls, exploits: dict) -> dict[str, str]:
        """Serialize exploit pickups."""
        return {tuple_to_coord_string(pos): e.exploit_key for pos, e in exploits.items()}

    @classmethod
    def _serialize_node_capacity(cls, nodes: dict) -> dict[str, int]:
        """Serialize node used_capacity values with coordinate string keys."""
        return {tuple_to_coord_string(pos): node.used_capacity for pos, node in nodes.items()}

    @classmethod
    def _serialize_enemies(cls, enemies: list) -> list[dict[str, Any]]:
        """Serialize enemy data."""
        serialized = []
        for e in enemies:
            enemy_data = {
                "id": e.id,
                "type": e.type,
                "x": e.position.x,
                "y": e.position.y,
                "cpu": e.cpu,
                "max_cpu": e.max_cpu,  # Save max_cpu for proper ascension handling
                "state": e.state.value,
                "move_cooldown": e.move_cooldown,
                "disabled_turns": e.disabled_turns,
                "blinded_turns": e.blinded_turns,
                "alert_timer": e.alert_timer,
                "patrol_index": e.patrol_index,
                "last_seen_player": (
                    {"x": e.last_seen_player.x, "y": e.last_seen_player.y}
                    if getattr(e, "last_seen_player", None)
                    else None
                ),
            }

            if e.patrol_points:
                enemy_data["patrol_points"] = [{"x": p.x, "y": p.y} for p in e.patrol_points]

            # Save movement queue
            if hasattr(e, "move_queue") and e.move_queue:
                enemy_data["move_queue"] = [{"x": p.x, "y": p.y} for p in e.move_queue]

            # Save patrol restoration state for hostile enemies returning to patrol
            enemy_data["original_patrol_index"] = e.original_patrol_index

            # Save original movement type for virus mimic behavior
            if e.original_movement_type is not None:
                enemy_data["original_movement_type"] = e.original_movement_type.value

            serialized.append(enemy_data)

        return serialized

    @classmethod
    def _serialize_metrics(cls, game: "GameEngine") -> dict[str, Any]:
        """Serialize session metrics for save file."""
        from rsp.systems.metrics import save_checkpoint

        return save_checkpoint()
