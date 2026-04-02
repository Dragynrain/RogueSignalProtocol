"""Centralized version management.

Loads version from game_rules.json - the single source of truth.
All other files should import VERSION from this module.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Default fallback (should never be used if game_rules.json exists)
_DEFAULT_VERSION = "0.0.0"


def _load_version() -> str:
    """Load version from game_rules.json."""
    # Try multiple paths to handle both development and packaged scenarios
    possible_paths = [
        Path("game_rules.json"),  # Current directory (packaged)
        Path(__file__).parent / "game_rules.json",  # Same directory as this file
    ]

    for path in possible_paths:
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    rules = json.load(f)
                version = rules.get("version", _DEFAULT_VERSION)
                logger.debug("Loaded version %s from %s", version, path)
                return version
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load version from %s: %s", path, e)
                continue

    logger.error("game_rules.json not found - using default version")
    return _DEFAULT_VERSION


# Load version at module import time
VERSION = _load_version()

# Convenience formatted strings
VERSION_DISPLAY = f"Version {VERSION}"
VERSION_SHORT = VERSION.split()[0] if " " in VERSION else VERSION  # Strips suffix if present


def get_version() -> str:
    """Get the current version string."""
    return VERSION


def get_version_display() -> str:
    """Get the version string formatted for display (e.g., 'Version 1.0.0')."""
    return VERSION_DISPLAY


def get_version_short() -> str:
    """Get just the version number without suffix (strips suffix if present)."""
    return VERSION_SHORT
