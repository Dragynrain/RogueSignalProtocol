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

import json
import logging
import os
import platform
import sys
import traceback
import zipfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from rsp.core.errors import GameErrorHandler
from rsp.core.file_paths import get_data_directory

if TYPE_CHECKING:
    from rsp.core.engine import GameEngine


class DebugExporter:
    """Handles creation of debug packages for bug reporting."""

    @classmethod
    def _get_export_dir(cls) -> Path:
        """Get the debug export directory path (supports portable/AppData modes)."""
        return get_data_directory() / "debug_exports"

    @classmethod
    def create_debug_package(
        cls, game_engine: Optional["GameEngine"] = None, crash_info: str | None = None
    ) -> Path | None:
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
            cls._get_export_dir().mkdir(exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            zip_filename = cls._get_export_dir() / f"debug_{timestamp}.zip"

            logging.info(f"Debug Export: Creating debug package: {zip_filename}")

            # Create zip file
            with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
                # 1. System information
                cls._add_system_info(zipf, crash_info, game_engine)

                # 2. Save files (from disk)
                cls._add_directory_to_zip(zipf, str(get_data_directory() / "saves"), "saves/")

                # 2b. Current game state as save file (if active game exists)
                if game_engine:
                    cls._add_active_save(zipf, game_engine)

                # 3. Log files
                cls._add_directory_to_zip(zipf, str(get_data_directory() / "logs"), "logs/")

                # 4. Metrics database
                cls._add_directory_to_zip(zipf, str(get_data_directory() / "metrics"), "metrics/")

                # 5. Game state snapshot (if game engine available)
                if game_engine:
                    logging.info(
                        f"Debug Export: Adding game snapshot (level={game_engine.level}, turn={game_engine.turn})"
                    )
                    cls._add_game_snapshot(zipf, game_engine)
                else:
                    logging.warning(
                        "Debug Export: No game engine provided - snapshot will not be included"
                    )

                # 6. Reproduction steps template
                cls._add_reproduction_template(zipf)

                # 7. Config file hashes (detect modifications)
                cls._add_config_hashes(zipf)

            file_size = zip_filename.stat().st_size
            logging.info(f"Debug Export: Package created successfully, size={file_size} bytes")

            return zip_filename

        except Exception as e:
            GameErrorHandler.handle_error(
                e, "create_debug_package", "Failed to create debug package", fatal=False
            )
            return None

    @classmethod
    def _add_system_info(
        cls, zipf: zipfile.ZipFile, crash_info: str | None = None, game_engine=None
    ) -> None:
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

        # Note if active game state is included
        if game_engine:
            info_lines.extend(
                [
                    "=== ACTIVE GAME STATE ===",
                    f"Level: {game_engine.level}",
                    f"Turn: {game_engine.turn}",
                    f"Game Over: {game_engine.game_over}",
                    f"Player CPU: {game_engine.player.cpu}/{game_engine.player.max_cpu}",
                    f"Enemies: {len(game_engine.enemies)}",
                    "Active game state saved as: saves/rogue_signal_save_ACTIVE.json",
                    "",
                ]
            )

        # Add TCOD version
        try:
            import tcod

            info_lines.append(f"TCOD Version: {tcod.__version__}")
        except ImportError:
            info_lines.append("TCOD Version: Not installed")

        # Add miniaudio version (audio backend)
        try:
            import miniaudio

            info_lines.append(f"miniaudio Version: {miniaudio.__version__}")
        except ImportError:
            info_lines.append("miniaudio Version: Not installed")

        info_lines.append("")

        # Add crash info if provided
        if crash_info:
            info_lines.extend(["=== CRASH INFORMATION ===", crash_info, ""])

        # Add current working directory
        info_lines.extend(
            [
                "=== ENVIRONMENT ===",
                f"Working Directory: {os.getcwd()}",
                f"Executable: {sys.executable}",
                "",
            ]
        )

        zipf.writestr("system_info.txt", "\n".join(info_lines))

    @classmethod
    def _add_directory_to_zip(
        cls, zipf: zipfile.ZipFile, dir_path: str, arcname_prefix: str
    ) -> None:
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
                    GameErrorHandler.handle_error(
                        e,
                        "add_file_to_debug_zip",
                        f"Failed to add {file_path} to debug package",
                        fatal=False,
                    )

    @classmethod
    def _add_game_snapshot(cls, zipf: zipfile.ZipFile, game_engine: "GameEngine") -> None:
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
                        "cpu": e.cpu,
                    }
                    for e in game_engine.enemies
                ],
                "game_over": game_engine.game_over,
            }

            zipf.writestr("game_snapshot.json", json.dumps(snapshot, indent=2))
            logging.info(
                f"Debug Export: Game snapshot added successfully ({len(game_engine.enemies)} enemies)"
            )

        except Exception as e:
            GameErrorHandler.handle_error(
                e,
                "add_game_snapshot",
                "Failed to create game snapshot for debug package",
                fatal=False,
            )

    @classmethod
    def _add_active_save(cls, zipf: zipfile.ZipFile, game_engine: "GameEngine") -> None:
        """Save the current active game state directly to the debug package."""
        try:
            from rsp.systems.save import SaveGameManager

            # Create a temporary save of the current game state
            save_data = SaveGameManager.create_save_data(game_engine)

            # Add it to the zip as the active save
            zipf.writestr("saves/rogue_signal_save_ACTIVE.json", json.dumps(save_data, indent=2))
            logging.info("Debug Export: Active game state saved to package")

        except Exception as e:
            GameErrorHandler.handle_error(
                e,
                "add_active_save_to_debug",
                "Failed to save active game state to debug package",
                fatal=False,
            )

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
                    with open(config_file, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    hash_info.append(f"{config_file}: {file_hash}")
                except Exception as e:
                    GameErrorHandler.handle_error(
                        e,
                        "hash_config_file",
                        f"Failed to hash {config_file} for debug package",
                        fatal=False,
                    )
                    hash_info.append(f"{config_file}: ERROR - {e}")
            else:
                hash_info.append(f"{config_file}: MISSING")

        zipf.writestr("config_hashes.txt", "\n".join(hash_info))


def export_debug_package(game_engine: Optional["GameEngine"] = None) -> Path | None:
    """
    Convenience function to export debug package.

    Args:
        game_engine: Current game engine instance

    Returns:
        Path to created zip file, or None if failed
    """
    return DebugExporter.create_debug_package(game_engine=game_engine)


def export_crash_report(
    exception: Exception, game_engine: Optional["GameEngine"] = None
) -> Path | None:
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
    crash_info += "".join(
        traceback.format_exception(type(exception), exception, exception.__traceback__)
    )

    return DebugExporter.create_debug_package(game_engine=game_engine, crash_info=crash_info)
