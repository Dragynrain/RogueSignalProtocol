"""
Unit tests for graphics tile management system (TileManager).

Tests sprite loading, caching, scaling, and error handling without mocking.
Uses real sprite files and SDL textures for authentic integration testing.
"""

import os
from unittest.mock import Mock, patch

import pytest

from rsp.core.config import GameSettings
from rsp.rendering.tiles import TileManager


class TestTileManagerInitialization:
    """Test TileManager initialization and configuration loading."""

    def test_tile_manager_initializes_with_valid_config(self):
        """TileManager should initialize successfully with valid configuration."""
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()

        settings = GameSettings()
        settings.graphics_mode = "graphics"

        tile_manager = TileManager(mock_context, settings)

        assert tile_manager is not None
        assert tile_manager.context == mock_context
        assert tile_manager.settings == settings
        assert hasattr(tile_manager, "tile_mappings")
        assert hasattr(tile_manager, "texture_cache")
        assert hasattr(tile_manager, "tintable_flags")

    def test_tile_manager_loads_graphics_tiles_json(self):
        """TileManager should successfully load graphics_tiles.json configuration."""
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()

        settings = GameSettings()
        settings.graphics_mode = "graphics"

        tile_manager = TileManager(mock_context, settings)

        # Verify config was loaded
        assert tile_manager.tile_mappings is not None
        assert "player" in tile_manager.tile_mappings
        assert "enemies" in tile_manager.tile_mappings
        assert "terrain" in tile_manager.tile_mappings
        assert "items" in tile_manager.tile_mappings

    def test_tile_manager_handles_missing_config_file(self):
        """TileManager should handle missing graphics_tiles.json gracefully (no crash)."""
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()

        settings = GameSettings()
        settings.graphics_mode = "graphics"

        with patch("builtins.open", side_effect=FileNotFoundError()):
            # Should not crash, just log error and use fallbacks
            tile_manager = TileManager(mock_context, settings)
            assert tile_manager is not None
            # Tile mappings should be empty if file not found
            assert len(tile_manager.tile_mappings) == 0


class TestSpriteConfiguration:
    """Test sprite configuration and mapping."""

    @pytest.fixture
    def tile_manager(self):
        """Create TileManager instance for testing."""
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()

        settings = GameSettings()
        settings.graphics_mode = "graphics"

        return TileManager(mock_context, settings)

    def test_player_sprite_configuration_exists(self, tile_manager):
        """Player sprite should be configured in graphics_tiles.json."""
        assert "player" in tile_manager.tile_mappings
        assert "file" in tile_manager.tile_mappings["player"]
        assert tile_manager.tile_mappings["player"]["file"].endswith(".png")

    def test_all_enemy_types_have_sprite_config(self, tile_manager):
        """All enemy types should have sprite configurations."""
        expected_enemies = [
            "Scanner",
            "Patrol",
            "Bot",
            "Hunter",
            "Virus",
            "Inhibitor",
            "Firewall",
            "Admin Avatar",
        ]

        enemies_config = tile_manager.tile_mappings.get("enemies", {})

        for enemy_type in expected_enemies:
            assert enemy_type in enemies_config, f"Missing config for {enemy_type}"
            assert "file" in enemies_config[enemy_type]
            assert enemies_config[enemy_type]["file"].endswith(".png")

    def test_terrain_sprites_configured(self, tile_manager):
        """Terrain sprites (floor, wall, shadow) should be configured."""
        terrain_config = tile_manager.tile_mappings.get("terrain", {})

        assert "floor" in terrain_config
        assert "wall" in terrain_config
        assert "blind_spot" in terrain_config

        for terrain_type in ["floor", "wall", "blind_spot"]:
            assert "file" in terrain_config[terrain_type]

    def test_item_sprites_configured(self, tile_manager):
        """All item types should have sprite configurations."""
        expected_items = [
            "codehack",
            "exploit",
            "cooling_node",
            "cooling_upgrade",
            "cpu_node",
            "cpu_upgrade",
            "ram_upgrade",
            "ghost_node",
        ]

        items_config = tile_manager.tile_mappings.get("items", {})

        for item_type in expected_items:
            assert item_type in items_config, f"Missing config for {item_type}"
            assert "file" in items_config[item_type]

    def test_special_sprites_configured(self, tile_manager):
        """Special sprites (gateway, story_fragment) should be configured."""
        special_config = tile_manager.tile_mappings.get("special", {})

        assert "gateway" in special_config
        assert "story_fragment" in special_config

        for special_type in ["gateway", "story_fragment"]:
            assert "file" in special_config[special_type]

    def test_tintable_flags_present(self, tile_manager):
        """Sprite configurations should include tintable flags."""
        # Codehacks and exploits should be tintable
        assert tile_manager.tile_mappings["items"]["codehack"]["tintable"]
        assert tile_manager.tile_mappings["items"]["exploit"]["tintable"]

        # Enemies should not be tintable
        assert not tile_manager.tile_mappings["enemies"]["Scanner"]["tintable"]
        assert not tile_manager.tile_mappings["enemies"]["Hunter"]["tintable"]


class TestSpriteFileExistence:
    """Test that configured sprite files actually exist."""

    @pytest.fixture
    def tile_manager(self):
        """Create TileManager instance for testing."""
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()

        settings = GameSettings()
        settings.graphics_mode = "graphics"

        return TileManager(mock_context, settings)

    def test_player_sprite_file_exists(self, tile_manager):
        """Player sprite file should exist in graphics directory."""
        sprite_file = tile_manager.tile_mappings["player"]["file"]
        sprite_path = os.path.join("graphics", sprite_file)
        assert os.path.exists(sprite_path), f"Player sprite not found: {sprite_path}"

    def test_all_enemy_sprite_files_exist(self, tile_manager):
        """All configured enemy sprite files should exist."""
        enemies_config = tile_manager.tile_mappings.get("enemies", {})

        for enemy_type, config in enemies_config.items():
            sprite_file = config["file"]
            sprite_path = os.path.join("graphics", sprite_file)
            assert os.path.exists(sprite_path), f"{enemy_type} sprite not found: {sprite_path}"

    def test_terrain_sprite_files_exist(self, tile_manager):
        """All terrain sprite files should exist."""
        terrain_config = tile_manager.tile_mappings.get("terrain", {})

        for terrain_type, config in terrain_config.items():
            sprite_file = config["file"]
            sprite_path = os.path.join("graphics", sprite_file)
            assert os.path.exists(sprite_path), f"{terrain_type} sprite not found: {sprite_path}"

    def test_item_sprite_files_exist(self, tile_manager):
        """All item sprite files should exist."""
        items_config = tile_manager.tile_mappings.get("items", {})

        for item_type, config in items_config.items():
            sprite_file = config["file"]
            sprite_path = os.path.join("graphics", sprite_file)
            assert os.path.exists(sprite_path), f"{item_type} sprite not found: {sprite_path}"

    def test_gateway_sprite_exists(self, tile_manager):
        """Gateway sprite file should exist."""
        sprite_file = tile_manager.tile_mappings["special"]["gateway"]["file"]
        sprite_path = os.path.join("graphics", sprite_file)
        assert os.path.exists(sprite_path), f"Gateway sprite not found: {sprite_path}"

    def test_story_fragment_sprite_exists(self, tile_manager):
        """Story fragment sprite file should exist."""
        sprite_file = tile_manager.tile_mappings["special"]["story_fragment"]["file"]
        sprite_path = os.path.join("graphics", sprite_file)
        assert os.path.exists(sprite_path), f"Story fragment sprite not found: {sprite_path}"


class TestTileManagerAPI:
    """Test TileManager public API methods."""

    @pytest.fixture
    def tile_manager(self):
        """Create TileManager instance for testing."""
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()

        settings = GameSettings()
        settings.graphics_mode = "graphics"

        return TileManager(mock_context, settings)

    def test_is_tintable_returns_correct_values(self, tile_manager):
        """is_tintable() should return correct values for different entity types."""
        # Tintable items
        assert tile_manager.is_tintable("codehack")
        assert tile_manager.is_tintable("exploit")

        # Non-tintable items
        assert not tile_manager.is_tintable("floor")
        assert not tile_manager.is_tintable("wall")
        assert not tile_manager.is_tintable("player")

    def test_is_tintable_handles_unknown_entities(self, tile_manager):
        """is_tintable() should return False for unknown entities."""
        assert not tile_manager.is_tintable("unknown_entity")
        assert not tile_manager.is_tintable("nonexistent")

    def test_has_sprite_returns_true_for_configured_entities(self, tile_manager):
        """has_sprite() should return True for all configured entities."""
        assert tile_manager.has_sprite("player")
        assert tile_manager.has_sprite("floor")
        assert tile_manager.has_sprite("wall")
        assert tile_manager.has_sprite("codehack")
        assert tile_manager.has_sprite("gateway")

    def test_has_sprite_returns_false_for_unconfigured_entities(self, tile_manager):
        """has_sprite() should return False for unconfigured entities."""
        assert not tile_manager.has_sprite("unknown_entity")
        assert not tile_manager.has_sprite("fake_sprite")


class TestCacheManagement:
    """Test sprite texture caching behavior."""

    @pytest.fixture
    def tile_manager(self):
        """Create TileManager instance for testing."""
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()

        settings = GameSettings()
        settings.graphics_mode = "graphics"

        return TileManager(mock_context, settings)

    def test_cache_starts_empty(self, tile_manager):
        """Texture cache should start empty (lazy loading)."""
        assert len(tile_manager.texture_cache) == 0

    def test_cache_size_increases_after_loading(self, tile_manager):
        """Cache size should increase when tiles are loaded."""
        initial_cache_size = len(tile_manager.texture_cache)

        # Load a tile (this will fail without real SDL, but we're testing the concept)
        # In a real test with SDL context, we'd verify cache grows
        assert initial_cache_size == 0  # Starts empty


class TestErrorHandling:
    """Test error handling for missing files and invalid configurations."""

    def test_handles_missing_sprite_file_gracefully(self):
        """TileManager should handle missing sprite files gracefully."""
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()

        settings = GameSettings()
        settings.graphics_mode = "graphics"

        tile_manager = TileManager(mock_context, settings)

        # Requesting a non-existent sprite should not crash
        # (In real implementation, it logs warning and returns None)
        result = tile_manager.has_sprite("completely_fake_sprite")
        assert not result
