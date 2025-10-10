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

    with open('game_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Required top-level sections
    required_sections = ['display', 'ui', 'gameplay', 'audio', 'room_generation', 'balance', 'colors']
    for section in required_sections:
        if section not in config:
            print(f"ERROR: Missing section '{section}' in game_config.json")
            print(f"Available sections: {list(config.keys())}")
            return False

    # Validate display section
    display_keys = ['screen_width', 'screen_height', 'map_width', 'map_height', 'ui_height', 'sidebar_width', 'log_width', 'panel_height']
    for key in display_keys:
        if key not in config['display']:
            print(f"ERROR: Missing 'display.{key}' in game_config.json")
            return False

    # Validate gameplay section
    gameplay_keys = ['default_player_ram', 'default_player_cpu', 'max_heat', 'max_trace_level',
                     'trace_reduction_on_level', 'dungeon_seed_range', 'default_vision_range',
                     'max_save_attempts', 'nearby_enemy_alert_radius', 'virus_damage_per_turn']
    for key in gameplay_keys:
        if key not in config['gameplay']:
            print(f"ERROR: Missing 'gameplay.{key}' in game_config.json")
            return False

    # Validate balance section
    balance_keys = ['heat_reduction_normal', 'heat_reduction_boosted', 'trace_increase_interval',
                    'trace_increase_amount', 'cooling_node_effect', 'ghost_node_trace_reduction_percent',
                    'cpu_recovery_amount', 'enemy_elimination_cpu_reward', 'cpu_restore_min', 'cpu_restore_max',
                    'heat_reduction_instant', 'adjacent_distance_threshold', 'patrol_stuck_threshold',
                    'pathfinding_timeout_attempts', 'enhanced_vision_bonus', 'shadow_vision_reduction_factor',
                    'enemy_trace_alert_to_hostile', 'enemy_trace_continuous_hostile', 'enemy_memory_turns']
    for key in balance_keys:
        if key not in config['balance']:
            print(f"ERROR: Missing 'balance.{key}' in game_config.json")
            return False

    # Validate room_generation section
    room_gen_keys = ['min_rooms_base', 'room_level_multiplier', 'max_rooms', 'max_placement_attempts',
                     'min_room_size', 'max_room_size', 'room_padding', 'cooling_nodes_per_level',
                     'cpu_nodes_per_level', 'ghost_nodes_per_level', 'code_hacks_per_level',
                     'exploit_pickups_per_level', 'permanent_upgrades_per_level']
    for key in room_gen_keys:
        if key not in config['room_generation']:
            print(f"ERROR: Missing 'room_generation.{key}' in game_config.json")
            return False

    # Validate colors section
    color_categories = ['basic', 'game_elements', 'data_codes', 'message_log', 'enemies', 'ui']
    for category in color_categories:
        if category not in config['colors']:
            print(f"ERROR: Missing 'colors.{category}' in game_config.json")
            return False

    # Validate specific enemy colors
    enemy_colors = ['unaware', 'alert', 'hostile']
    for color in enemy_colors:
        if color not in config['colors']['enemies']:
            print(f"ERROR: Missing 'colors.enemies.{color}' in game_config.json")
            return False

    # Validate UI colors
    ui_colors = ['background', 'text', 'accent', 'highlight', 'electric_purple']
    for color in ui_colors:
        if color not in config['colors']['ui']:
            print(f"ERROR: Missing 'colors.ui.{color}' in game_config.json")
            return False

    # Check for light_gray in basic colors
    if 'light_gray' not in config['colors']['basic']:
        print(f"ERROR: Missing 'colors.basic.light_gray' in game_config.json")
        return False

    print("[OK] game_config.json is valid")
    return True


def validate_game_data():
    """Validate game_data.json structure."""
    print("\nValidating game_data.json...")

    with open('game_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Required top-level sections
    required_sections = ['enemy_types', 'exploits', 'upgrades', 'network_configs',
                         'difficulty_multipliers', 'balance']
    for section in required_sections:
        if section not in data:
            print(f"ERROR: Missing section '{section}' in game_data.json")
            print(f"Available sections: {list(data.keys())}")
            return False

    # Validate balance section has ai_behavior
    if 'balance' not in data:
        print(f"ERROR: Missing 'balance' section in game_data.json")
        return False

    if 'ai_behavior' not in data['balance']:
        print(f"ERROR: Missing 'balance.ai_behavior' section in game_data.json")
        print(f"Available balance keys: {list(data['balance'].keys())}")
        return False

    # Validate enemy types
    required_enemies = ['scanner', 'patrol', 'bot', 'firewall', 'hunter', 'virus', 'inhibitor', 'admin']
    for enemy in required_enemies:
        if enemy not in data['enemy_types']:
            print(f"ERROR: Missing enemy type '{enemy}' in game_data.json")
            return False

    # Validate exploits
    required_exploits = ['shadow_step', 'data_mimic', 'noise_maker', 'buffer_overflow',
                         'code_injection', 'system_crash', 'threat_scan', 'network_scan',
                         'log_wiper', 'antivirus', 'denial_of_service', 'memory_leak']
    for exploit in required_exploits:
        if exploit not in data['exploits']:
            print(f"ERROR: Missing exploit '{exploit}' in game_data.json")
            return False

    # Validate network configs for levels 1, 2, 3
    for level in [1, 2, 3]:
        level_str = str(level)
        if level_str not in data['network_configs']:
            print(f"ERROR: Missing network config for level {level} in game_data.json")
            return False

        config = data['network_configs'][level_str]
        required_keys = ['enemies', 'shadow_coverage', 'name', 'cooling_nodes', 'cpu_nodes',
                         'ghost_nodes', 'code_hacks', 'exploit_pickups', 'permanent_upgrades']
        for key in required_keys:
            if key not in config:
                print(f"ERROR: Missing '{key}' in network_configs.{level} in game_data.json")
                print(f"Available keys: {list(config.keys())}")
                return False

    # Validate difficulty multipliers
    difficulties = ['easy', 'normal', 'hard', 'nightmare']
    for difficulty in difficulties:
        if difficulty not in data['difficulty_multipliers']:
            print(f"ERROR: Missing difficulty '{difficulty}' in difficulty_multipliers")
            return False

    # Validate balance section has required values
    if 'cpu_restore_min' not in data['balance']:
        print(f"ERROR: Missing 'balance.cpu_restore_min' in game_data.json")
        return False

    if 'cpu_restore_max' not in data['balance']:
        print(f"ERROR: Missing 'balance.cpu_restore_max' in game_data.json")
        return False

    print("[OK] game_data.json is valid")
    return True


def validate_story_content():
    """Validate story_content.json structure."""
    print("\nValidating story_content.json...")

    with open('story_content.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'fragments' not in data:
        print(f"ERROR: Missing 'fragments' section in story_content.json")
        print(f"Available sections: {list(data.keys())}")
        return False

    if not isinstance(data['fragments'], list):
        print(f"ERROR: 'fragments' must be a list in story_content.json")
        return False

    if len(data['fragments']) == 0:
        print(f"ERROR: 'fragments' list is empty in story_content.json")
        return False

    print(f"[OK] story_content.json is valid ({len(data['fragments'])} fragments found)")
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
        print(f"ERROR: story_content.json not found: {e}")
        all_valid = False
    except json.JSONDecodeError as e:
        print(f"ERROR: story_content.json has invalid JSON syntax: {e}")
        all_valid = False
    except Exception as e:
        print(f"ERROR: Unexpected error validating story_content.json: {e}")
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
