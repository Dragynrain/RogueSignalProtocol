#!/usr/bin/env python3
"""
Core game logic and state management.
Extracted from RogueSignalProtocol.py for better organization.
"""

import logging
import random
from typing import Optional, Dict, Any

# Import configuration and game entities
from game_config import GameConfig, GameBalance
from game_entities import Colors


class GameStateManager:
    """Manages core game state including level, turn count, and spawning."""
    
    def __init__(self):
        self.current_level = 1
        self.turn_count = 0
        self.game_paused = False
        self.admin_spawned_this_level = False
        self.network_configs = {}
        
    def advance_turn(self):
        """Advance the turn counter."""
        self.turn_count += 1
        
    def reset_for_new_level(self):
        """Reset state when advancing to a new level."""
        self.current_level += 1
        self.admin_spawned_this_level = False
        self.turn_count = 0
        
    def get_current_network_config(self):
        """Get network configuration for current level."""
        if self.current_level not in self.network_configs:
            # Generate network config for this level
            self.network_configs[self.current_level] = {
                'security_level': min(5, self.current_level // 2 + 1),
                'admin_chance': min(0.8, 0.1 + (self.current_level - 1) * 0.05),
                'patrol_density': min(3, 1 + self.current_level // 3)
            }
        return self.network_configs[self.current_level]
        
    def should_spawn_admin(self) -> bool:
        """Determine if an admin should spawn this level."""
        if self.admin_spawned_this_level:
            return False
            
        config = self.get_current_network_config()
        if random.random() < config['admin_chance']:
            self.admin_spawned_this_level = True
            return True
        return False


class TurnProcessor:
    """Handles turn-based game logic and effects processing."""
    
    def __init__(self, game_state: GameStateManager):
        self.game_state = game_state
        
    def process_turn(self, player, message_log):
        """Process all turn-based effects and updates."""
        self.game_state.advance_turn()
        
        # Process heat management
        self._process_heat_management(player, message_log)
        
        # Process temporary effects
        self._process_temporary_effects(player, message_log)
        
        # Process detection increase
        self._process_detection_increase(player, message_log)
        
    def _process_heat_management(self, player, message_log):
        """Handle heat reduction over time."""
        if player.heat > 0:
            # Check if player is near cooling node
            cooling_boost = getattr(player, 'near_cooling_node', False)
            reduction = GameBalance.HEAT_REDUCTION_BOOSTED if cooling_boost else GameBalance.HEAT_REDUCTION_NORMAL
            
            old_heat = player.heat
            player.heat = max(0, player.heat - reduction)
            
            if old_heat != player.heat:
                heat_color = Colors.CYAN if cooling_boost else Colors.BLUE
                message_log.add_message(f"Heat reduced by {reduction} (now {player.heat})", heat_color)
                
    def _process_temporary_effects(self, player, message_log):
        """Process temporary status effects."""
        # Process virus duration
        if hasattr(player, 'virus_duration') and player.virus_duration > 0:
            player.virus_duration -= 1
            if player.virus_duration <= 0:
                message_log.add_message("Virus effect has worn off", Colors.GREEN)
                
        # Process other temporary effects
        effects_to_remove = []
        if hasattr(player, 'temporary_effects'):
            for effect_name, duration in player.temporary_effects.items():
                duration -= 1
                if duration <= 0:
                    effects_to_remove.append(effect_name)
                    message_log.add_message(f"{effect_name} effect has worn off", Colors.YELLOW)
                else:
                    player.temporary_effects[effect_name] = duration
                    
            for effect in effects_to_remove:
                del player.temporary_effects[effect]
                
    def _process_detection_increase(self, player, message_log):
        """Handle gradual detection increase."""
        # Increase detection every N turns based on game balance
        if self.game_state.turn_count % GameBalance.DETECTION_INCREASE_INTERVAL == 0:
            old_detection = player.detection
            player.detection = min(100, player.detection + GameBalance.DETECTION_INCREASE_AMOUNT)
            
            if player.detection != old_detection:
                message_log.add_message(
                    f"Network security tightening... Detection: {player.detection}%", 
                    Colors.YELLOW
                )