"""
Custom exception classes for the Rogue Signal Protocol game.
"""


class GameError(Exception):
    """Base exception for all game-related errors."""
    pass


class DataLoadError(GameError):
    """Raised when data loading operations fail."""
    pass


class SaveLoadError(GameError):
    """Raised when save/load operations fail."""
    pass


class GameLogicError(GameError):
    """Raised when game logic encounters an invalid state."""
    pass


class RenderingError(GameError):
    """Raised when rendering operations fail."""
    pass


class InputError(GameError):
    """Raised when input handling encounters an error."""
    pass


class ConfigurationError(GameError):
    """Raised when configuration is invalid or missing."""
    pass


class AudioError(GameError):
    """Raised when audio system encounters an error."""
    pass


class MapGenerationError(GameError):
    """Raised when map generation fails."""
    pass


class InvalidPositionError(GameLogicError):
    """Raised when an invalid position is used in game logic."""
    
    def __init__(self, position, message="Invalid position"):
        self.position = position
        super().__init__(f"{message}: {position}")


class EntityNotFoundError(GameLogicError):
    """Raised when a required game entity cannot be found."""
    
    def __init__(self, entity_type, entity_id=None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        message = f"Entity of type '{entity_type}' not found"
        if entity_id:
            message += f" with ID: {entity_id}"
        super().__init__(message)