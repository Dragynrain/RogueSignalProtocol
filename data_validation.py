#!/usr/bin/env python3
"""
Data validation for JSON configuration files.
Ensures data integrity and provides helpful error messages for modders.
"""

import json
import logging
from typing import Dict, Any, List, Union

from data_loading import DataLoader


class DataValidator:
    """Validates JSON data files for correctness and completeness."""
    
    @classmethod
    def validate_all_data(cls) -> Dict[str, bool]:
        """Validate all data files and return results."""
        results = {
            'game_data': cls.validate_game_data(),
            'game_config': cls.validate_game_config(),
            'story_content': cls.validate_story_content(),
            'user_settings': cls.validate_user_settings()
        }
        
        all_valid = all(results.values())
        if all_valid:
            logging.info("All data files validated successfully")
        else:
            logging.warning(f"Data validation issues found: {results}")
        
        return results
    
    @classmethod
    def validate_game_data(cls) -> bool:
        """Validate game_data.json structure and values."""
        try:
            data = DataLoader.load_game_data()
            
            # Check required top-level sections
            required_sections = ['enemy_types', 'exploits', 'upgrades', 'network_configs', 'balance']
            for section in required_sections:
                if section not in data:
                    logging.error(f"Missing required section '{section}' in game_data.json")
                    return False
            
            # Validate enemy types
            if not cls._validate_enemy_types(data.get('enemy_types', {})):
                return False
            
            # Validate exploits
            if not cls._validate_exploits(data.get('exploits', {})):
                return False
            
            # Validate upgrades
            if not cls._validate_upgrades(data.get('upgrades', {})):
                return False
            
            # Validate network configs
            if not cls._validate_network_configs(data.get('network_configs', {})):
                return False
            
            # Validate balance configuration
            if not cls._validate_balance_config(data.get('balance', {})):
                return False
            
            logging.info("game_data.json validation passed")
            return True
            
        except Exception as e:
            logging.error(f"Failed to validate game_data.json: {e}")
            return False
    
    @classmethod
    def _validate_enemy_types(cls, enemy_types: Dict[str, Any]) -> bool:
        """Validate enemy type definitions."""
        required_fields = ['symbol', 'cpu', 'vision', 'movement', 'name', 'damage']
        valid_movements = ['STATIC', 'RANDOM', 'SEEK', 'TRACK', 'PATROL', 'LINEAR']
        
        for enemy_id, enemy_data in enemy_types.items():
            # Check required fields
            for field in required_fields:
                if field not in enemy_data:
                    logging.error(f"Enemy '{enemy_id}' missing required field '{field}'")
                    return False
            
            # Validate data types and ranges
            if not isinstance(enemy_data['cpu'], int) or enemy_data['cpu'] <= 0:
                logging.error(f"Enemy '{enemy_id}' has invalid CPU value: {enemy_data['cpu']}")
                return False
            
            if not isinstance(enemy_data['vision'], int) or enemy_data['vision'] < 0:
                logging.error(f"Enemy '{enemy_id}' has invalid vision value: {enemy_data['vision']}")
                return False
            
            if enemy_data['movement'] not in valid_movements:
                logging.error(f"Enemy '{enemy_id}' has invalid movement type: {enemy_data['movement']}")
                return False
            
            if not isinstance(enemy_data['damage'], int) or enemy_data['damage'] < 0:
                logging.error(f"Enemy '{enemy_id}' has invalid damage value: {enemy_data['damage']}")
                return False
            
            # Validate symbol length
            if len(enemy_data['symbol']) != 1:
                logging.error(f"Enemy '{enemy_id}' symbol must be exactly 1 character")
                return False
        
        return True
    
    @classmethod
    def _validate_exploits(cls, exploits: Dict[str, Any]) -> bool:
        """Validate exploit definitions."""
        required_fields = ['name', 'ram', 'heat', 'range', 'category', 'damage', 'targeting', 'description']
        valid_categories = ['stealth', 'combat', 'utility', 'emergency']
        valid_targeting = ['NONE', 'SINGLE', 'AREA']
        
        for exploit_id, exploit_data in exploits.items():
            # Check required fields
            for field in required_fields:
                if field not in exploit_data:
                    logging.error(f"Exploit '{exploit_id}' missing required field '{field}'")
                    return False
            
            # Validate data types and ranges
            if not isinstance(exploit_data['ram'], int) or exploit_data['ram'] < 0:
                logging.error(f"Exploit '{exploit_id}' has invalid RAM cost: {exploit_data['ram']}")
                return False
            
            if not isinstance(exploit_data['heat'], int) or exploit_data['heat'] < 0:
                logging.error(f"Exploit '{exploit_id}' has invalid heat cost: {exploit_data['heat']}")
                return False
            
            if not isinstance(exploit_data['range'], int) or exploit_data['range'] < 0:
                logging.error(f"Exploit '{exploit_id}' has invalid range: {exploit_data['range']}")
                return False
            
            if not isinstance(exploit_data['damage'], int) or exploit_data['damage'] < 0:
                logging.error(f"Exploit '{exploit_id}' has invalid damage: {exploit_data['damage']}")
                return False
            
            if exploit_data['category'] not in valid_categories:
                logging.error(f"Exploit '{exploit_id}' has invalid category: {exploit_data['category']}")
                return False
            
            if exploit_data['targeting'] not in valid_targeting:
                logging.error(f"Exploit '{exploit_id}' has invalid targeting: {exploit_data['targeting']}")
                return False
            
            # Validate description length
            if len(exploit_data['description']) < 10:
                logging.warning(f"Exploit '{exploit_id}' has very short description")
        
        return True
    
    @classmethod
    def _validate_upgrades(cls, upgrades: Dict[str, Any]) -> bool:
        """Validate upgrade definitions."""
        required_fields = ['name', 'symbol', 'color', 'stat_type', 'bonus_amount']
        valid_stat_types = ['ram', 'cpu', 'heat']
        
        for upgrade_id, upgrade_data in upgrades.items():
            # Check required fields
            for field in required_fields:
                if field not in upgrade_data:
                    logging.error(f"Upgrade '{upgrade_id}' missing required field '{field}'")
                    return False
            
            # Validate stat type
            if upgrade_data['stat_type'] not in valid_stat_types:
                logging.error(f"Upgrade '{upgrade_id}' has invalid stat_type: {upgrade_data['stat_type']}")
                return False
            
            # Validate bonus amount
            if not isinstance(upgrade_data['bonus_amount'], int) or upgrade_data['bonus_amount'] <= 0:
                logging.error(f"Upgrade '{upgrade_id}' has invalid bonus_amount: {upgrade_data['bonus_amount']}")
                return False
            
            # Validate color format
            color = upgrade_data['color']
            if not isinstance(color, list) or len(color) != 3:
                logging.error(f"Upgrade '{upgrade_id}' has invalid color format: {color}")
                return False
            
            for component in color:
                if not isinstance(component, int) or component < 0 or component > 255:
                    logging.error(f"Upgrade '{upgrade_id}' has invalid color component: {component}")
                    return False
        
        return True
    
    @classmethod
    def _validate_network_configs(cls, network_configs: Dict[str, Any]) -> bool:
        """Validate network configuration definitions."""
        required_fields = ['enemies', 'shadow_coverage', 'name', 'background_detection']
        
        for level_id, config in network_configs.items():
            # Check required fields
            for field in required_fields:
                if field not in config:
                    logging.error(f"Network config '{level_id}' missing required field '{field}'")
                    return False
            
            # Validate enemy count
            if not isinstance(config['enemies'], int) or config['enemies'] < 0:
                logging.error(f"Network config '{level_id}' has invalid enemy count: {config['enemies']}")
                return False
            
            # Validate shadow coverage
            if not isinstance(config['shadow_coverage'], (int, float)) or config['shadow_coverage'] < 0 or config['shadow_coverage'] > 1:
                logging.error(f"Network config '{level_id}' has invalid shadow_coverage: {config['shadow_coverage']}")
                return False
            
            # Validate background detection
            if not isinstance(config['background_detection'], int) or config['background_detection'] < 0:
                logging.error(f"Network config '{level_id}' has invalid background_detection: {config['background_detection']}")
                return False
        
        return True
    
    @classmethod
    def _validate_balance_config(cls, balance: Dict[str, Any]) -> bool:
        """Validate balance configuration."""
        required_sections = ['player_stats', 'temporary_effects', 'combat', 'code_patches']
        
        for section in required_sections:
            if section not in balance:
                logging.error(f"Balance config missing required section '{section}'")
                return False
        
        # Validate player stats
        player_stats = balance['player_stats']
        required_player_stats = ['starting_cpu', 'max_cpu', 'starting_heat', 'max_heat']
        for stat in required_player_stats:
            if stat not in player_stats:
                logging.error(f"Player stats missing '{stat}'")
                return False
            if not isinstance(player_stats[stat], int) or player_stats[stat] < 0:
                logging.error(f"Player stat '{stat}' has invalid value: {player_stats[stat]}")
                return False
        
        # Validate temporary effects
        temp_effects = balance['temporary_effects']
        if 'exploit_efficiency_multiplier' in temp_effects:
            multiplier = temp_effects['exploit_efficiency_multiplier']
            if not isinstance(multiplier, (int, float)) or multiplier <= 0 or multiplier > 1:
                logging.error(f"Invalid exploit_efficiency_multiplier: {multiplier}")
                return False
        
        return True
    
    @classmethod
    def validate_game_config(cls) -> bool:
        """Validate game_config.json structure and values."""
        try:
            config = DataLoader.load_config()
            
            # Check required sections
            required_sections = ['screen', 'map', 'ui', 'gameplay']
            for section in required_sections:
                if section not in config:
                    logging.error(f"Missing required section '{section}' in game_config.json")
                    return False
            
            # Validate screen dimensions
            screen = config['screen']
            if not isinstance(screen['width'], int) or screen['width'] <= 0:
                logging.error(f"Invalid screen width: {screen['width']}")
                return False
            if not isinstance(screen['height'], int) or screen['height'] <= 0:
                logging.error(f"Invalid screen height: {screen['height']}")
                return False
            
            # Validate map dimensions
            game_map = config['map']
            if not isinstance(game_map['width'], int) or game_map['width'] <= 0:
                logging.error(f"Invalid map width: {game_map['width']}")
                return False
            if not isinstance(game_map['height'], int) or game_map['height'] <= 0:
                logging.error(f"Invalid map height: {game_map['height']}")
                return False
            
            logging.info("game_config.json validation passed")
            return True
            
        except Exception as e:
            logging.error(f"Failed to validate game_config.json: {e}")
            return False
    
    @classmethod
    def validate_story_content(cls) -> bool:
        """Validate story_content.json structure and values."""
        try:
            fragments = DataLoader.load_story_fragments()
            
            if not isinstance(fragments, list):
                logging.error("Story fragments must be a list")
                return False
            
            if len(fragments) == 0:
                logging.warning("No story fragments found")
                return True
            
            # Validate each fragment
            for i, fragment in enumerate(fragments):
                if not isinstance(fragment, str):
                    logging.error(f"Story fragment {i} must be a string")
                    return False
                
                if len(fragment) < 10:
                    logging.warning(f"Story fragment {i} is very short")
            
            logging.info("story_content.json validation passed")
            return True
            
        except Exception as e:
            logging.error(f"Failed to validate story_content.json: {e}")
            return False
    
    @classmethod
    def validate_user_settings(cls) -> bool:
        """Validate user_settings.json structure and values."""
        try:
            settings = DataLoader.load_user_settings()
            
            # Validate volume settings
            volume_fields = ['master_volume', 'sfx_volume', 'music_volume']
            for field in volume_fields:
                if field in settings:
                    value = settings[field]
                    if not isinstance(value, (int, float)) or value < 0 or value > 1:
                        logging.error(f"Invalid {field}: {value} (must be 0.0-1.0)")
                        return False
            
            # Validate graphics mode
            if 'graphics_mode' in settings:
                valid_modes = ['terminal', 'graphics', 'ascii']
                if settings['graphics_mode'] not in valid_modes:
                    logging.error(f"Invalid graphics_mode: {settings['graphics_mode']}")
                    return False
            
            logging.info("user_settings.json validation passed")
            return True
            
        except Exception as e:
            logging.error(f"Failed to validate user_settings.json: {e}")
            return False
    
    @classmethod
    def generate_validation_report(cls) -> str:
        """Generate a comprehensive validation report."""
        results = cls.validate_all_data()
        
        report = "=== Data Validation Report ===\n"
        for file_name, is_valid in results.items():
            status = "VALID" if is_valid else "INVALID"
            report += f"{file_name}: {status}\n"
        
        all_valid = all(results.values())
        report += f"\nOverall Status: {'All files valid' if all_valid else 'Issues found'}\n"
        
        if not all_valid:
            report += "\nPlease check the log output for specific validation errors.\n"
        
        return report


def main():
    """Run data validation and print report."""
    # Configure logging to show validation messages
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    validator = DataValidator()
    report = validator.generate_validation_report()
    print(report)


if __name__ == "__main__":
    main()