#!/usr/bin/env python3
"""
Unit tests for game_data.py - Enemy types, exploits, upgrades validation.
Tests the static data that drives game balance and mechanics.
"""

import pytest
from game_data import GameData, GameUpgrades, GameBalance
from game_entities import EnemyTypeDefinition, ExploitDefinition, UpgradeDefinition
from game_entities import EnemyMovement, TargetingMode


class TestEnemyTypes:
    """Test enemy type definitions and validation."""
    
    def test_enemy_types_exist(self):
        """Test that all expected enemy types are defined."""
        expected_enemies = {
            'scanner', 'patrol', 'bot', 'firewall', 'hunter', 
            'virus', 'inhibitor', 'admin'
        }
        
        assert set(GameData.ENEMY_TYPES.keys()) == expected_enemies
    
    def test_enemy_types_have_valid_stats(self):
        """Test that all enemy types have valid stat values."""
        for enemy_type, definition in GameData.ENEMY_TYPES.items():
            # Type check
            assert isinstance(definition, EnemyTypeDefinition), f"{enemy_type} is not EnemyTypeDefinition"
            
            # HP must be positive
            assert definition.cpu > 0, f"{enemy_type} has invalid HP: {definition.cpu}"
            
            # Vision must be non-negative
            assert definition.vision >= 0, f"{enemy_type} has negative vision: {definition.vision}"
            
            # Damage must be non-negative
            assert definition.damage >= 0, f"{enemy_type} has negative damage: {definition.damage}"
            
            # Name must not be empty
            assert definition.name.strip(), f"{enemy_type} has empty name"
            
            # Symbol must be single character
            assert len(definition.symbol) == 1, f"{enemy_type} symbol must be single char: '{definition.symbol}'"
            
            # Movement must be valid enum
            assert isinstance(definition.movement, EnemyMovement), f"{enemy_type} has invalid movement type"
    
    def test_enemy_symbols_are_unique(self):
        """Test that all enemy symbols are unique."""
        symbols = [definition.symbol for definition in GameData.ENEMY_TYPES.values()]
        assert len(symbols) == len(set(symbols)), "Enemy symbols must be unique"
    
    def test_enemy_symbols_are_letters(self):
        """Test that all enemy symbols are uppercase letters A-Z."""
        for enemy_type, definition in GameData.ENEMY_TYPES.items():
            symbol = definition.symbol
            assert symbol.isupper() and symbol.isalpha(), f"{enemy_type} symbol '{symbol}' must be uppercase letter"
    
    @pytest.mark.parametrize("enemy_type,expected_properties", [
        ('scanner', {'damage': 0, 'movement': EnemyMovement.STATIC}),  # Pure detection
        ('firewall', {'cpu': 80, 'damage': 5}),  # High HP, low attack  
        ('admin', {'cpu': 250, 'damage': 45}),  # Boss-level stats
        ('virus', {'damage': 0}),  # No direct damage - uses status effects
    ])
    def test_specific_enemy_properties(self, enemy_type, expected_properties):
        """Test specific properties of important enemy types."""
        definition = GameData.ENEMY_TYPES[enemy_type]
        
        for property_name, expected_value in expected_properties.items():
            actual_value = getattr(definition, property_name)
            assert actual_value == expected_value, f"{enemy_type}.{property_name} should be {expected_value}, got {actual_value}"
    
    def test_enemy_damage_ranges(self):
        """Test that enemy damage values are within reasonable ranges."""
        for enemy_type, definition in GameData.ENEMY_TYPES.items():
            # Damage should be 0-50 range for balance
            assert 0 <= definition.damage <= 50, f"{enemy_type} damage {definition.damage} outside expected range"
    
    def test_enemy_vision_ranges(self):
        """Test that enemy vision values are reasonable."""
        for enemy_type, definition in GameData.ENEMY_TYPES.items():
            # Vision should be 0-10 range
            assert 0 <= definition.vision <= 10, f"{enemy_type} vision {definition.vision} outside expected range"
    
    def test_enemy_hp_ranges(self):
        """Test that enemy HP values are reasonable."""
        for enemy_type, definition in GameData.ENEMY_TYPES.items():
            # HP should be 10-300 range
            assert 10 <= definition.cpu <= 300, f"{enemy_type} HP {definition.cpu} outside expected range"


class TestExploits:
    """Test exploit definitions and validation."""
    
    def test_exploits_exist(self):
        """Test that core exploits are defined."""
        expected_exploits = {
            'shadow_step', 'data_mimic', 'noise_maker', 'buffer_overflow',
            'code_injection', 'system_crash', 'threat_scan', 'log_wiper',
            'antivirus', 'emp_burst', 'memory_leak', 'network_scan'
        }
        
        assert set(GameData.EXPLOITS.keys()) == expected_exploits
    
    def test_exploits_have_valid_properties(self):
        """Test that all exploits have valid property values."""
        for exploit_name, definition in GameData.EXPLOITS.items():
            # Type check
            assert isinstance(definition, ExploitDefinition), f"{exploit_name} is not ExploitDefinition"
            
            # Name must not be empty
            assert definition.name.strip(), f"{exploit_name} has empty name"
            
            # RAM cost must be positive
            assert definition.ram > 0, f"{exploit_name} has invalid RAM cost: {definition.ram}"
            
            # Heat cost must be positive
            assert definition.heat > 0, f"{exploit_name} has invalid heat cost: {definition.heat}"
            
            # Range must be non-negative
            assert definition.range >= 0, f"{exploit_name} has negative range: {definition.range}"
            
            # Damage must be non-negative
            assert definition.damage >= 0, f"{exploit_name} has negative damage: {definition.damage}"
            
            # Category must not be empty
            assert definition.category.strip(), f"{exploit_name} has empty category"
            
            # Targeting must be valid enum
            assert isinstance(definition.targeting, TargetingMode), f"{exploit_name} has invalid targeting mode"
    
    def test_exploit_categories_are_valid(self):
        """Test that exploit categories are from expected set."""
        valid_categories = {"stealth", "combat", "utility", "emergency"}
        
        for exploit_name, definition in GameData.EXPLOITS.items():
            assert definition.category in valid_categories, f"{exploit_name} has invalid category: {definition.category}"
    
    def test_exploit_damage_ranges(self):
        """Test that exploit damage values are reasonable."""
        for exploit_name, definition in GameData.EXPLOITS.items():
            # Damage should be 0-50 range for balance
            assert 0 <= definition.damage <= 50, f"{exploit_name} damage {definition.damage} outside expected range"
    
    def test_exploit_cost_ranges(self):
        """Test that exploit costs are reasonable."""
        for exploit_name, definition in GameData.EXPLOITS.items():
            # RAM cost should be 1-5 range
            assert 1 <= definition.ram <= 5, f"{exploit_name} RAM cost {definition.ram} outside expected range"
            
            # Heat cost should be 10-60 range  
            assert 10 <= definition.heat <= 60, f"{exploit_name} heat cost {definition.heat} outside expected range"
    
    def test_exploit_range_values(self):
        """Test that exploit ranges are reasonable."""
        for exploit_name, definition in GameData.EXPLOITS.items():
            # Range should be 0-10
            assert 0 <= definition.range <= 10, f"{exploit_name} range {definition.range} outside expected range"
    
    @pytest.mark.parametrize("exploit_name,expected_properties", [
        ('shadow_step', {'damage': 0, 'category': 'stealth', 'targeting': TargetingMode.SINGLE}),
        ('buffer_overflow', {'range': 1, 'damage': 40, 'category': 'combat'}),
        ('system_crash', {'targeting': TargetingMode.AREA, 'damage': 30}),
        ('threat_scan', {'damage': 0, 'category': 'utility', 'range': 0}),
        ('network_scan', {'damage': 0, 'range': 0}),
    ])
    def test_specific_exploit_properties(self, exploit_name, expected_properties):
        """Test specific properties of key exploits."""
        definition = GameData.EXPLOITS[exploit_name]
        
        for property_name, expected_value in expected_properties.items():
            actual_value = getattr(definition, property_name)
            assert actual_value == expected_value, f"{exploit_name}.{property_name} should be {expected_value}, got {actual_value}"
    
    def test_utility_exploits_have_no_damage(self):
        """Test that utility exploits don't deal damage."""
        utility_exploits = [name for name, defn in GameData.EXPLOITS.items() if defn.category == 'utility']
        
        for exploit_name in utility_exploits:
            damage = GameData.EXPLOITS[exploit_name].damage
            assert damage == 0, f"Utility exploit {exploit_name} should not deal damage, got {damage}"
    
    def test_stealth_exploits_have_no_damage(self):
        """Test that stealth exploits don't deal damage."""
        stealth_exploits = [name for name, defn in GameData.EXPLOITS.items() if defn.category == 'stealth']
        
        for exploit_name in stealth_exploits:
            damage = GameData.EXPLOITS[exploit_name].damage
            assert damage == 0, f"Stealth exploit {exploit_name} should not deal damage, got {damage}"


class TestUpgrades:
    """Test upgrade definitions and validation."""
    
    def test_upgrades_exist(self):
        """Test that core upgrades are defined."""
        expected_upgrades = {'ram_boost', 'cpu_boost', 'heat_boost'}
        
        assert set(GameUpgrades.UPGRADES.keys()) == expected_upgrades
    
    def test_upgrades_have_valid_properties(self):
        """Test that all upgrades have valid properties."""
        for upgrade_name, definition in GameUpgrades.UPGRADES.items():
            # Type check
            assert isinstance(definition, UpgradeDefinition), f"{upgrade_name} is not UpgradeDefinition"
            
            # Name must not be empty
            assert definition.name.strip(), f"{upgrade_name} has empty name"
            
            # Symbol must be single character
            assert len(definition.symbol) == 1, f"{upgrade_name} symbol must be single char: '{definition.symbol}'"
            
            # Color must be valid RGB tuple
            color = definition.color
            assert isinstance(color, tuple), f"{upgrade_name} color must be tuple"
            assert len(color) == 3, f"{upgrade_name} color must have 3 components"
            for component in color:
                assert isinstance(component, int), f"{upgrade_name} color components must be integers"
                assert 0 <= component <= 255, f"{upgrade_name} color component out of range: {component}"
            
            # Stat type must not be empty
            assert definition.stat_type.strip(), f"{upgrade_name} has empty stat_type"
            
            # Bonus amount must be positive
            assert definition.bonus_amount > 0, f"{upgrade_name} has non-positive bonus: {definition.bonus_amount}"
    
    def test_upgrade_symbols_are_unique(self):
        """Test that all upgrade symbols are unique."""
        symbols = [definition.symbol for definition in GameUpgrades.UPGRADES.values()]
        assert len(symbols) == len(set(symbols)), "Upgrade symbols must be unique"
    
    def test_upgrade_stat_types_are_valid(self):
        """Test that upgrade stat types are from expected set."""
        valid_stat_types = {"ram", "cpu", "heat"}
        
        for upgrade_name, definition in GameUpgrades.UPGRADES.items():
            assert definition.stat_type in valid_stat_types, f"{upgrade_name} has invalid stat_type: {definition.stat_type}"
    
    @pytest.mark.parametrize("upgrade_name,expected_properties", [
        ('ram_boost', {'symbol': '[', 'stat_type': 'ram', 'bonus_amount': 4}),
        ('cpu_boost', {'symbol': ']', 'stat_type': 'cpu', 'bonus_amount': 20}),
        ('heat_boost', {'symbol': '=', 'stat_type': 'heat', 'bonus_amount': 20}),
    ])
    def test_specific_upgrade_properties(self, upgrade_name, expected_properties):
        """Test specific properties of each upgrade."""
        definition = GameUpgrades.UPGRADES[upgrade_name]
        
        for property_name, expected_value in expected_properties.items():
            actual_value = getattr(definition, property_name)
            assert actual_value == expected_value, f"{upgrade_name}.{property_name} should be {expected_value}, got {actual_value}"


class TestGameBalance:
    """Test game balance constants and calculations."""
    
    def test_balance_constants_are_reasonable(self):
        """Test that balance constants are within reasonable ranges."""
        # CPU restoration
        assert 0 < GameBalance.CPU_RESTORE_MIN <= GameBalance.CPU_RESTORE_MAX
        assert GameBalance.CPU_RESTORE_MAX <= 50, "CPU restore max too high"
        
        # Heat reduction
        assert 0 < GameBalance.HEAT_REDUCTION_INSTANT <= 50, "Heat reduction out of range"
        
        # Detection thresholds
        assert 0 < GameBalance.DETECTION_THRESHOLD_ALERT < GameBalance.DETECTION_THRESHOLD_HOSTILE
        assert GameBalance.DETECTION_THRESHOLD_HOSTILE <= 100, "Hostile threshold too high"
        
        # Effect durations
        assert 0 < GameBalance.SPEED_BOOST_DURATION <= 10, "Speed boost duration out of range"
        assert 0 < GameBalance.ENHANCED_VISION_DURATION <= 10, "Vision duration out of range"
        assert 0 < GameBalance.EXPLOIT_EFFICIENCY_DURATION <= 15, "Efficiency duration out of range"
        
        # Virus system
        assert 0 < GameBalance.VIRUS_BASE_DURATION <= GameBalance.VIRUS_MAX_DURATION
        assert GameBalance.VIRUS_MAX_DURATION <= 15, "Virus max duration too long"
        assert 0 < GameBalance.VIRUS_DAMAGE_PER_TURN <= 10, "Virus damage per turn out of range"
    
    def test_exploit_cpu_costs(self):
        """Test exploit CPU cost calculations."""
        # Test known exploits
        known_exploits = [
            "shadow_step", "buffer_overflow", "code_injection", 
            "system_crash", "threat_scan", "log_wiper", 
            "antivirus", "emp_burst", "memory_leak"
        ]
        
        for exploit_name in known_exploits:
            cpu_cost = GameBalance.get_exploit_cpu_cost(exploit_name)
            assert 0 < cpu_cost <= 50, f"{exploit_name} CPU cost {cpu_cost} out of range"
        
        # Test unknown exploit returns default
        unknown_cost = GameBalance.get_exploit_cpu_cost("unknown_exploit")
        assert unknown_cost == 10, "Unknown exploit should return default cost of 10"
    
    def test_difficulty_multipliers(self):
        """Test enemy difficulty multipliers."""
        # Test known difficulties
        difficulties = ["easy", "normal", "hard", "nightmare"]
        
        for difficulty in difficulties:
            multiplier = GameBalance.get_enemy_difficulty_multiplier(difficulty)
            assert 0.5 <= multiplier <= 2.0, f"{difficulty} multiplier {multiplier} out of reasonable range"
        
        # Test that multipliers are ordered correctly
        easy = GameBalance.get_enemy_difficulty_multiplier("easy")
        normal = GameBalance.get_enemy_difficulty_multiplier("normal") 
        hard = GameBalance.get_enemy_difficulty_multiplier("hard")
        nightmare = GameBalance.get_enemy_difficulty_multiplier("nightmare")
        
        assert easy < normal < hard < nightmare, "Difficulty multipliers not properly ordered"
        
        # Test unknown difficulty returns normal
        unknown_mult = GameBalance.get_enemy_difficulty_multiplier("unknown")
        assert unknown_mult == 1.0, "Unknown difficulty should return 1.0"
    
    def test_balance_constant_types(self):
        """Test that balance constants are correct types."""
        # Integer constants
        int_constants = [
            'CPU_RESTORE_MIN', 'CPU_RESTORE_MAX', 'HEAT_REDUCTION_INSTANT',
            'DETECTION_THRESHOLD_ALERT', 'DETECTION_THRESHOLD_HOSTILE',
            'SPEED_BOOST_DURATION', 'ENHANCED_VISION_DURATION', 'EXPLOIT_EFFICIENCY_DURATION',
            'VIRUS_BASE_DURATION', 'VIRUS_MAX_DURATION', 'VIRUS_DAMAGE_PER_TURN'
        ]
        
        for const_name in int_constants:
            if hasattr(GameBalance, const_name):
                value = getattr(GameBalance, const_name)
                assert isinstance(value, int), f"{const_name} should be int, got {type(value)}"
    
    def test_exploit_costs_consistency(self):
        """Test that exploit costs are consistent between data and balance."""
        # Check that exploits with CPU costs in GameBalance exist in GameData
        balance_exploits = [
            "shadow_step", "buffer_overflow", "code_injection", 
            "system_crash", "threat_scan", "log_wiper", 
            "antivirus", "emp_burst", "memory_leak"
        ]
        
        for exploit_name in balance_exploits:
            assert exploit_name in GameData.EXPLOITS, f"Exploit {exploit_name} in balance but not in data"


class TestDataIntegrity:
    """Test overall data integrity and consistency."""
    
    def test_no_empty_collections(self):
        """Test that no data collections are empty."""
        assert len(GameData.ENEMY_TYPES) > 0, "Enemy types collection is empty"
        assert len(GameData.EXPLOITS) > 0, "Exploits collection is empty"
        assert len(GameUpgrades.UPGRADES) > 0, "Upgrades collection is empty"
    
    def test_data_structure_consistency(self):
        """Test that data structures are internally consistent."""
        # All enemy types should have corresponding balance values if needed
        for enemy_type in GameData.ENEMY_TYPES.keys():
            # Enemy types should have reasonable names
            definition = GameData.ENEMY_TYPES[enemy_type]
            assert len(definition.name) > 2, f"Enemy {enemy_type} name too short: '{definition.name}'"
        
        # All exploits should have descriptions
        for exploit_name, definition in GameData.EXPLOITS.items():
            assert len(definition.description) > 5, f"Exploit {exploit_name} description too short"
    
    def test_firewall_attack_value(self):
        """Test that firewall has the new attack value of 5 damage."""
        firewall = GameData.ENEMY_TYPES['firewall']
        assert firewall.damage == 5, f"Firewall should have 5 damage, got {firewall.damage}"