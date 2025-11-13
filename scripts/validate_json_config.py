#!/usr/bin/env python3
"""
JSON Configuration Validation Script
Validates that all required JSON configuration keys exist and match code expectations.
NO FALLBACKS - fails immediately if any required configuration is missing.
"""

import json
import sys


def validate_game_config():
    """Validate game_config.json structure."""
    print("Validating game_config.json...")

    with open("game_config.json", encoding="utf-8") as f:
        config = json.load(f)

    # Required top-level sections
    required_sections = [
        "display",
        "ui",
        "gameplay",
        "audio",
        "room_generation",
        "balance",
        "colors",
    ]
    for section in required_sections:
        if section not in config:
            print(f"ERROR: Missing section '{section}' in game_config.json")
            print(f"Available sections: {list(config.keys())}")
            return False

    # Validate display section
    display_keys = [
        "screen_width",
        "screen_height",
        "map_width",
        "map_height",
        "ui_height",
        "sidebar_width",
        "log_width",
        "panel_height",
    ]
    for key in display_keys:
        if key not in config["display"]:
            print(f"ERROR: Missing 'display.{key}' in game_config.json")
            return False

    # Validate gameplay section
    gameplay_keys = [
        "default_player_ram",
        "default_player_cpu",
        "max_heat",
        "max_trace_level",
        "trace_reduction_on_level",
        "dungeon_seed_range",
        "default_vision_range",
        "max_save_attempts",
        "nearby_enemy_alert_radius",
        "virus_damage_per_turn",
    ]
    for key in gameplay_keys:
        if key not in config["gameplay"]:
            print(f"ERROR: Missing 'gameplay.{key}' in game_config.json")
            return False

    # Validate balance section
    balance_keys = [
        "heat_reduction_normal",
        "heat_reduction_boosted",
        "trace_increase_interval",
        "trace_increase_amount",
        "cooling_node_effect",
        "ghost_node_trace_reduction_percent",
        "cpu_recovery_amount",
        "enemy_elimination_cpu_reward",
        "cpu_restore_min",
        "cpu_restore_max",
        "heat_reduction_instant",
        "adjacent_distance_threshold",
        "patrol_stuck_threshold",
        "pathfinding_timeout_attempts",
        "enhanced_vision_bonus",
        "blind_spot_vision_reduction_factor",
        "enemy_trace_alert_to_hostile",
        "enemy_trace_continuous_hostile",
        "enemy_memory_turns",
    ]
    for key in balance_keys:
        if key not in config["balance"]:
            print(f"ERROR: Missing 'balance.{key}' in game_config.json")
            return False

    # Validate room_generation section
    room_gen_keys = [
        "min_rooms_base",
        "room_level_multiplier",
        "max_rooms",
        "max_placement_attempts",
        "min_room_size",
        "max_room_size",
        "room_padding",
    ]
    # NOTE: Special node counts (cooling, cpu, ghost, code_hacks, etc) moved to game_content.json network_configs
    for key in room_gen_keys:
        if key not in config["room_generation"]:
            print(f"ERROR: Missing 'room_generation.{key}' in game_config.json")
            return False

    # Validate colors section
    color_categories = ["basic", "game_elements", "data_codes", "message_log", "enemies", "ui"]
    for category in color_categories:
        if category not in config["colors"]:
            print(f"ERROR: Missing 'colors.{category}' in game_config.json")
            return False

    # Validate specific enemy colors
    enemy_colors = ["unaware", "alert", "hostile"]
    for color in enemy_colors:
        if color not in config["colors"]["enemies"]:
            print(f"ERROR: Missing 'colors.enemies.{color}' in game_config.json")
            return False

    # Validate UI colors
    ui_colors = ["background", "text", "accent", "highlight", "electric_purple"]
    for color in ui_colors:
        if color not in config["colors"]["ui"]:
            print(f"ERROR: Missing 'colors.ui.{color}' in game_config.json")
            return False

    # Check for light_gray in basic colors
    if "light_gray" not in config["colors"]["basic"]:
        print("ERROR: Missing 'colors.basic.light_gray' in game_config.json")
        return False

    print("[OK] game_config.json is valid")
    return True


def validate_game_data():
    """Validate game_data.json structure."""
    print("\nValidating game_data.json...")

    with open("game_data.json", encoding="utf-8") as f:
        data = json.load(f)

    # Required top-level sections
    required_sections = [
        "enemy_types",
        "exploits",
        "upgrades",
        "network_configs",
        "difficulty_multipliers",
        "balance",
    ]
    for section in required_sections:
        if section not in data:
            print(f"ERROR: Missing section '{section}' in game_data.json")
            print(f"Available sections: {list(data.keys())}")
            return False

    # Validate balance section has ai_behavior
    if "balance" not in data:
        print("ERROR: Missing 'balance' section in game_data.json")
        return False

    if "ai_behavior" not in data["balance"]:
        print("ERROR: Missing 'balance.ai_behavior' section in game_data.json")
        print(f"Available balance keys: {list(data['balance'].keys())}")
        return False

    # Validate enemy types
    required_enemies = [
        "scanner",
        "patrol",
        "bot",
        "firewall",
        "hunter",
        "virus",
        "inhibitor",
        "admin",
    ]
    for enemy in required_enemies:
        if enemy not in data["enemy_types"]:
            print(f"ERROR: Missing enemy type '{enemy}' in game_data.json")
            return False

    # Validate exploits
    required_exploits = [
        "system_hop",
        "traffic_masquerade",
        "decoy_swarm",
        "buffer_overflow",
        "code_injection",
        "system_crash",
        "threat_scan",
        "network_scan",
        "log_wiper",
        "antivirus",
        "denial_of_service",
        "memory_leak",
    ]
    for exploit in required_exploits:
        if exploit not in data["exploits"]:
            print(f"ERROR: Missing exploit '{exploit}' in game_data.json")
            return False

    # Validate network configs for levels 1, 2, 3
    for level in [1, 2, 3]:
        level_str = str(level)
        if level_str not in data["network_configs"]:
            print(f"ERROR: Missing network config for level {level} in game_data.json")
            return False

        config = data["network_configs"][level_str]
        required_keys = [
            "enemies",
            "blind_spot_coverage",
            "name",
            "cooling_nodes",
            "cpu_nodes",
            "ghost_nodes",
            "code_hacks",
            "exploit_pickups",
            "permanent_upgrades",
        ]
        for key in required_keys:
            if key not in config:
                print(f"ERROR: Missing '{key}' in network_configs.{level} in game_data.json")
                print(f"Available keys: {list(config.keys())}")
                return False

    # Validate difficulty multipliers
    difficulties = ["easy", "normal", "hard", "nightmare"]
    for difficulty in difficulties:
        if difficulty not in data["difficulty_multipliers"]:
            print(f"ERROR: Missing difficulty '{difficulty}' in difficulty_multipliers")
            return False

    # Validate balance section has required values
    if "cpu_restore_min" not in data["balance"]:
        print("ERROR: Missing 'balance.cpu_restore_min' in game_data.json")
        return False

    if "cpu_restore_max" not in data["balance"]:
        print("ERROR: Missing 'balance.cpu_restore_max' in game_data.json")
        return False

    print("[OK] game_data.json is valid")
    return True


def validate_story_content():
    """Validate narrative_content.json structure."""
    print("\nValidating narrative_content.json...")

    with open("narrative_content.json", encoding="utf-8") as f:
        data = json.load(f)

    if "fragments" not in data:
        print("ERROR: Missing 'fragments' section in narrative_content.json")
        print(f"Available sections: {list(data.keys())}")
        return False

    if not isinstance(data["fragments"], list):
        print("ERROR: 'fragments' must be a list in narrative_content.json")
        return False

    if len(data["fragments"]) == 0:
        print("ERROR: 'fragments' list is empty in narrative_content.json")
        return False

    print(f"[OK] narrative_content.json is valid ({len(data['fragments'])} fragments found)")
    return True


def validate_graphics_tiles():
    """Validate graphics_tiles.json structure and file references."""
    print("\nValidating graphics_tiles.json...")

    import os

    try:
        with open("graphics_tiles.json", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("[SKIP] graphics_tiles.json not found (optional file for graphics mode)")
        return True  # Optional file, not an error

    # Check for required sections
    required_sections = ["player", "enemies", "terrain", "items"]
    for section in required_sections:
        if section not in data:
            print(f"ERROR: Missing section '{section}' in graphics_tiles.json")
            print(f"Available sections: {list(data.keys())}")
            return False

    # Validate player entry
    if "file" not in data["player"]:
        print("ERROR: Missing 'file' key in player section")
        return False

    # Check if graphics directory exists
    graphics_dir = "graphics"
    if not os.path.isdir(graphics_dir):
        print(f"WARNING: Graphics directory '{graphics_dir}' not found")
        print("[SKIP] Skipping file existence checks")
        return True  # Don't fail if graphics folder missing (could be dev environment)

    # Validate sprite files exist
    missing_files = []
    validated_count = 0

    def check_sprite_file(entity_name, entity_data, category):
        """Helper to check if sprite file exists."""
        nonlocal validated_count, missing_files

        if not isinstance(entity_data, dict):
            print(f"WARNING: '{entity_name}' in {category} is not a dict")
            return

        if "file" not in entity_data:
            print(f"WARNING: '{entity_name}' in {category} missing 'file' key")
            return

        sprite_file = entity_data["file"]
        sprite_path = os.path.join(graphics_dir, sprite_file)

        if not os.path.exists(sprite_path):
            missing_files.append((category, entity_name, sprite_file))
        else:
            validated_count += 1

    # Check player sprite
    if isinstance(data["player"], dict) and "file" in data["player"]:
        check_sprite_file("player", data["player"], "player")

    # Check enemies
    if isinstance(data["enemies"], dict):
        for enemy_name, enemy_data in data["enemies"].items():
            if not enemy_name.startswith("_"):  # Skip comment fields
                check_sprite_file(enemy_name, enemy_data, "enemies")

    # Check terrain
    if isinstance(data["terrain"], dict):
        for terrain_name, terrain_data in data["terrain"].items():
            if not terrain_name.startswith("_"):
                check_sprite_file(terrain_name, terrain_data, "terrain")

    # Check items
    if isinstance(data["items"], dict):
        for item_name, item_data in data["items"].items():
            if not item_name.startswith("_"):
                check_sprite_file(item_name, item_data, "items")

    # Report results
    if missing_files:
        print(f"\nWARNING: {len(missing_files)} sprite files not found:")
        for category, entity, filename in missing_files[:10]:  # Show first 10
            print(f"  - {category}.{entity}: {filename}")
        if len(missing_files) > 10:
            print(f"  ... and {len(missing_files) - 10} more")
        print(
            f"\n[OK] graphics_tiles.json structure is valid ({validated_count} sprites referenced)"
        )
        print(f"     {len(missing_files)} sprites missing (will use glyph fallbacks)")
        return True  # Structure valid even if some files missing

    print(f"[OK] graphics_tiles.json is valid ({validated_count} sprites found)")
    return True


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("JSON Configuration Validation")
    print("=" * 60)

    all_valid = True

    try:
        if not validate_game_config():
            all_valid = False
    except FileNotFoundError as e:
        print(f"ERROR: game_config.json not found: {e}")
        all_valid = False
    except json.JSONDecodeError as e:
        print(f"ERROR: game_config.json has invalid JSON syntax: {e}")
        all_valid = False
    except Exception as e:
        print(f"ERROR: Unexpected error validating game_config.json: {e}")
        all_valid = False

    try:
        if not validate_game_data():
            all_valid = False
    except FileNotFoundError as e:
        print(f"ERROR: game_data.json not found: {e}")
        all_valid = False
    except json.JSONDecodeError as e:
        print(f"ERROR: game_data.json has invalid JSON syntax: {e}")
        all_valid = False
    except Exception as e:
        print(f"ERROR: Unexpected error validating game_data.json: {e}")
        all_valid = False

    try:
        if not validate_story_content():
            all_valid = False
    except FileNotFoundError as e:
        print(f"ERROR: narrative_content.json not found: {e}")
        all_valid = False
    except json.JSONDecodeError as e:
        print(f"ERROR: narrative_content.json has invalid JSON syntax: {e}")
        all_valid = False
    except Exception as e:
        print(f"ERROR: Unexpected error validating narrative_content.json: {e}")
        all_valid = False

    try:
        if not validate_graphics_tiles():
            all_valid = False
    except json.JSONDecodeError as e:
        print(f"ERROR: graphics_tiles.json has invalid JSON syntax: {e}")
        all_valid = False
    except Exception as e:
        print(f"ERROR: Unexpected error validating graphics_tiles.json: {e}")
        all_valid = False

    print("\n" + "=" * 60)
    if all_valid:
        print("[OK] ALL JSON CONFIGURATIONS ARE VALID")
        print("=" * 60)
        return 0
    else:
        print("[FAILED] VALIDATION FAILED - FIX ERRORS ABOVE")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
