"""
Comprehensive configuration management system with validation and persistence.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union, Callable, Type
from pathlib import Path
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import threading
from copy import deepcopy

from ..core.exceptions import ConfigurationError
from ..events import EventManager, Event


@dataclass
class ConfigChangeEvent(Event):
    """Event fired when configuration changes."""
    section: str
    key: str
    old_value: Any
    new_value: Any
    source: str = "user"
    
    def get_event_type(self) -> str:
        return "config_changed"


class ConfigValidator(ABC):
    """Abstract base for configuration validators."""
    
    @abstractmethod
    def validate(self, value: Any) -> tuple[bool, str]:
        """
        Validate a configuration value.
        
        Args:
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass


class RangeValidator(ConfigValidator):
    """Validator for numeric ranges."""
    
    def __init__(self, min_value: Union[int, float], max_value: Union[int, float]):
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> tuple[bool, str]:
        try:
            num_value = float(value)
            if self.min_value <= num_value <= self.max_value:
                return True, ""
            return False, f"Value must be between {self.min_value} and {self.max_value}"
        except (ValueError, TypeError):
            return False, "Value must be a number"


class ChoiceValidator(ConfigValidator):
    """Validator for predefined choices."""
    
    def __init__(self, choices: List[Any]):
        self.choices = choices
    
    def validate(self, value: Any) -> tuple[bool, str]:
        if value in self.choices:
            return True, ""
        return False, f"Value must be one of: {', '.join(map(str, self.choices))}"


class TypeValidator(ConfigValidator):
    """Validator for specific types."""
    
    def __init__(self, expected_type: Type):
        self.expected_type = expected_type
    
    def validate(self, value: Any) -> tuple[bool, str]:
        if isinstance(value, self.expected_type):
            return True, ""
        return False, f"Value must be of type {self.expected_type.__name__}"


@dataclass
class ConfigOption:
    """Configuration option with metadata and validation."""
    key: str
    default_value: Any
    description: str = ""
    validator: Optional[ConfigValidator] = None
    requires_restart: bool = False
    hidden: bool = False
    category: str = "general"
    
    def validate(self, value: Any) -> tuple[bool, str]:
        """Validate a value for this option."""
        if self.validator:
            return self.validator.validate(value)
        return True, ""


class ConfigSection:
    """
    Configuration section with options and validation.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._options: Dict[str, ConfigOption] = {}
        self._values: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    def add_option(self, option: ConfigOption) -> 'ConfigSection':
        """
        Add a configuration option to this section.
        
        Args:
            option: Configuration option to add
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            self._options[option.key] = option
            if option.key not in self._values:
                self._values[option.key] = option.default_value
        return self
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        with self._lock:
            if key in self._values:
                return self._values[key]
            if key in self._options:
                return self._options[key].default_value
            return default
    
    def set(self, key: str, value: Any, validate: bool = True) -> bool:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: New value
            validate: Whether to validate the value
            
        Returns:
            True if value was set successfully
        """
        with self._lock:
            if key not in self._options:
                logging.warning(f"Unknown config option: {self.name}.{key}")
                return False
            
            option = self._options[key]
            
            # Validate if requested
            if validate:
                is_valid, error_msg = option.validate(value)
                if not is_valid:
                    logging.error(f"Invalid config value for {self.name}.{key}: {error_msg}")
                    return False
            
            old_value = self._values.get(key, option.default_value)
            self._values[key] = value
            
            # Fire change event if value actually changed
            if old_value != value:
                try:
                    from ..services import try_resolve_service
                    event_manager = try_resolve_service(EventManager)
                    if event_manager:
                        event = ConfigChangeEvent(
                            section=self.name,
                            key=key,
                            old_value=old_value,
                            new_value=value
                        )
                        event_manager.emit(event)
                except Exception as e:
                    logging.warning(f"Could not emit config change event: {e}")
            
            logging.debug(f"Config changed: {self.name}.{key} = {value}")
            return True
    
    def reset(self, key: str = None) -> None:
        """
        Reset configuration to defaults.
        
        Args:
            key: Specific key to reset (None for all)
        """
        with self._lock:
            if key:
                if key in self._options:
                    self._values[key] = self._options[key].default_value
            else:
                for option_key, option in self._options.items():
                    self._values[option_key] = option.default_value
    
    def get_all_values(self) -> Dict[str, Any]:
        """Get all configuration values for this section."""
        with self._lock:
            return self._values.copy()
    
    def get_options(self) -> Dict[str, ConfigOption]:
        """Get all configuration options for this section."""
        with self._lock:
            return self._options.copy()
    
    def has_option(self, key: str) -> bool:
        """Check if option exists in this section."""
        return key in self._options
    
    def get_changed_values(self) -> Dict[str, Any]:
        """Get values that differ from defaults."""
        changed = {}
        with self._lock:
            for key, option in self._options.items():
                current_value = self._values.get(key, option.default_value)
                if current_value != option.default_value:
                    changed[key] = current_value
        return changed


class ConfigManager:
    """
    Central configuration management system.
    
    Provides hierarchical configuration with validation, persistence,
    and change notification.
    """
    
    def __init__(self, config_file: str = "game_config.json",
                 auto_save: bool = True):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
            auto_save: Whether to auto-save changes
        """
        self.config_file = Path(config_file)
        self.auto_save = auto_save
        
        self._sections: Dict[str, ConfigSection] = {}
        self._lock = threading.RLock()
        self._loaded = False
        
        # Register default sections
        self._register_default_sections()
        
        logging.info(f"Configuration manager initialized (file: {config_file})")
    
    def _register_default_sections(self) -> None:
        """Register default configuration sections."""
        # Display section
        display_section = ConfigSection("display", "Display and rendering settings")
        display_section.add_option(ConfigOption(
            "width", 120, "Screen width in characters",
            RangeValidator(80, 200), category="display"
        ))
        display_section.add_option(ConfigOption(
            "height", 40, "Screen height in characters",
            RangeValidator(25, 80), category="display"
        ))
        display_section.add_option(ConfigOption(
            "fullscreen", False, "Enable fullscreen mode",
            TypeValidator(bool), requires_restart=True, category="display"
        ))
        display_section.add_option(ConfigOption(
            "tileset", "dejavu10x10_gs_tc.png", "Tileset file to use",
            TypeValidator(str), requires_restart=True, category="display"
        ))
        
        # Audio section
        audio_section = ConfigSection("audio", "Audio and sound settings")
        audio_section.add_option(ConfigOption(
            "master_volume", 0.7, "Master volume level",
            RangeValidator(0.0, 1.0), category="audio"
        ))
        audio_section.add_option(ConfigOption(
            "sfx_volume", 0.8, "Sound effects volume",
            RangeValidator(0.0, 1.0), category="audio"
        ))
        audio_section.add_option(ConfigOption(
            "music_volume", 0.6, "Music volume",
            RangeValidator(0.0, 1.0), category="audio"
        ))
        audio_section.add_option(ConfigOption(
            "enabled", True, "Enable audio system",
            TypeValidator(bool), category="audio"
        ))
        
        # Gameplay section
        gameplay_section = ConfigSection("gameplay", "Gameplay and difficulty settings")
        gameplay_section.add_option(ConfigOption(
            "difficulty", "normal", "Game difficulty level",
            ChoiceValidator(["easy", "normal", "hard", "expert"]), category="gameplay"
        ))
        gameplay_section.add_option(ConfigOption(
            "auto_save", True, "Enable automatic saving",
            TypeValidator(bool), category="gameplay"
        ))
        gameplay_section.add_option(ConfigOption(
            "permadeath", False, "Enable permadeath mode",
            TypeValidator(bool), category="gameplay"
        ))
        
        # Controls section
        controls_section = ConfigSection("controls", "Input and control settings")
        controls_section.add_option(ConfigOption(
            "move_repeat_delay", 150, "Movement key repeat delay (ms)",
            RangeValidator(50, 500), category="controls"
        ))
        controls_section.add_option(ConfigOption(
            "mouse_enabled", True, "Enable mouse input",
            TypeValidator(bool), category="controls"
        ))
        
        # Debug section
        debug_section = ConfigSection("debug", "Debug and development settings")
        debug_section.add_option(ConfigOption(
            "enabled", False, "Enable debug mode",
            TypeValidator(bool), hidden=True, category="debug"
        ))
        debug_section.add_option(ConfigOption(
            "show_fps", False, "Show FPS counter",
            TypeValidator(bool), category="debug"
        ))
        debug_section.add_option(ConfigOption(
            "log_level", "WARNING", "Logging level",
            ChoiceValidator(["DEBUG", "INFO", "WARNING", "ERROR"]), category="debug"
        ))
        
        # Register all sections
        self.add_section(display_section)
        self.add_section(audio_section)
        self.add_section(gameplay_section)
        self.add_section(controls_section)
        self.add_section(debug_section)
    
    def add_section(self, section: ConfigSection) -> 'ConfigManager':
        """
        Add a configuration section.
        
        Args:
            section: Configuration section to add
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            self._sections[section.name] = section
        logging.debug(f"Added config section: {section.name}")
        return self
    
    def get_section(self, name: str) -> Optional[ConfigSection]:
        """Get configuration section by name."""
        return self._sections.get(name)
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            section: Section name
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        config_section = self.get_section(section)
        if config_section:
            return config_section.get(key, default)
        return default
    
    def set(self, section: str, key: str, value: Any, validate: bool = True) -> bool:
        """
        Set configuration value.
        
        Args:
            section: Section name
            key: Configuration key
            value: New value
            validate: Whether to validate the value
            
        Returns:
            True if value was set successfully
        """
        config_section = self.get_section(section)
        if not config_section:
            logging.error(f"Unknown config section: {section}")
            return False
        
        success = config_section.set(key, value, validate)
        
        if success and self.auto_save:
            self.save()
        
        return success
    
    def load(self, file_path: str = None) -> bool:
        """
        Load configuration from file.
        
        Args:
            file_path: Optional override for config file path
            
        Returns:
            True if loaded successfully
        """
        config_path = Path(file_path) if file_path else self.config_file
        
        try:
            if not config_path.exists():
                logging.info(f"Config file not found: {config_path}, using defaults")
                self._loaded = True
                return True
            
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load values into sections
            loaded_count = 0
            with self._lock:
                for section_name, section_data in data.items():
                    if section_name in self._sections:
                        section = self._sections[section_name]
                        for key, value in section_data.items():
                            if section.has_option(key):
                                section.set(key, value, validate=True)
                                loaded_count += 1
                            else:
                                logging.warning(f"Unknown config option: {section_name}.{key}")
                    else:
                        logging.warning(f"Unknown config section: {section_name}")
            
            self._loaded = True
            logging.info(f"Loaded configuration from {config_path} ({loaded_count} values)")
            return True
            
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            return False
    
    def save(self, file_path: str = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            file_path: Optional override for config file path
            
        Returns:
            True if saved successfully
        """
        config_path = Path(file_path) if file_path else self.config_file
        
        try:
            # Build configuration data
            data = {}
            with self._lock:
                for section_name, section in self._sections.items():
                    section_data = section.get_all_values()
                    if section_data:  # Only save non-empty sections
                        data[section_name] = section_data
            
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file with pretty formatting
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, sort_keys=True)
            
            logging.info(f"Saved configuration to {config_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            return False
    
    def reset_all(self) -> None:
        """Reset all configuration to defaults."""
        with self._lock:
            for section in self._sections.values():
                section.reset()
        
        if self.auto_save:
            self.save()
        
        logging.info("Reset all configuration to defaults")
    
    def reset_section(self, section_name: str) -> bool:
        """
        Reset a specific section to defaults.
        
        Args:
            section_name: Name of section to reset
            
        Returns:
            True if section was reset successfully
        """
        section = self.get_section(section_name)
        if section:
            section.reset()
            if self.auto_save:
                self.save()
            logging.info(f"Reset section '{section_name}' to defaults")
            return True
        return False
    
    def get_all_sections(self) -> Dict[str, ConfigSection]:
        """Get all configuration sections."""
        with self._lock:
            return self._sections.copy()
    
    def get_changed_values(self) -> Dict[str, Dict[str, Any]]:
        """Get all values that differ from defaults."""
        changed = {}
        with self._lock:
            for section_name, section in self._sections.items():
                section_changed = section.get_changed_values()
                if section_changed:
                    changed[section_name] = section_changed
        return changed
    
    def validate_all(self) -> List[str]:
        """
        Validate all current configuration values.
        
        Returns:
            List of validation error messages
        """
        errors = []
        with self._lock:
            for section_name, section in self._sections.items():
                for key, option in section.get_options().items():
                    current_value = section.get(key)
                    is_valid, error_msg = option.validate(current_value)
                    if not is_valid:
                        errors.append(f"{section_name}.{key}: {error_msg}")
        return errors
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get comprehensive configuration information."""
        with self._lock:
            sections_info = {}
            for section_name, section in self._sections.items():
                options_info = {}
                for key, option in section.get_options().items():
                    options_info[key] = {
                        "current_value": section.get(key),
                        "default_value": option.default_value,
                        "description": option.description,
                        "requires_restart": option.requires_restart,
                        "category": option.category,
                        "hidden": option.hidden
                    }
                
                sections_info[section_name] = {
                    "description": section.description,
                    "options": options_info
                }
            
            return {
                "config_file": str(self.config_file),
                "auto_save": self.auto_save,
                "loaded": self._loaded,
                "sections": sections_info
            }
    
    def is_loaded(self) -> bool:
        """Check if configuration has been loaded."""
        return self._loaded