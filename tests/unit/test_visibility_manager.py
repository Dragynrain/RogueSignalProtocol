#!/usr/bin/env python3
"""
Unit tests for the Visibility Manager.

Tests FOV calculations, caching, player/enemy vision, and performance.
The Visibility Manager is CRITICAL for gameplay as it handles all vision
calculations for the stealth-based game mechanics.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from game_visibility_manager import VisibilityManager
from game_entities import Position
from game_map import GameMap


class TestVisibilityManagerInitialization:
    """Test VisibilityManager initialization."""

    def test_initialization_with_map(self):
        """VisibilityManager initializes with a game map."""
        mock_map = Mock(spec=GameMap)
        vm = VisibilityManager(mock_map)

        assert vm.game_map is mock_map
        assert vm._cached_player_fov is None
        assert vm._cached_turn == -1

    def test_initialization_empty_caches(self):
        """VisibilityManager starts with empty caches."""
        mock_map = Mock(spec=GameMap)
        vm = VisibilityManager(mock_map)

        assert vm._cached_player_fov is None
        assert vm._cached_enhanced_fov is None
        assert len(vm._enemy_fov_cache) == 0
        assert vm._cached_turn == -1
        assert vm._enemy_cache_turn == -1


class TestPlayerVisibility:
    """Test player visibility calculations."""

    def test_get_player_visible_tiles_computes_on_first_call(self):
        """First call to get_player_visible_tiles computes FOV."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        # Mock player
        mock_player = Mock()
        mock_player.position = Position(10, 10)
        mock_player.get_vision_range.return_value = 5

        # Mock FOV computation
        with patch.object(vm, '_compute_fov_set', return_value={(10, 10), (11, 10), (10, 11)}):
            visible_tiles = vm.get_player_visible_tiles(mock_player, current_turn=1)

            # Should have computed FOV
            assert visible_tiles == {(10, 10), (11, 10), (10, 11)}
            assert vm._cached_turn == 1
            assert vm._cached_player_pos == Position(10, 10)

    def test_get_player_visible_tiles_uses_cache_on_same_turn(self):
        """Subsequent calls on same turn use cached FOV."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        # Mock player
        mock_player = Mock()
        mock_player.position = Position(10, 10)
        mock_player.get_vision_range.return_value = 5

        # First call
        with patch.object(vm, '_compute_fov_set', return_value={(10, 10)}) as mock_compute:
            vm.get_player_visible_tiles(mock_player, current_turn=1)
            assert mock_compute.call_count == 1

            # Second call on same turn
            vm.get_player_visible_tiles(mock_player, current_turn=1)
            # Should not compute again
            assert mock_compute.call_count == 1

    def test_get_player_visible_tiles_recomputes_on_movement(self):
        """FOV recomputes when player moves."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        # Mock player
        mock_player = Mock()
        mock_player.get_vision_range.return_value = 5

        # First call at position (10, 10)
        mock_player.position = Position(10, 10)
        with patch.object(vm, '_compute_fov_set', return_value={(10, 10)}) as mock_compute:
            vm.get_player_visible_tiles(mock_player, current_turn=1)
            assert mock_compute.call_count == 1

            # Player moves to (11, 10)
            mock_player.position = Position(11, 10)
            vm.get_player_visible_tiles(mock_player, current_turn=1)
            # Should recompute
            assert mock_compute.call_count == 2

    def test_get_player_visible_tiles_recomputes_on_vision_change(self):
        """FOV recomputes when vision range changes."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        # Mock player
        mock_player = Mock()
        mock_player.position = Position(10, 10)

        # First call with vision range 5
        mock_player.get_vision_range.return_value = 5
        with patch.object(vm, '_compute_fov_set', return_value={(10, 10)}) as mock_compute:
            vm.get_player_visible_tiles(mock_player, current_turn=1)
            assert mock_compute.call_count == 1

            # Vision range increases to 8 (enhanced vision upgrade)
            mock_player.get_vision_range.return_value = 8
            vm.get_player_visible_tiles(mock_player, current_turn=1)
            # Should recompute
            assert mock_compute.call_count == 2


class TestEnhancedVision:
    """Test enhanced vision (threat scan) functionality."""

    def test_get_enhanced_visible_tiles_same_as_normal_if_ranges_match(self):
        """Enhanced vision uses regular cache if ranges are equal."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        mock_player = Mock()
        mock_player.position = Position(10, 10)
        mock_player.get_vision_range.return_value = 5

        with patch.object(vm, '_compute_fov_set', return_value={(10, 10)}):
            # Get normal vision
            normal_tiles = vm.get_player_visible_tiles(mock_player, current_turn=1)

            # Get enhanced vision with same range
            enhanced_tiles = vm.get_enhanced_visible_tiles(mock_player, current_turn=1, enhanced_range=5)

            # Should be the same
            assert normal_tiles == enhanced_tiles

    def test_get_enhanced_visible_tiles_expands_vision(self):
        """Enhanced vision extends range beyond normal vision."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        mock_player = Mock()
        mock_player.position = Position(10, 10)
        mock_player.get_vision_range.return_value = 5

        def compute_fov_mock(x, y, radius):
            """Mock FOV computation that returns more tiles for larger radius."""
            if radius == 5:
                return {(10, 10), (11, 10)}
            elif radius == 8:
                return {(10, 10), (11, 10), (12, 10), (13, 10)}

        with patch.object(vm, '_compute_fov_set', side_effect=compute_fov_mock):
            # Normal vision (radius 5)
            normal_tiles = vm.get_player_visible_tiles(mock_player, current_turn=1)
            assert len(normal_tiles) == 2

            # Enhanced vision (radius 8)
            enhanced_tiles = vm.get_enhanced_visible_tiles(mock_player, current_turn=1, enhanced_range=8)
            assert len(enhanced_tiles) == 4

    def test_get_enhanced_visible_tiles_caches_separately(self):
        """Enhanced vision maintains separate cache."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        mock_player = Mock()
        mock_player.position = Position(10, 10)
        mock_player.get_vision_range.return_value = 5

        with patch.object(vm, '_compute_fov_set', return_value={(10, 10)}) as mock_compute:
            # Call regular vision first to initialize turn cache
            vm.get_player_visible_tiles(mock_player, current_turn=1)
            assert mock_compute.call_count == 1

            # First enhanced call
            vm.get_enhanced_visible_tiles(mock_player, current_turn=1, enhanced_range=8)
            assert mock_compute.call_count == 2

            # Second enhanced call on same turn - should use cache
            vm.get_enhanced_visible_tiles(mock_player, current_turn=1, enhanced_range=8)
            # Should not compute again
            assert mock_compute.call_count == 2


class TestCanPlayerSee:
    """Test player visibility checks for specific positions."""

    def test_can_player_see_visible_position(self):
        """can_player_see returns True for visible positions."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        mock_player = Mock()
        mock_player.position = Position(10, 10)
        mock_player.get_vision_range.return_value = 5

        with patch.object(vm, '_compute_fov_set', return_value={(10, 10), (11, 10), (10, 11)}):
            # Check visible position
            assert vm.can_player_see(mock_player, Position(11, 10), current_turn=1) is True
            assert vm.can_player_see(mock_player, Position(10, 11), current_turn=1) is True

    def test_can_player_see_invisible_position(self):
        """can_player_see returns False for invisible positions."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        mock_player = Mock()
        mock_player.position = Position(10, 10)
        mock_player.get_vision_range.return_value = 5

        with patch.object(vm, '_compute_fov_set', return_value={(10, 10), (11, 10)}):
            # Check invisible position
            assert vm.can_player_see(mock_player, Position(20, 20), current_turn=1) is False


class TestEnemyVision:
    """Test enemy vision calculations."""

    def test_can_enemy_see_player_when_visible(self):
        """can_enemy_see_player returns True when player is in enemy FOV."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        mock_enemy = Mock()
        mock_enemy.x = 15
        mock_enemy.y = 15
        mock_enemy.type_data.vision = 5

        mock_player = Mock()
        mock_player.x = 16
        mock_player.y = 15

        with patch.object(vm, '_compute_fov_set', return_value={(16, 15), (15, 15)}):
            result = vm.can_enemy_see_player(mock_enemy, mock_player, current_turn=1)
            assert result is True

    def test_can_enemy_see_player_when_not_visible(self):
        """can_enemy_see_player returns False when player not in enemy FOV."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        mock_enemy = Mock()
        mock_enemy.x = 15
        mock_enemy.y = 15
        mock_enemy.type_data.vision = 5

        mock_player = Mock()
        mock_player.x = 30
        mock_player.y = 30

        with patch.object(vm, '_compute_fov_set', return_value={(16, 15), (15, 15)}):
            result = vm.can_enemy_see_player(mock_enemy, mock_player, current_turn=1)
            assert result is False

    def test_enemy_vision_cached_per_turn(self):
        """Enemy FOV is cached and reused within the same turn."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        mock_enemy = Mock()
        mock_enemy.x = 15
        mock_enemy.y = 15
        mock_enemy.type_data.vision = 5

        mock_player = Mock()
        mock_player.x = 16
        mock_player.y = 15

        with patch.object(vm, '_compute_fov_set', return_value={(16, 15)}) as mock_compute:
            # First call
            vm.can_enemy_see_player(mock_enemy, mock_player, current_turn=1)
            assert mock_compute.call_count == 1

            # Second call on same turn, same enemy
            vm.can_enemy_see_player(mock_enemy, mock_player, current_turn=1)
            # Should use cache
            assert mock_compute.call_count == 1

    def test_enemy_vision_cache_cleared_on_new_turn(self):
        """Enemy FOV cache is cleared when turn changes."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        mock_enemy = Mock()
        mock_enemy.x = 15
        mock_enemy.y = 15
        mock_enemy.type_data.vision = 5

        mock_player = Mock()
        mock_player.x = 16
        mock_player.y = 15

        with patch.object(vm, '_compute_fov_set', return_value={(16, 15)}) as mock_compute:
            # Turn 1
            vm.can_enemy_see_player(mock_enemy, mock_player, current_turn=1)
            assert len(vm._enemy_fov_cache) == 1

            # Turn 2 - cache should clear
            vm.can_enemy_see_player(mock_enemy, mock_player, current_turn=2)
            assert mock_compute.call_count == 2


class TestCacheInvalidation:
    """Test cache invalidation."""

    def test_invalidate_cache_clears_all_caches(self):
        """invalidate_cache clears all cached data."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        # Set up some cached data
        vm._cached_player_fov = {(10, 10)}
        vm._cached_enhanced_fov = {(10, 10), (11, 10)}
        vm._enemy_fov_cache[(15, 15, 5)] = {(16, 15)}
        vm._cached_turn = 5

        # Invalidate
        vm.invalidate_cache()

        # All caches should be cleared
        assert vm._cached_player_fov is None
        assert vm._cached_enhanced_fov is None
        assert len(vm._enemy_fov_cache) == 0
        assert vm._cached_turn == -1

    def test_invalidate_cache_forces_recomputation(self):
        """After invalidation, next call recomputes FOV."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        mock_player = Mock()
        mock_player.position = Position(10, 10)
        mock_player.get_vision_range.return_value = 5

        with patch.object(vm, '_compute_fov_set', return_value={(10, 10)}) as mock_compute:
            # First call
            vm.get_player_visible_tiles(mock_player, current_turn=1)
            assert mock_compute.call_count == 1

            # Invalidate cache
            vm.invalidate_cache()

            # Next call should recompute even on same turn
            vm.get_player_visible_tiles(mock_player, current_turn=1)
            assert mock_compute.call_count == 2


class TestVisionStats:
    """Test vision statistics reporting."""

    def test_get_vision_stats_empty_cache(self):
        """get_vision_stats returns correct stats for empty cache."""
        mock_map = Mock(spec=GameMap)
        vm = VisibilityManager(mock_map)

        stats = vm.get_vision_stats()

        assert stats['cached_turn'] == -1
        assert stats['player_fov_cached'] is False
        assert stats['enhanced_fov_cached'] is False
        assert stats['enemy_fov_entries'] == 0
        assert stats['player_fov_tiles'] == 0

    def test_get_vision_stats_with_cached_data(self):
        """get_vision_stats returns correct stats with cached data."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        mock_player = Mock()
        mock_player.position = Position(10, 10)
        mock_player.get_vision_range.return_value = 5

        with patch.object(vm, '_compute_fov_set', return_value={(10, 10), (11, 10), (10, 11)}):
            vm.get_player_visible_tiles(mock_player, current_turn=5)

        stats = vm.get_vision_stats()

        assert stats['cached_turn'] == 5
        assert stats['player_fov_cached'] is True
        assert stats['player_fov_tiles'] == 3


class TestIsPositionVisible:
    """Test quick position visibility checks."""

    def test_is_position_visible_when_in_set(self):
        """is_position_visible returns True when position is in set."""
        mock_map = Mock(spec=GameMap)
        vm = VisibilityManager(mock_map)

        visible_tiles = {(10, 10), (11, 10), (10, 11)}
        pos = Position(11, 10)

        assert vm.is_position_visible(pos, visible_tiles) is True

    def test_is_position_visible_when_not_in_set(self):
        """is_position_visible returns False when position not in set."""
        mock_map = Mock(spec=GameMap)
        vm = VisibilityManager(mock_map)

        visible_tiles = {(10, 10), (11, 10), (10, 11)}
        pos = Position(20, 20)

        assert vm.is_position_visible(pos, visible_tiles) is False


class TestComputeFOVSet:
    """Test internal FOV computation."""

    def test_compute_fov_set_out_of_bounds_returns_empty(self):
        """_compute_fov_set returns empty set for out-of-bounds positions."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        # Position outside map bounds
        result = vm._compute_fov_set(x=100, y=100, vision_range=5)

        assert result == set()

    def test_compute_fov_set_negative_position_returns_empty(self):
        """_compute_fov_set returns empty set for negative positions."""
        mock_map = Mock(spec=GameMap)
        mock_map.width = 50
        mock_map.height = 50
        vm = VisibilityManager(mock_map)

        # Negative position
        result = vm._compute_fov_set(x=-5, y=-5, vision_range=5)

        assert result == set()
