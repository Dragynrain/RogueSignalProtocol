#!/usr/bin/env python3
"""
Save game management system.
Extracted from RogueSignalProtocol.py for better organization.
"""

import json
import os
import time
import logging
from typing import List, Dict, Any, Optional

# Import game modules
from game_config import GameConfig
from game_characters import Enemy


class SaveGameManager:
    """Manages complete game save/load operations."""
    
    SAVE_FILE = "rogue_signal_save.json"
    
    @classmethod
    def save_exists(cls) -> bool:
        """Check if a save file exists."""
        return os.path.exists(cls.SAVE_FILE)
    
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
    def save_game(cls, game: 'GameEngine') -> bool:
        """Save complete game state to file with robust error handling."""
        if game is None:
            logging.error("Cannot save: game object is None")
            return False
        
        if game.player is None:
            logging.error("Cannot save: player object is None") 
            return False
            
        # Attempt save with retry logic
        for attempt in range(GameConfig.MAX_SAVE_ATTEMPTS):
            try:
                # Gather all game state data
                save_data = {
                    "version": "dev",
                    "timestamp": time.time(),
                    
                    # Game state
                    "level": game.level,
                    "turn": game.turn,
                    "game_over": game.game_over,
                    "admin_spawned": game.admin_spawned,
                    "dungeon_seed": game.game_state.dungeon_seed,
                    
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
                        "detection": game.player.detection,
                        "ram_total": game.player.ram_total,
                        "speed_moves_remaining": game.player.speed_moves_remaining,
                        "temporary_effects": dict(game.player.temporary_effects),
                        "equipped_exploits": game.player.inventory_manager.equipped_exploits.copy(),
                        "max_equipped_exploits": game.player.inventory_manager.max_equipped_exploits,
                        "inventory_items": cls._serialize_inventory(game.player.inventory_manager.items)
                    },
                    
                    # Game effects and state
                    "game_effects": {
                        "threat_scan_turns": game.game_state.threat_scan_turns,
                        "noise_locations": [{"x": pos.x, "y": pos.y} for pos in game.game_state.noise_locations],
                        "distraction_points": {f"{pos.x},{pos.y}": turns for pos, turns in game.game_state.distraction_points.items()}
                    },
                    
                    # Map state (items and special locations only - layout regenerated)
                    "map_state": {
                        "code_hacks": cls._serialize_code_hacks(game.game_map.code_hacks),
                        "exploit_pickups": cls._serialize_exploit_pickups(game.game_map.exploit_pickups),
                        "permanent_upgrades": {f"{pos[0]},{pos[1]}": upgrade_key for pos, upgrade_key in game.game_map.permanent_upgrades.items()},
                        "story_fragments": {f"{pos[0]},{pos[1]}": fragment.fragment_index for pos, fragment in game.game_map.story_fragments.items()},
                        "gateway": {"x": game.game_map.gateway.x, "y": game.game_map.gateway.y} if game.game_map.gateway else None,
                        "explored_tiles": [f"{x},{y}" for x, y in game.game_map.explored_tiles],
                        "last_known_enemy_positions": {str(enemy_id): {"x": pos.x, "y": pos.y, "turn": turn} for enemy_id, (pos, turn) in game.game_map.last_known_enemy_positions.items()}
                    },
                    
                    # Enemies
                    "enemies": cls._serialize_enemies(game.enemies),
                    "enemy_next_id": getattr(Enemy, '_next_id', 1),
                    
                    # Data patch effects for this run
                    "code_hack_effects": game.code_hack_effects,
                    "discovered_code_effects": game.discovered_code_effects,
                    
                    # Overclocking state
                    "overclock_confirmation": getattr(game, 'overclock_confirmation', False),
                    "overclock_exploit": getattr(game, 'overclock_exploit', None),
                    
                    # UI state (optional - for better user experience)
                    "ui_state": {
                        "inventory_selection": game.inventory_selection,
                        "lore_viewer_selection": game.lore_viewer_selection
                    }
                }
            
                # Write to temporary file first, then atomic rename for safety
                temp_file = cls.SAVE_FILE + '.tmp'
                try:
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(save_data, f, indent=2, ensure_ascii=False, default=cls._numpy_converter)
                    
                    # Atomic rename to prevent corruption
                    import shutil
                    shutil.move(temp_file, cls.SAVE_FILE)
                    
                    logging.info("Game saved successfully")
                    return True
                finally:
                    # Clean up temp file if it exists
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except (OSError, FileNotFoundError):
                            pass  # Temp file cleanup failure is not critical
                
            except (IOError, OSError) as e:
                logging.warning(f"Save attempt {attempt + 1} failed with I/O error: {e}")
                if attempt == GameConfig.MAX_SAVE_ATTEMPTS - 1:
                    logging.error("All save attempts failed")
                    return False
                time.sleep(0.1)  # Brief delay before retry
                
            except (ValueError, TypeError) as e:
                logging.error(f"Data serialization error (no retry): {e}")
                return False
                
            except (PermissionError, OSError) as e:
                logging.error(f"File system error during save: {e}")
                return False
            except TypeError as e:
                logging.error(f"JSON encoding error during save: {e}")
                return False
            except Exception as e:
                import traceback
                logging.error(f"Unexpected save error: {e}")
                logging.error(traceback.format_exc())
                return False
                
        return False  # Should never reach here
    
    @classmethod
    def load_game(cls) -> Optional[Dict[str, Any]]:
        """Load complete game state from file."""
        if not cls.save_exists():
            return None
            
        try:
            # Read file content first to check for corruption
            with open(cls.SAVE_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Check if file is empty or contains only whitespace
            if not content:
                logging.error("Save file is empty or corrupted")
                return None
            
            # Try to parse JSON with better error reporting
            try:
                save_data = json.loads(content)
                logging.info("Game loaded successfully")
                return save_data
            except json.JSONDecodeError as e:
                logging.error(f"Save file corrupted - JSON decode error at line {e.lineno}, column {e.colno}: {e.msg}")
                logging.error(f"Problematic content around error: {content[max(0, e.pos-50):e.pos+50]}")
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
                os.remove(cls.SAVE_FILE)
                logging.info("Save file deleted")
            return True
        except Exception as e:
            import traceback
            logging.error(f"Failed to delete save: {e}")
            logging.error(traceback.format_exc())
            return False
    
    @classmethod
    def get_save_timestamp(cls) -> Optional[str]:
        """Get formatted timestamp of save file."""
        if not cls.save_exists():
            return None
        
        try:
            save_data = cls.load_game()
            if save_data and "timestamp" in save_data:
                import datetime
                timestamp = save_data["timestamp"]
                dt = datetime.datetime.fromtimestamp(timestamp)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # Fallback to file modification time
                import datetime
                stat_result = os.stat(cls.SAVE_FILE)
                dt = datetime.datetime.fromtimestamp(stat_result.st_mtime)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            import traceback
            logging.warning(f"Could not get save timestamp: {e}")
            logging.warning(traceback.format_exc())
            return "Unknown"
    
    @classmethod
    def _serialize_inventory(cls, items: List) -> List[Dict[str, Any]]:
        """Serialize inventory items."""
        serialized = []
        for item in items:
            if hasattr(item, 'item_type'):
                item_data = {
                    "type": item.item_type,
                    "name": item.name,
                    "description": item.description
                }
                
                if hasattr(item, 'color_name'):  # CodeHack
                    item_data.update({
                        "color": item.color_name,
                        "effect": item.effect,
                        "quantity": getattr(item, 'quantity', 1),
                        "discovered": getattr(item, 'discovered', False)
                    })
                elif hasattr(item, 'exploit_key'):  # ExploitItem
                    item_data.update({
                        "exploit_key": item.exploit_key,
                        "ram_cost": item.ram_cost
                    })
                elif hasattr(item, 'fragment_index'):  # StoryFragment
                    item_data.update({
                        "fragment_index": item.fragment_index
                    })
                
                serialized.append(item_data)
        
        return serialized
    
    @classmethod
    def _serialize_code_hacks(cls, patches: Dict) -> Dict[str, Dict]:
        """Serialize codes."""
        return {
            f"{pos[0]},{pos[1]}": {
                "color": patch.color_name,
                "effect": patch.effect,
                "name": patch.name,
                "quantity": patch.quantity,
                "discovered": patch.discovered
            }
            for pos, patch in patches.items()
        }
    
    @classmethod
    def _serialize_exploit_pickups(cls, exploits: Dict) -> Dict[str, str]:
        """Serialize exploit pickups."""
        return {
            f"{pos[0]},{pos[1]}": exploit.exploit_key 
            for pos, exploit in exploits.items()
        }
    
    @classmethod
    def _serialize_enemies(cls, enemies: List) -> List[Dict[str, Any]]:
        """Serialize enemy data."""
        serialized = []
        for enemy in enemies:
            enemy_data = {
                "id": enemy.id,
                "type": enemy.type,
                "x": enemy.position.x,
                "y": enemy.position.y,
                "cpu": enemy.cpu,
                "state": enemy.state.value,
                "move_cooldown": enemy.move_cooldown,
                "disabled_turns": enemy.disabled_turns,
                "alert_timer": enemy.alert_timer,
                "patrol_index": enemy.patrol_index,
                "patrol_stuck_counter": enemy.patrol_stuck_counter,
                "movement_queue": [{"x": pos.x, "y": pos.y} for pos in getattr(enemy, 'movement_queue', [])],
                "last_target": {"x": enemy.last_target.x, "y": enemy.last_target.y} if enemy.last_target else None,
                "last_seen_player": {
                    "x": enemy.last_seen_player.x, 
                    "y": enemy.last_seen_player.y
                } if enemy.last_seen_player else None
            }
            
            if enemy.patrol_points:
                enemy_data["patrol_points"] = [
                    {"x": point.x, "y": point.y} 
                    for point in enemy.patrol_points
                ]
            
            serialized.append(enemy_data)
        
        return serialized