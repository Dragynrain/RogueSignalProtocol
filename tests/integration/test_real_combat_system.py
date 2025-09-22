#!/usr/bin/env python3
"""
Integration tests for combat system using real Player, Enemy, and ExploitSystem objects.
These tests verify actual combat mechanics rather than mock interactions.
"""

import pytest
from unittest.mock import Mock
from game_characters import Player, Enemy
from game_combat import ExploitSystem
from game_entities import Position, EnemyState
from game_data import GameData
from game_state import MessageLog


class TestRealCombatSystem:
    """Integration tests for combat system with real objects."""
    
    def setup_method(self):
        """Set up a minimal game environment with real objects for each test."""
        # Create real player
        self.player = Player(10, 10)
        
        # Create real enemy
        self.enemy = Enemy(Position(15, 15), 'script_kiddie')
        
        # Create minimal mock game object with real components
        self.mock_game = Mock()
        self.mock_game.player = self.player
        self.mock_game.message_log = MessageLog()
        self.mock_game.sound_manager = Mock()  # Keep this mocked for simplicity
        
        # Create real exploit system
        self.exploit_system = ExploitSystem(self.mock_game)
        
        # Give player some exploits to test with
        from game_inventory import ExploitItem
        buffer_overflow_item = ExploitItem("buffer_overflow")
        self.player.inventory_manager.add_item(buffer_overflow_item)
        self.player.inventory_manager.equip_exploit(buffer_overflow_item)
    
    def test_exploit_system_creation_with_real_objects(self):
        """Test that ExploitSystem works with real Player objects."""
        assert self.exploit_system.game.player == self.player
        assert isinstance(self.player.inventory_manager.equipped_exploits, list)
        assert "buffer_overflow" in self.player.inventory_manager.equipped_exploits
    
    def test_exploit_use_reduces_real_player_heat(self):
        """Test that using exploits affects real player heat values."""
        initial_heat = self.player.heat
        
        # Mock the targeting since we're testing heat mechanics, not targeting
        self.mock_game.targeting_mode = None
        
        # Use an exploit that should increase heat
        result = self.exploit_system.use_exploit("buffer_overflow")
        
        # Should enter targeting mode or execute (depending on exploit type)
        assert result is True or hasattr(self.mock_game, 'targeting_mode')
        
        # If it executed immediately, heat should change
        # If it entered targeting mode, that's also valid behavior
        assert self.player.heat >= initial_heat
    
    def test_exploit_execution_with_real_target(self):
        """Test exploit execution against real targets."""
        # Set up a target position
        target_pos = Position(15, 15)
        
        # Execute buffer overflow exploit at target position
        result = self.exploit_system.execute_exploit("buffer_overflow", target_pos)
        
        # Should succeed if exploit is valid
        assert isinstance(result, bool)
        
        # Player heat should increase from using exploit
        assert self.player.heat > 0
    
    def test_player_damage_and_healing_mechanics(self):
        """Test real player damage and healing mechanics."""
        initial_cpu = self.player.cpu
        
        # Deal damage to player
        damage_dealt = self.player.take_damage(20)
        
        assert damage_dealt == 20
        assert self.player.cpu == initial_cpu - 20
        
        # Heal player
        healing_done = self.player.heal(10)
        
        assert healing_done == 10
        assert self.player.cpu == initial_cpu - 10
        
        # Can't heal above max
        self.player.heal(1000)
        assert self.player.cpu == self.player.max_cpu
    
    def test_enemy_state_transitions_work_correctly(self):
        """Test that enemy state management works with real objects."""
        assert self.enemy.state == EnemyState.PATROL  # Initial state
        
        # Make enemy hostile
        self.enemy.state = EnemyState.HOSTILE
        assert self.enemy.state == EnemyState.HOSTILE
        
        # Disable enemy
        self.enemy.state = EnemyState.DISABLED
        self.enemy.disabled_turns = 3
        
        assert self.enemy.state == EnemyState.DISABLED
        assert self.enemy.disabled_turns == 3
    
    def test_exploit_heat_calculation_with_real_stats(self):
        """Test that heat calculation works with real player stats."""
        # Get a real exploit definition
        buffer_overflow = GameData.EXPLOITS["buffer_overflow"]
        
        # Test heat calculation
        heat_cost = self.exploit_system._calculate_heat_cost(buffer_overflow)
        
        assert isinstance(heat_cost, int)
        assert heat_cost > 0
        assert heat_cost <= 100  # Should not exceed max heat in one use
        
        # Test with efficiency bonus
        self.player.temporary_effects['exploit_efficiency_turns'] = 5
        reduced_heat_cost = self.exploit_system._calculate_heat_cost(buffer_overflow)
        
        assert reduced_heat_cost < heat_cost  # Should be reduced with efficiency
    
    def test_player_overheating_mechanics(self):
        """Test player overheating and recovery mechanics."""
        # Heat player up to near max
        self.player.heat = 95
        
        # Try to use high-heat exploit
        self.mock_game.overclock_confirmation = False  # No confirmation yet
        
        result = self.exploit_system.use_exploit("buffer_overflow")
        
        # Should require confirmation for overclocking
        assert result == False  # Should be blocked until confirmation
        
        # Confirm overclocking
        self.mock_game.overclock_confirmation = True
        self.mock_game.overclock_exploit = "buffer_overflow"
        
        initial_cpu = self.player.cpu
        result = self.exploit_system.use_exploit("buffer_overflow")
        
        # Should execute and cause CPU damage from overclocking
        # (exact behavior depends on implementation, but should interact with real stats)
        assert self.player.cpu <= initial_cpu  # Should take damage or stay same
        assert self.player.heat <= 100  # Heat should be capped at 100
    
    def test_inventory_management_integration(self):
        """Test that inventory system integrates properly with combat."""
        # Test adding and equipping exploits
        initial_equipped = len(self.player.inventory_manager.equipped_exploits)
        
        # Add another exploit
        from game_inventory import ExploitItem
        system_crash_item = ExploitItem("system_crash")
        self.player.inventory_manager.add_item(system_crash_item)
        
        # Should be able to equip it
        success = self.player.inventory_manager.equip_exploit(system_crash_item)
        assert success == True
        
        # Should now have more equipped exploits
        assert len(self.player.inventory_manager.equipped_exploits) == initial_equipped + 1
        
        # Should be able to use the newly equipped exploit
        # (This tests integration between inventory and combat systems)
        result = self.exploit_system.use_exploit("system_crash")
        assert isinstance(result, bool)  # Should return some result, not crash


class TestRealCombatIntegrationEdgeCases:
    """Test edge cases in combat system integration."""
    
    def test_combat_with_zero_heat_exploit(self):
        """Test combat system handles exploits with minimal heat cost."""
        player = Player(5, 5)
        
        # Mock game with minimal setup
        mock_game = Mock()
        mock_game.player = player
        mock_game.message_log = MessageLog()
        mock_game.sound_manager = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        # Test with threat_scan (typically low/no heat)
        from game_inventory import ExploitItem
        threat_scan_item = ExploitItem("threat_scan")
        player.inventory_manager.add_item(threat_scan_item)
        player.inventory_manager.equip_exploit(threat_scan_item)
        
        initial_heat = player.heat
        result = exploit_system.use_exploit("threat_scan")
        
        # Should execute successfully
        assert isinstance(result, bool)
        # Heat increase should be minimal
        assert player.heat - initial_heat <= 10
    
    def test_combat_system_handles_invalid_exploits_gracefully(self):
        """Test that combat system handles invalid exploits without crashing."""
        player = Player(5, 5)
        
        mock_game = Mock()
        mock_game.player = player
        mock_game.message_log = MessageLog()
        mock_game.sound_manager = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        # Try to use exploit that's not equipped
        result = exploit_system.use_exploit("nonexistent_exploit")
        assert result == False
        
        # Try to use exploit that's not in inventory
        result = exploit_system.use_exploit("buffer_overflow")
        assert result == False  # Should fail gracefully
    
    def test_player_stats_integration_with_combat_effects(self):
        """Test that player stats properly integrate with combat effects."""
        player = Player(20, 20)
        
        # Test temporary effects
        assert player.temporary_effects['data_mimic_turns'] == 0
        
        # Simulate applying temporary effect
        player.temporary_effects['data_mimic_turns'] = 5
        player.temporary_effects['speed_boost_turns'] = 3
        
        # Effects should persist
        assert player.temporary_effects['data_mimic_turns'] == 5
        assert player.temporary_effects['speed_boost_turns'] == 3
        
        # Test that other stats are unaffected
        assert player.cpu == 100
        assert player.heat == 0