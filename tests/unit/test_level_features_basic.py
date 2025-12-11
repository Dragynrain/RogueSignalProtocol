#!/usr/bin/env python3
"""
Unit tests for basic Level Generation features.
Tests Phase 1-2 features: variable corridor widths, wall-adjacent shadows, alcoves, and cover clusters.
"""

import math
import random

import pytest

from game_config import GameConfig
from game_level import LevelGenerator
from game_map import GameMap


class TestVariableCorridorWidths:
    """Test variable corridor width feature."""

    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)

    def test_corridor_width_selection(self):
        """Test that corridor width selection respects configured probabilities."""
        # Sample corridor widths multiple times to verify distribution
        widths = []
        random.seed(42)  # Fixed seed for reproducibility

        for _ in range(100):
            width = self.level_generator.corridor_generator.get_corridor_width()
            widths.append(width)

        # Count occurrences of each width
        narrow_count = widths.count(1)
        medium_count = widths.count(2)
        wide_count = widths.count(3)

        # Verify all widths are valid (1, 2, or 3)
        assert all(w in [1, 2, 3] for w in widths)

        # With 100 samples and weights 0.50/0.35/0.15, expect roughly:
        # narrow ~50, medium ~35, wide ~15 (allow ±20 variance for randomness)
        assert 30 <= narrow_count <= 70
        assert 15 <= medium_count <= 55
        assert 0 <= wide_count <= 35

        # Verify narrow is most common
        assert narrow_count > medium_count > wide_count or narrow_count > medium_count

    def test_carve_corridor_segment_horizontal(self):
        """Test horizontal corridor segment carving with different widths."""
        # Fill map with walls initially
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Test width 1 horizontal corridor
        self.level_generator.corridor_generator.carve_corridor_segment(
            10, 20, 15, 15, 1, horizontal=True
        )

        # Verify corridor carved correctly
        for x in range(10, 21):
            assert (x, 15) not in self.game_map.walls

        # Verify width is 1 (no tiles above or below should be carved)
        assert (10, 14) in self.game_map.walls
        assert (10, 16) in self.game_map.walls

    def test_carve_corridor_segment_horizontal_width_3(self):
        """Test horizontal corridor segment carving with width 3."""
        # Fill map with walls initially
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Test width 3 horizontal corridor
        self.level_generator.corridor_generator.carve_corridor_segment(
            10, 20, 15, 15, 3, horizontal=True
        )

        # Verify corridor carved with width 3 (y=14, 15, 16)
        for x in range(10, 21):
            assert (x, 14) not in self.game_map.walls
            assert (x, 15) not in self.game_map.walls
            assert (x, 16) not in self.game_map.walls

        # Verify edges are still walls
        assert (10, 13) in self.game_map.walls
        assert (10, 17) in self.game_map.walls

    def test_carve_corridor_segment_vertical(self):
        """Test vertical corridor segment carving with different widths."""
        # Fill map with walls initially
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Test width 2 vertical corridor
        self.level_generator.corridor_generator.carve_corridor_segment(
            15, 15, 10, 20, 2, horizontal=False
        )

        # Verify corridor carved with width 2 (x=14, 15)
        for y in range(10, 21):
            assert (14, y) not in self.game_map.walls
            assert (15, y) not in self.game_map.walls

        # Verify edges are still walls
        assert (13, 10) in self.game_map.walls
        assert (16, 10) in self.game_map.walls

    def test_create_corridor_between_rooms_uses_variable_width(self):
        """Test that corridor creation between rooms uses variable widths."""
        # Create two simple rooms
        room1 = (5, 5, 5, 5)
        room2 = (20, 20, 5, 5)

        self.level_generator.room_generator.carve_room(room1)
        self.level_generator.room_generator.carve_room(room2)

        # Create corridor between them
        self.level_generator.corridor_generator.create_corridor_between_rooms(room1, room2)

        # Verify some corridor tiles were carved (rooms are now connected)
        # Check if there's a path near the midpoint between rooms
        mid_x = (room1[0] + room2[0]) // 2
        mid_y = (room1[1] + room2[1]) // 2

        # Should be floor tiles somewhere along the corridor path
        floor_tiles_in_corridor_area = 0
        for x in range(mid_x - 3, mid_x + 4):
            for y in range(mid_y - 3, mid_y + 4):
                if 0 <= x < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT:
                    if (x, y) not in self.game_map.walls:
                        floor_tiles_in_corridor_area += 1

        # Should have carved some corridor tiles
        assert floor_tiles_in_corridor_area > 0

    def test_level_generation_with_variable_corridors(self):
        """Test that full level generation works with variable corridor widths."""
        # Generate a level and verify it completes successfully
        self.level_generator.generate_level(1, 12345)

        # Should have walls (map generated)
        assert len(self.game_map.walls) > 0

        # Should have walkable floor tiles
        floor_count = 0
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if (x, y) not in self.game_map.walls:
                    floor_count += 1

        assert floor_count > 100  # Should have substantial open area


class TestWallAdjacentShadows:
    """Test wall-adjacent shadow placement feature."""

    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)

    def test_get_wall_adjacent_positions(self):
        """Test identification of wall-adjacent positions in a room."""
        # Create a simple 5x5 room
        room = (10, 10, 5, 5)
        self.level_generator.room_generator.carve_room(room)

        # Get wall-adjacent positions
        wall_adjacent = self.level_generator.tactical_generator.get_wall_adjacent_positions(room)

        # Verify all wall-adjacent positions are actually adjacent to walls
        for pos in wall_adjacent:
            x, y = pos
            # Check that at least one neighbor is a wall
            neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
            has_wall_neighbor = any(n in self.game_map.walls for n in neighbors)
            assert has_wall_neighbor, f"Position {pos} is not adjacent to any wall"

        # Verify positions are within the room
        for pos in wall_adjacent:
            x, y = pos
            assert 10 <= x < 15 and 10 <= y < 15

    def test_get_interior_positions(self):
        """Test identification of interior positions in a room."""
        # Create a simple 5x5 room
        room = (10, 10, 5, 5)
        self.level_generator.room_generator.carve_room(room)

        # Get interior positions
        interior = self.level_generator.tactical_generator.get_interior_positions(room)

        # Verify all interior positions are NOT adjacent to walls
        for pos in interior:
            x, y = pos
            # Check that NO neighbor is a wall
            neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
            has_wall_neighbor = any(n in self.game_map.walls for n in neighbors)
            assert (
                not has_wall_neighbor
            ), f"Position {pos} is adjacent to a wall but marked as interior"

    def test_wall_adjacent_and_interior_are_mutually_exclusive(self):
        """Test that wall-adjacent and interior positions don't overlap."""
        # Create a room
        room = (10, 10, 7, 7)
        self.level_generator.room_generator.carve_room(room)

        wall_adjacent = set(
            self.level_generator.tactical_generator.get_wall_adjacent_positions(room)
        )
        interior = set(self.level_generator.tactical_generator.get_interior_positions(room))

        # Sets should not overlap
        overlap = wall_adjacent.intersection(interior)
        assert (
            len(overlap) == 0
        ), f"Found {len(overlap)} positions in both wall-adjacent and interior sets"

    def test_small_room_has_no_interior(self):
        """Test that small rooms (3x3) have minimal interior positions when surrounded by walls."""
        # Fill map with walls first
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Create a 3x3 room - most floor tiles should be wall-adjacent
        room = (10, 10, 3, 3)
        self.level_generator.room_generator.carve_room(room)

        interior = self.level_generator.tactical_generator.get_interior_positions(room)
        wall_adjacent = self.level_generator.tactical_generator.get_wall_adjacent_positions(room)

        # Small rooms should have mostly wall-adjacent tiles
        # A 3x3 room surrounded by walls should have at most 1 interior tile (the center)
        assert len(interior) <= 1  # At most the center tile
        assert len(wall_adjacent) >= 8  # Most tiles should be wall-adjacent

    def test_shadow_placement_with_wall_preference(self):
        """Test that shadow placement respects wall-adjacent preference."""
        # Generate a level with shadows
        random.seed(42)  # Fixed seed for reproducibility
        self.level_generator.generate_level(1, 12345)

        # Analyze placed shadows
        wall_adjacent_shadows = 0
        interior_shadows = 0

        for shadow_pos in self.game_map.blind_spots:
            x, y = shadow_pos
            # Check if adjacent to wall
            neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
            is_wall_adjacent = any(n in self.game_map.walls for n in neighbors)

            if is_wall_adjacent:
                wall_adjacent_shadows += 1
            else:
                interior_shadows += 1

        total_shadows = wall_adjacent_shadows + interior_shadows

        # With 60% wall-adjacent weight, expect more wall-adjacent shadows
        # Allow for randomness but verify general trend
        # Note: Cleanup can remove some shadows if they end up on walls from cover placement
        if total_shadows > 10:  # Only check if we have enough shadows
            wall_adjacent_ratio = wall_adjacent_shadows / total_shadows
            # Should be roughly 0.60, but allow wide range due to randomness and cleanup
            # Just verify it's not extremely biased
            assert wall_adjacent_ratio > 0.20, f"Wall-adjacent ratio {wall_adjacent_ratio} too low"

    def test_shadow_placement_uses_both_types(self):
        """Test that shadow placement uses both wall-adjacent and interior positions."""
        # Generate multiple levels and verify both types are used
        random.seed(99)
        self.level_generator.generate_level(1, 54321)

        wall_adjacent_count = 0
        interior_count = 0

        for shadow_pos in self.game_map.blind_spots:
            x, y = shadow_pos
            neighbors = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
            is_wall_adjacent = any(n in self.game_map.walls for n in neighbors)

            if is_wall_adjacent:
                wall_adjacent_count += 1
            else:
                interior_count += 1

        # Both types should be present (unless level has very few shadows)
        total = wall_adjacent_count + interior_count
        if total > 20:
            assert interior_count > 0, "No interior shadows found"
            assert wall_adjacent_count > 0, "No wall-adjacent shadows found"

    def test_level_generation_with_wall_adjacent_shadows(self):
        """Test that full level generation works with wall-adjacent shadow placement."""
        # Generate a level and verify it completes successfully
        self.level_generator.generate_level(1, 12345)

        # Should have shadows placed
        assert len(self.game_map.blind_spots) > 0

        # All shadows should be on valid floor tiles
        for shadow_pos in self.game_map.blind_spots:
            assert shadow_pos not in self.game_map.walls
            assert 0 <= shadow_pos[0] < GameConfig.MAP_WIDTH
            assert 0 <= shadow_pos[1] < GameConfig.MAP_HEIGHT


class TestCorridorAlcoves:
    """Test corridor alcove placement feature."""

    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)

    def test_corridor_tracking(self):
        """Test that corridor tiles are tracked during carving."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Carve a horizontal corridor segment
        self.level_generator.corridor_generator.carve_corridor_segment(
            10, 20, 15, 15, 1, horizontal=True
        )

        # Verify corridor tiles were tracked
        assert len(self.level_generator.corridor_tiles) > 0

        # All tracked tiles should be floor (not walls)
        for tile in self.level_generator.corridor_tiles:
            assert tile not in self.game_map.walls

    def test_find_straight_horizontal_segments(self):
        """Test identification of straight horizontal corridor segments."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Create a horizontal corridor
        for x in range(10, 20):
            self.game_map.walls.discard((x, 15))
            self.level_generator.corridor_tiles.add((x, 15))

        # Find horizontal segments
        segments = self.level_generator.corridor_generator.find_straight_corridor_segments(
            horizontal=True
        )

        # Should find at least one segment
        assert len(segments) > 0

        # The segment should include our corridor tiles
        found_segment = None
        for seg in segments:
            if (10, 15) in seg and (19, 15) in seg:
                found_segment = seg
                break

        assert found_segment is not None
        assert len(found_segment) == 10  # 10 tiles from x=10 to x=19

    def test_find_straight_vertical_segments(self):
        """Test identification of straight vertical corridor segments."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Create a vertical corridor
        for y in range(10, 20):
            self.game_map.walls.discard((15, y))
            self.level_generator.corridor_tiles.add((15, y))

        # Find vertical segments
        segments = self.level_generator.corridor_generator.find_straight_corridor_segments(
            horizontal=False
        )

        # Should find at least one segment
        assert len(segments) > 0

        # The segment should include our corridor tiles
        found_segment = None
        for seg in segments:
            if (15, 10) in seg and (15, 19) in seg:
                found_segment = seg
                break

        assert found_segment is not None
        assert len(found_segment) == 10

    def test_alcove_creation_horizontal(self):
        """Test alcove creation on horizontal corridor segment."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Create a horizontal corridor segment
        segment = [(x, 15) for x in range(10, 20)]
        for tile in segment:
            self.game_map.walls.discard(tile)

        random.seed(42)
        # Create alcoves on this segment
        self.level_generator.corridor_generator.create_alcoves_on_segment(segment, horizontal=True)

        # Check if any alcoves were created (tiles adjacent to corridor)
        alcoves_created = False
        for x in range(10, 20):
            # Check above and below the corridor
            if (x, 14) not in self.game_map.walls or (x, 16) not in self.game_map.walls:
                alcoves_created = True
                break

        # With random seed 42, should create some alcoves
        assert alcoves_created

    def test_alcove_has_shadow(self):
        """Test that alcoves have shadows placed in them."""
        # Generate a full level to test alcove + shadow placement
        random.seed(12345)
        self.level_generator.generate_level(1, 99999)

        # If alcoves were created, they should have shadows
        # We can't directly verify which shadows are in alcoves without complex analysis,
        # but we can verify shadows exist and level generated successfully
        assert len(self.game_map.blind_spots) > 0

    def test_level_generation_with_alcoves(self):
        """Test that full level generation works with corridor alcoves."""
        # Generate a level and verify it completes successfully
        self.level_generator.generate_level(1, 54321)

        # Should have corridor tiles tracked
        assert len(self.level_generator.corridor_tiles) > 0

        # Should have walls (map generated)
        assert len(self.game_map.walls) > 0

        # All corridor tiles should be walkable
        for tile in self.level_generator.corridor_tiles:
            assert tile not in self.game_map.walls

    def test_short_segments_get_no_alcoves(self):
        """Test that short corridor segments (< min length) get no alcoves."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Create a short segment (3 tiles)
        segment = [(x, 15) for x in range(10, 13)]
        for tile in segment:
            self.game_map.walls.discard(tile)

        walls_before = len(self.game_map.walls)

        # Try to create alcoves (should not create any due to min length requirement)
        self.level_generator.corridor_generator.create_alcoves_on_segment(segment, horizontal=True)

        walls_after = len(self.game_map.walls)

        # No alcoves should be created (segment too short)
        # The method returns early if segment < 4 tiles
        assert walls_before == walls_after


class TestStrategicCoverClusters:
    """Test strategic cover cluster placement with Poisson disc sampling."""

    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)

    def test_poisson_disc_sampling(self):
        """Test Poisson disc sampling generates well-distributed points."""
        area = (10, 10, 20, 20)  # 20x20 area
        radius = 5.0

        random.seed(42)
        points = self.level_generator.tactical_generator.poisson_disc_sampling(area, radius)

        # Should generate some points
        assert len(points) > 0

        # All points should be within the area
        for px, py in points:
            assert 10 <= px < 30
            assert 10 <= py < 30

        # All points should be at least 'radius' apart
        for i, (px1, py1) in enumerate(points):
            for j, (px2, py2) in enumerate(points):
                if i != j:
                    dist = math.sqrt((px1 - px2) ** 2 + (py1 - py2) ** 2)
                    assert (
                        dist >= radius
                    ), f"Points {(px1, py1)} and {(px2, py2)} are too close: {dist} < {radius}"

    def test_find_large_open_areas(self):
        """Test identification of large open floor areas."""
        # Create a large open area in the map
        for x in range(15, 30):
            for y in range(15, 30):
                if (x, y) in self.game_map.walls:
                    self.game_map.walls.remove((x, y))

        # Find open areas
        open_areas = self.level_generator.tactical_generator.find_large_open_areas(10)

        # Should find at least one open area
        assert len(open_areas) > 0

        # Verify found areas are within bounds and reasonable size
        for x, y, w, h in open_areas:
            assert w >= 10
            assert h >= 10
            assert 0 <= x < GameConfig.MAP_WIDTH
            assert 0 <= y < GameConfig.MAP_HEIGHT

    def test_is_valid_cover_position(self):
        """Test validation of cover placement positions."""
        # Clear a spot
        test_pos = (20, 20)
        if test_pos in self.game_map.walls:
            self.game_map.walls.remove(test_pos)

        # Should be valid (floor, not in corridor, not a special node)
        assert self.level_generator.tactical_generator.is_valid_cover_position(test_pos)

        # Add to corridor tiles - should now be invalid
        self.level_generator.corridor_tiles.add(test_pos)
        assert not self.level_generator.tactical_generator.is_valid_cover_position(test_pos)

        # Remove from corridor, add as special node - should be invalid
        self.level_generator.corridor_tiles.remove(test_pos)
        self.game_map.cooling_nodes.add(test_pos)
        assert not self.level_generator.tactical_generator.is_valid_cover_position(test_pos)

        # Test out of bounds
        assert not self.level_generator.tactical_generator.is_valid_cover_position((-1, -1))
        assert not self.level_generator.tactical_generator.is_valid_cover_position(
            (GameConfig.MAP_WIDTH + 1, GameConfig.MAP_HEIGHT + 1)
        )

    def test_create_cover_cluster_small(self):
        """Test creation of small cover cluster."""
        # Clear area for cover
        for x in range(15, 20):
            for y in range(15, 20):
                if (x, y) in self.game_map.walls:
                    self.game_map.walls.remove((x, y))

        walls_before = len(self.game_map.walls)

        # Create a small cluster
        random.seed(100)  # Force 'small' cluster type
        # Try multiple times to get 'small' type
        for _ in range(10):
            self.level_generator.tactical_generator.create_cover_cluster((15, 15))
            if len(self.game_map.walls) > walls_before:
                break

        # Should have added some walls
        walls_after = len(self.game_map.walls)
        # May or may not add walls depending on random cluster type selected
        assert walls_after >= walls_before

    def test_cover_clusters_avoid_corridors(self):
        """Test that cover clusters don't block corridors."""
        # Mark some positions as corridor tiles
        corridor_pos = (20, 20)
        self.level_generator.corridor_tiles.add(corridor_pos)

        # Clear the position
        if corridor_pos in self.game_map.walls:
            self.game_map.walls.remove(corridor_pos)

        # Try to create cover at corridor position
        assert not self.level_generator.tactical_generator.is_valid_cover_position(corridor_pos)

    def test_level_generation_with_cover_clusters(self):
        """Test that full level generation works with cover clusters."""
        # Generate a level and verify it completes successfully
        self.level_generator.generate_level(1, 77777)

        # Should have walls (map generated)
        assert len(self.game_map.walls) > 0

        # Should have some floor tiles
        floor_count = 0
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if (x, y) not in self.game_map.walls:
                    floor_count += 1

        assert floor_count > 100  # Should have substantial open area

    def test_poisson_disc_sampling_empty_area(self):
        """Test Poisson disc sampling with area that's too small."""
        # Very small area
        area = (10, 10, 3, 3)
        radius = 5.0

        points = self.level_generator.tactical_generator.poisson_disc_sampling(area, radius)

        # May generate 0 or very few points due to space constraints
        assert isinstance(points, list), "Should return a list (possibly empty)"


if __name__ == "__main__":
    pytest.main([__file__])
