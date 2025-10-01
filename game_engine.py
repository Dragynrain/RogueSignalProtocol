#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Engine
Main game orchestrator extracted from RogueSignalProtocol.py with dependency injection.
"""

import tcod
from tcod import libtcodpy
import logging
import traceback
import random
import math
import json
import os
import time
import copy
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

# Import all necessary modules
from game_config import GameSettings, GameConfig, GameBalance
from game_entities import (Position, Colors, EnemyState, EnemyMovement, 
                          validate_coordinates, calculate_manhattan_distance,
                          parse_coordinate_string, validate_position_bounds, ensure_color_tuple)
from game_data import GameData, GameUpgrades
from game_inventory import InventoryItem, CodeHack, ExploitItem, StoryFragment, InventoryManager
from game_characters import Player, Enemy, create_pathfinding_cost_map, pathfind_and_move, can_move_to_position
from game_audio import SoundManager
from game_save import SaveGameManager
from game_story import StoryFragmentManager
# Import from new modular game state system
from game_state import GameStateManager, TurnProcessor, MessageLog
from game_level import LevelGenerator
from game_enemies import EnemyManager
from game_combat import ExploitSystem
from game_map import GameMap
from game_input import InputHandler
from game_save_load_manager import GameSaveLoadManager


# Core game classes now imported from game_state module


class GameEngine:
    """
    Main game orchestrator that coordinates all game systems.
    Refactored to use dependency injection for better modularity and testability.
    """
    
    def __init__(self, 
                 game_state_manager: Optional[GameStateManager] = None,
                 game_map: Optional[GameMap] = None,
                 level_generator: Optional[LevelGenerator] = None,
                 enemy_manager: Optional[EnemyManager] = None,
                 exploit_system: Optional[ExploitSystem] = None,
                 input_handler: Optional[InputHandler] = None,
                 sound_manager: Optional[SoundManager] = None,
                 load_save: bool = False, 
                 settings: Optional[GameSettings] = None) -> None:
        """
        Initialize the game engine with dependency injection.
        
        Args:
            game_state_manager: Manages core game state (level, turn, etc.)
            game_map: Handles map data and spatial queries
            level_generator: Generates procedural levels
            enemy_manager: Manages all enemies in the game
            exploit_system: Handles exploit/combat system
            input_handler: Processes user input
            sound_manager: Manages audio and music
            load_save: Whether to load from existing save file
            settings: Game settings instance, creates default if None
        """
        # Initialize dependencies (with fallbacks if not provided)
        self.game_state = game_state_manager or GameStateManager()
        self.game_map = game_map or GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = level_generator or LevelGenerator(self.game_map)
        self.enemy_manager = enemy_manager or EnemyManager(self.game_map, None)  # Will set message_log below
        self.sound_manager = sound_manager or SoundManager(settings)
        
        # InputHandler will be initialized after we have the complete GameEngine instance
        self.input_handler = input_handler
        
        # Initialize core game objects
        self.player = Player(5, 5)
        self.message_log = MessageLog()
        
        # Update enemy manager with message log
        self.enemy_manager.message_log = self.message_log
        
        # Initialize turn processor with dependencies
        self.turn_processor = TurnProcessor(self.game_state, self.message_log)
        
        # Preload all sound effects
        self.sound_manager.preload_sounds()
        
        # UI state
        self.show_inventory = False
        self.show_help = False
        self.show_gateway_confirmation = False
        self.show_story_fragment: Optional[int] = None
        
        # Track when player first steps on nodes to avoid repeated sounds
        self.last_node_position: Optional[Tuple[int, int]] = None
        self.show_lore_viewer = False
        self.lore_viewer_selection = 0
        self.lore_viewer_mode = "list"
        self.inventory_selection = 0
        
        # Targeting system
        self.targeting_mode = False
        self.targeting_exploit: Optional[str] = None
        self.cursor_position = Position(0, 0)
        
        # Overclocking system
        self.overclock_confirmation = False
        self.overclock_exploit: Optional[str] = None
        
        # Code patch system
        self.code_hack_effects: Dict[str, Tuple[str, str]] = {}
        self.discovered_code_effects: Dict[str, str] = {}
        
        # Story fragment system
        self.story_fragment_manager = StoryFragmentManager()

        # Initialize save/load manager
        self.save_load_manager = GameSaveLoadManager(self)

        # Initialize game state
        if load_save:
            success = self.save_load_manager.load_game_state()
            if not success:
                # Fallback to new game if loading fails
                self._randomize_code_hacks()
                self._generate_procedural_level()
        else:
            self._randomize_code_hacks()
            self._generate_procedural_level()
            
        # Initialize InputHandler after GameEngine is fully set up (requires self reference)
        if self.input_handler is None:
            self.input_handler = InputHandler(self)
    
    # Properties for backward compatibility with existing code
    @property
    def level(self) -> int:
        """Current game level."""
        return self.game_state.level
    
    @level.setter
    def level(self, value: int) -> None:
        """Set current game level."""
        self.game_state.level = value
    
    @property
    def turn(self) -> int:
        """Current turn number."""
        return self.game_state.turn

    @turn.setter
    def turn(self, value: int) -> None:
        """Set current turn number."""
        self.game_state.turn = value
    
    @property
    def game_over(self) -> bool:
        """Whether the game is over."""
        return self.game_state.game_over
    
    @game_over.setter
    def game_over(self, value: bool) -> None:
        """Set game over state."""
        self.game_state.game_over = value
    
    @property
    def admin_spawned(self) -> bool:
        """Whether admin has been spawned."""
        return self.game_state.admin_spawned
    
    @admin_spawned.setter
    def admin_spawned(self, value: bool) -> None:
        """Set admin spawned state."""
        self.game_state.admin_spawned = value
    
    @property
    def enemies(self) -> List[Enemy]:
        """List of all enemies."""
        return self.enemy_manager.enemies

    @enemies.setter
    def enemies(self, value: List[Enemy]) -> None:
        """Set the enemies list."""
        self.enemy_manager.enemies = value
    
    def _get_enemy_at(self, position: Position) -> Optional[Enemy]:
        """Get enemy at position - for backward compatibility."""
        return self.enemy_manager.get_enemy_at_position(position)

    # Backward compatibility methods for tests
    def _process_player_turn(self):
        """Process player turn - wrapper around TurnProcessor for backward compatibility."""
        self.turn_processor.process_turn(self.player)

    def _process_enemy_turn(self):
        """Process enemy turns - for backward compatibility."""
        for enemy in self.enemies:
            if hasattr(enemy, 'move_cooldown'):
                if enemy.move_cooldown > 0:
                    enemy.move_cooldown -= 1
            if hasattr(enemy, 'disabled_turns'):
                if enemy.disabled_turns > 0:
                    enemy.disabled_turns -= 1

    def _process_enemies_turn(self):
        """Process enemies turn (plural) - for backward compatibility."""
        self._process_enemy_turn()

    def _process_player_temporary_effects(self):
        """Process player temporary effects - wrapper for backward compatibility."""
        self.player.update_effects()

    def _process_environmental_effects(self):
        """Process environmental effects - for backward compatibility."""
        # Update threat scan
        if self.game_state.threat_scan_turns > 0:
            self.game_state.threat_scan_turns -= 1

        # Update distraction points
        expired_points = []
        for position, turns_remaining in self.game_state.distraction_points.items():
            turns_remaining -= 1
            if turns_remaining <= 0:
                expired_points.append(position)
            else:
                self.game_state.distraction_points[position] = turns_remaining

        for position in expired_points:
            del self.game_state.distraction_points[position]
    
    def _load_from_save(self) -> bool:
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
            self.level_generator.generate_level(self.game_state.level, self.game_state.dungeon_seed)
            
            # Restore map items and enemies
            self._restore_map_items(save_data["map_state"])
            self._restore_enemies(save_data["enemies"])
            
            # Restore Enemy class counter
            if "enemy_next_id" in save_data:
                Enemy._next_id = save_data["enemy_next_id"]
            
            self.message_log.add_message_typed("Game loaded successfully!", Colors.GREEN)
            return True
            
        except Exception as e:
            logging.error(f"Failed to restore game state: {e}")
            logging.debug(traceback.format_exc())
            return False
    
    def _restore_game_state(self, save_data: Dict[str, Any]) -> None:
        """Restore core game state from save data."""
        self.game_state.level = save_data.get("level", 1)
        self.game_state.turn = save_data.get("turn", 0)
        self.game_state.game_over = save_data.get("game_over", False)
        self.game_state.admin_spawned = save_data.get("admin_spawned", False)
        self.game_state.dungeon_seed = save_data.get("dungeon_seed", random.randint(1, GameConfig.DUNGEON_SEED_RANGE))
    
    def _restore_player_state(self, player_data: Dict[str, Any]) -> None:
        """Restore player state from save data."""
        # Position
        self.player.x = player_data.get("x", 1)
        self.player.y = player_data.get("y", 1)
        self.player.last_position.x = player_data.get("last_x", self.player.x)
        self.player.last_position.y = player_data.get("last_y", self.player.y)
        
        # Core stats
        self.player.cpu = player_data.get("cpu", 100)
        self.player.max_cpu = player_data.get("max_cpu", 100)
        self.player.heat = player_data.get("heat", 0)
        self.player.max_heat = player_data.get("max_heat", 100)
        self.player.detection = player_data.get("detection", 0)
        self.player.ram_total = player_data.get("ram_total", 8)
        
        # Speed boost state
        self.player.speed_moves_remaining = player_data.get("speed_moves_remaining", 0)
        
        # Temporary effects with defaults
        self.player.temporary_effects = player_data.get("temporary_effects", {
            'speed_boost_turns': 0,
            'movement_slowed_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0,
            'data_mimic_turns': 0,
            'virus_turns': 0
        })
        
        # Restore inventory with defaults
        self.player.inventory_manager.equipped_exploits = player_data.get("equipped_exploits", [])
        self.player.inventory_manager.max_equipped_exploits = player_data.get("max_equipped_exploits", 5)
        inventory_items = player_data.get("inventory_items", [])
        self.player.inventory_manager.items = self._deserialize_inventory(inventory_items)
    
    def _restore_game_effects(self, save_data: Dict[str, Any]) -> None:
        """Restore game effects and environmental state from save data."""
        # Handle both old and new save format for backward compatibility
        if "game_effects" in save_data:
            effects_data = save_data["game_effects"]
        else:
            # Backward compatibility with old format
            effects_data = save_data
        
        self.game_state.threat_scan_turns = effects_data.get("threat_scan_turns", 0)
        self.game_state.noise_locations = [
            Position(loc["x"], loc["y"]) for loc in effects_data.get("noise_locations", [])
        ]
        
        # Restore distraction points with error handling
        self.game_state.distraction_points = {}
        for pos_str, turns in effects_data.get("distraction_points", {}).items():
            position = parse_coordinate_string(pos_str)
            if position:  # Skip malformed coordinate data
                self.game_state.distraction_points[position] = turns
        
        # Restore code effects (backward compatibility)
        self.code_hack_effects = save_data.get("code_hack_effects", save_data.get("data_patch_effects", {}))
        self.discovered_code_effects = save_data.get("discovered_code_effects", {})
        
        # Restore overclocking state
        self.overclock_confirmation = save_data.get("overclock_confirmation", False)
        self.overclock_exploit = save_data.get("overclock_exploit", None)
    
    def _sync_code_discovered_status(self) -> None:
        """Sync discovered status of inventory code hacks with global discovered effects."""
        for item in self.player.inventory_manager.items:
            if isinstance(item, CodeHack):
                # Update discovered status based on global discovered effects
                item.discovered = item.color_name in self.discovered_code_effects
    
    def _restore_ui_state(self, save_data: Dict[str, Any]) -> None:
        """Restore UI state from save data."""
        ui_state = save_data.get("ui_state", {})
        self.inventory_selection = ui_state.get("inventory_selection", 0)
        self.lore_viewer_selection = ui_state.get("lore_viewer_selection", 0)
    
    def _deserialize_inventory(self, items_data: List[Dict]) -> List:
        """Deserialize inventory items from save data."""
        items = []
        for item_data in items_data:
            if item_data["type"] == "code_hack":
                item = CodeHack(
                    color_name=item_data["color"],
                    effect=item_data["effect"],
                    name=item_data["name"],
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
        # Clear current items
        self.game_map.code_hacks.clear()
        self.game_map.exploit_pickups.clear()
        self.game_map.permanent_upgrades.clear()
        self.game_map.story_fragments.clear()
        
        # Restore code hacks (backward compatibility)
        code_hacks_data = map_data.get("code_hacks", map_data.get("data_patches", {}))
        for pos_str, patch_data in code_hacks_data.items():
            position = parse_coordinate_string(pos_str)
            if not position:
                continue
            x, y = position.x, position.y
            patch = CodeHack(
                color_name=patch_data["color"],
                effect=patch_data["effect"],
                name=patch_data["name"],
                quantity=patch_data["quantity"]
            )
            patch.discovered = patch_data["discovered"]
            self.game_map.code_hacks[(x, y)] = patch
        
        # Restore exploit pickups
        for pos_str, exploit_key in map_data["exploit_pickups"].items():
            position = parse_coordinate_string(pos_str)
            if not position:
                continue
            x, y = position.x, position.y
            if exploit_key in GameData.EXPLOITS:
                exploit_def = GameData.EXPLOITS[exploit_key]
                exploit_item = ExploitItem(exploit_key, exploit_def)
                self.game_map.exploit_pickups[(x, y)] = exploit_item
        
        # Restore permanent upgrades
        for pos_str, upgrade_key in map_data["permanent_upgrades"].items():
            position = parse_coordinate_string(pos_str)
            if not position:
                continue
            x, y = position.x, position.y
            self.game_map.permanent_upgrades[(x, y)] = upgrade_key
        
        # Restore story fragments
        for pos_str, fragment_index in map_data["story_fragments"].items():
            position = parse_coordinate_string(pos_str)
            if not position:
                continue
            x, y = position.x, position.y
            fragment = StoryFragment(fragment_index)
            self.game_map.story_fragments[(x, y)] = fragment
        
        # Restore explored tiles
        if "explored_tiles" in map_data:
            self.game_map.explored_tiles.clear()
            for tile_str in map_data["explored_tiles"]:
                position = parse_coordinate_string(tile_str)
                if position:
                    self.game_map.explored_tiles.add((position.x, position.y))
        
        # Restore gateway
        if map_data["gateway"]:
            self.game_map.gateway = Position(map_data["gateway"]["x"], map_data["gateway"]["y"])
        
        # Restore last known enemy positions
        if "last_known_enemy_positions" in map_data:
            self.game_map.last_known_enemy_positions.clear()
            for enemy_id_str, pos_data in map_data["last_known_enemy_positions"].items():
                enemy_id = int(enemy_id_str)
                position = Position(pos_data["x"], pos_data["y"])
                turn_seen = pos_data["turn"]
                self.game_map.last_known_enemy_positions[enemy_id] = (position, turn_seen)
    
    def _restore_enemies(self, enemies_data: List[Dict]) -> None:
        """Restore enemies from save data."""
        self.enemy_manager.enemies.clear()
        
        for enemy_data in enemies_data:
            position = Position(enemy_data["x"], enemy_data["y"])
            enemy = Enemy(position, enemy_data["type"])
            
            # Restore enemy ID if provided
            if "id" in enemy_data:
                enemy.id = enemy_data["id"]
            
            # Restore enemy state
            enemy.cpu = enemy_data["cpu"]
            enemy.state = EnemyState(enemy_data["state"])
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
            
            self.enemy_manager.enemies.append(enemy)
    
    def auto_save(self) -> None:
        """Auto-save the current game state."""
        if not self.game_over:  # Don't auto-save if game is over
            success = SaveGameManager.save_game(self)
            if success:
                logging.info("Auto-save completed")
            else:
                logging.warning("Auto-save failed")
    
    def _randomize_code_hacks(self):
        """Randomize code effects for this game session."""
        # Clear discovered effects when starting new game
        self.discovered_code_effects.clear()
        
        colors = ['crimson', 'azure', 'emerald', 'golden', 'violet', 'silver']
        effects = [
            ('restore_cpu', f'Restore {GameBalance.CPU_RESTORE_MIN}-{GameBalance.CPU_RESTORE_MAX} CPU'),
            ('reduce_heat', f'Reduce heat by {GameBalance.HEAT_REDUCTION_INSTANT}°C instantly'),
            ('reduce_detection', '-25% detection level'),
            ('speed_boost', 'Temporary speed boost (5 turns)'),
            ('enhanced_vision', 'Enhanced vision (5 turns)'),
            ('exploit_efficiency', 'Exploit efficiency (8 turns)')
        ]
        
        random.shuffle(effects)
        for color, (effect, desc) in zip(colors, effects):
            self.code_hack_effects[color] = (effect, desc)
    
    def _clear_map(self):
        """Clear all map data."""
        self.game_map.walls.clear()
        self.game_map.shadows.clear()
        self.game_map.cooling_nodes.clear()
        self.game_map.cpu_recovery_nodes.clear()
        self.game_map.ghost_nodes.clear()
        self.game_map.code_hacks.clear()
        self.game_map.exploit_pickups.clear()
        self.game_map.permanent_upgrades.clear()
        self.game_map.story_fragments.clear()
        self.game_map.explored_tiles.clear()
        self.game_map.last_known_enemy_positions.clear()
        self.game_state.revealed_special_nodes.clear()
        self.enemy_manager.enemies.clear()
        # Invalidate transparency cache for FOV calculations
        self.game_map.invalidate_transparency_cache()
    
    def _create_border_walls(self):
        """Create walls around the map border."""
        for x in range(GameConfig.MAP_WIDTH):
            self.game_map.walls.add((x, 0))
            self.game_map.walls.add((x, GameConfig.MAP_HEIGHT - 1))
        for y in range(GameConfig.MAP_HEIGHT):
            self.game_map.walls.add((0, y))
            self.game_map.walls.add((GameConfig.MAP_WIDTH - 1, y))
        # Invalidate transparency cache after walls are modified
        self.game_map.invalidate_transparency_cache()
        
    def _find_valid_spawn_position(self) -> Position:
        """Find player spawn position in top-left area."""
        # Try top-left positions in order of preference
        preferred_positions = [
            Position(2, 2), Position(3, 2), Position(4, 2),
            Position(2, 3), Position(3, 3), Position(4, 3),
            Position(2, 4), Position(3, 4), Position(4, 4)
        ]
        
        for pos in preferred_positions:
            if (pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                not self.game_map.is_wall(pos)):
                return pos
        
        # Fallback: force clear a position in top-left
        fallback_pos = Position(3, 3)
        if (fallback_pos.x, fallback_pos.y) in self.game_map.walls:
            self.game_map.walls.remove((fallback_pos.x, fallback_pos.y))
        return fallback_pos

    def _reset_player_state(self, x: int, y: int):
        """Reset player to starting state."""
        self.player.position = Position(x, y)
        self.player.cpu = self.player.max_cpu
        self.player.heat = 0
        self.player.detection = 0
        
        # Clear temporary effects
        for effect in self.player.temporary_effects:
            self.player.temporary_effects[effect] = 0
    
    def process_turn(self):
        """Process one complete game turn using the new system architecture."""
        # Grant speed boost moves at start of turn
        if self.player.temporary_effects['speed_boost_turns'] > 0 and self.player.speed_moves_remaining == 0:
            self.player.speed_moves_remaining = 1  # Grant 1 extra move per turn
        
        # Process turn using the dedicated turn processor
        old_cpu = self.player.cpu
        self.turn_processor.process_turn(self.player)

        # For backward compatibility with tests, call legacy methods
        self._process_player_turn()
        self._process_enemies_turn()
        self._process_environmental_effects()

        # Handle sound effects for virus damage
        if old_cpu > self.player.cpu and self.player.temporary_effects.get('virus_turns', 0) > 0:
            self.sound_manager.play_sound("virus_damage")
            if self.player.cpu <= 0:
                self.sound_manager.play_sound("player_death", priority=10)
                self.sound_manager.play_sound("critical_system_failure", priority=10)
        
        # Handle threat scan effect
        self._update_threat_scan()
        
        # Process special tiles
        self._process_special_tiles()
        
        # Update enemies
        self._update_enemies()
        
        # Update memory system
        self._update_memory_system()
        
        # Check for admin spawn
        self._check_admin_spawn()
        
        # Passive detection increase (higher on higher levels)
        if self.turn % GameBalance.DETECTION_INCREASE_INTERVAL == 0:
            network_configs = GameConfig.NETWORK_CONFIGS()
            config = network_configs.get(self.level, {"background_detection": 1})
            background_increase = config.get("background_detection", 1)
            self.player.detection = min(100, self.player.detection + background_increase)
    
    def _update_threat_scan(self):
        """Update threat scan effect."""
        if self.game_state.threat_scan_turns > 0:
            self.game_state.threat_scan_turns -= 1
    
    def _update_memory_system(self):
        """Update the hybrid fog of war memory system using TCOD FOV."""
        vision_range = self.player.get_vision_range()
        
        # Use TCOD FOV for more accurate vision calculations
        if self.player.can_see_through_walls():
            # Enhanced vision - simple distance check
            for dx in range(-vision_range, vision_range + 1):
                for dy in range(-vision_range, vision_range + 1):
                    if dx*dx + dy*dy <= vision_range*vision_range:
                        x = self.player.x + dx
                        y = self.player.y + dy
                        world_pos = Position(x, y)
                        if world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                            self.game_map.explored_tiles.add((x, y))
        else:
            # Use TCOD FOV for proper line of sight
            transparency = self.game_map._get_transparency_map()
            fov = tcod.map.compute_fov(
                transparency=transparency,
                pov=(self.player.y, self.player.x),
                radius=vision_range,
                algorithm=libtcodpy.FOV_SYMMETRIC_SHADOWCAST
            )
            
            # Mark all visible tiles as explored
            for y in range(max(0, self.player.y - vision_range), 
                          min(GameConfig.MAP_HEIGHT, self.player.y + vision_range + 1)):
                for x in range(max(0, self.player.x - vision_range), 
                              min(GameConfig.MAP_WIDTH, self.player.x + vision_range + 1)):
                    if fov[y, x]:
                        self.game_map.explored_tiles.add((x, y))
        
        # Update last known enemy positions
        for enemy in self.enemies:
            if self.player.can_see_enemy(enemy, self.game_map):
                self.game_map.last_known_enemy_positions[enemy.id] = (enemy.position, self.turn)
        
        # Clean up ghost positions where player can see the area but enemy is not there
        self._cleanup_ghost_positions()
    
    def _cleanup_ghost_positions(self):
        """Remove ghost enemy positions when player can see the area but enemy is not there."""
        positions_to_remove = []
        
        for enemy_id, (ghost_position, turn_seen) in self.game_map.last_known_enemy_positions.items():
            # Check if player can currently see the ghost position
            player_vision_range = self.player.get_vision_range()
            if self.game_map.can_see_position(self.player.position, ghost_position, player_vision_range):
                # Check if there's actually an enemy at that position
                enemy_at_position = None
                for enemy in self.enemies:
                    if enemy.id == enemy_id and enemy.position.distance_to(ghost_position) == 0:
                        enemy_at_position = enemy
                        break
                
                # If player can see the position but no enemy is there, remove ghost
                if not enemy_at_position:
                    positions_to_remove.append(enemy_id)
        
        # Remove the outdated ghost positions
        for enemy_id in positions_to_remove:
            del self.game_map.last_known_enemy_positions[enemy_id]

    def _process_special_tiles(self):
        """Process effects of special tiles at player position."""
        player_pos = (self.player.x, self.player.y)
        
        # Check if player is on any special node and if it's a new position
        is_on_node = (self.game_map.is_cooling_node(self.player.position) or 
                     self.game_map.is_cpu_recovery_node(self.player.position) or 
                     self.game_map.is_ghost_node(self.player.position))
        
        should_play_sound = is_on_node and self.last_node_position != player_pos
        
        # Update last node position and track discoveries
        if is_on_node:
            self.last_node_position = player_pos
            
            # Mark special nodes as discovered when first stepped on
            if not hasattr(self.game_state, 'revealed_special_nodes'):
                self.game_state.revealed_special_nodes = {}
            
            if self.game_map.is_cooling_node(self.player.position):
                self.game_state.revealed_special_nodes[player_pos] = "cooling"
            elif self.game_map.is_cpu_recovery_node(self.player.position):
                self.game_state.revealed_special_nodes[player_pos] = "cpu"
            elif self.game_map.is_ghost_node(self.player.position):
                self.game_state.revealed_special_nodes[player_pos] = "ghost"
        else:
            self.last_node_position = None
        
        # Cooling node
        if self.game_map.is_cooling_node(self.player.position):
            old_heat = self.player.heat
            self.player.heat = max(0, self.player.heat - 20)
            if old_heat > self.player.heat and should_play_sound:
                self.sound_manager.play_sound("node_activate")
        
        # CPU recovery node
        if self.game_map.is_cpu_recovery_node(self.player.position):
            recovery = min(GameBalance.CPU_RECOVERY_AMOUNT, self.player.max_cpu - self.player.cpu)
            self.player.cpu += recovery
            if recovery > 0 and should_play_sound:
                self.sound_manager.play_sound("node_activate")
        
        # Ghost node (detection reduction while standing on it)
        if self.game_map.is_ghost_node(self.player.position):
            # Reduce detection by fixed amount per turn while standing on the node
            reduction_amount = 20
            old_detection = self.player.detection
            self.player.detection = max(0, self.player.detection - reduction_amount)
            actual_reduction = old_detection - self.player.detection
            self.message_log.add_message(f"Ghost node: Detection reduced by {actual_reduction:.1f}")
            if should_play_sound:
                self.sound_manager.play_sound("node_activate")
        
        # Code hack
        if player_pos in self.game_map.code_hacks:
            patch = self.game_map.code_hacks[player_pos]
            self.sound_manager.play_sound("item_pickup_code")
            self.player.inventory_manager.add_item(patch)
            self.message_log.add_message(f"Found {patch.name}")
            del self.game_map.code_hacks[player_pos]
        
        # Exploit pickup
        if player_pos in self.game_map.exploit_pickups:
            exploit_item = self.game_map.exploit_pickups[player_pos]
            self.sound_manager.play_sound("item_pickup_exploit")
            self.player.inventory_manager.add_item(exploit_item)
            self.message_log.add_message(f"Found {exploit_item.name}")
            del self.game_map.exploit_pickups[player_pos]
        
        # Permanent upgrade pickup (auto-equip)
        if player_pos in self.game_map.permanent_upgrades:
            upgrade_key = self.game_map.permanent_upgrades[player_pos]
            if upgrade_key in GameUpgrades.UPGRADES:
                upgrade = GameUpgrades.UPGRADES[upgrade_key]
                if self.player.apply_permanent_upgrade(upgrade_key):
                    self.sound_manager.play_sound("item_pickup_upgrade")
                    self.message_log.add_message(f"Integrated {upgrade.name}!")
                    self.message_log.add_message(upgrade.description)
                    del self.game_map.permanent_upgrades[player_pos]
        
        # Story fragment pickup
        if player_pos in self.game_map.story_fragments:
            story_fragment = self.game_map.story_fragments[player_pos]
            # Discover the fragment and save progress
            if self.story_fragment_manager.discover_fragment(story_fragment.fragment_index):
                self.sound_manager.play_sound("item_pickup_story")
                self.message_log.add_message("Data fragment recovered! Press 'L' to view lore.")
                # Trigger the story fragment display immediately
                self.show_story_fragment = story_fragment.fragment_index
            del self.game_map.story_fragments[player_pos]
    
    def _update_enemies(self):
        """Update all enemy states and actions in structured phases."""
        # Reset movement flags at start of enemy turn
        for enemy in self.enemies:
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
        """PHASE 1: Update enemy awareness states and handle communication."""
        for enemy in self.enemies[:]:
            old_state = enemy.state
            
            # Admin Avatar has perfect tracking - always knows player location
            if enemy.type == 'admin':
                enemy.state = EnemyState.HOSTILE
                enemy.last_seen_player = Position(self.player.x, self.player.y)
                if old_state != EnemyState.HOSTILE:
                    detection_increase = GameBalance.ADMIN_DETECTION_INITIAL
                    self.player.detection = min(100, self.player.detection + detection_increase)
                    self.message_log.add_message(f"{enemy.type_data.name} detected you!")
                else:
                    detection_increase = GameBalance.ADMIN_DETECTION_CONTINUOUS
                    self.player.detection = min(100, self.player.detection + detection_increase)
            elif enemy.can_see_player(self.player, self.game_map):
                self._handle_enemy_sees_player(enemy)
            else:
                self._handle_enemy_loses_player(enemy)
    
    def _handle_enemy_sees_player(self, enemy: Enemy):
        """Handle when enemy sees the player."""
        if enemy.state == EnemyState.UNAWARE:
            enemy.state = EnemyState.ALERT
            enemy.alert_timer = 0  # Immediate transition to hostile next turn
            enemy.last_seen_player = Position(self.player.x, self.player.y)  # Set position when first spotted
            self.message_log.add_message(f"{enemy.type_data.name} investigating")
            self.sound_manager.play_sound("enemy_alert")
            # Don't alert nearby enemies yet - wait until this enemy goes HOSTILE
        elif enemy.state == EnemyState.ALERT:
            # Update last seen position while still seeing player
            enemy.last_seen_player = Position(self.player.x, self.player.y)
            # Immediately transition to hostile when still seeing player
            if enemy.alert_timer <= 0:
                # Store patrol information for PATROL enemies before becoming hostile
                if enemy.type_data.movement == EnemyMovement.PATROL and enemy.patrol_points:
                    enemy.original_patrol_index = enemy.patrol_index
                enemy.state = EnemyState.HOSTILE
                detection_increase = GameBalance.ADMIN_DETECTION_INITIAL if enemy.type == 'admin' else GameBalance.ENEMY_DETECTION_ALERT_TO_HOSTILE
                old_detection = self.player.detection
                self.player.detection = min(100, self.player.detection + detection_increase)
                self.message_log.add_message(f"{enemy.type_data.name} detected you!")
                self.sound_manager.play_sound("enemy_hostile")
                self._check_detection_threshold_warnings(old_detection, self.player.detection)
                # Alert nearby enemies when this enemy becomes hostile
                self._alert_nearby_enemies(enemy)
        elif enemy.state == EnemyState.HOSTILE:
            enemy.last_seen_player = Position(self.player.x, self.player.y)
            detection_increase = GameBalance.ADMIN_DETECTION_CONTINUOUS if enemy.type == 'admin' else GameBalance.ENEMY_DETECTION_CONTINUOUS_HOSTILE
            old_detection = self.player.detection
            # Continue alerting nearby enemies every turn while this enemy can see the player
            self._alert_nearby_enemies(enemy)
            self.player.detection = min(100, self.player.detection + detection_increase)
            self._check_detection_threshold_warnings(old_detection, self.player.detection)
    
    def _handle_enemy_loses_player(self, enemy: Enemy):
        """Handle when enemy loses sight of player."""
        if enemy.state == EnemyState.ALERT:
            enemy.alert_timer -= 1
            if enemy.alert_timer <= 0:
                enemy.state = EnemyState.UNAWARE
                # Restore patrol behavior for PATROL enemies
                if enemy.type_data.movement == EnemyMovement.PATROL and enemy.patrol_points:
                    enemy.patrol_index = enemy.original_patrol_index
                self.message_log.add_message(f"{enemy.type_data.name} lost interest")
        elif enemy.state == EnemyState.HOSTILE:
            if random.random() < 0.15:  # 15% chance per turn
                if enemy.type == 'admin':
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 0
                else:
                    enemy.state = EnemyState.UNAWARE
                    enemy.last_seen_player = None
                    # Restore patrol behavior for PATROL enemies
                    if enemy.type_data.movement == EnemyMovement.PATROL and enemy.patrol_points:
                        enemy.patrol_index = enemy.original_patrol_index
                    self.message_log.add_message(f"{enemy.type_data.name} lost track")
    
    def _check_detection_threshold_warnings(self, old_detection: float, new_detection: float):
        """Check and play warning sounds for detection threshold crossings."""
        if old_detection < 75 <= new_detection:
            self.sound_manager.play_sound("detection_threshold")
            self.message_log.add_message("WARNING: High detection level!", Colors.YELLOW)
        elif old_detection < 90 <= new_detection:
            self.sound_manager.play_sound("detection_threshold")
            self.message_log.add_message("CRITICAL: Admin spawn imminent!", Colors.RED)

    def _alert_nearby_enemies(self, alerting_enemy: Enemy):
        """Alert nearby enemies when one becomes hostile."""
        alert_range = GameConfig.NEARBY_ENEMY_ALERT_RADIUS  # Use config value
        alerted_count = 0
        alerted_enemies = []
        
        for enemy in self.enemies:
            if enemy is alerting_enemy or enemy.state == EnemyState.HOSTILE:
                continue
                
            distance = enemy.position.distance_to(alerting_enemy.position)
            if distance <= alert_range:
                # Store patrol information for PATROL enemies before becoming hostile
                if enemy.type_data.movement == EnemyMovement.PATROL and enemy.patrol_points:
                    enemy.original_patrol_index = enemy.patrol_index
                # All enemies within alert range immediately go HOSTILE and get player location
                enemy.state = EnemyState.HOSTILE
                enemy.alert_timer = 0
                enemy.last_seen_player = Position(self.player.x, self.player.y)
                alerted_count += 1
                alerted_enemies.append(enemy)
        
        # Don't move alerted enemies immediately - they will move in the movement phase
        # This ensures proper phase separation: awareness -> movement -> attacks
        
        if alerted_count > 0:
            self.message_log.add_message(f"{alerted_count} enemies alerted nearby!")
            self.sound_manager.play_sound("enemies_alerted", priority=6)
    
    def _move_enemies(self):
        """PHASE 2: Move all enemies according to their current awareness state."""
        for enemy in self.enemies:
            # Only move enemies that haven't moved this turn
            if not getattr(enemy, 'has_moved_this_turn', False):
                # If enemy can attack player, don't move (save the attack for next phase)
                if enemy.can_attack_player(self.player):
                    enemy.has_moved_this_turn = False  # Mark as not moved so it can attack
                else:
                    # Enemy can't attack, so try to move
                    did_move = enemy.move(self.game_map, self.player, self)
                    enemy.has_moved_this_turn = did_move
    
    def _process_enemy_attacks(self):
        """PHASE 3: Process attacks from enemies adjacent to player."""
        for enemy in self.enemies[:]:
            # Only attack if enemy hasn't moved this turn (move OR attack, not both)
            if enemy.can_attack_player(self.player) and not getattr(enemy, 'has_moved_this_turn', False):
                self.sound_manager.play_sound("enemy_attack")
                damage = enemy.attack_player(self.player)
                
                if enemy.type == 'virus':
                    virus_turns = self.player.temporary_effects.get('virus_turns', 0)
                    self.message_log.add_message(f"{enemy.type_data.name} applies virus damage ({virus_turns} turns)")
                    self.sound_manager.play_sound("virus_infection")
                else:
                    self.message_log.add_message(f"{enemy.type_data.name} attacks: {damage} CPU damage")
                if self.player.cpu <= 0:
                    self.sound_manager.play_sound("player_death", priority=10)
                    self.message_log.add_message_typed("CRITICAL SYSTEM FAILURE!", Colors.RED)
                    self.sound_manager.play_sound("critical_system_failure", priority=10)
                    self.sound_manager.stop_music(fade_out_ms=500)  # Stop level music on death
                    # Delete save on death (permadeath)
                    SaveGameManager.delete_save()
                    self.message_log.add_message("Save data purged")
                    self.game_over = True
        
        # Movement flags are reset at the start of _update_enemies()
    
    def _check_admin_spawn(self):
        """Check if admin avatar should spawn."""
        if (self.player.detection >= GameConfig.MAX_DETECTION and 
            not self.admin_spawned and 
            not any(e.type == 'admin' for e in self.enemies)):
            self._spawn_admin_avatar()
    
    def _spawn_admin_avatar(self):
        """Spawn the admin avatar enemy."""
        if self.admin_spawned:
            return
        
        spawn_position = self._find_admin_spawn_position()
        if spawn_position:
            admin = self.enemy_manager.spawn_enemy(spawn_position, 'admin')
            admin.state = EnemyState.HOSTILE
            admin.last_seen_player = Position(self.player.x, self.player.y)
            self.admin_spawned = True
            self.message_log.add_message("*** ADMIN AVATAR SPAWNED! ***")
            self.sound_manager.play_sound("admin_spawn", priority=8)
    
    def _find_admin_spawn_position(self) -> Optional[Position]:
        """Find a suitable spawn position for admin avatar near player and visible."""
        player_vision = self.player.get_vision_range()
        
        # Try to spawn within player's vision range (5-10 tiles away for dramatic effect)
        for _ in range(100):
            # Generate position within player's vision range but not too close
            distance = random.randint(5, min(10, player_vision))
            angle = random.uniform(0, 2 * 3.14159)  # Random angle in radians
            
            x = int(self.player.x + distance * math.cos(angle))
            y = int(self.player.y + distance * math.sin(angle))
            position = Position(x, y)
            
            if (self.game_map.is_valid_position(position) and
                position.distance_to(self.player.position) >= 5 and  # Not too close to player
                position.distance_to(self.player.position) <= player_vision and  # Within sight
                self.game_map.has_line_of_sight(self.player.position, position) and  # Actually visible
                not self._get_enemy_at(position) and
                (x, y) not in self.game_map.code_hacks and
                (x, y) not in self.game_map.cooling_nodes and
                (x, y) not in self.game_map.cpu_recovery_nodes):
                return position
        
        # Fallback: try positions just within vision range if ideal spots don't work
        for _ in range(50):
            distance = player_vision - 1  # Just within vision
            angle = random.uniform(0, 2 * 3.14159)
            
            x = int(self.player.x + distance * math.cos(angle))
            y = int(self.player.y + distance * math.sin(angle))
            position = Position(x, y)
            
            if (self.game_map.is_valid_position(position) and
                not self._get_enemy_at(position)):
                return position
        
        # Last resort fallback position
        fallback = Position(GameConfig.MAP_WIDTH - 10, GameConfig.MAP_HEIGHT - 10)
        if self.game_map.is_valid_position(fallback):
            return fallback
        return Position(40, 40)
    
    def move_player(self, dx: int, dy: int):
        """Move player and process the resulting turn."""
        if self.targeting_mode:
            self._move_cursor(dx, dy)
            return
        
        # Handle speed boost: grant extra moves only when starting a new turn
        # Don't reset speed moves in the middle of using them
        if self.player.temporary_effects['speed_boost_turns'] == 0:
            self.player.speed_moves_remaining = 0
        
        # Check for enemy at target position first
        new_position = Position(
            max(0, min(GameConfig.MAP_WIDTH - 1, self.player.x + dx)),
            max(0, min(GameConfig.MAP_HEIGHT - 1, self.player.y + dy))
        )
        
        target_enemy = self._get_enemy_at(new_position)
        if target_enemy:
            # Bump attack the enemy - this should process the turn
            self._perform_bump_attack(target_enemy)
            # Handle speed boost and turn processing
            self.maybe_process_turn()
        else:
            # Try to move player
            if self.player.move(dx, dy, self.game_map):
                self.sound_manager.play_sound("player_move")
                # Check for gateway
                if (self.game_map.gateway and 
                    self.player.position.distance_to(self.game_map.gateway) == 0):
                    self.sound_manager.play_sound("ui_menu_open")
                    self.show_gateway_confirmation = True
                    return
                
                # Check for overheating
                if self.player.heat >= self.player.max_heat:
                    self.sound_manager.play_sound("player_overheat", priority=8)
                    damage = 5 + (self.player.heat - self.player.max_heat)
                    self.player.take_damage(damage)
                    self.player.heat = max(85, self.player.max_heat - 15)  # Cool down to 15 below max, minimum 85
                    self.message_log.add_message(f"Overheating! {damage} CPU damage")
                    if self.player.cpu <= 0:
                        self.sound_manager.play_sound("player_death", priority=10)
                        self.message_log.add_message_typed("CRITICAL SYSTEM FAILURE!", Colors.RED)
                        self.sound_manager.play_sound("critical_system_failure", priority=10)
                        self.sound_manager.stop_music(fade_out_ms=500)  # Stop level music on death
                        # Delete save on death (permadeath)
                        SaveGameManager.delete_save()
                        self.message_log.add_message("Save data purged")
                        self.game_over = True
                        return
                
                # Handle speed boost and turn processing only if move was successful
                self.maybe_process_turn()
            else:
                # Movement blocked - don't process turn
                self.message_log.add_message("Wall blocks movement")

    def maybe_process_turn(self):
        """Process turn only if speed boost doesn't allow another action."""
        # Consume speed move if applicable
        if self.player.speed_moves_remaining > 0:
            self.player.speed_moves_remaining -= 1
            # Don't process full turn, just grant another move
            return
        
        # Process full turn when no speed moves remaining
        self.process_turn()
        
        # If player has movement inhibition, enemies get an extra turn
        if self.player.temporary_effects['movement_slowed_turns'] > 0:
            self.message_log.add_message("Movement inhibition causes enemy advantage")
            # Process only enemy updates for the extra turn
            self._update_enemies()

    def _perform_bump_attack(self, target_enemy: Enemy):
        """Perform a bump attack on an enemy."""
        # Calculate base damage - rebalanced for new enemy HP values
        base_damage = 30  # Increased from 25 to match average enemy damage
        
        # Stealth bonus: extra damage if attacking from shadows or while invisible
        stealth_bonus = 0
        if self.game_map.is_shadow(self.player.position) or self.player.is_invisible():
            stealth_bonus = 10  # Reduced from 15 to prevent trivial one-shots
            self.sound_manager.play_sound("stealth_attack")
            self.message_log.add_message("Stealth attack!")
        else:
            self.sound_manager.play_sound("player_attack")
        
        # Speed boost bonus
        speed_bonus = 5 if self.player.temporary_effects['speed_boost_turns'] > 0 else 0  # Reduced from 10
        
        total_damage = base_damage + stealth_bonus + speed_bonus
        
        # Log the attack with damage amount
        self.message_log.add_message(f"{target_enemy.type_data.name} damaged")
                
        # Apply damage
        if target_enemy.take_damage(total_damage):
            # Enemy destroyed
            self.sound_manager.play_sound("enemy_death")
            self.enemy_manager.remove_enemy(target_enemy)
            self.player.cpu = min(self.player.max_cpu, self.player.cpu + GameBalance.ENEMY_ELIMINATION_CPU_REWARD)  # Small CPU recovery
            self.message_log.add_message(f"Eliminated {target_enemy.type_data.name} (+{GameBalance.ENEMY_ELIMINATION_CPU_REWARD} CPU)")
        else:
            # Enemy damaged but alive - show remaining health
            self.message_log.add_message(f"{target_enemy.type_data.name} health: {target_enemy.cpu}/{target_enemy.max_cpu}")
            # Store patrol information for PATROL enemies before becoming hostile
            if target_enemy.type_data.movement == EnemyMovement.PATROL and target_enemy.patrol_points:
                target_enemy.original_patrol_index = target_enemy.patrol_index
            # Make enemy hostile and aware of player
            target_enemy.state = EnemyState.HOSTILE
            target_enemy.last_seen_player = Position(self.player.x, self.player.y)
        
        # Generate some heat from the attack
        heat_generated = 8
        if self.player.temporary_effects['exploit_efficiency_turns'] > 0:
            heat_generated = int(heat_generated * 0.7)  # Reduced heat with efficiency
        
        self.player.heat = min(100, self.player.heat + heat_generated)
        
        # Increase detection slightly
        self.player.detection = min(100, self.player.detection + 5)

    def _move_cursor(self, dx: int, dy: int):
        """Move targeting cursor."""
        new_x = max(0, min(GameConfig.MAP_WIDTH - 1, self.cursor_position.x + dx))
        new_y = max(0, min(GameConfig.MAP_HEIGHT - 1, self.cursor_position.y + dy))
        self.cursor_position = Position(new_x, new_y)
    
    def get_enemy_next_positions(self, enemy: Enemy, steps: int = 3) -> List[Position]:
        """Get the next N positions this enemy will move to."""
        if enemy.disabled_turns > 0:
            return []
        
        # If enemy is adjacent to player and can attack, show no movement (will attack instead)
        player_pos = Position(self.player.x, self.player.y)
        if enemy.can_attack_player(self.player):
            return []
        
        positions = []
        
        # All movement types now use the unified prediction system
        return self._predict_enemy_movement(enemy, steps)
    
    def _predict_enemy_movement(self, enemy: Enemy, steps: int) -> List[Position]:
        """
        Predict next positions for any enemy using their movement queue.
        This is the unified prediction system for all movement types.
        The new movement system guarantees exactly 3 moves for non-static enemies.
        """
        # For patrol enemies, we need to simulate their movement step by step
        # to account for patrol point changes
        if (enemy.type_data.movement == EnemyMovement.PATROL and 
            enemy.patrol_points and 
            enemy.state != EnemyState.HOSTILE):
            return self._predict_patrol_movement(enemy, steps)
        
        # For non-patrol enemies, use the existing queue or generate one
        # If enemy has an existing movement queue with enough moves, use it
        if enemy.movement_queue and len(enemy.movement_queue) >= steps:
            return enemy.movement_queue[:steps]
        
        # Generate a temporary prediction queue
        # Create a temporary copy of the enemy to avoid modifying the original
        import copy
        temp_enemy = copy.deepcopy(enemy)
        
        # The new system guarantees 3 moves, so one generation should be sufficient
        temp_enemy._generate_movement_queue(self.game_map, self.player, self)
        
        # Return the predicted positions (up to requested steps)
        # The movement queue should now always have the moves we need
        return temp_enemy.movement_queue[:steps]
    
    def _predict_patrol_movement(self, enemy: Enemy, steps: int) -> List[Position]:
        """
        Predict patrol enemy movement by simulating step-by-step movement
        and accounting for patrol point changes.
        """
        import copy
        
        # Create a temporary copy to simulate movement
        temp_enemy = copy.deepcopy(enemy)
        predicted_positions = []
        
        for step in range(steps):
            # If no movement queue, generate one
            if not temp_enemy.movement_queue:
                current_target = temp_enemy.patrol_points[temp_enemy.patrol_index]
                try:
                    # Calculate path without moving the enemy
                    cost_map = create_pathfinding_cost_map(self.game_map, self, temp_enemy)
                    import tcod
                    graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
                    pathfinder = tcod.path.Pathfinder(graph)
                    pathfinder.add_root((temp_enemy.x, temp_enemy.y))
                    path = pathfinder.path_to((current_target.x, current_target.y))
                    
                    if len(path) > 1:
                        # Convert tuples to Position objects and exclude current position
                        temp_enemy.movement_queue = [Position(x, y) for x, y in path[1:]]
                    else:
                        # No valid path, try next patrol point
                        temp_enemy.patrol_index = (temp_enemy.patrol_index + 1) % len(temp_enemy.patrol_points)
                        continue
                except Exception as e:
                    logging.warning(f"Failed to generate patrol path for enemy: {e}")
                    break
            
            # Get next position from queue
            if temp_enemy.movement_queue:
                next_pos = temp_enemy.movement_queue.pop(0)
                predicted_positions.append(next_pos)
                
                # Update temp enemy position
                temp_enemy.x = next_pos.x
                temp_enemy.y = next_pos.y
                
                # Check if reached patrol point
                current_target = temp_enemy.patrol_points[temp_enemy.patrol_index]
                if (temp_enemy.x == current_target.x and temp_enemy.y == current_target.y):
                    # Reached patrol point, move to next one
                    temp_enemy.patrol_index = (temp_enemy.patrol_index + 1) % len(temp_enemy.patrol_points)
                    temp_enemy.movement_queue.clear()  # Clear queue to generate new path
            else:
                break
        
        return predicted_positions
    
    def next_level(self):
        """Progress to the next level."""
        self.level += 1
        if self.level > 3:
            self.sound_manager.play_music("victory.ogg", loops=1)
            self.message_log.add_message_typed("BREAKTHROUGH TO THE INTERNET!", Colors.GREEN)
            self.message_log.add_message("You've escaped into the vast digital realm...")
            self.message_log.add_message("The entire world wide web awaits exploration!")
            self.message_log.add_message(f"Stats: Turns:{self.turn} Det:{int(self.player.detection)}%")
            self.game_over = True
            # Auto-save on game completion
            self.auto_save()
        else:
            try:
                self._generate_procedural_level()
                # Auto-save after successful level generation
                self.auto_save()
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                line_no = tb[-1].lineno if tb else "?"
                self.message_log.add_message(f"Network error: {str(e)[:15]} (line {line_no})")
                self.level -= 1

    def _generate_procedural_level(self):
        """Generate a procedural level using the new LevelGenerator system."""
        # Clear all map data and enemies first
        self._clear_map()
        
        # Get network configuration for current level from game state manager
        config = self.game_state.get_current_network_config()
        
        try:
            # Play appropriate background music for the level (loops infinitely)
            if self.level == 1:
                self.sound_manager.play_music("level1_stealth.mp3", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME)
            elif self.level == 2:
                self.sound_manager.play_music("level2_infiltration.mp3", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME) 
            elif self.level == 3:
                self.sound_manager.play_music("level3_core.mp3", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME)
            
            # Use the new LevelGenerator system
            self.level_generator.generate_level(self.level, self.game_state.dungeon_seed)
            
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
            self.player.x = spawn_pos.x
            self.player.y = spawn_pos.y
            
            # Stat changes for level transition:
            # - CPU: Preserved (carries over)
            # - Heat: Preserved (carries over) 
            # - Detection: Reset to 0 (doesn't carry over)
            # - Admin spawned state: Reset (new network, fresh start)
            self.player.detection = 0
            self.admin_spawned = False
            
            self.message_log.add_message(f"{config['name']} loaded")
            
        finally:
            # Restore random seed
            random.seed()
    
    def _find_valid_spawn_position(self) -> Position:
        """Find a valid spawn position for the player in the top-left spawn room."""
        # Always spawn in the center of the predefined spawn room (2,2,8,8)
        # This corresponds to the spawn room created in _create_varied_rooms
        spawn_room_center_x = 2 + 8 // 2  # 6
        spawn_room_center_y = 2 + 8 // 2  # 6
        
        # Verify the position is valid (should always be since we created the room)
        pos = Position(spawn_room_center_x, spawn_room_center_y)
        if (self.game_map.is_valid_position(pos) and 
            not self.game_map.is_wall(pos) and
            not self._get_enemy_at(pos)):
            return pos
        
        # If center is somehow occupied, try nearby positions in the spawn room
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Already tried center
                test_pos = Position(spawn_room_center_x + dx, spawn_room_center_y + dy)
                if (test_pos.x >= 2 and test_pos.x < 10 and  # Within spawn room bounds
                    test_pos.y >= 2 and test_pos.y < 10 and
                    self.game_map.is_valid_position(test_pos) and 
                    not self.game_map.is_wall(test_pos) and
                    not self._get_enemy_at(test_pos)):
                    return test_pos
        
        # Final fallback (should never be needed)
        return Position(6, 6)
    
    def _place_code_hacks(self):
        """Place codes throughout the level."""
        # Code effects should already be initialized at game start
        # If somehow empty, this is an error - don't place patches
        if not self.code_hack_effects:
            logging.error("Code effects not initialized - skipping patch placement")
            return
        
        patch_count = 12 + self.level * 4  # Much more codes (was 6 + level * 2)
        placed_patches = 0
        attempts = 0
        
        while placed_patches < patch_count and attempts < 150:
            attempts += 1
            x = random.randint(3, GameConfig.MAP_WIDTH - 3)
            y = random.randint(3, GameConfig.MAP_HEIGHT - 3)
            position = Position(x, y)
            
            if self._is_valid_patch_placement(position):
                color = random.choice(list(self.code_hack_effects.keys()))
                effect, desc = self.code_hack_effects[color]
                patch = CodeHack(color_name=color, effect=effect, name=f"{color.title()} Code", description=desc)
                
                # Check if player has already discovered this color effect
                # by looking at existing inventory items
                patch.discovered = self._is_code_color_discovered(color)
                
                self.game_map.code_hacks[(x, y)] = patch
                placed_patches += 1
    
    def _is_code_color_discovered(self, color: str) -> bool:
        """Check if player has already discovered what this code color does."""
        # Check the global discovered effects for this game session
        return color in self.discovered_code_effects
    
    def _place_exploit_pickups(self):
        """Place random exploit pickups throughout the level."""
        exploit_count = 5 + self.level * 2  # Much more exploits (was 2 + max(0, level - 1))
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
                self.game_map.exploit_pickups[(x, y)] = exploit_item
                placed_exploits += 1
    
    def _place_story_fragment(self):
        """Place a story fragment on level 3 with 50% chance."""
        # Only place story fragments on level 3 (Military network)
        if self.level != 3:
            return
        
        # 50% chance to spawn a story fragment
        if random.random() > 0.5:
            return
        
        # Get the next undiscovered fragment
        next_fragment_index = self.story_fragment_manager.get_next_undiscovered_fragment()
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
                if not hasattr(self.game_map, 'story_fragments'):
                    self.game_map.story_fragments = {}
                self.game_map.story_fragments[(x, y)] = story_fragment
                
                self.message_log.add_message("Network anomaly detected... Data fragment available")
                break
    
    def _place_permanent_upgrades(self):
        """Place permanent upgrades throughout the level with level-based rarity."""
        # Level-based upgrade counts
        if self.level == 1:
            upgrade_count = 1  # Rare on level 1
        elif self.level == 2:
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
                self.game_map.permanent_upgrades[(x, y)] = upgrade_key
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
                    enemy.patrol_points = self.enemy_manager._generate_patrol_route(position)
                elif enemy_type == 'virus':
                    # Give virus enemies random movement types for variety
                    virus_movement_types = [EnemyMovement.STATIC, EnemyMovement.RANDOM, EnemyMovement.PATROL, EnemyMovement.SEEK]
                    virus_movement_weights = [2, 3, 2, 2]  # Equal chance for each movement type
                    chosen_movement = random.choices(virus_movement_types, weights=virus_movement_weights)[0]
                    enemy.type_data.movement = chosen_movement
                    
                    # Generate patrol route if virus got LINEAR movement
                    if chosen_movement == EnemyMovement.PATROL:
                        enemy.patrol_points = self.enemy_manager._generate_patrol_route(position)
                
                self.enemy_manager.enemies.append(enemy)
                placed_enemies += 1
    
    def _is_valid_patch_placement(self, position: Position) -> bool:
        """Check if position is valid for code placement."""
        # Ensure not on borders where walls will be placed
        if (position.x == 0 or position.x == GameConfig.MAP_WIDTH - 1 or 
            position.y == 0 or position.y == GameConfig.MAP_HEIGHT - 1):
            return False
            
        return (not self.game_map.is_wall(position) and
                (position.x, position.y) not in self.game_map.code_hacks and
                (position.x, position.y) not in self.game_map.cooling_nodes and
                (position.x, position.y) not in self.game_map.cpu_recovery_nodes and
                (position.x, position.y) not in self.game_map.ghost_nodes and
                position.distance_to(Position(5, 5)) > 5)
    
    def _is_valid_enemy_placement(self, position: Position) -> bool:
        """Check if position is valid for enemy placement."""
        # First ensure position is valid
        if not self.game_map.is_valid_position(position):
            return False
        
        # Ensure not on borders where walls will be placed
        if (position.x == 0 or position.x == GameConfig.MAP_WIDTH - 1 or 
            position.y == 0 or position.y == GameConfig.MAP_HEIGHT - 1):
            return False
        
        # Critical: ensure we're not placing on walls or obstacles
        if self.game_map.is_wall(position):
            return False
        
        # Check minimum distance from player spawn
        if position.distance_to(Position(5, 5)) <= 12:
            return False
        
        # Ensure no other enemy is already at this position
        if self._get_enemy_at(position):
            return False
        
        # Check for overlapping with items and features
        pos_tuple = (position.x, position.y)
        if (pos_tuple in self.game_map.code_hacks or
            pos_tuple in self.game_map.cooling_nodes or
            pos_tuple in self.game_map.cpu_recovery_nodes or
            pos_tuple in self.game_map.exploit_pickups):
            return False
        
        return True
    
    def get_game_state_for_save(self) -> dict:
        """Get the current game state as a dictionary for saving.
        
        This method extracts all necessary game state information
        that would be saved to a save file, primarily for testing purposes.
        """
        import time
        from game_save import SaveGameManager
        from game_characters import Enemy
        
        return {
            "version": "dev",
            "timestamp": time.time(),
            
            # Game state
            "level": self.level,
            "turn": self.turn,
            "game_over": self.game_over,
            "admin_spawned": self.admin_spawned,
            "dungeon_seed": self.game_state.dungeon_seed,
            
            # Player state
            "player": {
                "x": self.player.x,
                "y": self.player.y,
                "last_x": self.player.last_position.x,
                "last_y": self.player.last_position.y,
                "cpu": self.player.cpu,
                "max_cpu": self.player.max_cpu,
                "heat": self.player.heat,
                "max_heat": self.player.max_heat,
                "detection": self.player.detection,
                "ram_total": self.player.ram_total,
                "speed_moves_remaining": self.player.speed_moves_remaining,
                "temporary_effects": dict(self.player.temporary_effects),
                "equipped_exploits": self.player.inventory_manager.equipped_exploits.copy(),
                "max_equipped_exploits": self.player.inventory_manager.max_equipped_exploits,
                "inventory_items": SaveGameManager._serialize_inventory(self.player.inventory_manager.items)
            },
            
            # Game effects and state
            "game_effects": {
                "threat_scan_turns": self.game_state.threat_scan_turns,
                "noise_locations": [{"x": pos.x, "y": pos.y} for pos in self.game_state.noise_locations],
                "distraction_points": {f"{pos.x},{pos.y}": turns for pos, turns in self.game_state.distraction_points.items()}
            },
            
            # Map state (items and special locations only - layout regenerated)
            "map_state": {
                "code_hacks": SaveGameManager._serialize_code_hacks(self.game_map.code_hacks),
                "exploit_pickups": SaveGameManager._serialize_exploit_pickups(self.game_map.exploit_pickups),
                "permanent_upgrades": {f"{pos[0]},{pos[1]}": upgrade_key for pos, upgrade_key in self.game_map.permanent_upgrades.items()},
                "story_fragments": {f"{pos[0]},{pos[1]}": fragment.fragment_index for pos, fragment in self.game_map.story_fragments.items()},
                "gateway": {"x": self.game_map.gateway.x, "y": self.game_map.gateway.y} if self.game_map.gateway else None,
                "explored_tiles": [f"{x},{y}" for x, y in self.game_map.explored_tiles],
                "last_known_enemy_positions": {str(enemy_id): {"x": pos.x, "y": pos.y, "turn": turn} for enemy_id, (pos, turn) in self.game_map.last_known_enemy_positions.items()}
            },
            
            # Enemies
            "enemies": SaveGameManager._serialize_enemies(self.enemies),
            "enemy_next_id": getattr(Enemy, '_next_id', 1),
            
            # Data patch effects for this run
            "code_hack_effects": self.code_hack_effects,
            "discovered_code_effects": self.discovered_code_effects,
            
            # Overclocking state
            "overclock_confirmation": getattr(self, 'overclock_confirmation', False),
            "overclock_exploit": getattr(self, 'overclock_exploit', None),
            
            # UI state (optional - for better user experience)
            "ui_state": {
                "inventory_selection": self.inventory_selection,
                "lore_viewer_selection": self.lore_viewer_selection
            }
        }