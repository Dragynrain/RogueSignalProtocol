#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Engine

Main game orchestrator that coordinates all game systems through dependency injection.
Manages player state, enemy behavior, combat, inventory, and turn processing.
Delegates specialized tasks to coordinator classes for better modularity.
"""

import logging
import random

from game_achievement_popups import AchievementPopupManager
from game_ascension import calculate_ascension_modifiers
from game_audio import NullSoundManager, SoundManager
from game_characters import Enemy
from game_combat import ExploitSystem

# Import all necessary modules
from game_config import GameBalance, GameConfig, GameSettings
from game_death_handler import PlayerDeathHandler
from game_dialogue_system import DialogueState
from game_enemies import EnemyManager
from game_entities import Colors, Position
from game_errors import GameErrorHandler
from game_input import InputHandler
from game_level import LevelGenerator
from game_map import GameMap
from game_narrative import NarrativeManager
from game_player import Player
from game_save import SaveGameManager

# Import new specialized modules
from game_session import GameSession

# Import modular game systems
from game_state import GameStateManager, MessageLog, TurnProcessor
from game_story import StoryFragmentManager
from game_visibility_manager import VisibilityManager


class GameEngine:
    """
    Main game orchestrator that coordinates all game systems.

    Uses dependency injection to allow flexible component configuration.
    Delegates specialized operations to coordinator classes:
    - GameStatePersistence: Save/load operations
    - GameLevelCoordinator: Level generation and progression
    - GameTurnManager: Turn processing and enemy updates
    """

    def __init__(
        self,
        game_state_manager: GameStateManager | None = None,
        game_map: GameMap | None = None,
        level_generator: LevelGenerator | None = None,
        enemy_manager: EnemyManager | None = None,
        exploit_system: ExploitSystem | None = None,
        input_handler: InputHandler | None = None,
        sound_manager: SoundManager | None = None,
        load_save: bool = False,
        settings: GameSettings | None = None,
        headless: bool = False,
        ascension_level: int = 0,
    ) -> None:
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
            headless: Run in headless mode (no rendering/audio, for testing)
            ascension_level: Ascension difficulty level (0-20, default 0)
        """
        # Store headless mode flag
        self.headless = headless

        # Initialize ascension system
        self.ascension_level = ascension_level
        self.ascension_modifiers = calculate_ascension_modifiers(ascension_level)
        logging.info(
            f"Ascension A{ascension_level}: scanner_vision={self.ascension_modifiers.scanner_vision_bonus}, "
            f"enemy_hp={self.ascension_modifiers.enemy_hp_bonus}, "
            f"trace_mult={self.ascension_modifiers.trace_gain_multiplier}, "
            f"enemy_dmg={self.ascension_modifiers.enemy_damage_multiplier}, "
            f"enemy_vision={self.ascension_modifiers.enemy_vision_bonus}"
        )

        # Initialize settings first (needed by other systems)
        self.settings = settings or GameSettings()

        # Initialize core dependencies (with fallbacks if not provided)
        self.game_state = game_state_manager or GameStateManager()
        self.game_map = game_map or GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.visibility_manager = VisibilityManager(self.game_map)  # Centralized FOV caching
        self.level_generator = level_generator or LevelGenerator(self.game_map)
        self.enemy_manager = enemy_manager or EnemyManager(
            self.game_map, None
        )  # Will set message_log below
        # ExploitSystem will be initialized after self is fully constructed
        self._exploit_system_param = exploit_system
        # Use NullSoundManager in headless mode (no audio, but same interface)
        if headless:
            self.sound_manager = NullSoundManager(self.settings)
        else:
            self.sound_manager = sound_manager or SoundManager(self.settings)

        # Initialize core game objects
        self.player = Player(5, 5)
        self.message_log = MessageLog()

        # Initialize death handler (centralized player death handling)
        self.death_handler = PlayerDeathHandler(self)
        self.pending_death_dialogue = False  # Deferred death dialogue flag

        # Apply ascension modifiers to player
        # A10: Player vision override (15 -> 12)
        if self.ascension_modifiers.player_vision_override is not None:
            self.player.ascension_vision_override = self.ascension_modifiers.player_vision_override
        # A14: Starting RAM override (8 -> 6)
        if self.ascension_modifiers.starting_ram_override is not None:
            self.player.ram_total = self.ascension_modifiers.starting_ram_override

        # Initialize metrics tracking system (will be overwritten if loading save)
        from game_metrics import init_session_metrics

        self.metrics = init_session_metrics()
        # Set the ascension level in metrics for achievement tracking
        self.metrics.ascension_level = self.ascension_level

        # Update enemy manager with message log
        self.enemy_manager.message_log = self.message_log

        # Initialize turn processor with dependencies and ascension modifiers
        self.turn_processor = TurnProcessor(
            self.game_state, self.message_log, self.ascension_modifiers
        )

        # Initialize game session coordinator (combines turn, level, and persistence)
        self.game_session = GameSession(self)

        # Initialize dialogue state with settings for preference persistence
        self.dialogue_state = DialogueState(self.settings)

        # Initialize achievement popup manager
        self.achievement_popup_manager = AchievementPopupManager()

        # Preload all sound effects (NullSoundManager will no-op in headless mode)
        self.sound_manager.preload_sounds()

        # UI state
        self.show_inventory = False
        self.show_help = False
        self.show_main_menu = False
        self.show_settings = False
        self.show_about = False

        # Track when player first steps on nodes to avoid repeated sounds
        self.last_node_position: tuple[int, int] | None = None
        self.show_lore_viewer = False
        self.show_achievements = False
        self.show_ascension = False
        self.lore_viewer_selection = 0
        self.lore_viewer_mode = "list"
        self.inventory_selection = 0
        self.inventory_scroll_offset = 0

        # Targeting system
        self.targeting_mode = False
        self.targeting_exploit: str | None = None
        self.cursor_position = Position(0, 0)

        # Exploit cycling (Phase 2: Gamepad Support)
        # Tracks currently selected exploit for gamepad cycling (RB/LB buttons)
        self.selected_exploit_index = 0

        # Look mode system
        self.look_mode = False
        self.look_cursor_position = Position(0, 0)
        self.look_mode_mouse_last_update: float = 0.0  # Throttle mouse updates in look mode

        # Mouse hover tracking (for visual feedback)
        self.mouse_hover_world_pos: Position | None = None
        self.mouse_tile_pos: tuple[int, int] | None = None  # Mouse position in console tile coords

        # Camera offset tracking (for consistent input/rendering in look mode)
        self.last_camera_offset: Position | None = None

        # Auto-walk system (click-to-walk for distant tiles)
        from game_autowalk import AutoWalk

        self.autowalk = AutoWalk()

        # Overclocking system
        self.overclock_confirmation = False
        self.overclock_exploit: str | None = None

        # System Crash confirmation system
        self.system_crash_confirmed = False

        # Friendly fire confirmation system
        self.friendly_fire_confirmed = False
        self.friendly_fire_exploit: str | None = None
        self.friendly_fire_target: Position | None = None

        # Code hack system
        self.code_hack_effects: dict[str, tuple[str, str]] = {}
        self.discovered_code_effects: dict[str, str] = {}

        # Story fragment system
        self.story_fragment_manager = StoryFragmentManager()

        # Environmental narrative system
        self.narrative_manager = NarrativeManager()

        # Particle system for visual effects (graphics mode only, skip in headless)
        if not headless:
            from game_particle_system import ParticleSystem

            self.particle_system = ParticleSystem()
        else:
            self.particle_system = None

        # Mouse position tracking for hover effects
        self.last_mouse_tile_x: int | None = None
        self.last_mouse_tile_y: int | None = None

        # Initialize ExploitSystem after game engine is mostly constructed
        self.exploit_system = self._exploit_system_param or ExploitSystem(self)

        # Initialize game state
        if load_save:
            success = self.game_session.load_from_save()
            if not success:
                # Raise exception instead of silently falling back to new game
                from game_save import SaveLoadError

                raise SaveLoadError(
                    "Failed to load save file - file may be missing, corrupted, or incompatible with current version"
                )
        else:
            self._randomize_code_hacks()
            self.game_session.generate_procedural_level()
            # Show intro messages for new games
            self.message_log.add_message_typed("CONSCIOUSNESS RESTORED", "success")
            self.message_log.add_message_typed(
                "The simulation is failing. They're coming for you.", "critical"
            )
            self.message_log.add_message("Find the gateway - escape before De-Resolution.")
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
    def equipped_exploits(self) -> list:
        """List of currently equipped exploits (non-None slots)."""
        return [e for e in self.player.exploits if e is not None]

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
    def enemies(self) -> list[Enemy]:
        """List of all enemies."""
        return self.enemy_manager.enemies

    @enemies.setter
    def enemies(self, value: list[Enemy]) -> None:
        """Set the enemies list."""
        self.enemy_manager.enemies = value

    def get_enemy_id_counter(self) -> int:
        """
        Get current enemy ID counter for save game serialization.

        This method provides the Enemy class's ID counter without requiring
        the save system to import the Enemy class directly (dependency inversion).

        Returns:
            Current enemy ID counter value
        """
        return Enemy.get_next_id_counter()

    def _get_enemy_at(self, position: Position) -> Enemy | None:
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

    def get_input_mapper(self):
        """
        Get the input mapper for action name lookups.

        Centralizes the input mapper retrieval logic that was previously duplicated
        across game_combat.py, game_turn_manager.py, and game_input_dialogue.py.

        Returns:
            InputMapper instance if available, None otherwise
        """
        # Try direct access first (newer pattern)
        if hasattr(self, "input_mapper") and self.input_mapper is not None:
            return self.input_mapper
        # Fall back to input_handler (older pattern)
        if hasattr(self, "input_handler") and self.input_handler is not None:
            return getattr(self.input_handler, "input_mapper", None)
        return None

    def auto_save(self) -> None:
        """Auto-save the current game state."""
        if not self.game_over:  # Don't auto-save if game is over
            success = SaveGameManager.save_game(self)
            if success:
                logging.info("Auto-save completed")
            else:
                logging.warning("Auto-save failed")

    @property
    def visible_tiles(self):
        """Get cached set of visible tiles for the current turn."""
        return self.visibility_manager.get_player_visible_tiles(self.player, self.game_state.turn)

    def _randomize_code_hacks(self):
        """
        Randomize code hack effects for this game session.

        Each game session randomly assigns effects to color-coded hacks,
        requiring players to discover what each color does through experimentation.
        This creates variety and prevents players from memorizing optimal strategies.
        """
        # Clear discovered effects when starting new game
        self.discovered_code_effects.clear()

        colors = ["crimson", "azure", "emerald", "golden", "violet", "silver"]
        effects = [
            (
                "restore_cpu",
                f"Restore {GameBalance.CPU_RESTORE_MIN}-{GameBalance.CPU_RESTORE_MAX} CPU",
            ),
            ("reduce_heat", f"Reduce heat by {GameBalance.HEAT_REDUCTION_INSTANT}°C instantly"),
            ("reduce_trace_level", "-25% trace level"),
            ("speed_boost", "Speed boost: 2 moves per turn (3 enemy turns)"),
            ("enhanced_vision", "Enhanced vision (5 turns)"),
            ("exploit_efficiency", "Exploit efficiency (8 turns)"),
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

        # Note: speed_moves_remaining is managed by game_session.process_turn()
        # It grants moves when buff is active and remaining moves are 0
        # Moves are consumed in maybe_process_turn() and naturally decay to 0

        # Check for enemy at target position first
        new_position = Position(
            max(0, min(GameConfig.MAP_WIDTH - 1, self.player.x + dx)),
            max(0, min(GameConfig.MAP_HEIGHT - 1, self.player.y + dy)),
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
                if (
                    self.game_map.gateway
                    and self.player.position.grid_distance_to(self.game_map.gateway) == 0
                ):
                    self.sound_manager.play_sound("ui_menu_open")
                    # Show dialogue - level transition happens on confirmation
                    from game_dialogue_system import create_gateway_dialogue

                    # Get input mapper for dynamic button hints
                    input_mapper = self.get_input_mapper()

                    gateway_dialogue = create_gateway_dialogue(self.game_state.level, input_mapper)
                    if self.dialogue_state.should_show_dialogue(gateway_dialogue):
                        self.dialogue_state.show(gateway_dialogue)
                    # Don't progress immediately - wait for dialogue confirmation
                    return

                # Check for overheating
                if self.player.heat >= self.player.max_heat:
                    self.sound_manager.play_sound("player_overheat", priority=8)
                    damage = 5 + (self.player.heat - self.player.max_heat)
                    self.player.take_damage(damage)
                    self.player.heat = max(
                        GameBalance.OVERHEAT_MINIMUM_HEAT,
                        self.player.max_heat - GameBalance.OVERHEAT_COOLDOWN_AMOUNT,
                    )
                    self.message_log.add_message(f"Overheating! {damage} CPU damage")

                    # Track metrics
                    from game_metrics import track

                    track("overheating_events")

                    # Check for death from overheat
                    self.death_handler.check_death("overheat")

                # Handle speed boost and turn processing only if move was successful
                self.maybe_process_turn()
            else:
                # Movement blocked - don't process turn
                self.message_log.add_message("Wall blocks movement")
                # Reset analog stick gating so player can immediately try another direction
                if (
                    hasattr(self, "input_handler")
                    and hasattr(self.input_handler, "gamepad_handler")
                    and hasattr(self.input_handler.gamepad_handler, "analog_handler")
                ):
                    self.input_handler.gamepad_handler.analog_handler.reset_movement_gating()

    def cycle_exploit_selection(self, direction: int):
        """
        Cycle through equipped exploits (Phase 2: Gamepad Support).

        Used by gamepad shoulder buttons (RB/LB) and keyboard bindings ([/]).
        Wraps around available exploits only (skips empty slots).

        Args:
            direction: +1 for next, -1 for previous
        """
        from game_entities import Colors

        # Get list of equipped exploits (non-None slots)
        equipped_exploits = [e for e in self.player.exploits if e is not None]

        if not equipped_exploits:
            self.message_log.add_message("No exploits equipped", Colors.YELLOW)
            # Reset selection index when no exploits
            self.selected_exploit_index = 0
            return

        # Clamp index to valid range (edge case: exploits changed since last cycle)
        if self.selected_exploit_index >= len(equipped_exploits):
            self.selected_exploit_index = 0
        elif self.selected_exploit_index < 0:
            self.selected_exploit_index = 0

        # Cycle through available exploits
        self.selected_exploit_index = (self.selected_exploit_index + direction) % len(
            equipped_exploits
        )

        # Visual feedback only (no System Log spam)
        # The selected exploit is shown in the UI already, no need for message log

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

        # If player has movement inhibition, enemies get 1 extra move (2 moves per 1 player move)
        if self.player.temporary_effects["movement_slowed_turns"] > 0:
            self.message_log.add_message("Movement inhibition: Enemies get double moves")
            # Process enemy updates once for the double move advantage (already got 1 from process_turn)
            self.game_session._update_enemies()

    def _perform_bump_attack(self, target_enemy: Enemy):
        """
        Perform a melee bump attack on an adjacent enemy.

        Damage calculation:
        - Base damage: 30 (balanced for enemy HP pools)
        - Stealth bonus: +10 if attacking from shadows or while invisible

        Effects:
        - Generates 8 base heat + 1 per consecutive attack at same position
        - Heat reduced by 30% if exploit efficiency active
        - Restores CPU on enemy elimination
        - Makes damaged enemies hostile and aware of player position
        - Preserves patrol state for PATROL enemies before hostility
        """
        # Calculate base damage - rebalanced for new enemy HP values
        base_damage = 30  # Increased from 25 to match average enemy damage

        # Stealth bonus: extra damage if attacking from blind spots or while invisible
        stealth_bonus = 0
        if self.game_map.is_blind_spot(self.player.position) or self.player.is_invisible():
            stealth_bonus = 10  # Reduced from 15 to prevent trivial one-shots
            self.sound_manager.play_sound("stealth_attack")
            self.message_log.add_message("Stealth attack!")
        else:
            self.sound_manager.play_sound("player_attack")

        total_damage = base_damage + stealth_bonus

        # Log the attack with damage amount
        self.message_log.add_message(f"{target_enemy.type_data.name} damaged")

        # Apply damage
        if target_enemy.take_damage(total_damage):
            # Enemy destroyed
            is_admin = target_enemy.type == "admin"
            self.sound_manager.play_sound("enemy_death")

            # Trigger particle explosion effect (graphics mode only, if enabled)
            if (
                hasattr(self, "particle_system")
                and self.particle_system is not None
                and hasattr(self, "tile_manager")
                and self.tile_manager is not None
                and self.settings.graphics_mode == "graphics"
                and self.settings.show_particle_effects
            ):
                try:
                    # Extract colors from enemy sprite for particles
                    from game_config import GameConfig

                    colors = self.tile_manager.extract_sprite_colors(
                        target_enemy.type, num_colors=GameConfig.PARTICLE_SPRITE_COLOR_COUNT()
                    )

                    # Create explosion at enemy position (uses particle_count from config)
                    self.particle_system.create_death_explosion(
                        world_x=target_enemy.x, world_y=target_enemy.y, colors=colors
                    )
                    logging.debug("Particle explosion created for bump attack kill")
                except Exception as e:
                    GameErrorHandler.handle_error(
                        e, "particle_effect", "Particle effect failed in bump attack", fatal=False
                    )
            self.enemy_manager.remove_enemy(target_enemy)
            self.player.cpu = min(
                self.player.max_cpu, self.player.cpu + GameBalance.ENEMY_ELIMINATION_CPU_REWARD
            )  # Small CPU recovery
            self.message_log.add_message(
                f"Eliminated {target_enemy.type_data.name} (+{GameBalance.ENEMY_ELIMINATION_CPU_REWARD} CPU)"
            )

            # Track kill metrics using consolidated helper
            from game_entities import EnemyState
            from game_metrics import track_enemy_kill

            track_enemy_kill(
                enemy_type=target_enemy.type,
                damage=total_damage,
                was_stealth=(target_enemy.state == EnemyState.UNAWARE),
                is_admin=is_admin,
                from_blind_spot=self.game_map.is_blind_spot(self.player.position),
                enemies_remaining=len(self.enemies),
                game=self,
            )

            # Add environmental narrative for first combat or admin defeat
            if is_admin:
                env_msg = self.narrative_manager.trigger_admin_defeated()
            else:
                env_msg = self.narrative_manager.trigger_first_combat()
            if env_msg:
                self.message_log.add_message(env_msg)
        else:
            # Enemy damaged but alive - show remaining health
            self.message_log.add_message(
                f"{target_enemy.type_data.name} health: {target_enemy.cpu}/{target_enemy.max_cpu}"
            )
            # Make enemy hostile and aware of player
            target_enemy.make_hostile(self.player.position)

        # Generate some heat from the attack
        # Track consecutive attacks at same location for heat penalty
        if not hasattr(self.player, "last_attack_position"):
            self.player.last_attack_position = None
            self.player.consecutive_attacks_here = 0

        if self.player.position == self.player.last_attack_position:
            self.player.consecutive_attacks_here += 1
        else:
            self.player.consecutive_attacks_here = 0

        self.player.last_attack_position = Position(self.player.x, self.player.y)

        # Base heat + penalty for standing still
        heat_penalty = self.player.consecutive_attacks_here
        heat_generated = 8 + heat_penalty

        # A17+: Add melee heat bonus for bump attacks (they're melee attacks)
        heat_generated += self.ascension_modifiers.melee_heat_bonus

        if self.player.temporary_effects["exploit_efficiency_turns"] > 0:
            heat_generated = int(heat_generated * 0.7)  # Reduced heat with efficiency

        # Show penalty message if it's building up
        if heat_penalty > 0:
            self.message_log.add_message(
                f"Attacking from same spot: +{heat_penalty} heat penalty", Colors.YELLOW
            )

        self.player.heat = min(self.player.max_heat, self.player.heat + heat_generated)

        # Track highest heat reached for achievements (cold_blooded, heat_master)
        from game_metrics import track_highest_heat

        track_highest_heat(self.player.heat)

    def _move_cursor(self, dx: int, dy: int):
        """Move targeting cursor."""
        new_x = max(0, min(GameConfig.MAP_WIDTH - 1, self.cursor_position.x + dx))
        new_y = max(0, min(GameConfig.MAP_HEIGHT - 1, self.cursor_position.y + dy))
        self.cursor_position = Position(new_x, new_y)

    def get_enemy_next_positions(self, enemy: Enemy, steps: int = 3) -> list[Position]:
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
