#!/usr/bin/env python3
"""
Centralized error handling utilities for the game.
Provides consistent error logging and user notification patterns.
"""

import logging
import traceback
from typing import Optional, Any
from game_entities import Colors


class GameErrorHandler:
    """Centralized error handling for consistent logging and user notification."""

    @staticmethod
    def handle_error(error: Exception, context: str, user_message: Optional[str] = None,
                    fatal: bool = False) -> None:
        """
        Handle an error with consistent logging and user notification.

        Args:
            error: The exception that occurred
            context: Context description of where the error occurred
            user_message: Optional user-friendly message to display
            fatal: Whether this is a fatal error that should stop execution
        """
        # Create detailed error message for logging
        error_details = f"{context}: {type(error).__name__}: {str(error)}"

        # Console output (always visible to user)
        print(f"ERROR: {error_details}")
        if user_message:
            print(f"User Impact: {user_message}")

        # Logging for debugging
        logging.error(error_details)
        logging.error(f"Exception details: {str(error)}")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.error(traceback.format_exc())

        if fatal:
            print("FATAL ERROR: Game cannot continue")
            logging.critical(f"Fatal error in {context}: {error}")
            raise error

    @staticmethod
    def handle_warning(message: str, context: str) -> None:
        """
        Handle a warning with consistent logging pattern.

        Args:
            message: Warning message
            context: Context where warning occurred
        """
        warning_msg = f"{context}: {message}"
        print(f"WARNING: {warning_msg}")
        logging.warning(warning_msg)

    @staticmethod
    def handle_safe_operation(operation_func, context: str, fallback_value: Any = None,
                            user_message: Optional[str] = None) -> Any:
        """
        Safely execute an operation with error handling.

        Args:
            operation_func: Function to execute safely
            context: Context description for error reporting
            fallback_value: Value to return if operation fails
            user_message: User-friendly message if operation fails

        Returns:
            Result of operation_func or fallback_value on error
        """
        try:
            return operation_func()
        except Exception as e:
            GameErrorHandler.handle_error(e, context, user_message)
            return fallback_value

    @staticmethod
    def log_game_event(message: str, level: str = "info") -> None:
        """
        Log a game event for debugging (not user-visible errors).

        Args:
            message: Message to log
            level: Logging level (debug, info, warning, error)
        """
        log_func = getattr(logging, level.lower(), logging.info)
        log_func(f"Game Event: {message}")