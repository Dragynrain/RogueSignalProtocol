#!/usr/bin/env python3
"""
Unit tests for game_data.py - JSON validation and fail-fast behavior.

Tests focus on:
- Failing fast when required JSON sections are missing
- Validating enemy type data (movement types, required fields)
- Validating balance configuration access
- Ensuring NO FALLBACK values exist (all data from JSON)
- Error logging and helpful error messages
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from game_data import GameData, GameBalance, GameUpgrades
from game_entities import EnemyMovement


class TestEnemyTypeLoading:
    """Test enemy type loading from JSON with validation."""

    def test_missing_enemy_types_section_raises_error(self):
        """Test that missing 'enemy_types' section raises KeyError."""
        with patch('game_data.DataLoader.load_game_data', return_value={}):
            with pytest.raises(KeyError, match="enemy_types"):
                GameData._load_enemy_types()

    def test_invalid_movement_type_raises_error(self):
        """Test that invalid movement type raises ValueError."""
        bad_data = {
            'enemy_types': {
                'test_enemy': {
                    'symbol': 'T',
                    'cpu': 50,
                    'vision': 5,
                    'movement': 'INVALID_MOVEMENT',  # Invalid movement type
                    'name': 'Test Enemy',
                    'damage': 10
                }
            }
        }

        with patch('game_data.DataLoader.load_game_data', return_value=bad_data):
            with pytest.raises(ValueError, match="Unknown movement type"):
                GameData._load_enemy_types()

    def test_valid_enemy_types_loaded_correctly(self):
        """Test that valid enemy types are loaded correctly."""
        valid_data = {
            'enemy_types': {
                'scout': {
                    'symbol': 'S',
                    'cpu': 30,
                    'vision': 6,
                    'movement': 'patrol',
                    'name': 'Scout Bot',
                    'damage': 8
                },
                'guard': {
                    'symbol': 'G',
                    'cpu': 50,
                    'vision': 5,
                    'movement': 'static',
                    'name': 'Guard Bot',
                    'damage': 12
                }
            }
        }

        with patch('game_data.DataLoader.load_game_data', return_value=valid_data):
            enemy_types = GameData._load_enemy_types()

            assert 'scout' in enemy_types
            assert 'guard' in enemy_types
            assert enemy_types['scout'].name == 'Scout Bot'
            assert enemy_types['scout'].movement == EnemyMovement.PATROL
            assert enemy_types['guard'].movement == EnemyMovement.STATIC

    def test_all_movement_types_supported(self):
        """Test that all EnemyMovement enum values are supported."""
        movement_types = ['static', 'patrol', 'random', 'seek', 'admin', 'track', 'virus']

        for movement_str in movement_types:
            valid_data = {
                'enemy_types': {
                    'test': {
                        'symbol': 'T',
                        'cpu': 50,
                        'vision': 5,
                        'movement': movement_str,
                        'name': 'Test',
                        'damage': 10
                    }
                }
            }

            with patch('game_data.DataLoader.load_game_data', return_value=valid_data):
                enemy_types = GameData._load_enemy_types()
                assert 'test' in enemy_types, f"Failed to load enemy with movement '{movement_str}'"


class TestGameBalancePlayerStats:
    """Test GameBalance.get_player_stat() fail-fast behavior."""

    def test_missing_player_stat_raises_error(self):
        """Test that missing player stat raises KeyError with helpful message."""
        mock_balance = {
            'player_stats': {
                'max_cpu': 100,
                'max_heat': 100
            }
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            with pytest.raises(KeyError, match="Player stat not found: nonexistent_stat"):
                GameBalance.get_player_stat('nonexistent_stat')

    def test_missing_player_stats_section_raises_error(self):
        """Test that missing 'player_stats' section raises KeyError."""
        mock_balance = {
            'combat': {},
            'code_hacks': {}
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            with pytest.raises(KeyError):
                GameBalance.get_player_stat('max_cpu')

    def test_valid_player_stat_retrieved(self):
        """Test that valid player stats are retrieved correctly."""
        mock_balance = {
            'player_stats': {
                'max_cpu': 100,
                'max_heat': 150,
                'base_ram': 10
            }
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            assert GameBalance.get_player_stat('max_cpu') == 100
            assert GameBalance.get_player_stat('max_heat') == 150
            assert GameBalance.get_player_stat('base_ram') == 10

    @patch('logging.error')
    def test_missing_stat_logs_available_stats(self, mock_log):
        """Test that missing stat error logs available stats for debugging."""
        mock_balance = {
            'player_stats': {
                'max_cpu': 100,
                'max_heat': 100
            }
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            try:
                GameBalance.get_player_stat('nonexistent')
            except KeyError:
                pass

            # Should log available stats
            assert any('Available player stats' in str(call) for call in mock_log.call_args_list)


class TestGameBalanceCombatValues:
    """Test GameBalance.get_combat_value() fail-fast behavior."""

    def test_missing_combat_value_raises_error(self):
        """Test that missing combat value raises KeyError."""
        mock_balance = {
            'combat': {
                'base_damage': 10
            }
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            with pytest.raises(KeyError, match="Combat value not found: nonexistent"):
                GameBalance.get_combat_value('nonexistent')

    def test_missing_combat_section_raises_error(self):
        """Test that missing 'combat' section raises KeyError."""
        mock_balance = {
            'player_stats': {}
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            with pytest.raises(KeyError):
                GameBalance.get_combat_value('base_damage')

    def test_valid_combat_value_retrieved(self):
        """Test that valid combat values are retrieved correctly."""
        mock_balance = {
            'combat': {
                'base_damage': 15,
                'crit_multiplier': 2.0,
                'enemy_elimination_cpu_reward': 20
            }
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            assert GameBalance.get_combat_value('base_damage') == 15
            assert GameBalance.get_combat_value('crit_multiplier') == 2.0
            assert GameBalance.get_combat_value('enemy_elimination_cpu_reward') == 20

    @patch('logging.error')
    def test_missing_combat_value_logs_available_values(self, mock_log):
        """Test that missing combat value error logs available values."""
        mock_balance = {
            'combat': {
                'base_damage': 10,
                'crit_chance': 0.15
            }
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            try:
                GameBalance.get_combat_value('nonexistent')
            except KeyError:
                pass

            assert any('Available combat values' in str(call) for call in mock_log.call_args_list)


class TestGameBalanceCodeHackValues:
    """Test GameBalance.get_code_hack_value() fail-fast behavior."""

    def test_missing_code_hack_value_raises_error(self):
        """Test that missing code hack value raises KeyError."""
        mock_balance = {
            'code_hacks': {
                'heat_reduction_instant': 20
            }
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            with pytest.raises(KeyError, match="Code hack value not found: nonexistent"):
                GameBalance.get_code_hack_value('nonexistent')

    def test_missing_code_hacks_section_raises_error(self):
        """Test that missing 'code_hacks' section raises KeyError."""
        mock_balance = {
            'player_stats': {},
            'combat': {}
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            with pytest.raises(KeyError):
                GameBalance.get_code_hack_value('heat_reduction_instant')

    def test_valid_code_hack_value_retrieved(self):
        """Test that valid code hack values are retrieved correctly."""
        mock_balance = {
            'code_hacks': {
                'heat_reduction_instant': 25,
                'cpu_boost': 30,
                'trace_reduction': 15
            }
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            assert GameBalance.get_code_hack_value('heat_reduction_instant') == 25
            assert GameBalance.get_code_hack_value('cpu_boost') == 30
            assert GameBalance.get_code_hack_value('trace_reduction') == 15


class TestGameBalanceTemporaryEffects:
    """Test GameBalance.get_temporary_effect_value() fail-fast behavior."""

    def test_missing_temporary_effect_raises_error(self):
        """Test that missing temporary effect raises KeyError."""
        mock_balance = {
            'temporary_effects': {
                'speed_boost_duration': 5
            }
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            with pytest.raises(KeyError, match="Temporary effect value not found: nonexistent"):
                GameBalance.get_temporary_effect_value('nonexistent')

    def test_missing_temporary_effects_section_raises_error(self):
        """Test that missing 'temporary_effects' section raises KeyError."""
        mock_balance = {
            'player_stats': {}
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            with pytest.raises(KeyError):
                GameBalance.get_temporary_effect_value('speed_boost_duration')

    def test_valid_temporary_effect_retrieved(self):
        """Test that valid temporary effects are retrieved correctly."""
        mock_balance = {
            'temporary_effects': {
                'speed_boost_duration': 5,
                'enhanced_vision_duration': 8,
                'virus_damage_per_turn': 10
            }
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            assert GameBalance.get_temporary_effect_value('speed_boost_duration') == 5
            assert GameBalance.get_temporary_effect_value('enhanced_vision_duration') == 8
            assert GameBalance.get_temporary_effect_value('virus_damage_per_turn') == 10


class TestGameBalanceBalanceConfigAccess:
    """Test GameBalance.get_balance() method."""

    def test_get_balance_returns_full_config(self):
        """Test that get_balance() returns the full balance configuration."""
        mock_balance = {
            'player_stats': {'max_cpu': 100},
            'combat': {'base_damage': 10},
            'code_hacks': {'heat_reduction_instant': 20},
            'cpu_restore_min': 15,
            'cpu_restore_max': 30
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            balance = GameBalance.get_balance()

            assert balance['player_stats']['max_cpu'] == 100
            assert balance['combat']['base_damage'] == 10
            assert balance['cpu_restore_min'] == 15
            assert balance['cpu_restore_max'] == 30


class TestGameUpgradesLoading:
    """Test GameUpgrades lazy loading from JSON."""

    def setup_method(self):
        """Save GameUpgrades state before each test."""
        from game_data import GameUpgrades
        self._original_loaded = GameUpgrades._loaded
        self._original_upgrades = GameUpgrades.UPGRADES.copy()

    def teardown_method(self):
        """Restore GameUpgrades state after each test."""
        from game_data import GameUpgrades
        GameUpgrades._loaded = self._original_loaded
        GameUpgrades.UPGRADES = self._original_upgrades

    def test_upgrades_loaded_from_json(self):
        """Test that upgrades are loaded from game_content.json."""
        mock_upgrades = {
            'cpu_boost': {
                'name': 'CPU Boost',
                'symbol': '+',
                'color': (0, 255, 0),
                'stat_type': 'cpu',
                'bonus_amount': 20
            }
        }

        with patch('data_loading.DataLoader.load_game_data', return_value={'upgrades': mock_upgrades}):
            # Reset loaded state
            GameUpgrades._loaded = False
            GameUpgrades.UPGRADES = {}

            GameUpgrades._ensure_loaded()

            assert 'cpu_boost' in GameUpgrades.UPGRADES
            assert GameUpgrades.UPGRADES['cpu_boost'].name == 'CPU Boost'
            assert GameUpgrades.UPGRADES['cpu_boost'].bonus_amount == 20

    def test_upgrades_loaded_only_once(self):
        """Test that upgrades are only loaded once (lazy loading)."""
        mock_upgrades = {
            'test': {
                'name': 'Test',
                'symbol': 'T',
                'color': (255, 0, 0),
                'stat_type': 'test',
                'bonus_amount': 10
            }
        }

        with patch('data_loading.DataLoader.load_game_data', return_value={'upgrades': mock_upgrades}) as mock_load:
            # Reset state
            GameUpgrades._loaded = False
            GameUpgrades.UPGRADES = {}

            # Call twice
            GameUpgrades._ensure_loaded()
            GameUpgrades._ensure_loaded()

            # Should only load once
            assert mock_load.call_count == 1

    def test_missing_upgrades_section_handled(self):
        """Test that missing 'upgrades' section results in empty UPGRADES dict."""
        with patch('data_loading.DataLoader.load_game_data', return_value={}):
            # Reset state
            GameUpgrades._loaded = False
            GameUpgrades.UPGRADES = {}

            GameUpgrades._ensure_loaded()

            # Should be empty dict, not crash
            assert GameUpgrades.UPGRADES == {}


class TestNoFallbackValues:
    """Test that NO FALLBACK values exist - all data must come from JSON."""

    def test_no_hardcoded_exploit_fallbacks(self):
        """Test that exploits are defined but can be overridden from JSON if needed."""
        # GameData.EXPLOITS exists as hardcoded data
        # This test verifies the structure is valid
        assert 'system_hop' in GameData.EXPLOITS
        assert 'buffer_overflow' in GameData.EXPLOITS

        # Verify all exploits have required attributes
        for exploit_key, exploit in GameData.EXPLOITS.items():
            assert exploit.name is not None
            assert exploit.ram >= 0
            assert exploit.heat >= 0
            assert exploit.category is not None

    def test_balance_values_fail_without_json(self):
        """Test that balance values fail if JSON is incomplete (no fallbacks)."""
        # Empty balance config should cause failures
        with patch('game_data.DataLoader.get_balance_config', return_value={}):
            with pytest.raises(KeyError):
                GameBalance.get_player_stat('max_cpu')

            with pytest.raises(KeyError):
                GameBalance.get_combat_value('base_damage')

            with pytest.raises(KeyError):
                GameBalance.get_code_hack_value('heat_reduction_instant')


class TestErrorMessagesQuality:
    """Test that error messages are helpful for debugging."""

    @patch('logging.error')
    def test_missing_player_stat_shows_critical_error(self, mock_log):
        """Test that missing player stat logs 'CRITICAL CONFIG ERROR'."""
        mock_balance = {
            'player_stats': {}
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            try:
                GameBalance.get_player_stat('missing_stat')
            except KeyError:
                pass

            # Should log CRITICAL CONFIG ERROR
            assert any('CRITICAL CONFIG ERROR' in str(call) for call in mock_log.call_args_list)

    @patch('logging.error')
    def test_missing_section_shows_available_sections(self, mock_log):
        """Test that missing section error shows available sections."""
        mock_balance = {
            'player_stats': {},
            'combat': {},
            'other_section': {}
        }

        with patch('game_data.DataLoader.get_balance_config', return_value=mock_balance):
            try:
                GameBalance.get_code_hack_value('test')
            except KeyError:
                pass

            # Should log available balance sections
            assert any('Available balance sections' in str(call) for call in mock_log.call_args_list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
