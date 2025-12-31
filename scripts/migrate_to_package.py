#!/usr/bin/env python3
"""
Migration script to reorganize flat game_*.py files into src/rsp/ package structure.

Usage:
    python scripts/migrate_to_package.py --dry-run    # Preview changes
    python scripts/migrate_to_package.py              # Execute migration

This script:
1. Creates the src/rsp/ directory structure
2. Moves and renames game_*.py files to appropriate subpackages
3. Updates all imports in source and test files
4. Handles both 'import game_X' and 'from game_X import Y' patterns
"""

import argparse
import re
from pathlib import Path

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).parent.parent

# File mappings: old_name -> (subpackage, new_name)
# Format: "game_foo.py" -> ("subpkg", "foo.py")
# NOTE: RogueSignalProtocol.py stays at project root (not moved to package)
# It's handled separately as the entry point that imports from rsp.*
FILE_MAPPINGS = {
    # Core - engine, config, state, errors
    "game_engine.py": ("core", "engine.py"),
    "game_config.py": ("core", "config.py"),
    "game_state.py": ("core", "state.py"),
    "game_errors.py": ("core", "errors.py"),
    "game_data.py": ("core", "data.py"),
    "game_session.py": ("core", "session.py"),
    "game_file_paths.py": ("core", "file_paths.py"),
    "game_platform.py": ("core", "platform.py"),
    "game_version.py": ("core", "version.py"),
    "game_loop.py": ("core", "loop.py"),
    "data_loading.py": ("core", "data_loading.py"),

    # Entities - position, player, enemies, characters
    "game_position.py": ("entities", "position.py"),
    "game_entities.py": ("entities", "base.py"),
    "game_player.py": ("entities", "player.py"),
    "game_characters.py": ("entities", "characters.py"),
    "game_enemies.py": ("entities", "enemies.py"),
    "game_entity_enums.py": ("entities", "enums.py"),

    # Combat - combat system, turns, inventory
    "game_combat.py": ("combat", "combat.py"),
    "game_turn_manager.py": ("combat", "turn_manager.py"),
    "game_inventory.py": ("combat", "inventory.py"),

    # Level - map, generation, pathfinding
    "game_map.py": ("level", "map.py"),
    "game_level.py": ("level", "generator.py"),
    "game_level_coordinator.py": ("level", "coordinator.py"),
    "game_level_layout.py": ("level", "layout.py"),
    "game_level_placement.py": ("level", "placement.py"),
    "game_level_structure.py": ("level", "structure.py"),
    "game_level_tactical.py": ("level", "tactical.py"),
    "game_pathfinding.py": ("level", "pathfinding.py"),
    "game_visibility_manager.py": ("level", "visibility.py"),

    # Input - all input handling
    "game_input.py": ("input", "handler.py"),
    "game_input_actions.py": ("input", "actions.py"),
    "game_input_analog.py": ("input", "analog.py"),
    "game_input_base.py": ("input", "base.py"),
    "game_input_coordinates.py": ("input", "coordinates.py"),
    "game_input_device_tracker.py": ("input", "device_tracker.py"),
    "game_input_dialogue.py": ("input", "dialogue.py"),
    "game_input_gamepad.py": ("input", "gamepad.py"),
    "game_input_gameplay.py": ("input", "gameplay.py"),
    "game_input_mappings.py": ("input", "mappings.py"),
    "game_input_modals.py": ("input", "modals.py"),

    # Rendering - all rendering code
    "game_rendering_base.py": ("rendering", "base.py"),
    "game_rendering_core.py": ("rendering", "core.py"),
    "game_rendering_glyphs.py": ("rendering", "glyphs.py"),
    "game_rendering_graphics.py": ("rendering", "graphics.py"),
    "game_rendering_ui.py": ("rendering", "ui.py"),
    "game_rendering_utils.py": ("rendering", "utils.py"),
    "game_graphics_tiles.py": ("rendering", "tiles.py"),
    "game_coordinate_helpers.py": ("rendering", "coordinates.py"),
    "game_tile_dimension_calculator.py": ("rendering", "dimensions.py"),
    "font_loader_freetype.py": ("rendering", "font_loader.py"),
    "game_particle_system.py": ("rendering", "particles.py"),

    # UI - menus, dialogs, screens
    "game_menus.py": ("ui", "menus.py"),
    "game_menu_base.py": ("ui", "menu_base.py"),
    "game_menu_main.py": ("ui", "menu_main.py"),
    "game_menu_settings.py": ("ui", "menu_settings.py"),
    "game_menu_controls.py": ("ui", "menu_controls.py"),
    "game_menu_about.py": ("ui", "menu_about.py"),
    "game_menu_achievements.py": ("ui", "menu_achievements.py"),
    "game_menu_ascension.py": ("ui", "menu_ascension.py"),
    "game_menu_background.py": ("ui", "menu_background.py"),
    "game_menu_graphics_preview.py": ("ui", "menu_graphics_preview.py"),
    "game_menu_help_graphics.py": ("ui", "menu_help_graphics.py"),
    "game_menu_help_lore.py": ("ui", "menu_help_lore.py"),
    "game_menu_utilities.py": ("ui", "menu_utilities.py"),
    "game_dialogue_system.py": ("ui", "dialogue.py"),
    "game_info_panel.py": ("ui", "info_panel.py"),
    "game_message_log_renderer.py": ("ui", "message_log.py"),
    "game_status_bar_renderer.py": ("ui", "status_bar.py"),
    "game_screen_utilities.py": ("ui", "screen_utils.py"),
    "game_victory_screen.py": ("ui", "victory.py"),
    "game_ui.py": ("ui", "common.py"),
    "game_help_content.py": ("ui", "help_content.py"),
    "game_help_hints.py": ("ui", "help_hints.py"),

    # Systems - audio, achievements, metrics, save
    "game_audio.py": ("systems", "audio.py"),
    "game_achievements.py": ("systems", "achievements.py"),
    "game_achievement_popups.py": ("systems", "achievement_popups.py"),
    "game_metrics.py": ("systems", "metrics.py"),
    "game_save.py": ("systems", "save.py"),
    "game_state_persistence.py": ("systems", "persistence.py"),
    "game_ascension.py": ("systems", "ascension.py"),
    "game_death_handler.py": ("systems", "death.py"),

    # Utils - misc utilities
    "game_unicode_chars.py": ("utils", "unicode.py"),
    "game_color_manager.py": ("utils", "colors.py"),
    "game_color_thresholds.py": ("utils", "color_thresholds.py"),
    "game_mouse_utils.py": ("utils", "mouse.py"),
    "game_autowalk.py": ("utils", "autowalk.py"),
    "game_narrative.py": ("utils", "narrative.py"),
    "game_story.py": ("utils", "story.py"),
    "game_inspection.py": ("utils", "inspection.py"),
    "debug_export.py": ("utils", "debug_export.py"),
}


def get_module_name(filename: str) -> str:
    """Get module name from filename (without .py)."""
    return filename.replace(".py", "")


def build_import_mapping() -> dict[str, str]:
    """Build mapping from old module names to new import paths."""
    mapping = {}
    for old_file, (subpkg, new_file) in FILE_MAPPINGS.items():
        old_module = get_module_name(old_file)
        new_module = get_module_name(new_file)

        if subpkg:
            new_import = f"rsp.{subpkg}.{new_module}"
        else:
            new_import = f"rsp.{new_module}"

        mapping[old_module] = new_import

    return mapping


def create_directory_structure(dry_run: bool = True) -> list[Path]:
    """Create the src/rsp/ directory structure."""
    src_dir = PROJECT_ROOT / "src"
    rsp_dir = src_dir / "rsp"

    subpackages = set()
    for _, (subpkg, _) in FILE_MAPPINGS.items():
        if subpkg:
            subpackages.add(subpkg)

    dirs_to_create = [src_dir, rsp_dir]
    dirs_to_create.extend(rsp_dir / pkg for pkg in sorted(subpackages))

    created = []
    for d in dirs_to_create:
        if not d.exists():
            if dry_run:
                print(f"  Would create: {d}")
            else:
                d.mkdir(parents=True, exist_ok=True)
                print(f"  Created: {d}")
            created.append(d)

    # Create __init__.py files
    init_locations = [rsp_dir] + [rsp_dir / pkg for pkg in subpackages]
    for loc in init_locations:
        init_file = loc / "__init__.py"
        if not init_file.exists():
            if dry_run:
                print(f"  Would create: {init_file}")
            else:
                init_file.write_text('"""Package initialization."""\n')
                print(f"  Created: {init_file}")

    return created


def move_files(dry_run: bool = True, update_imports: bool = True) -> list[tuple[Path, Path]]:
    """Move files from root to new locations, optionally updating imports during copy."""
    moves = []
    rsp_dir = PROJECT_ROOT / "src" / "rsp"
    import_mapping = build_import_mapping() if update_imports else {}

    for old_file, (subpkg, new_file) in FILE_MAPPINGS.items():
        src = PROJECT_ROOT / old_file
        if not src.exists():
            print(f"  SKIP (not found): {old_file}")
            continue

        if subpkg:
            dst = rsp_dir / subpkg / new_file
        else:
            dst = rsp_dir / new_file

        if dry_run:
            print(f"  Would move: {old_file} -> {dst.relative_to(PROJECT_ROOT)}")
        else:
            # Read content, update imports, write to destination
            content = src.read_text(encoding="utf-8")

            if update_imports:
                for old_module, new_import in import_mapping.items():
                    # Pattern 1: from game_foo import X, Y, Z
                    pattern1 = rf"^from {re.escape(old_module)} import (.+)$"
                    replacement1 = rf"from {new_import} import \1"
                    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)

                    # Pattern 2: import game_foo
                    pattern2 = rf"^import {re.escape(old_module)}$"
                    replacement2 = f"import {new_import}"
                    content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)

                    # Pattern 3: import game_foo as alias
                    pattern3 = rf"^import {re.escape(old_module)} as (\w+)$"
                    replacement3 = rf"import {new_import} as \1"
                    content = re.sub(pattern3, replacement3, content, flags=re.MULTILINE)

            dst.write_text(content, encoding="utf-8")
            print(f"  Copied: {old_file} -> {dst.relative_to(PROJECT_ROOT)}")

        moves.append((src, dst))

    return moves


def update_imports_in_file(filepath: Path, import_mapping: dict[str, str], dry_run: bool = True) -> int:
    """Update imports in a single file. Returns count of changes."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return 0

    changes = 0

    for old_module, new_import in import_mapping.items():
        # Pattern 1: from game_foo import X, Y, Z
        pattern1 = rf"^from {re.escape(old_module)} import (.+)$"
        replacement1 = rf"from {new_import} import \1"
        content, n = re.subn(pattern1, replacement1, content, flags=re.MULTILINE)
        changes += n

        # Pattern 2: import game_foo
        pattern2 = rf"^import {re.escape(old_module)}$"
        replacement2 = f"import {new_import}"
        content, n = re.subn(pattern2, replacement2, content, flags=re.MULTILINE)
        changes += n

        # Pattern 3: import game_foo as alias
        pattern3 = rf"^import {re.escape(old_module)} as (\w+)$"
        replacement3 = rf"import {new_import} as \1"
        content, n = re.subn(pattern3, replacement3, content, flags=re.MULTILINE)
        changes += n

        # Pattern 4: patch("game_foo...") - update mock patch targets
        # Handles both patch("game_foo.X") and @patch("game_foo.X")
        pattern4 = rf'patch\("{re.escape(old_module)}\.([^"]+)"\)'
        replacement4 = rf'patch("{new_import}.\1")'
        content, n = re.subn(pattern4, replacement4, content)
        changes += n

        # Pattern 5: patch("game_foo", ...) - patch the whole module
        pattern5 = rf'patch\("{re.escape(old_module)}"\)'
        replacement5 = rf'patch("{new_import}")'
        content, n = re.subn(pattern5, replacement5, content)
        changes += n

    if changes > 0:
        if dry_run:
            print(f"  Would update {filepath.relative_to(PROJECT_ROOT)}: {changes} import(s)")
        else:
            filepath.write_text(content, encoding="utf-8")
            print(f"  Updated {filepath.relative_to(PROJECT_ROOT)}: {changes} import(s)")

    return changes


def update_conftest_path(dry_run: bool = True) -> None:
    """Update conftest.py to add src to Python path."""
    conftest = PROJECT_ROOT / "tests" / "conftest.py"
    if not conftest.exists():
        print("  SKIP: conftest.py not found")
        return

    content = conftest.read_text(encoding="utf-8")
    original = content

    # The current path setup line
    old_path_line = 'sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))'

    # New path setup that also adds src
    new_path_setup = '''# Add project root and src directory to Python path for rsp package imports
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, 'src'))'''

    if old_path_line in content:
        content = content.replace(
            f"# Add the project root to Python path so we can import game modules\n{old_path_line}",
            new_path_setup
        )

    if content != original:
        if dry_run:
            print("  Would update conftest.py path setup")
        else:
            conftest.write_text(content, encoding="utf-8")
            print("  Updated conftest.py path setup")


def update_all_imports(dry_run: bool = True) -> int:
    """Update imports in all Python files."""
    import_mapping = build_import_mapping()
    total_changes = 0

    # Update conftest.py path setup first
    update_conftest_path(dry_run)

    # Find all Python files in src/rsp/
    rsp_dir = PROJECT_ROOT / "src" / "rsp"
    if rsp_dir.exists():
        for py_file in rsp_dir.rglob("*.py"):
            total_changes += update_imports_in_file(py_file, import_mapping, dry_run)

    # Find all Python files in tests/
    tests_dir = PROJECT_ROOT / "tests"
    if tests_dir.exists():
        for py_file in tests_dir.rglob("*.py"):
            total_changes += update_imports_in_file(py_file, import_mapping, dry_run)

    return total_changes


def show_import_mapping():
    """Display the import mapping for review."""
    mapping = build_import_mapping()
    print("\nImport mapping (old -> new):")
    print("-" * 60)
    for old, new in sorted(mapping.items()):
        print(f"  {old:40} -> {new}")


def update_entry_point(dry_run: bool = True) -> None:
    """Update RogueSignalProtocol.py to import from the rsp package."""
    entry_point = PROJECT_ROOT / "RogueSignalProtocol.py"
    import_mapping = build_import_mapping()

    if not entry_point.exists():
        print(f"  ERROR: {entry_point} not found")
        return

    content = entry_point.read_text(encoding="utf-8")
    original = content

    # Add sys.path manipulation after the initial imports
    path_setup = '''
# Add src directory to path for rsp package imports
import sys as _sys
from pathlib import Path as _Path
_src_dir = _Path(__file__).parent / "src"
_sys.path.insert(0, str(_src_dir))
del _sys, _Path, _src_dir
'''

    # Insert path setup after the first block of standard imports
    # Look for the pattern where tcod is imported
    if "import tcod" in content and "# Add src directory" not in content:
        content = content.replace(
            "import tcod\n",
            f"import tcod\n{path_setup}\n"
        )

    # Update imports using the same logic as other files
    for old_module, new_import in import_mapping.items():
        pattern1 = rf"^from {re.escape(old_module)} import (.+)$"
        replacement1 = rf"from {new_import} import \1"
        content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)

        pattern2 = rf"^import {re.escape(old_module)}$"
        replacement2 = f"import {new_import}"
        content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)

    if content != original:
        if dry_run:
            print(f"  Would update: {entry_point.name}")
        else:
            entry_point.write_text(content, encoding="utf-8")
            print(f"  Updated: {entry_point.name}")
    else:
        print(f"  No changes needed: {entry_point.name}")


def delete_old_files(dry_run: bool = True) -> int:
    """Delete original files from root after successful migration."""
    deleted = 0
    for old_file in FILE_MAPPINGS.keys():
        src = PROJECT_ROOT / old_file
        if src.exists():
            if dry_run:
                print(f"  Would delete: {old_file}")
            else:
                src.unlink()
                print(f"  Deleted: {old_file}")
            deleted += 1
    return deleted


def main():
    parser = argparse.ArgumentParser(description="Migrate to src/rsp/ package structure")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--show-mapping", action="store_true", help="Show import mapping and exit")
    parser.add_argument("--step", choices=["dirs", "move", "imports", "entry", "cleanup"],
                        help="Run only one step")
    parser.add_argument("--no-cleanup", action="store_true", help="Skip deleting old files")
    args = parser.parse_args()

    if args.show_mapping:
        show_import_mapping()
        return

    dry_run = args.dry_run
    mode = "DRY RUN" if dry_run else "EXECUTING"

    print(f"\n{'='*60}")
    print(f"Migration to src/rsp/ package structure ({mode})")
    print(f"{'='*60}\n")

    if args.step is None or args.step == "dirs":
        print("Step 1: Creating directory structure...")
        create_directory_structure(dry_run)
        print()

    if args.step is None or args.step == "move":
        print("Step 2: Moving files (with import updates)...")
        move_files(dry_run, update_imports=True)
        print()

    if args.step is None or args.step == "imports":
        print("Step 3: Updating imports in test files...")
        total = update_all_imports(dry_run)
        print(f"\nTotal import changes: {total}")
        print()

    if args.step is None or args.step == "entry":
        print("Step 4: Updating entry point (RogueSignalProtocol.py)...")
        update_entry_point(dry_run)
        print()

    if (args.step is None or args.step == "cleanup") and not args.no_cleanup:
        print("Step 5: Cleaning up old files...")
        deleted = delete_old_files(dry_run)
        print(f"\nDeleted {deleted} files")
        print()

    if dry_run:
        print("\n" + "="*60)
        print("This was a DRY RUN. No changes were made.")
        print("Run without --dry-run to execute the migration.")
        print("="*60)


if __name__ == "__main__":
    main()
