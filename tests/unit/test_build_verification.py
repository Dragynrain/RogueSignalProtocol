"""TDD tests for build verification.

These tests verify that the build system produces valid binaries and includes
all required assets. They are designed to run in CI after a build is complete.
"""

import os
from pathlib import Path

import pytest


# Required assets that must be bundled with every release
REQUIRED_JSON_FILES = [
    "game_content.json",
    "game_rules.json",
    "graphics_tiles.json",
    "narrative_content.json",
]

REQUIRED_FONT_FILES = [
    "KreativeSquare.ttf",
]

REQUIRED_ASSET_FOLDERS = [
    "graphics",
    "sound",
    "music",
]


class TestAssetBundling:
    """Tests to verify all required assets are present in the source tree.

    These tests run before building to ensure assets exist.
    Post-build verification happens in CI workflow steps.
    """

    def test_all_required_json_files_exist(self):
        """Verify all required JSON config files exist in the project root."""
        project_root = Path(__file__).parent.parent.parent

        for json_file in REQUIRED_JSON_FILES:
            file_path = project_root / json_file
            assert file_path.exists(), f"Required JSON file missing: {json_file}"
            assert file_path.stat().st_size > 0, f"JSON file is empty: {json_file}"

    def test_all_required_font_files_exist(self):
        """Verify all required font files exist in the project root."""
        project_root = Path(__file__).parent.parent.parent

        for font_file in REQUIRED_FONT_FILES:
            file_path = project_root / font_file
            assert file_path.exists(), f"Required font file missing: {font_file}"
            assert file_path.stat().st_size > 0, f"Font file is empty: {font_file}"

    def test_all_required_asset_folders_exist(self):
        """Verify all required asset folders exist and contain files."""
        project_root = Path(__file__).parent.parent.parent

        for folder in REQUIRED_ASSET_FOLDERS:
            folder_path = project_root / folder
            assert folder_path.exists(), f"Required asset folder missing: {folder}"
            assert folder_path.is_dir(), f"Asset path is not a directory: {folder}"

            # Verify folder is not empty
            files = list(folder_path.rglob("*"))
            assert len(files) > 0, f"Asset folder is empty: {folder}"

    def test_main_entry_point_exists(self):
        """Verify the main entry point script exists."""
        project_root = Path(__file__).parent.parent.parent
        entry_point = project_root / "RogueSignalProtocol.py"

        assert entry_point.exists(), "Main entry point RogueSignalProtocol.py missing"
        assert entry_point.stat().st_size > 0, "Main entry point is empty"

    def test_requirements_file_exists(self):
        """Verify requirements.txt exists for dependency installation."""
        project_root = Path(__file__).parent.parent.parent
        requirements = project_root / "requirements.txt"

        assert requirements.exists(), "requirements.txt missing"
        assert requirements.stat().st_size > 0, "requirements.txt is empty"


class TestPyInstallerSpecs:
    """Tests to verify PyInstaller spec files are valid."""

    def test_windows_spec_exists(self):
        """Verify Windows PyInstaller spec file exists."""
        project_root = Path(__file__).parent.parent.parent
        spec_file = project_root / "RogueSignalProtocol.spec"

        assert spec_file.exists(), "Windows spec file missing: RogueSignalProtocol.spec"

    def test_linux_spec_exists(self):
        """Verify Linux PyInstaller spec file exists."""
        project_root = Path(__file__).parent.parent.parent
        spec_file = project_root / "RogueSignalProtocol-linux.spec"

        assert spec_file.exists(), "Linux spec file missing: RogueSignalProtocol-linux.spec"

    def test_linux_spec_uses_png_icon(self):
        """Verify Linux spec references PNG icon, not ICO."""
        project_root = Path(__file__).parent.parent.parent
        spec_file = project_root / "RogueSignalProtocol-linux.spec"

        content = spec_file.read_text()
        assert "logo.png" in content, "Linux spec should use logo.png for icon"
        assert "logo.ico" not in content, "Linux spec should not reference logo.ico"

    def test_linux_spec_no_exe_extension(self):
        """Verify Linux spec doesn't add .exe extension."""
        project_root = Path(__file__).parent.parent.parent
        spec_file = project_root / "RogueSignalProtocol-linux.spec"

        content = spec_file.read_text()
        # The name should be 'RogueSignalProtocol' not 'RogueSignalProtocol.exe'
        assert "name='RogueSignalProtocol'" in content, "Linux spec should have correct name"

    def test_logo_png_exists_for_linux_builds(self):
        """Verify logo.png exists in project root for Linux builds."""
        project_root = Path(__file__).parent.parent.parent
        logo = project_root / "logo.png"

        assert logo.exists(), "logo.png missing in project root (required for Linux builds)"


class TestCrossplatformImports:
    """Tests to verify cross-platform code can be imported without errors."""

    def test_game_platform_module_imports(self):
        """Verify game_platform module imports successfully."""
        import game_platform

        # Verify key functions exist
        assert hasattr(game_platform, "is_windows")
        assert hasattr(game_platform, "is_linux")
        assert hasattr(game_platform, "is_macos")
        assert hasattr(game_platform, "set_dpi_awareness")

    def test_game_file_paths_module_imports(self):
        """Verify game_file_paths module imports successfully on all platforms."""
        import game_file_paths

        # Verify key functions exist
        assert hasattr(game_file_paths, "get_data_directory")
        assert hasattr(game_file_paths, "show_fatal_error_and_exit")

    def test_game_loop_module_imports(self):
        """Verify game_loop module imports without Windows-specific crashes."""
        # This would fail on Linux if DPI awareness code wasn't properly guarded
        import game_loop

        assert game_loop is not None

    def test_all_core_modules_import(self):
        """Verify all core game modules can be imported."""
        # These imports would fail if there are platform-specific issues
        import game_engine
        import game_entities
        import game_combat
        import game_enemies
        import game_config

        assert all([game_engine, game_entities, game_combat, game_enemies, game_config])
