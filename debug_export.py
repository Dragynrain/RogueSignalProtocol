#!/usr/bin/env python3
"""
Debug Package Export System

Creates comprehensive debug packages for bug reporting:
- Save files (current game, progress, settings)
- Log files (debug, error, graphics)
- Metrics database (play history)
- System information (Python version, OS, etc.)
- Game state snapshot (for reproduction)
- Screenshot (visual state)

Export triggered by:
- Shift+F12 hotkey during gameplay
- "Export Debug Package" button in Settings menu
- Auto-export on unhandled exceptions (crash handler)

Output: debug_exports/debug_YYYY-MM-DD_HHMM.zip
"""

import os
import sys
import json
import zipfile
import logging
import platform
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


class DebugExporter:
    """Handles creation of debug packages for bug reporting."""

    EXPORT_DIR = Path("debug_exports")

    @classmethod
    def create_debug_package(cls,
                            game_engine: Optional['GameEngine'] = None,
                            crash_info: Optional[str] = None) -> Optional[Path]:
        """
        Create a comprehensive debug package.

        Args:
            game_engine: Current game engine instance (for snapshot)
            crash_info: Exception info if this is a crash export

        Returns:
            Path to created zip file, or None if failed
        """
        try:
            # Create export directory
            cls.EXPORT_DIR.mkdir(exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            zip_filename = cls.EXPORT_DIR / f"debug_{timestamp}.zip"

            logging.info(f"Debug Export: Creating debug package: {zip_filename}")

            # Create zip file
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 1. System information
                cls._add_system_info(zipf, crash_info)

                # 2. Save files
                cls._add_directory_to_zip(zipf, "saves", "saves/")

                # 3. Log files
                cls._add_directory_to_zip(zipf, "logs", "logs/")

                # 4. Metrics database
                cls._add_directory_to_zip(zipf, "metrics", "metrics/")

                # 5. Game state snapshot (if game engine available)
                if game_engine:
                    cls._add_game_snapshot(zipf, game_engine)

                # 6. Reproduction steps template
                cls._add_reproduction_template(zipf)

                # 7. Config file hashes (detect modifications)
                cls._add_config_hashes(zipf)

            file_size = zip_filename.stat().st_size
            logging.info(f"Debug Export: Package created successfully, size={file_size} bytes")

            return zip_filename

        except Exception as e:
            logging.error(f"Debug Export: Failed to create debug package: {e}")
            logging.error(traceback.format_exc())
            return None

    @classmethod
    def _add_system_info(cls, zipf: zipfile.ZipFile, crash_info: Optional[str] = None) -> None:
        """Add system_info.txt with environment details."""
        info_lines = [
            "=== SYSTEM INFORMATION ===",
            f"Export Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Python Version: {sys.version}",
            f"Platform: {platform.platform()}",
            f"OS: {platform.system()} {platform.release()}",
            f"Architecture: {platform.machine()}",
            "",
        ]

        # Add TCOD version
        try:
            import tcod
            info_lines.append(f"TCOD Version: {tcod.__version__}")
        except ImportError:
            info_lines.append("TCOD Version: Not installed")

        # Add pygame version
        try:
            import pygame
            info_lines.append(f"Pygame Version: {pygame.version.ver}")
        except ImportError:
            info_lines.append("Pygame Version: Not installed")

        info_lines.append("")

        # Add crash info if provided
        if crash_info:
            info_lines.extend([
                "=== CRASH INFORMATION ===",
                crash_info,
                ""
            ])

        # Add current working directory
        info_lines.extend([
            "=== ENVIRONMENT ===",
            f"Working Directory: {os.getcwd()}",
            f"Executable: {sys.executable}",
            ""
        ])

        zipf.writestr("system_info.txt", "\n".join(info_lines))

    @classmethod
    def _add_directory_to_zip(cls, zipf: zipfile.ZipFile, dir_path: str, arcname_prefix: str) -> None:
        """Add entire directory to zip file."""
        dir_path_obj = Path(dir_path)

        if not dir_path_obj.exists():
            logging.debug(f"Debug Export: Directory not found: {dir_path}")
            return

        for file_path in dir_path_obj.rglob("*"):
            if file_path.is_file():
                arcname = arcname_prefix + str(file_path.relative_to(dir_path))
                try:
                    zipf.write(file_path, arcname)
                    logging.debug(f"Debug Export: Added {arcname}")
                except Exception as e:
                    logging.warning(f"Debug Export: Failed to add {file_path}: {e}")

    @classmethod
    def _add_game_snapshot(cls, zipf: zipfile.ZipFile, game_engine: 'GameEngine') -> None:
        """Add current game state snapshot for reproduction."""
        try:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "level": game_engine.level,
                "turn": game_engine.turn,
                "dungeon_seed": game_engine.game_state.dungeon_seed,
                "player": {
                    "position": {"x": game_engine.player.x, "y": game_engine.player.y},
                    "cpu": game_engine.player.cpu,
                    "max_cpu": game_engine.player.max_cpu,
                    "heat": game_engine.player.heat,
                    "trace_level": game_engine.player.trace_level,
                    "equipped_exploits": game_engine.player.inventory_manager.equipped_exploits,
                },
                "enemies": [
                    {
                        "type": e.type,
                        "position": {"x": e.position.x, "y": e.position.y},
                        "state": e.state.value,
                        "cpu": e.cpu
                    }
                    for e in game_engine.enemies
                ],
                "game_over": game_engine.game_over,
            }

            zipf.writestr("game_snapshot.json", json.dumps(snapshot, indent=2))
            logging.debug("Debug Export: Added game snapshot")

        except Exception as e:
            logging.warning(f"Debug Export: Failed to create game snapshot: {e}")

    @classmethod
    def _add_reproduction_template(cls, zipf: zipfile.ZipFile) -> None:
        """Add template for player to describe the issue."""
        template = """=== BUG REPORT - REPRODUCTION STEPS ===

Please fill in the following information to help us fix the issue:

1. What were you doing when the issue occurred?
   [Describe your actions here]


2. What did you expect to happen?
   [Describe expected behavior]


3. What actually happened?
   [Describe what went wrong]


4. Can you reproduce this issue consistently?
   [ ] Yes, every time
   [ ] Sometimes
   [ ] No, it happened once


5. Additional notes (optional):
   [Any other relevant information]


Thank you for helping improve Rogue Signal Protocol!
"""
        zipf.writestr("PLEASE_FILL_OUT.txt", template)

    @classmethod
    def _add_config_hashes(cls, zipf: zipfile.ZipFile) -> None:
        """Add hashes of config files to detect modifications."""
        import hashlib

        config_files = [
            "game_content.json",
            "game_rules.json",
            "narrative_content.json",
        ]

        hash_info = ["=== CONFIG FILE HASHES ===", ""]

        for config_file in config_files:
            if Path(config_file).exists():
                try:
                    with open(config_file, 'rb') as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    hash_info.append(f"{config_file}: {file_hash}")
                except Exception as e:
                    hash_info.append(f"{config_file}: ERROR - {e}")
            else:
                hash_info.append(f"{config_file}: MISSING")

        zipf.writestr("config_hashes.txt", "\n".join(hash_info))


def export_debug_package(game_engine: Optional['GameEngine'] = None) -> Optional[Path]:
    """
    Convenience function to export debug package.

    Args:
        game_engine: Current game engine instance

    Returns:
        Path to created zip file, or None if failed
    """
    return DebugExporter.create_debug_package(game_engine=game_engine)


def export_crash_report(exception: Exception, game_engine: Optional['GameEngine'] = None) -> Optional[Path]:
    """
    Export debug package with crash information.

    Args:
        exception: The exception that caused the crash
        game_engine: Current game engine instance (if available)

    Returns:
        Path to created zip file, or None if failed
    """
    crash_info = f"Exception: {type(exception).__name__}\n"
    crash_info += f"Message: {str(exception)}\n\n"
    crash_info += "Stack Trace:\n"
    crash_info += "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))

    return DebugExporter.create_debug_package(game_engine=game_engine, crash_info=crash_info)
