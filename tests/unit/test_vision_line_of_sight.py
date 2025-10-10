#!/usr/bin/env python3
"""
Vision and Line-of-Sight Tests - Test Category 3
Tests for player vision, enemy detection, shadow concealment, and wall blocking.

PHILOSOPHY: Test gameplay behavior, not TCOD internals
- Test what players experience (can I see the enemy? can they see me?)
- Test game rules (shadows hide, walls block, admin sees through invisibility)
- DO NOT test TCOD's algorithm implementation (trust the library)
- DO NOT test Bresenham implementation details (legacy code)
"""

import pytest
from unittest.mock import Mock, patch
from game_characters import Player, Enemy
from game_map import GameMap
from game_entities import Position
from tests.fixtures.simple_fixtures import player


class TestVisionLineOfSight:
    """Test suite for vision and line-of-sight functionality."""

    def setup_method(self):
        """Setup common test objects."""
        self.game_map = GameMap(20, 20)
        self.player = player(x=10, y=10)

        # Clear the map (no walls initially)
        self.game_map.walls.clear()
        self.game_map.shadows.clear()
        self.game_map.invalidate_transparency_cache()


class TestPlayerVisionRange(TestVisionLineOfSight):
    """Test player vision range and enhancements."""

    def test_base_vision_range(self):
        """Player has correct base vision range."""
        test_player = player()
        assert test_player.base_vision_range == 15
        assert test_player.get_vision_range() == 15

    def test_enhanced_vision_increases_range(self):
        """Enhanced vision temporary effect increases range."""
        test_player = player()
        test_player.temporary_effects['enhanced_vision_turns'] = 5
        assert test_player.get_vision_range() == 17  # Base 15 + 2 bonus

    def test_enhanced_vision_allows_wall_sight(self):
        """Enhanced vision allows seeing through walls."""
        test_player = player()
        assert not test_player.can_see_through_walls()

        test_player.temporary_effects['enhanced_vision_turns'] = 5
        assert test_player.can_see_through_walls()

    def test_player_sees_enemy_within_range(self):
        """Player can see enemy within vision range."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(15, 10), "test_enemy")  # 5 units away
            assert self.player.can_see_enemy(enemy, self.game_map) == True

    def test_player_cannot_see_enemy_beyond_range(self):
        """Player cannot see enemy beyond vision range."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(30, 10), "test_enemy")  # 20 units away
            assert self.player.can_see_enemy(enemy, self.game_map) == False


class TestShadowConcealment(TestVisionLineOfSight):
    """Test shadow concealment mechanics for stealth gameplay."""

    def test_enemy_in_shadow_not_visible_from_distance(self):
        """Enemy in shadow is not visible from distance."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(13, 10), "test_enemy")  # 3 units away
            self.game_map.shadows.add((13, 10))

            assert self.player.can_see_enemy(enemy, self.game_map) == False

    def test_enemy_in_shadow_visible_when_adjacent(self):
        """Enemy in shadow is visible when adjacent (close quarters rule)."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(11, 10), "test_enemy")  # 1 unit away
            self.game_map.shadows.add((11, 10))

            assert self.player.can_see_enemy(enemy, self.game_map) == True

    def test_player_in_shadow_has_normal_vision_out(self):
        """Player in shadow has normal outgoing vision (shadows block vision IN, not OUT)."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            self.game_map.shadows.add((10, 10))

            # Close enemy - visible
            enemy_close = Enemy(Position(13, 10), "test_enemy")  # 3 units
            assert self.player.can_see_enemy(enemy_close, self.game_map) == True

            # Distant enemy - also visible now (shadows don't block vision going OUT)
            enemy_far = Enemy(Position(17, 10), "test_enemy")  # 7 units
            assert self.player.can_see_enemy(enemy_far, self.game_map) == True

    def test_ghost_nodes_act_as_shadows(self):
        """Ghost nodes function as shadows for concealment."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(13, 10), "test_enemy")
            self.game_map.ghost_nodes.add((13, 10))

            assert self.player.can_see_enemy(enemy, self.game_map) == False

    def test_invisible_player_cannot_be_seen(self):
        """Invisible player (data mimic) cannot be seen by enemies."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(12, 10), "test_enemy")
            self.player.temporary_effects['data_mimic_turns'] = 3

            assert enemy.can_see_player(self.player, self.game_map) == False

    def test_admin_sees_through_invisibility(self):
        """Admin enemies can see invisible players."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'admin': Mock(movement=Mock(), cpu=100, vision=10, damage=20)
        }):
            admin_enemy = Enemy(Position(12, 10), "admin")
            self.player.temporary_effects['data_mimic_turns'] = 3

            assert admin_enemy.can_see_player(self.player, self.game_map) == True


class TestWallBlocking(TestVisionLineOfSight):
    """Test wall sight-line blocking mechanics."""

    def test_wall_blocks_line_of_sight(self):
        """Wall between player and enemy blocks vision."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(12, 10), "test_enemy")
            self.game_map.walls.add((11, 10))
            self.game_map.invalidate_transparency_cache()

            assert self.player.can_see_enemy(enemy, self.game_map) == False

    def test_clear_line_allows_vision(self):
        """Clear line of sight allows vision."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(12, 10), "test_enemy")
            assert self.player.can_see_enemy(enemy, self.game_map) == True

    def test_enhanced_vision_sees_through_walls(self):
        """Enhanced vision allows seeing through walls."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(12, 10), "test_enemy")
            self.game_map.walls.add((11, 10))
            self.game_map.invalidate_transparency_cache()

            self.player.temporary_effects['enhanced_vision_turns'] = 5
            assert self.player.can_see_enemy(enemy, self.game_map) == True

    def test_diagonal_wall_blocking(self):
        """Walls block diagonal sight lines correctly."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(13, 13), "test_enemy")
            self.game_map.walls.add((11, 11))
            self.game_map.walls.add((12, 12))
            self.game_map.invalidate_transparency_cache()

            assert self.player.can_see_enemy(enemy, self.game_map) == False


class TestEnemyVision(TestVisionLineOfSight):
    """Test enemy vision ranges and detection mechanics."""

    def test_enemy_vision_range_limits(self):
        """Enemy cannot see player beyond their vision range."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=5, damage=10)
        }):
            # Within range
            enemy = Enemy(Position(14, 10), "test_enemy")  # 4 units away
            assert enemy.can_see_player(self.player, self.game_map) == True

            # Beyond range
            enemy.position = Position(4, 10)  # 6 units away
            assert enemy.can_see_player(self.player, self.game_map) == False

    def test_disabled_enemy_cannot_see(self):
        """Disabled enemy cannot see player."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(12, 10), "test_enemy")
            enemy.disabled_turns = 3

            assert enemy.can_see_player(self.player, self.game_map) == False

    def test_enemy_cannot_see_player_in_shadow(self):
        """Enemy cannot see player in shadow from distance."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(13, 10), "test_enemy")
            self.game_map.shadows.add((10, 10))

            assert enemy.can_see_player(self.player, self.game_map) == False

    def test_enemy_sees_adjacent_player_in_shadow(self):
        """Enemy can see adjacent player even in shadow."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(11, 10), "test_enemy")
            self.game_map.shadows.add((10, 10))

            assert enemy.can_see_player(self.player, self.game_map) == True

    def test_admin_has_perfect_tracking(self):
        """Admin enemy has perfect tracking regardless of conditions."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'admin': Mock(movement=Mock(), cpu=100, vision=10, damage=20)
        }):
            admin_enemy = Enemy(Position(19, 19), "admin")

            # Add obstacles
            self.game_map.walls.add((15, 15))
            self.game_map.shadows.add((10, 10))
            self.player.temporary_effects['data_mimic_turns'] = 3
            self.game_map.invalidate_transparency_cache()

            # Admin should still see player
            assert admin_enemy.can_see_player(self.player, self.game_map) == True


class TestStealthGameplayScenarios(TestVisionLineOfSight):
    """Test complete stealth gameplay scenarios."""

    def test_hiding_in_shadows(self):
        """Player hiding in shadows is not detected from distance."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'guard': Mock(movement=Mock(), cpu=50, vision=8, damage=10)
        }):
            enemy = Enemy(Position(15, 10), "guard")  # 5 units away
            self.game_map.shadows.add((10, 10))

            # Enemy should not see player in shadow
            assert not enemy.can_see_player(self.player, self.game_map)

            # Player moves out of shadow
            self.player.position = Position(11, 10)

            # Enemy should now see player
            assert enemy.can_see_player(self.player, self.game_map)

    def test_using_walls_for_cover(self):
        """Using walls for cover blocks mutual vision."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'guard': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            self.player.position = Position(8, 10)
            enemy = Enemy(Position(12, 10), "guard")

            self.game_map.walls.add((10, 10))
            self.game_map.invalidate_transparency_cache()

            # Mutual vision blocked
            assert not enemy.can_see_player(self.player, self.game_map)
            assert not self.player.can_see_enemy(enemy, self.game_map)

    def test_data_mimic_invisibility(self):
        """Data mimic makes player invisible to normal enemies."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'scanner': Mock(movement=Mock(), cpu=50, vision=10, damage=10),
            'admin': Mock(movement=Mock(), cpu=100, vision=10, damage=20)
        }):
            scanner = Enemy(Position(12, 10), "scanner")
            admin = Enemy(Position(13, 10), "admin")

            # Both see player initially
            assert scanner.can_see_player(self.player, self.game_map)
            assert admin.can_see_player(self.player, self.game_map)

            # Activate invisibility
            self.player.temporary_effects['data_mimic_turns'] = 3

            # Scanner cannot see, admin can
            assert not scanner.can_see_player(self.player, self.game_map)
            assert admin.can_see_player(self.player, self.game_map)

    def test_enhanced_vision_exploit(self):
        """Enhanced vision allows seeing through walls."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'hidden_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(13, 10), "hidden_enemy")

            self.game_map.walls.add((11, 10))
            self.game_map.walls.add((12, 10))
            self.game_map.invalidate_transparency_cache()

            # Cannot see through wall initially
            assert not self.player.can_see_enemy(enemy, self.game_map)

            # Activate enhanced vision
            self.player.temporary_effects['enhanced_vision_turns'] = 5

            # Now can see through walls
            assert self.player.can_see_enemy(enemy, self.game_map)


class TestMapVisionUtilities(TestVisionLineOfSight):
    """Test GameMap vision utility methods."""

    def test_can_see_position_within_range(self):
        """can_see_position works within vision range."""
        start = Position(10, 10)
        end = Position(13, 10)
        vision_range = 5

        assert self.game_map.can_see_position(start, end, vision_range) == True

    def test_can_see_position_beyond_range(self):
        """can_see_position fails beyond vision range."""
        start = Position(10, 10)
        end = Position(16, 10)  # 6 units away
        vision_range = 5

        assert self.game_map.can_see_position(start, end, vision_range) == False

    def test_can_see_position_blocked_by_wall(self):
        """can_see_position blocked by wall even within range."""
        start = Position(10, 10)
        end = Position(13, 10)
        vision_range = 10

        self.game_map.walls.add((11, 10))
        self.game_map.invalidate_transparency_cache()

        assert self.game_map.can_see_position(start, end, vision_range) == False

    def test_transparency_cache_invalidation(self):
        """Transparency cache invalidates correctly when map changes."""
        start = Position(10, 10)
        end = Position(12, 10)

        # Initially clear
        assert self.game_map.has_line_of_sight_tcod(start, end) == True

        # Add wall
        self.game_map.walls.add((11, 10))
        self.game_map.invalidate_transparency_cache()

        # Now blocked
        assert self.game_map.has_line_of_sight_tcod(start, end) == False

    def test_out_of_bounds_positions(self):
        """Vision methods handle out of bounds positions correctly."""
        # Start out of bounds
        start = Position(-1, -1)
        end = Position(10, 10)
        assert not self.game_map.can_see_position(start, end, 10)

        # End out of bounds
        start = Position(10, 10)
        end = Position(25, 25)
        assert not self.game_map.can_see_position(start, end, 10)


if __name__ == "__main__":
    pytest.main([__file__])
