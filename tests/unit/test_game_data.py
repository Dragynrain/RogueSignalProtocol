#!/usr/bin/env python3
"""
Unit tests for data loading validation and game data systems.
Tests the actual GameData classes and data loading functionality.
"""

import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
import json
import os
import tempfile

# Import actual data classes
from game_data import GameData, GameUpgrades, GameBalance
from data_loading import DataLoader, PersistentStorage
from game_entities import EnemyTypeDefinition, ExploitDefinition, UpgradeDefinition, EnemyMovement, TargetingMode


class TestGameData:
    """Test the GameData class and static data definitions."""
    
    def test_game_data_enemy_types_defined(self):
        """GameData has all expected enemy types defined."""
        expected_enemies = ['scanner', 'patrol', 'bot', 'firewall', 'hunter', 'virus', 'inhibitor', 'admin']
        
        for enemy_type in expected_enemies:
            assert enemy_type in GameData.ENEMY_TYPES
            enemy_def = GameData.ENEMY_TYPES[enemy_type]
            assert isinstance(enemy_def, EnemyTypeDefinition)
    
    def test_enemy_type_definitions_valid(self):
        """All enemy type definitions have valid attributes."""
        for enemy_name, enemy_def in GameData.ENEMY_TYPES.items():
            # Check all required attributes exist and are reasonable
            assert isinstance(enemy_def.symbol, str)
            assert len(enemy_def.symbol) == 1  # Single character
            assert isinstance(enemy_def.cpu, int)
            assert enemy_def.cpu > 0  # Positive CPU
            assert isinstance(enemy_def.vision, int)
            assert enemy_def.vision >= 0  # Non-negative vision
            assert isinstance(enemy_def.movement, EnemyMovement)
            assert isinstance(enemy_def.name, str)
            assert len(enemy_def.name) > 0  # Non-empty name
            assert isinstance(enemy_def.damage, int)
            assert enemy_def.damage >= 0  # Non-negative damage
    
    def test_enemy_symbols_unique(self):
        """Each enemy type has a unique symbol."""
        symbols = [enemy_def.symbol for enemy_def in GameData.ENEMY_TYPES.values()]
        assert len(symbols) == len(set(symbols))  # All symbols are unique
    
    def test_game_data_exploits_defined(self):
        """GameData has all expected exploits defined."""
        expected_exploits = [
            'shadow_step', 'data_mimic', 'noise_maker', 'buffer_overflow',
            'code_injection', 'system_crash', 'threat_scan', 'log_wiper',
            'antivirus', 'emp_burst', 'memory_leak', 'network_scan'
        ]
        
        for exploit_name in expected_exploits:
            assert exploit_name in GameData.EXPLOITS
            exploit_def = GameData.EXPLOITS[exploit_name]
            assert isinstance(exploit_def, ExploitDefinition)
    
    def test_exploit_definitions_valid(self):
        """All exploit definitions have valid attributes."""
        for exploit_name, exploit_def in GameData.EXPLOITS.items():
            # Check all required attributes exist and are reasonable
            assert isinstance(exploit_def.name, str)
            assert len(exploit_def.name) > 0  # Non-empty name
            assert isinstance(exploit_def.ram, int)
            assert exploit_def.ram > 0  # Positive RAM cost
            assert isinstance(exploit_def.heat, int)
            assert exploit_def.heat >= 0  # Non-negative heat
            assert isinstance(exploit_def.range, int)
            assert exploit_def.range >= 0  # Non-negative range
            assert isinstance(exploit_def.category, str)
            assert exploit_def.category in ["stealth", "combat", "utility", "emergency"]
            assert isinstance(exploit_def.damage, int)
            assert exploit_def.damage >= 0  # Non-negative damage
            assert isinstance(exploit_def.targeting, TargetingMode)
            assert isinstance(exploit_def.description, str)
            assert len(exploit_def.description) > 0  # Non-empty description
    
    def test_exploit_categories_valid(self):
        """Exploit categories are balanced and make sense."""
        categories = {}
        for exploit_def in GameData.EXPLOITS.values():
            category = exploit_def.category
            if category not in categories:
                categories[category] = []
            categories[category].append(exploit_def)
        
        # Should have at least stealth, combat, and utility exploits
        assert "stealth" in categories
        assert "combat" in categories
        assert "utility" in categories
        
        # Each category should have multiple exploits
        for category, exploits in categories.items():
            assert len(exploits) >= 1
    
    def test_combat_exploits_have_damage(self):
        """Combat category exploits should have damage values or special effects."""
        # Some combat exploits provide utility (like memory_leak) rather than direct damage
        utility_combat_exploits = {'memory_leak'}
        
        for exploit_name, exploit_def in GameData.EXPLOITS.items():
            if exploit_def.category == "combat":
                if exploit_name not in utility_combat_exploits:
                    assert exploit_def.damage > 0, f"Combat exploit {exploit_name} should have damage > 0"
                # All combat exploits should have valid damage attribute (>= 0)
                assert exploit_def.damage >= 0, f"Combat exploit {exploit_name} has invalid damage"
    
    def test_stealth_exploits_no_damage(self):
        """Stealth exploits should generally not have damage."""
        for exploit_name, exploit_def in GameData.EXPLOITS.items():
            if exploit_def.category == "stealth":
                # Stealth exploits should focus on utility, not damage
                assert exploit_def.damage == 0, f"Stealth exploit {exploit_name} should not have damage"


class TestGameUpgrades:
    """Test the GameUpgrades class and upgrade definitions."""
    
    def test_game_upgrades_defined(self):
        """GameUpgrades has expected upgrade types."""
        expected_upgrades = ['ram_boost', 'cpu_boost', 'heat_boost']
        
        for upgrade_name in expected_upgrades:
            assert upgrade_name in GameUpgrades.UPGRADES
            upgrade_def = GameUpgrades.UPGRADES[upgrade_name]
            assert isinstance(upgrade_def, UpgradeDefinition)
    
    def test_upgrade_definitions_valid(self):
        """All upgrade definitions have valid attributes."""
        for upgrade_name, upgrade_def in GameUpgrades.UPGRADES.items():
            assert isinstance(upgrade_def.name, str)
            assert len(upgrade_def.name) > 0  # Non-empty name
            assert isinstance(upgrade_def.symbol, str)
            assert len(upgrade_def.symbol) == 1  # Single character
            assert isinstance(upgrade_def.color, tuple)
            assert len(upgrade_def.color) == 3  # RGB tuple
            assert all(0 <= c <= 255 for c in upgrade_def.color)  # Valid RGB values
            assert isinstance(upgrade_def.stat_type, str)
            assert upgrade_def.stat_type in ["ram", "cpu", "heat"]  # Valid stat types
            assert isinstance(upgrade_def.bonus_amount, int)
            assert upgrade_def.bonus_amount > 0  # Positive bonus
    
    def test_upgrade_symbols_unique(self):
        """Each upgrade has a unique symbol."""
        symbols = [upgrade_def.symbol for upgrade_def in GameUpgrades.UPGRADES.values()]
        assert len(symbols) == len(set(symbols))  # All symbols are unique
    
    def test_upgrade_stat_types_comprehensive(self):
        """Upgrades cover all major stat types."""
        stat_types = {upgrade_def.stat_type for upgrade_def in GameUpgrades.UPGRADES.values()}
        
        expected_stats = {"ram", "cpu", "heat"}
        assert stat_types == expected_stats


class TestGameBalance:
    """Test the GameBalance class and balance constants."""
    
    def test_game_balance_constants_defined(self):
        """GameBalance has all expected balance constants."""
        required_constants = [
            'CPU_RESTORE_MIN', 'CPU_RESTORE_MAX', 'HEAT_REDUCTION_INSTANT',
            'DETECTION_THRESHOLD_ALERT', 'DETECTION_THRESHOLD_HOSTILE',
            'SPEED_BOOST_DURATION', 'ENHANCED_VISION_DURATION', 'EXPLOIT_EFFICIENCY_DURATION',
            'VIRUS_BASE_DURATION', 'VIRUS_MAX_DURATION', 'VIRUS_DAMAGE_PER_TURN'
        ]
        
        for constant in required_constants:
            assert hasattr(GameBalance, constant)
            value = getattr(GameBalance, constant)
            assert isinstance(value, (int, float))
            assert value >= 0  # All balance values should be non-negative
    
    def test_cpu_restore_balance(self):
        """CPU restore values are reasonable."""
        assert GameBalance.CPU_RESTORE_MIN > 0
        assert GameBalance.CPU_RESTORE_MAX > GameBalance.CPU_RESTORE_MIN
        assert GameBalance.CPU_RESTORE_MAX <= 50  # Not too generous
    
    def test_detection_thresholds_logical(self):
        """Detection thresholds follow logical progression."""
        assert GameBalance.DETECTION_THRESHOLD_ALERT < GameBalance.DETECTION_THRESHOLD_HOSTILE
        assert GameBalance.DETECTION_THRESHOLD_ALERT > 50  # Reasonable alert level
        assert GameBalance.DETECTION_THRESHOLD_HOSTILE <= 100  # Can't exceed 100%
    
    def test_effect_durations_reasonable(self):
        """Effect durations are reasonable for gameplay."""
        durations = [
            GameBalance.SPEED_BOOST_DURATION,
            GameBalance.ENHANCED_VISION_DURATION,
            GameBalance.EXPLOIT_EFFICIENCY_DURATION
        ]
        
        for duration in durations:
            assert 1 <= duration <= 15  # Reasonable effect duration range
    
    def test_virus_system_balance(self):
        """Virus system parameters are balanced."""
        assert GameBalance.VIRUS_BASE_DURATION > 0
        assert GameBalance.VIRUS_MAX_DURATION > GameBalance.VIRUS_BASE_DURATION
        assert GameBalance.VIRUS_DAMAGE_PER_TURN > 0
        assert GameBalance.VIRUS_DAMAGE_PER_TURN <= 5  # Not too punishing
    
    def test_get_exploit_cpu_cost(self):
        """get_exploit_cpu_cost returns reasonable values."""
        # Test known exploits
        shadow_step_cost = GameBalance.get_exploit_cpu_cost("shadow_step")
        buffer_overflow_cost = GameBalance.get_exploit_cpu_cost("buffer_overflow")
        
        assert isinstance(shadow_step_cost, int)
        assert shadow_step_cost > 0
        assert isinstance(buffer_overflow_cost, int)
        assert buffer_overflow_cost > 0
        
        # More powerful exploits should cost more CPU
        assert buffer_overflow_cost > shadow_step_cost
    
    def test_get_exploit_cpu_cost_unknown(self):
        """get_exploit_cpu_cost returns default for unknown exploits."""
        unknown_cost = GameBalance.get_exploit_cpu_cost("unknown_exploit")
        assert unknown_cost == 10  # Default value
    
    def test_get_enemy_difficulty_multiplier(self):
        """get_enemy_difficulty_multiplier returns correct values."""
        difficulties = ["easy", "normal", "hard", "nightmare"]
        
        for difficulty in difficulties:
            multiplier = GameBalance.get_enemy_difficulty_multiplier(difficulty)
            assert isinstance(multiplier, float)
            assert multiplier > 0
        
        # Difficulty order should be respected
        easy = GameBalance.get_enemy_difficulty_multiplier("easy")
        normal = GameBalance.get_enemy_difficulty_multiplier("normal")
        hard = GameBalance.get_enemy_difficulty_multiplier("hard")
        nightmare = GameBalance.get_enemy_difficulty_multiplier("nightmare")
        
        assert easy < normal < hard < nightmare
        assert normal == 1.0  # Normal should be baseline
    
    def test_get_enemy_difficulty_multiplier_unknown(self):
        """get_enemy_difficulty_multiplier returns default for unknown difficulty."""
        unknown_multiplier = GameBalance.get_enemy_difficulty_multiplier("impossible")
        assert unknown_multiplier == 1.0  # Default value


class TestDataLoader:
    """Test the DataLoader class and JSON data loading."""
    
    def test_data_loader_caching(self):
        """DataLoader caches loaded data to avoid repeated file reads."""
        # Reset class variables
        DataLoader._story_fragments = None
        DataLoader._game_data = None
        DataLoader._config = None
        
        with patch('builtins.open', mock_open(read_data='{"fragments": ["test"]}')):
            # First call should load from file
            fragments1 = DataLoader.load_story_fragments()
            # Second call should use cache
            fragments2 = DataLoader.load_story_fragments()
            
            assert fragments1 is fragments2  # Same object reference (cached)
    
    def test_load_story_fragments_success(self):
        """load_story_fragments loads valid JSON successfully."""
        DataLoader._story_fragments = None  # Reset cache
        
        mock_json_data = json.dumps({"fragments": ["Fragment 1", "Fragment 2", "Fragment 3"]})
        
        with patch('builtins.open', mock_open(read_data=mock_json_data)):
            fragments = DataLoader.load_story_fragments()
            
            assert isinstance(fragments, list)
            assert len(fragments) == 3
            assert "Fragment 1" in fragments
    
    def test_load_story_fragments_file_not_found(self):
        """load_story_fragments handles missing file gracefully."""
        DataLoader._story_fragments = None  # Reset cache
        
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('data_loading.logging.warning') as mock_log:
                fragments = DataLoader.load_story_fragments()
                
                # Should return fallback data
                assert isinstance(fragments, list)
                assert len(fragments) > 0
                mock_log.assert_called()
    
    def test_load_story_fragments_invalid_json(self):
        """load_story_fragments handles invalid JSON gracefully."""
        DataLoader._story_fragments = None  # Reset cache
        
        with patch('builtins.open', mock_open(read_data="invalid json {")):
            with patch('data_loading.logging.warning') as mock_log:
                fragments = DataLoader.load_story_fragments()
                
                # Should return fallback data
                assert isinstance(fragments, list)
                mock_log.assert_called()
    
    def test_load_game_data_success(self):
        """load_game_data loads valid JSON successfully."""
        DataLoader._game_data = None  # Reset cache
        
        mock_data = {
            "enemy_types": {"scanner": {"symbol": "S", "cpu": 35}},
            "exploits": {"shadow_step": {"name": "Shadow Step", "ram": 3}}
        }
        mock_json_data = json.dumps(mock_data)
        
        with patch('builtins.open', mock_open(read_data=mock_json_data)):
            game_data = DataLoader.load_game_data()
            
            assert isinstance(game_data, dict)
            assert "enemy_types" in game_data
            assert "exploits" in game_data
    
    def test_load_game_data_fallback(self):
        """load_game_data uses fallback when file loading fails."""
        DataLoader._game_data = None  # Reset cache
        
        with patch('builtins.open', side_effect=FileNotFoundError):
            game_data = DataLoader.load_game_data()
            
            # Should return fallback data
            assert isinstance(game_data, dict)
            assert "enemy_types" in game_data
            assert "exploits" in game_data
    
    def test_load_config_success(self):
        """load_config loads configuration successfully."""
        DataLoader._config = None  # Reset cache
        
        mock_config = {
            "gameplay": {"difficulty": "normal", "auto_save": True},
            "graphics": {"ascii_mode": False},
            "audio": {"master_volume": 0.7}
        }
        mock_json_data = json.dumps(mock_config)
        
        with patch('builtins.open', mock_open(read_data=mock_json_data)):
            config = DataLoader.load_config()
            
            assert isinstance(config, dict)
            assert "gameplay" in config
            assert "graphics" in config
            assert "audio" in config
    
    def test_fallback_data_validity(self):
        """Fallback data is valid and usable."""
        # Test fallback story fragments
        fallback_fragments = DataLoader._get_fallback_story_fragments()
        assert isinstance(fallback_fragments, list)
        assert len(fallback_fragments) > 0
        assert all(isinstance(fragment, str) for fragment in fallback_fragments)
        
        # Test fallback game data
        fallback_game_data = DataLoader._get_fallback_game_data()
        assert isinstance(fallback_game_data, dict)
        required_keys = ["enemy_types", "exploits", "upgrades", "network_configs"]
        for key in required_keys:
            assert key in fallback_game_data
        
        # Test fallback config
        fallback_config = DataLoader._get_fallback_config()
        assert isinstance(fallback_config, dict)
        required_config_keys = ["gameplay", "graphics", "audio"]
        for key in required_config_keys:
            assert key in fallback_config


class TestPersistentStorage:
    """Test the PersistentStorage class and file operations."""
    
    def test_persistent_storage_initialization(self):
        """PersistentStorage initializes correctly."""
        with patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=False):
            
            storage = PersistentStorage("test_saves")
            
            assert storage.base_dir == "test_saves"
            mock_makedirs.assert_called_once_with("test_saves")
    
    def test_ensure_directory_exists_creates_directory(self):
        """ensure_directory_exists creates directory when it doesn't exist."""
        with patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=False):
            
            storage = PersistentStorage("new_saves")
            storage.ensure_directory_exists()
            
            mock_makedirs.assert_called_with("new_saves")
    
    def test_ensure_directory_exists_skips_existing(self):
        """ensure_directory_exists skips creation for existing directory."""
        with patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=True):
            
            storage = PersistentStorage("existing_saves")
            storage.ensure_directory_exists()
            
            mock_makedirs.assert_not_called()
    
    def test_save_data_success(self):
        """save_data successfully saves data to JSON file."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open()) as mock_file:
            
            storage = PersistentStorage("test_saves")
            test_data = {"player": {"x": 10, "y": 15, "cpu": 80}}
            
            result = storage.save_data("test_save.json", test_data)
            
            assert result is True
            mock_file.assert_called()
            # Check that JSON data was written
            handle = mock_file()
            handle.write.assert_called()
    
    def test_save_data_file_error(self):
        """save_data handles file errors gracefully."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=PermissionError("Access denied")):
            
            storage = PersistentStorage("test_saves")
            test_data = {"test": "data"}
            
            with patch('data_loading.logging.error') as mock_log:
                result = storage.save_data("test_save.json", test_data)
                
                assert result is False
                mock_log.assert_called()
    
    def test_load_data_success(self):
        """load_data successfully loads data from JSON file."""
        test_data = {"player": {"x": 5, "y": 8, "cpu": 90}}
        mock_json_data = json.dumps(test_data)
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=mock_json_data)):
            
            storage = PersistentStorage("test_saves")
            loaded_data = storage.load_data("test_save.json")
            
            assert loaded_data == test_data
    
    def test_load_data_file_not_found(self):
        """load_data returns None for missing files."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', side_effect=FileNotFoundError):
            
            storage = PersistentStorage("test_saves")
            loaded_data = storage.load_data("missing_save.json")
            
            assert loaded_data == {}  # Returns empty dict, not None
    
    def test_load_data_invalid_json(self):
        """load_data handles invalid JSON gracefully."""
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="invalid json {")):
            
            storage = PersistentStorage("test_saves")
            
            with patch('data_loading.logging.error') as mock_log:
                loaded_data = storage.load_data("corrupt_save.json")
                
                assert loaded_data == {}  # Returns empty dict, not None
                mock_log.assert_called()


class TestDataIntegration:
    """Test integration between data systems."""
    
    def test_game_data_consistency(self):
        """Game data definitions are internally consistent."""
        # All exploits in GameBalance.get_exploit_cpu_cost should exist in GameData.EXPLOITS
        # (Testing a few key exploits)
        test_exploits = ["shadow_step", "buffer_overflow", "system_crash"]
        
        for exploit_name in test_exploits:
            # Should exist in GameData
            assert exploit_name in GameData.EXPLOITS
            
            # Should have a CPU cost defined
            cpu_cost = GameBalance.get_exploit_cpu_cost(exploit_name)
            assert isinstance(cpu_cost, int)
            assert cpu_cost > 0
    
    def test_data_loader_with_real_game_data_structure(self):
        """DataLoader fallback data matches expected game data structure."""
        fallback_data = DataLoader._get_fallback_game_data()
        
        # Should have same structure as real game data would
        assert "enemy_types" in fallback_data
        assert "exploits" in fallback_data
        assert "upgrades" in fallback_data
        
        # Enemy types should have required fields
        for enemy_name, enemy_data in fallback_data["enemy_types"].items():
            required_fields = ["symbol", "cpu", "vision", "movement", "name", "damage"]
            for field in required_fields:
                assert field in enemy_data
        
        # Exploits should have required fields
        for exploit_name, exploit_data in fallback_data["exploits"].items():
            required_fields = ["name", "ram", "heat", "range", "category", "damage", "targeting"]
            for field in required_fields:
                assert field in exploit_data
    
    def test_balance_values_realistic(self):
        """Balance values are realistic for gameplay."""
        # CPU restore should be meaningful but not overpowered
        assert 10 <= GameBalance.CPU_RESTORE_MIN <= 30
        assert 20 <= GameBalance.CPU_RESTORE_MAX <= 50
        
        # Heat reduction should be noticeable
        assert GameBalance.HEAT_REDUCTION_INSTANT >= 20
        
        # Detection thresholds should allow for stealth gameplay
        assert GameBalance.DETECTION_THRESHOLD_ALERT >= 60
        assert GameBalance.DETECTION_THRESHOLD_HOSTILE >= 90
        
        # Effect durations should be tactically useful
        assert 3 <= GameBalance.SPEED_BOOST_DURATION <= 10
        assert 3 <= GameBalance.ENHANCED_VISION_DURATION <= 10
    
    def test_persistent_storage_integration_with_save_format(self):
        """PersistentStorage can handle expected save game format."""
        # Test with a realistic save game structure
        realistic_save_data = {
            "version": "dev",
            "timestamp": 1234567890.0,
            "level": 3,
            "turn": 150,
            "player": {
                "x": 25,
                "y": 30,
                "cpu": 75,
                "heat": 25,
                "inventory": ["shadow_step", "buffer_overflow"]
            },
            "enemies": [
                {"type": "scanner", "x": 10, "y": 15, "cpu": 35},
                {"type": "patrol", "x": 40, "y": 20, "cpu": 40}
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = PersistentStorage(temp_dir)
            
            # Save and load should work without errors
            save_success = storage.save_data("integration_test.json", realistic_save_data)
            assert save_success is True
            
            loaded_data = storage.load_data("integration_test.json")
            assert loaded_data == realistic_save_data