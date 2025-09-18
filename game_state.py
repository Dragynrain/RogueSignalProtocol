#!/usr/bin/env python3
"""
Game State Management - Split from RogueSignalProtocol.py
Contains MessageLog, GameStateManager, and TurnProcessor classes.
"""

import random
from typing import List, Tuple, Optional, Dict, Any

from game_config import GameConfig, GameBalance
from game_entities import Position, Colors, ensure_color_tuple
from data_loading import DataLoader
from game_save import SaveGameManager


class MessageLog:
    """Manages game messages and logging."""
    
    def __init__(self, max_messages: int = 100):
        self.messages: List[Tuple[str, Tuple[int, int, int]]] = []
        self.max_messages = max_messages
    
    def add_message(self, text: str, color: Optional[Tuple[int, int, int]] = None, msg_type: Optional[str] = None):
        """Add a message to the log."""
        if not text:
            return
        
        if color is None:
            if msg_type:
                color = self._get_color_by_type(msg_type)
            else:
                color = self._determine_message_color(text)
        
        self.messages.append((text, color))
        
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def add_message_typed(self, text: str, msg_type: str):
        """Add a message with explicit type specification."""
        self.add_message(text, msg_type=msg_type)
    
    def _get_color_by_type(self, msg_type: str) -> Tuple[int, int, int]:
        """Get color for a specific message type."""
        config = DataLoader.load_config()
        message_colors = config.get("colors", {}).get("message_log", {})
        color_values = message_colors.get(msg_type, message_colors.get("default", [144, 238, 144]))
        
        # Use the ensure_color_tuple function for validation
        return ensure_color_tuple(color_values)
    
    def _determine_message_color(self, text: str) -> Tuple[int, int, int]:
        """Determine appropriate color for message based on content using JSON config."""
        text_lower = text.lower()
        
        # Get message type patterns from config
        config = DataLoader.load_config()
        message_types = config.get("message_types", {}).get("patterns", {})
        message_colors = config.get("colors", {}).get("message_log", {})
        
        # Check each message type for pattern matches
        for msg_type, patterns in message_types.items():
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    color_values = message_colors.get(msg_type)
                    if color_values:
                        return ensure_color_tuple(color_values)
        
        # Return default color if no pattern matches
        default_color = message_colors.get("default", [144, 238, 144])
        return ensure_color_tuple(default_color)
    
    def get_recent_messages(self, count: int) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Get the most recent messages."""
        return self.messages[-count:] if len(self.messages) > count else self.messages


class GameStateManager:
    """Manages core game state like level, turn, and game status."""
    
    def __init__(self):
        self.level: int = 1
        self.turn: int = 0
        self.game_over: bool = False
        self.admin_spawned: bool = False
        self.dungeon_seed: int = random.randint(1, GameConfig.DUNGEON_SEED_RANGE)
        
        # Game effects
        self.threat_scan_turns: int = 0
        self.noise_locations: List[Position] = []
        self.distraction_points: Dict[Position, int] = {}
        self.revealed_special_nodes: Dict[Tuple[int, int], str] = {}  # position -> node_type
    
    def advance_turn(self) -> None:
        """Advance to the next turn."""
        self.turn += 1
        
        # Update threat scan effect
        if self.threat_scan_turns > 0:
            self.threat_scan_turns -= 1
            
        # Decay distraction points
        expired_distractions = []
        for position, turns_remaining in self.distraction_points.items():
            if turns_remaining <= 1:
                expired_distractions.append(position)
            else:
                self.distraction_points[position] = turns_remaining - 1
                
        for position in expired_distractions:
            del self.distraction_points[position]
    
    def get_current_network_config(self) -> Dict[str, Any]:
        """Get configuration for the current network level."""
        network_configs = GameConfig.NETWORK_CONFIGS()
        return network_configs.get(self.level, network_configs[1])
    
    def should_spawn_admin(self, detection_level: float) -> bool:
        """Determine if admin should spawn based on detection level."""
        if self.admin_spawned:
            return False
            
        return detection_level >= GameConfig.MAX_DETECTION


class TurnProcessor:
    """Handles turn-based game logic and effects processing."""
    
    def __init__(self, game_state: GameStateManager, message_log: MessageLog):
        self.game_state = game_state
        self.message_log = message_log
    
    def process_turn(self, player) -> None:
        """Process a complete game turn including heat management and effects."""
        self.game_state.advance_turn()
        
        # Process heat reduction
        self._process_heat_management(player)
        
        # Process temporary effects
        self._process_temporary_effects(player)
        
        # Process detection increase
        self._process_detection_increase(player)
    
    def _process_heat_management(self, player) -> None:
        """Handle heat reduction over time."""
        if player.heat > 0:
            heat_reduction = (GameBalance.HEAT_REDUCTION_BOOSTED 
                            if player.temporary_effects['exploit_efficiency_turns'] > 0 
                            else GameBalance.HEAT_REDUCTION_NORMAL)
            
            old_heat = player.heat
            player.heat = max(0, player.heat - heat_reduction)
            
            # Heat reduction applied silently
    
    def _process_temporary_effects(self, player) -> None:
        """Process and decay temporary effects."""
        effects_to_update = list(player.temporary_effects.keys())
        
        for effect_name in effects_to_update:
            if player.temporary_effects[effect_name] > 0:
                # Handle virus damage over time BEFORE decrementing counter
                if effect_name == 'virus_turns':
                    virus_damage = GameConfig.VIRUS_DAMAGE_PER_TURN
                    actual_damage = player.take_damage(virus_damage)
                    self.message_log.add_message(f"Virus damage: {actual_damage} CPU damage")
                    
                    # Check for death from virus
                    if player.cpu <= 0:
                        self.message_log.add_message_typed("CRITICAL SYSTEM FAILURE!", Colors.RED)
                        SaveGameManager.delete_save()
                        self.message_log.add_message("Save data purged")
                        self.game_state.game_over = True
                        return  # Exit early if player dies
                
                # Now decrement the counter
                player.temporary_effects[effect_name] -= 1
                
                if player.temporary_effects[effect_name] == 0:
                    if effect_name == 'exploit_efficiency_turns':
                        self.message_log.add_message("Exploit efficiency boost expired")
                    elif effect_name == 'data_mimic_turns':
                        self.message_log.add_message("Data Mimic invisibility expired")
                    elif effect_name == 'speed_boost_turns':
                        self.message_log.add_message("Speed boost expired")
                    elif effect_name == 'movement_slowed_turns':
                        self.message_log.add_message("Movement returns to normal")
                    elif effect_name == 'virus_turns':
                        self.message_log.add_message("Virus purged from system")
    
    def _process_detection_increase(self, player) -> None:
        """Handle periodic detection level increases."""
        if self.game_state.turn % GameBalance.DETECTION_INCREASE_INTERVAL == 0:
            config = self.game_state.get_current_network_config()
            detection_increase = config.get('background_detection', 1) * GameBalance.DETECTION_INCREASE_AMOUNT
            
            old_detection = player.detection
            player.detection = min(100, player.detection + detection_increase)
            
            # Detection increases silently in background