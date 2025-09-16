"""
Command interface using Command pattern for input handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..game.entities import Game


class CommandStatus(Enum):
    """Status of command execution."""
    SUCCESS = "success"
    FAILED = "failed"
    INVALID = "invalid"
    BLOCKED = "blocked"
    QUEUED = "queued"


@dataclass
class CommandResult:
    """
    Result of command execution.
    
    Contains status, message, and any additional data from execution.
    """
    status: CommandStatus
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    consume_turn: bool = True
    
    def is_success(self) -> bool:
        """Check if command was successful."""
        return self.status == CommandStatus.SUCCESS
    
    def is_failed(self) -> bool:
        """Check if command failed."""
        return self.status == CommandStatus.FAILED
    
    def should_consume_turn(self) -> bool:
        """Check if command should consume a game turn."""
        return self.consume_turn and self.status == CommandStatus.SUCCESS


class Command(ABC):
    """
    Abstract base class for all game commands using Command pattern.
    
    This allows for:
    - Undo/redo functionality
    - Command queuing and batching
    - Macro recording and playback
    - Input remapping without changing game logic
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize command.
        
        Args:
            name: Command identifier
            description: Human-readable description
        """
        self.name = name
        self.description = description
        self.execution_count = 0
        self.last_result: Optional[CommandResult] = None
    
    @abstractmethod
    def execute(self, game_context: 'Game', **kwargs) -> CommandResult:
        """
        Execute the command.
        
        Args:
            game_context: Current game state
            **kwargs: Additional parameters for command
            
        Returns:
            Result of command execution
        """
        pass
    
    def can_execute(self, game_context: 'Game', **kwargs) -> bool:
        """
        Check if command can be executed in current context.
        
        Args:
            game_context: Current game state
            **kwargs: Additional parameters for command
            
        Returns:
            True if command can be executed
        """
        return True
    
    def get_cost(self, game_context: 'Game', **kwargs) -> Dict[str, int]:
        """
        Get resource cost of executing this command.
        
        Args:
            game_context: Current game state
            **kwargs: Additional parameters
            
        Returns:
            Dictionary of resource costs (heat, ram, etc.)
        """
        return {}
    
    def undo(self, game_context: 'Game') -> CommandResult:
        """
        Undo the command (if supported).
        
        Args:
            game_context: Current game state
            
        Returns:
            Result of undo operation
        """
        return CommandResult(
            CommandStatus.FAILED, 
            f"Undo not supported for {self.name}"
        )
    
    def can_undo(self) -> bool:
        """Check if this command supports undo."""
        return False
    
    def get_undo_data(self) -> Optional[Dict[str, Any]]:
        """Get data needed for undo operation."""
        return None
    
    def get_help_text(self) -> str:
        """Get help text for this command."""
        return self.description or f"Execute {self.name} command"
    
    def __str__(self) -> str:
        """String representation."""
        return self.name
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"Command(name='{self.name}', executions={self.execution_count})"


class UndoableCommand(Command):
    """
    Base class for commands that support undo functionality.
    """
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
        self._undo_data: Optional[Dict[str, Any]] = None
    
    def can_undo(self) -> bool:
        """Undoable commands support undo by default."""
        return True
    
    def store_undo_data(self, data: Dict[str, Any]) -> None:
        """Store data needed for undo operation."""
        self._undo_data = data.copy()
    
    def get_undo_data(self) -> Optional[Dict[str, Any]]:
        """Get stored undo data."""
        return self._undo_data


class CompositeCommand(Command):
    """
    Command that executes multiple sub-commands in sequence.
    
    Useful for macros and complex operations.
    """
    
    def __init__(self, name: str, commands: list[Command], description: str = ""):
        super().__init__(name, description)
        self.commands = commands[:]
        self.stop_on_failure = True
    
    def execute(self, game_context: 'Game', **kwargs) -> CommandResult:
        """Execute all sub-commands in sequence."""
        results = []
        
        for command in self.commands:
            if not command.can_execute(game_context, **kwargs):
                return CommandResult(
                    CommandStatus.BLOCKED,
                    f"Sub-command {command.name} cannot be executed"
                )
            
            result = command.execute(game_context, **kwargs)
            results.append(result)
            
            if self.stop_on_failure and not result.is_success():
                return CommandResult(
                    CommandStatus.FAILED,
                    f"Sub-command {command.name} failed: {result.message}",
                    {"failed_at": len(results), "results": results}
                )
        
        success_count = sum(1 for r in results if r.is_success())
        
        return CommandResult(
            CommandStatus.SUCCESS,
            f"Executed {success_count}/{len(self.commands)} commands",
            {"results": results}
        )
    
    def can_execute(self, game_context: 'Game', **kwargs) -> bool:
        """Check if all sub-commands can be executed."""
        return all(cmd.can_execute(game_context, **kwargs) for cmd in self.commands)
    
    def add_command(self, command: Command) -> None:
        """Add a command to the sequence."""
        self.commands.append(command)
    
    def remove_command(self, command: Command) -> bool:
        """Remove a command from the sequence."""
        try:
            self.commands.remove(command)
            return True
        except ValueError:
            return False


class ConditionalCommand(Command):
    """
    Command that executes only if a condition is met.
    """
    
    def __init__(self, name: str, base_command: Command, 
                 condition_func: callable, description: str = ""):
        super().__init__(name, description)
        self.base_command = base_command
        self.condition_func = condition_func
    
    def execute(self, game_context: 'Game', **kwargs) -> CommandResult:
        """Execute base command if condition is met."""
        if not self.condition_func(game_context, **kwargs):
            return CommandResult(
                CommandStatus.BLOCKED,
                f"Condition not met for {self.name}"
            )
        
        return self.base_command.execute(game_context, **kwargs)
    
    def can_execute(self, game_context: 'Game', **kwargs) -> bool:
        """Check condition and base command availability."""
        return (self.condition_func(game_context, **kwargs) and 
                self.base_command.can_execute(game_context, **kwargs))


class DelayedCommand(Command):
    """
    Command that executes after a specified delay.
    """
    
    def __init__(self, name: str, base_command: Command, 
                 delay_turns: int, description: str = ""):
        super().__init__(name, description)
        self.base_command = base_command
        self.delay_turns = delay_turns
        self.remaining_turns = 0
        self._queued = False
    
    def execute(self, game_context: 'Game', **kwargs) -> CommandResult:
        """Queue command for delayed execution."""
        if not self._queued:
            self.remaining_turns = self.delay_turns
            self._queued = True
            return CommandResult(
                CommandStatus.QUEUED,
                f"Command {self.name} queued for {self.delay_turns} turns"
            )
        
        # Check if delay has elapsed
        if self.remaining_turns > 0:
            self.remaining_turns -= 1
            return CommandResult(
                CommandStatus.QUEUED,
                f"Command {self.name} executing in {self.remaining_turns} turns"
            )
        
        # Execute the actual command
        self._queued = False
        return self.base_command.execute(game_context, **kwargs)
    
    def can_execute(self, game_context: 'Game', **kwargs) -> bool:
        """Always can queue, but check base command when actually executing."""
        if self.remaining_turns > 0:
            return True
        return self.base_command.can_execute(game_context, **kwargs)