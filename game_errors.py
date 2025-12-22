#!/usr/bin/env python3
"""
Rogue Signal Protocol - Error Handling Utilities

Centralized error handling for consistent logging and user notification.
GameErrorHandler provides static methods for error handling, warnings, and safe operations.
Special handlers for config and data loading errors with enhanced context.
"""

import logging
import traceback
from typing import Any


class GameErrorHandler:
    """Centralized error handling for consistent logging and user notification."""

    @staticmethod
    def handle_error(
        error: Exception, context: str, user_message: str | None = None, fatal: bool = False
    ) -> None:
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

        logging.debug(f"Error Handling: Caught {type(error).__name__} in {context}, fatal={fatal}")

        # Logging
        logging.error(f"ERROR: {error_details}")
        if user_message:
            logging.error(f"User Impact: {user_message}")

        logging.error(f"Exception details: {str(error)}")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.error(traceback.format_exc())

        if fatal:
            logging.critical("FATAL ERROR: Game cannot continue")
            logging.critical(f"Fatal error in {context}: {error}")
            raise error

    @staticmethod
    def handle_safe_operation(
        operation_func, context: str, fallback_value: Any = None, user_message: str | None = None
    ) -> Any:
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
            logging.debug(
                f"Error Handling: Safe operation failed in {context}, using fallback={fallback_value}"
            )
            GameErrorHandler.handle_error(e, context, user_message)
            return fallback_value

    @staticmethod
    def handle_config_error(operation: str, exception: Exception) -> None:
        """
        Handle configuration loading errors consistently.

        Args:
            operation: Description of what configuration operation failed
            exception: The exception that occurred

        Raises:
            The same exception type with enhanced message
        """
        logging.debug(
            f"Error Handling: Config error - {operation}, exception={type(exception).__name__}"
        )
        error_msg = f"CRITICAL CONFIG ERROR: {operation}"
        logging.error(error_msg)
        logging.error(f"Exception: {str(exception)}")

        # Re-raise with enhanced message but preserve original exception type
        if isinstance(exception, FileNotFoundError):
            raise FileNotFoundError(f"{operation} - file missing") from exception
        elif isinstance(exception, KeyError):
            raise KeyError(f"{operation} - required key missing") from exception
        else:
            raise type(exception)(f"{operation}: {str(exception)}") from exception
