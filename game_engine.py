#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Engine

Main game orchestrator that coordinates all game systems through dependency injection.
Manages player state, enemy behavior, combat, inventory, and turn processing.
Delegates specialized tasks to coordinator classes for better modularity.
"""

import logging
import random
from typing import List, Tuple, Optional, Dict, Any

# Import all necessary modules
from game_config import GameSettings, GameConfig, GameBalance
from game_entities import Position, Colors
from game_data import GameData, GameUpgrades
from game_inventory import InventoryItem, CodeHack, ExploitItem, StoryFragment, InventoryManager
from game_characters import Player, Enemy
from game_audio import SoundManager
from game_save import SaveGameManager
from game_story import StoryFragmentManager
from game_narrative import NarrativeManager

# Import modular game systems
from game_state import GameStateManager, TurnProcessor, MessageLog
from game_level import LevelGenerator
from game_enemies import EnemyManager
from game_combat import ExploitSystem
from game_map import GameMap
from game_input import InputHandler

# Import new specialized modules
from game_session import GameSession
from game_dialogue_system import DialogueState


class GameEngine:
    """
    Main game orchestrator that coordinates all game systems.

    Uses dependency injection to allow flexible component configuration.
    Delegates specialized operations to coordinator classes:
    - GameStatePersistence: Save/load operations
    - GameLevelCoordinator: Level generation and progression
    - GameTurnManager: Turn processing and enemy updates
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
        # Initialize settings first (needed by other systems)
        self.settings = settings or GameSettings()

        # Initialize core dependencies (with fallbacks if not provided)
        self.game_state = game_state_manager or GameStateManager()
        self.game_map = game_map or GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = level_generator or LevelGenerator(self.game_map)
        self.enemy_manager = enemy_manager or EnemyManager(self.game_map, None)  # Will set message_log below
        # ExploitSystem will be initialized after self is fully constructed
        self._exploit_system_param = exploit_system
        self.sound_manager = sound_manager or SoundManager(self.settings)

        # Initialize core game objects
        self.player = Player(5, 5)
        self.message_log = MessageLog()

        # Initialize metrics tracking system (will be overwritten if loading save)
        from game_metrics import init_session_metrics
        self.metrics = init_session_metrics()

        # Update enemy manager with message log
        self.enemy_manager.message_log = self.message_log

        # Initialize turn processor with dependencies
        self.turn_processor = TurnProcessor(self.game_state, self.message_log)

        # Initialize game session coordinator (combines turn, level, and persistence)
        self.game_session = GameSession(self)

        # Initialize dialogue state with settings for preference persistence
        self.dialogue_state = DialogueState(self.settings)

        # Preload all sound effects
        self.sound_manager.preload_sounds()

        # UI state
        self.show_inventory = False
        self.show_help = False
        self.show_story_fragment: Optional[int] = None

        # Track when player first steps on nodes to avoid repeated sounds
        self.last_node_position: Optional[Tuple[int, int]] = None
        self.show_lore_viewer = False
        self.lore_viewer_selection = 0
        self.lore_viewer_mode = "list"
        self.inventory_selection = 0
        self.inventory_scroll_offset = 0

        # Targeting system
        self.targeting_mode = False
        self.targeting_exploit: Optional[str] = None
        self.cursor_position = Position(0, 0)

        # Look mode system
        self.look_mode = False
        self.look_cursor_position = Position(0, 0)

        # Mouse hover tracking (for visual feedback)
        self.mouse_hover_world_pos: Optional[Position] = None
        self.mouse_tile_pos: Optional[Tuple[int, int]] = None  # Mouse position in console tile coords

        # Camera offset tracking (for consistent input/rendering in look mode)
        self.last_camera_offset: Optional[Position] = None

        # Auto-walk system (click-to-walk for distant tiles)
        from game_autowalk import AutoWalk
        self.autowalk = AutoWalk()

        # Overclocking system
        self.overclock_confirmation = False
        self.overclock_exploit: Optional[str] = None

        # Code hack system
        self.code_hack_effects: Dict[str, Tuple[str, str]] = {}
        self.discovered_code_effects: Dict[str, str] = {}

        # Story fragment system
        self.story_fragment_manager = StoryFragmentManager()

        # Environmental narrative system
        self.narrative_manager = NarrativeManager()

        # Mouse position tracking for hover effects
        self.last_mouse_tile_x: Optional[int] = None
        self.last_mouse_tile_y: Optional[int] = None

        # Initialize ExploitSystem after game engine is mostly constructed
        self.exploit_system = self._exploit_system_param or ExploitSystem(self)

        # Initialize game state
        if load_save:
            success = self.game_session.load_from_save()
            if not success:
                # Fallback to new game if loading fails
                self._randomize_code_hacks()
                self.game_session.generate_procedural_level()
        else:
            self._randomize_code_hacks()
            self.game_session.generate_procedural_level()
            # Show intro messages for new games
            self.message_log.add_message_typed("CONSCIOUSNESS RESTORED", 'cyan')
            self.message_log.add_message("The simulation is failing. They're coming for you.")
            self.message_log.add_message("Find the gateway (>) - escape before De-Resolution.")
            # Show intro dialogue
            from game_dialogue_system import create_intro_dialogue
            self.dialogue_state.show(create_intro_dialogue())

        # Initialize InputHandler after GameEngine is fully set up (requires self reference)
        if input_handler is None:
            self.input_handler = InputHandler(self)
        else:
            self.input_handler = input_handler

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
    # These methods delegate to the game session coordinator
    def _process_player_turn(self):
        """Process player turn by updating temporary effects and incrementing turn counter."""
        self.turn_processor.process_turn(self.player)

    def _process_enemies_turn(self):
        """Process all enemy turns (movement, attacks, AI decisions)."""
        self.game_session._update_enemies()

    def _process_special_tiles(self):
        """Process special tile effects (cooling nodes, CPU recovery, etc.)."""
        self.game_session._process_special_tiles()

    def _update_enemies(self):
        """Update enemy AI, movement, and pathfinding."""
        self.game_session._update_enemies()

    def _generate_procedural_level(self):
        """Generate a new procedural level with rooms, enemies, and items."""
        self.game_session.generate_procedural_level()

    def _update_enemy_awareness(self):
        """Update enemy awareness states based on FOV and player visibility."""
        self.game_session._update_all_enemy_awareness()

    def auto_save(self) -> None:
        """Auto-save the current game state."""
        if not self.game_over:  # Don't auto-save if game is over
            success = SaveGameManager.save_game(self)
            if success:
                logging.info("Auto-save completed")
            else:
                logging.warning("Auto-save failed")

    def _randomize_code_hacks(self):
        """
        Randomize code hack effects for this game session.

        Each game session randomly assigns effects to color-coded hacks,
        requiring players to discover what each color does through experimentation.
        This creates variety and prevents players from memorizing optimal strategies.
        """
        # Clear discovered effects when starting new game
        self.discovered_code_effects.clear()

        colors = ['crimson', 'azure', 'emerald', 'golden', 'violet', 'silver']
        effects = [
            ('restore_cpu', f'Restore {GameBalance.CPU_RESTORE_MIN}-{GameBalance.CPU_RESTORE_MAX} CPU'),
            ('reduce_heat', f'Reduce heat by {GameBalance.HEAT_REDUCTION_INSTANT}°C instantly'),
            ('reduce_trace_level', '-25% trace level'),
            ('speed_boost', 'Speed boost: 2 moves per turn (3 enemy turns)'),
            ('enhanced_vision', 'Enhanced vision (5 turns)'),
            ('exploit_efficiency', 'Exploit efficiency (8 turns)')
        ]

        random.shuffle(effects)
        for color, (effect, desc) in zip(colors, effects):
            self.code_hack_effects[color] = (effect, desc)

    def process_turn(self):
        """Process one complete game turn - delegates to GameSession."""
        self.game_session.process_turn()

    def move_player(self, dx: int, dy: int):
        """
        Move player by delta coordinates and process the resulting turn.

        Handles:
        - Cursor movement in targeting mode
        - Bump attacks on enemies
        - Movement validation and wall blocking
        - Gateway detection for level progression
        - Overheating damage calculation
        - Speed boost mechanics (extra moves per turn)

        Args:
            dx: Change in x coordinate (-1, 0, or 1)
            dy: Change in y coordinate (-1, 0, or 1)
        """
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

                # Track metrics
                from game_metrics import track
                track("steps_taken")

                # Check for gateway - show dialogue for user confirmation
                if (self.game_map.gateway and
                    self.player.position.distance_to(self.game_map.gateway) == 0):
                    self.sound_manager.play_sound("ui_menu_open")
                    # Show dialogue - level transition happens on confirmation
                    from game_dialogue_system import create_gateway_dialogue
                    if self.dialogue_state.should_show_dialogue(create_gateway_dialogue()):
                        self.dialogue_state.show(create_gateway_dialogue())
                    # Don't progress immediately - wait for dialogue confirmation
                    return

                # Check for overheating
                if self.player.heat >= self.player.max_heat:
                    self.sound_manager.play_sound("player_overheat", priority=8)
                    damage = 5 + (self.player.heat - self.player.max_heat)
                    self.player.take_damage(damage)
                    self.player.heat = max(85, self.player.max_heat - 15)  # Cool down to 15 below max, minimum 85
                    self.message_log.add_message(f"Overheating! {damage} CPU damage")

                    # Track metrics
                    from game_metrics import track
                    track("overheating_events")

                    # Death handling moved to game_turn_manager.py (called via maybe_process_turn)

                # Handle speed boost and turn processing only if move was successful
                self.maybe_process_turn()
            else:
                # Movement blocked - don't process turn
                self.message_log.add_message("Wall blocks movement")

    def maybe_process_turn(self):
        """
        Process turn only if speed boost doesn't grant another free action.

        Speed boost allows multiple moves per turn by granting speed_moves_remaining.
        Only processes a full turn (enemy moves, effects, etc.) when no speed moves remain.
        Movement inhibition causes enemies to get double moves (2 enemy turns per 1 player action).
        """
        # Consume speed move if applicable
        if self.player.speed_moves_remaining > 0:
            self.player.speed_moves_remaining -= 1
            # Don't process full turn, just grant another move
            return

        # Process full turn when no speed moves remaining
        self.process_turn()

        # If player has movement inhibition, enemies get 2 extra moves (2 moves per 1 player move)
        if self.player.temporary_effects['movement_slowed_turns'] > 0:
            self.message_log.add_message("Movement inhibition: Enemies get double moves")
            # Process enemy updates twice for the double move advantage
            self.game_session._update_enemies()
            self.game_session._update_enemies()

    def _perform_bump_attack(self, target_enemy: Enemy):
        """
        Perform a melee bump attack on an adjacent enemy.

        Damage calculation:
        - Base damage: 30 (balanced for enemy HP pools)
        - Stealth bonus: +10 if attacking from shadows or while invisible
        - Speed bonus: +5 if speed boost is active

        Effects:
        - Generates 8 heat (reduced by 30% if exploit efficiency active)
        - Restores CPU on enemy elimination
        - Makes damaged enemies hostile and aware of player position
        - Preserves patrol state for PATROL enemies before hostility
        """
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
            is_admin = target_enemy.type == 'admin'
            self.sound_manager.play_sound("enemy_death")
            self.enemy_manager.remove_enemy(target_enemy)
            self.player.cpu = min(self.player.max_cpu, self.player.cpu + GameBalance.ENEMY_ELIMINATION_CPU_REWARD)  # Small CPU recovery
            self.message_log.add_message(f"Eliminated {target_enemy.type_data.name} (+{GameBalance.ENEMY_ELIMINATION_CPU_REWARD} CPU)")

            # Track metrics
            from game_metrics import track
            from game_entities import EnemyState
            track("enemies_killed", category=target_enemy.type)
            track("damage_dealt", amount=total_damage)
            if target_enemy.state == EnemyState.UNAWARE:
                track("stealth_kills")

            # Add environmental narrative for first combat or admin defeat
            if is_admin:
                env_msg = self.narrative_manager.trigger_admin_defeated()
            else:
                env_msg = self.narrative_manager.trigger_first_combat()
            if env_msg:
                self.message_log.add_message(env_msg)
        else:
            # Enemy damaged but alive - show remaining health
            self.message_log.add_message(f"{target_enemy.type_data.name} health: {target_enemy.cpu}/{target_enemy.max_cpu}")
            # Store patrol information for PATROL enemies before becoming hostile
            from game_entities import EnemyMovement
            movement_type = target_enemy.get_movement_type()
            if movement_type == EnemyMovement.PATROL and target_enemy.patrol_points:
                target_enemy.original_patrol_index = target_enemy.patrol_index
            # Make enemy hostile and aware of player
            from game_entities import EnemyState
            target_enemy.state = EnemyState.HOSTILE
            target_enemy.last_seen_player = Position(self.player.x, self.player.y)

        # Generate some heat from the attack
        heat_generated = 8
        if self.player.temporary_effects['exploit_efficiency_turns'] > 0:
            heat_generated = int(heat_generated * 0.7)  # Reduced heat with efficiency

        self.player.heat = min(100, self.player.heat + heat_generated)

    def _move_cursor(self, dx: int, dy: int):
        """Move targeting cursor."""
        new_x = max(0, min(GameConfig.MAP_WIDTH - 1, self.cursor_position.x + dx))
        new_y = max(0, min(GameConfig.MAP_HEIGHT - 1, self.cursor_position.y + dy))
        self.cursor_position = Position(new_x, new_y)

    def get_enemy_next_positions(self, enemy: Enemy, steps: int = 3) -> List[Position]:
        """
        Get predicted next positions for an enemy from their movement queue.

        Returns up to 'steps' positions from the enemy's actual FIFO movement queue.
        This shows the player what the enemy is planning to do next, enabling
        tactical positioning and threat assessment. Disabled enemies return empty list.

        Args:
            enemy: The enemy to query
            steps: Maximum number of future positions to return (default 3)

        Returns:
            List of Position objects representing planned moves (empty if disabled)
        """
        if enemy.disabled_turns > 0:
            return []

        # Return up to 'steps' positions from the actual movement queue
        return enemy.move_queue[:steps]

    def next_level(self):
        """Progress to the next level - delegates to GameSession."""
        self.game_session.progress_to_next_level()

    def get_game_state_for_save(self) -> dict:
        """
        Get the current game state as a dictionary for saving.

        Serializes all necessary game state including:
        - Player stats, position, inventory, and temporary effects
        - Enemy positions, states, and AI data
        - Map items and special locations (gateway, nodes, pickups)
        - Code hack effects and discovered effects for this session
        - UI state for better user experience on load

        Map layout is NOT saved - regenerated using the same dungeon_seed.
        This reduces save file size while maintaining deterministic level generation.

        Returns:
            Dictionary containing all serialized game state
        """
        import time
        from game_save import SaveGameManager
        from game_characters import Enemy

        return {
            "version": "0.8.0 Alpha",
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
                "trace level": self.player.trace_level,
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

            # Code hack effects for this run
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