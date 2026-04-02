"""
Centralized player death handling.

This module provides a single entry point for all player death handling,
ensuring consistent behavior regardless of death cause (combat, virus,
overheat, self-damage, etc.).

Usage:
    # At damage sites, check for death with cause tracking:
    player.take_damage(damage)
    game.death_handler.check_death("combat", source="Scanner")

    # The handler is idempotent - multiple checks are safe:
    game.death_handler.check_death("virus")  # Only handles once per death
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rsp.core.engine import GameEngine


@dataclass
class DeathEvent:
    """
    Data about a player death event.

    Captures all relevant information at the moment of death for
    analytics, achievements, and UI display.
    """

    cause: str  # "combat", "virus", "overheat", "self_damage"
    source: str | None = None  # Enemy name, exploit name, etc.
    final_cpu: int = 0
    final_heat: int = 0
    final_trace: float = 0.0
    level: int = 1
    turn: int = 0
    position: tuple[int, int] = (0, 0)
    virus_turns: int = 0
    enemies_nearby: int = 0


class PlayerDeathHandler:
    """
    Centralized player death handling.

    Provides a single entry point for all death-related logic:
    - Setting game_over state
    - Closing active dialogues
    - Playing death sounds
    - Logging analytics
    - Finalizing metrics and checking achievements
    - Deleting save file (permadeath)
    - Queuing death dialogue

    The handler is idempotent - calling check_death() multiple times
    is safe and will only handle death once.
    """

    def __init__(self, game_engine: "GameEngine"):
        self.game = game_engine
        self._handled = False
        self._death_event: DeathEvent | None = None

    @property
    def is_handled(self) -> bool:
        """Whether death has been handled this session."""
        return self._handled

    @property
    def death_event(self) -> DeathEvent | None:
        """The death event if death occurred, None otherwise."""
        return self._death_event

    def check_death(self, cause: str, source: str | None = None) -> bool:
        """
        Check if player is dead and handle death if so.

        This is the primary entry point for death handling. Call this
        after any action that could kill the player.

        Args:
            cause: Death cause for analytics ("combat", "virus", "overheat", "self_damage")
            source: Optional source entity (enemy name, exploit name, etc.)

        Returns:
            True if player is dead (whether just now or already handled)
        """
        # Check idempotency first - if already handled, always return True
        # This prevents any edge cases where healing during death could cause issues
        if self._handled:
            return True  # Already handled this death

        if self.game.player.cpu > 0:
            return False

        # Don't process death if victory was already achieved
        # Victory takes precedence - player won, death UI should not appear
        if self.game.game_state.show_victory_screen:
            logging.debug("Death handler: Skipping death - victory already achieved")
            return True  # Player is "dead" but we don't handle it (victory wins)

        # Prologue death is handled differently - no permadeath
        if getattr(self.game, "prologue_mode", False):
            self._handle_prologue_death(cause, source)
            return True  # Player died, but we restart instead of game over

        # Build death event with full context
        player = self.game.player
        event = DeathEvent(
            cause=cause,
            source=source,
            final_cpu=player.cpu,
            final_heat=player.heat,
            final_trace=player.trace_level,
            level=self.game.level,
            turn=self.game.turn,
            position=(player.x, player.y),
            virus_turns=player.temporary_effects.get("virus_turns", 0),
            enemies_nearby=len(
                [e for e in self.game.enemies if e.position.grid_distance_to(player.position) < 10]
            ),
        )

        self._handle_death(event)
        return True

    def _handle_death(self, event: DeathEvent):
        """
        Handle player death - the single source of truth for death logic.

        Order of operations:
        1. Mark as handled (prevents re-entry)
        2. Set game_over state
        3. Force-close any active dialogues
        4. Play death sounds
        5. Log analytics
        6. Finalize metrics and check achievements
        7. Delete save file
        8. Queue death dialogue for next frame

        Exception handling ensures death is always properly completed even if
        individual steps fail. Critical operations (game_over, save deletion)
        are protected and always attempted.
        """
        self._handled = True
        self._death_event = event

        # 1. Set game state - CRITICAL, must always succeed
        self.game.game_over = True

        # 2. Force-close any active dialogues and clear queue - death has highest priority
        try:
            if self.game.dialogue_state.is_active() or self.game.dialogue_state.dialogue_queue:
                logging.warning(f"{event.cause.title()} death with dialogue active/queued - force-closing all")
                self.game.dialogue_state.close_and_clear_queue()
        except Exception as e:
            logging.error(f"Death handler: Failed to close dialogue: {e}")

        # 3. Play death sounds (only here, not in renderer)
        try:
            self.game.sound_manager.play_sound("player_death", priority=10)
            self.game.sound_manager.play_sound("critical_system_failure", priority=10)
        except Exception as e:
            logging.error(f"Death handler: Failed to play death sounds: {e}")

        # 4. Log analytics - non-critical, continue on failure
        try:
            self._log_death_analytics(event)
        except Exception as e:
            logging.error(f"Death handler: Failed to log analytics: {e}")

        # 5. Finalize metrics and check achievements - non-critical
        try:
            self._finalize_metrics(event)
        except Exception as e:
            logging.error(f"Death handler: Failed to finalize metrics: {e}")

        # 6. Delete save (permadeath) - CRITICAL for permadeath mechanic
        try:
            self._delete_save()
        except Exception as e:
            # Log as error but don't crash - game_over is already set
            logging.error(f"Death handler: CRITICAL - Failed to delete save: {e}")

        # 7. Queue death dialogue for next render frame
        # (allows damage messages to render first)
        self.game.pending_death_dialogue = True

    def _log_death_analytics(self, event: DeathEvent):
        """Log death information for debugging and analytics."""
        logging.warning("=" * 80)
        logging.warning(f"PLAYER DEATH - {event.cause.upper()}")
        if event.source:
            logging.warning(f"Source: {event.source}")
        logging.warning(f"Level: {event.level}, Turn: {event.turn}")
        logging.warning(f"Position: {event.position}")
        logging.warning(f"Final CPU: {event.final_cpu}")
        logging.warning(f"Final Heat: {event.final_heat}")
        logging.warning(f"Trace Level: {event.final_trace}")
        logging.warning(f"Active Virus: {event.virus_turns} turns")
        logging.warning(f"Enemies nearby: {event.enemies_nearby}")
        logging.warning("=" * 80)

        # Flush logs immediately to ensure death info is written
        for handler in logging.root.handlers:
            handler.flush()

    def _finalize_metrics(self, event: DeathEvent):
        """Finalize session metrics and check for achievements."""
        from rsp.systems.metrics import finalize_and_save_session

        newly_unlocked = finalize_and_save_session(
            victory=False,
            death_cause=event.cause,
            death_level=event.level,
            final_cpu=event.final_cpu,
        )
        if newly_unlocked:
            logging.info(f"Unlocked {len(newly_unlocked)} achievements on death")

    def _delete_save(self):
        """Delete save file on death (permadeath)."""
        from rsp.systems.save import SaveGameManager

        if SaveGameManager.save_exists():
            try:
                SaveGameManager.delete_save()
                logging.info("Save file deleted on death (permadeath)")
                self.game.message_log.add_message("Save data purged")
            except OSError as e:
                logging.error(f"Failed to delete save on death: {e}")

    def _handle_prologue_death(self, cause: str, source: str | None = None):
        """Handle death in prologue - restart without penalty."""
        from rsp.ui.dialogue import create_prologue_death_dialogue

        # Mark as handled to prevent re-entry during restart
        # Set early for re-entrancy protection, but use try/finally to ensure
        # we complete state changes even if intermediate operations fail
        self._handled = True

        try:
            # Clear any queued dialogues (like pending thoughts) before showing death dialogue
            # This prevents confusing messages appearing after the death notification
            self.game.dialogue_state.close_and_clear_queue()
        except (AttributeError, RuntimeError):
            pass

        # Play death sounds (still want audio feedback)
        try:
            self.game.sound_manager.play_sound("player_death", priority=10)
        except (RuntimeError, OSError, AttributeError):
            pass

        # Build death message from cause and source
        if source:
            death_message = f"{cause.title()} by {source}"
        else:
            death_message = cause.title()

        # Track death for hint system (per-section death count)
        current_section = self._get_prologue_section()
        self.game.prologue_death_count += 1
        # Get death count for this section BEFORE incrementing
        section_deaths = self.game.prologue_section_deaths.get(current_section, 0)
        # Get contextual death hint based on how many times died in this section
        hint = self._get_death_hint(current_section, section_deaths)
        # Now increment death count for this section
        self.game.prologue_section_deaths[current_section] = section_deaths + 1

        # Show death dialogue with tutorial message and optional hint
        self.game.dialogue_state.show(create_prologue_death_dialogue(death_message, hint))

        # Set flag for dialogue handler to trigger restart
        self.game.prologue_restart_pending = True

        # NOTE: Do NOT set game_over = True
        # NOTE: Do NOT delete save or finalize metrics

    def _get_prologue_section(self) -> int:
        """Determine which prologue section the player is in based on position.

        Uses centralized section boundaries from fixed_levels.py to ensure
        consistency with the actual layout.
        """
        from rsp.level.fixed_levels import get_prologue_section

        return get_prologue_section(self.game.player.position.y)

    def _get_death_hint(self, section: int, deaths_in_section: int) -> str | None:
        """Get contextual death hint based on section, death count, and heat.

        Provides escalating hints:
        - 1st death: Section-specific hint
        - 2nd death: Escalating hint (more specific guidance)
        - 3rd+ death: General encouragement or no hint

        Args:
            section: Current prologue section (1-5)
            deaths_in_section: Number of previous deaths in this section

        Returns:
            Hint string or None
        """
        from rsp.core.data_loading import get_prologue_death_hints

        hints = get_prologue_death_hints()
        if not hints:
            return None

        # Heat-specific hint takes priority (heat > 60 = exploit overuse)
        if self.game.player.heat > 60:
            return hints.get("heat_death")

        # First death in section: section-specific hint
        if deaths_in_section == 0:
            return hints.get(f"section_{section}")

        # Second death in section: escalating hint (more specific)
        if deaths_in_section == 1:
            escalating = hints.get(f"section_{section}_escalate")
            if escalating:
                return escalating
            # Fall back to general encouragement
            return hints.get("general_encouragement")

        # Third+ death: general encouragement only (don't spam hints)
        if deaths_in_section == 2:
            return hints.get("general_encouragement")

        # After 3 deaths in same section, no more hints (player knows)
        return None

    def reset(self):
        """Reset handler state for a new game."""
        self._handled = False
        self._death_event = None
