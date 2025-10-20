#!/usr/bin/env python3
"""
Game State Management

Contains core state management classes:
- MessageLog: Manages game messages with automatic color coding
- GameStateManager: Tracks level, turn, game status, and active effects
- TurnProcessor: Handles turn-based logic (heat, effects, trace level)

These classes work together to maintain consistent game state across turns.
"""

import random
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

from game_config import GameConfig, GameBalance
from game_entities import Position, Colors, ensure_color_tuple
from data_loading import DataLoader
from game_save import SaveGameManager


@dataclass
class Message:
    """
    Represents a single message in the game log.

    Attributes:
        text: Message content
        color: RGB color tuple for rendering
        msg_type: Optional type identifier for categorization
    """
    text: str
    color: Tuple[int, int, int]
    msg_type: Optional[str] = None


class MessageLog:
    """
    Manages game messages with automatic color coding.

    Analyzes message content to determine appropriate color based on
    patterns defined in JSON config. Maintains a rolling buffer of messages
    to prevent excessive memory usage.
    """
    
    def __init__(self, max_messages: int = 100):
        self.messages: List[Message] = []
        self.max_messages = max_messages
    
    def add_message(self, text: str, color: Optional[Tuple[int, int, int]] = None, msg_type: Optional[str] = None):
        """
        Add a message to the log with automatic color determination.

        Color is determined by:
        1. Explicit color parameter (highest priority)
        2. Message type parameter (uses JSON config colors)
        3. Content analysis (pattern matching from JSON config)

        Args:
            text: Message content
            color: Optional explicit color (overrides automatic detection)
            msg_type: Optional message type for color lookup
        """
        if not text:
            return

        if color is None:
            color = self._get_color_by_type(msg_type) if msg_type else self._determine_message_color(text)

        self.messages.append(Message(text=text, color=color, msg_type=msg_type))

        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def add_message_typed(self, text: str, msg_type: str):
        """Add a message with explicit type specification."""
        self.add_message(text, msg_type=msg_type)
    
    def _get_color_by_type(self, msg_type: str) -> Tuple[int, int, int]:
        """Get color for a specific message type."""
        config = DataLoader.load_config()
        message_colors = config.get("colors", {}).get("message_log", {})
        return ensure_color_tuple(message_colors.get(msg_type, message_colors.get("default", [144, 238, 144])))
    
    def _determine_message_color(self, text: str) -> Tuple[int, int, int]:
        """
        Determine appropriate color for message based on content.

        Checks message text against patterns defined in JSON config
        (message_types.patterns). First matching pattern determines the color.

        Args:
            text: Message content

        Returns:
            RGB color tuple (defaults to 'default' color if no match)
        """
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
    
    def get_recent_messages(self, count: int) -> List[Message]:
        """Get the most recent messages."""
        return self.messages[-count:] if len(self.messages) > count else self.messages


class GameStateManager:
    """
    Manages core game state like level, turn, and game status.

    Maintains:
    - Level progression and turn counter
    - Game over and admin spawn flags
    - Dungeon seed for deterministic level generation
    - Active effects (threat scan, distractions, revealed nodes)

    The just_loaded flag prevents enemy state updates immediately after loading
    to avoid double-processing.
    """

    def __init__(self):
        self.level: int = 1
        self.turn: int = 0
        self.game_over: bool = False
        self.admin_spawned: bool = False
        self.dungeon_seed: int = random.randint(1, GameConfig.DUNGEON_SEED_RANGE)
        self.just_loaded: bool = False  # Flag to prevent immediate enemy state updates after load

        # Game effects
        self.threat_scan_turns: int = 0
        self.noise_locations: List[Position] = []
        self.distraction_points: Dict[Position, int] = {}
        self.revealed_special_nodes: Dict[Tuple[int, int], str] = {}  # position -> node_type
    
    def advance_turn(self) -> None:
        """
        Advance to the next turn and update time-based effects.

        Decrements threat scan duration and decays distraction points.
        Removes expired distractions from the map.
        """
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
    
    def should_spawn_admin(self, trace_level: float) -> bool:
        """
        Determine if admin should spawn based on trace level.

        Admin spawns when trace level reaches maximum (100%) and hasn't
        already spawned. Admin is a powerful boss enemy that constantly
        pursues the player with perfect vision.

        Args:
            trace_level: Current player trace level (0-100)

        Returns:
            True if admin should spawn now
        """
        if self.admin_spawned:
            return False
            
        return trace_level >= GameConfig.MAX_TRACE_LEVEL


class TurnProcessor:
    """
    Handles turn-based game logic and effects processing.

    Coordinates turn progression with:
    - Heat reduction (passive cooling)
    - Temporary effect countdown
    - Trace level increase

    Does NOT handle enemy movement or special tiles - those are handled
    by GameTurnManager.
    """

    def __init__(self, game_state: GameStateManager, message_log: MessageLog):
        """
        Initialize turn processor.

        Args:
            game_state: GameStateManager instance
            message_log: MessageLog instance for status messages
        """
        self.game_state = game_state
        self.message_log = message_log

    def process_turn(self, player) -> None:
        """
        Process a complete game turn including heat management and effects.

        Called once per player action (move, exploit, etc).
        Updates player state and increments turn counter.

        Args:
            player: Player instance to update
        """
        self.game_state.advance_turn()
        
        # Process heat reduction
        self._process_heat_management(player)
        
        # Process temporary effects
        self._process_temporary_effects(player)
        
        # Process trace level increase
        self._process_trace_increase(player)
    
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
    
    def _process_trace_increase(self, player) -> None:
        """Handle periodic trace level increases."""
        if self.game_state.turn % GameBalance.TRACE_INCREASE_INTERVAL == 0:
            config = self.game_state.get_current_network_config()
            trace_increase = config.get('background_trace', 1) * GameBalance.TRACE_INCREASE_AMOUNT
            
            old_trace = player.trace_level
            player.trace_level = min(100, player.trace_level + trace_increase)
            
            # Trace Level increases silently in background