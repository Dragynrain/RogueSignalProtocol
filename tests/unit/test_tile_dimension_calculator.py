#!/usr/bin/env python3
"""
Unit tests for the Tile Dimension Calculator.

Tests tile size calculations for different resolutions, aspect ratios,
and graphics modes. Validates minimum size enforcement and fallback handling.
"""


from rsp.core.config import GameConfig
from rsp.rendering.dimensions import TileDimensionCalculator


class TestTileDimensionCalculatorGraphicsMode:
    """Test tile dimension calculations in graphics mode."""

    def test_graphics_mode_always_returns_64x64(self):
        """Graphics mode always returns fixed 64x64 regardless of window size."""
        # Test various resolutions - all should return (64, 64)
        resolutions = [
            (1920, 1080),  # 1080p
            (1280, 720),  # 720p
            (3840, 2160),  # 4K
            (7680, 4320),  # 8K
            (800, 600),  # Small window
            (2560, 1080),  # Ultrawide
        ]

        for width, height in resolutions:
            result = TileDimensionCalculator.calculate_from_window((width, height), "graphics")
            assert result == (
                64,
                64,
            ), f"Graphics mode should always return (64, 64) for {width}x{height}"

    def test_graphics_mode_direct_calculation(self):
        """Direct call to _calc_graphics_mode returns 64x64."""
        result = TileDimensionCalculator._calc_graphics_mode(1920, 1080)
        assert result == (64, 64)

    def test_graphics_mode_ignores_window_size(self):
        """Graphics mode calculation doesn't depend on window dimensions."""
        # These should all return the same result
        result1 = TileDimensionCalculator._calc_graphics_mode(100, 100)
        result2 = TileDimensionCalculator._calc_graphics_mode(8000, 8000)

        assert result1 == result2 == (64, 64)


class TestTileDimensionCalculatorGlyphMode:
    """Test tile dimension calculations in glyph/ASCII mode."""

    def test_glyph_mode_1920x1080(self):
        """Glyph mode calculates correct tile size for 1920x1080."""
        # 1920 / 80 = 24px width, 1080 / 50 = 21.6 -> 21px height
        result = TileDimensionCalculator.calculate_from_window((1920, 1080), "glyph")

        assert result[0] == 1920 // GameConfig.SCREEN_WIDTH
        assert result[1] == 1080 // GameConfig.SCREEN_HEIGHT

    def test_glyph_mode_1280x720(self):
        """Glyph mode calculates correct tile size for 1280x720."""
        # 1280 / 80 = 16px width, 720 / 50 = 14.4 -> 14px height
        result = TileDimensionCalculator.calculate_from_window((1280, 720), "glyph")

        assert result[0] == 1280 // GameConfig.SCREEN_WIDTH
        assert result[1] == 720 // GameConfig.SCREEN_HEIGHT

    def test_glyph_mode_4k_3840x2160(self):
        """Glyph mode calculates correct tile size for 4K."""
        # 3840 / 80 = 48px width, 2160 / 50 = 43.2 -> 43px height
        result = TileDimensionCalculator.calculate_from_window((3840, 2160), "glyph")

        assert result[0] == 3840 // GameConfig.SCREEN_WIDTH
        assert result[1] == 2160 // GameConfig.SCREEN_HEIGHT

    def test_glyph_mode_8k_7680x4320(self):
        """Glyph mode calculates correct tile size for 8K."""
        # 7680 / 80 = 96px width, 4320 / 50 = 86.4 -> 86px height
        result = TileDimensionCalculator.calculate_from_window((7680, 4320), "glyph")

        assert result[0] == 7680 // GameConfig.SCREEN_WIDTH
        assert result[1] == 4320 // GameConfig.SCREEN_HEIGHT

    def test_glyph_mode_ultrawide_2560x1080(self):
        """Glyph mode handles ultrawide 21:9 aspect ratio."""
        # 2560 / 80 = 32px width, 1080 / 50 = 21.6 -> 21px height
        result = TileDimensionCalculator.calculate_from_window((2560, 1080), "glyph")

        assert result[0] == 2560 // GameConfig.SCREEN_WIDTH
        assert result[1] == 1080 // GameConfig.SCREEN_HEIGHT

    def test_glyph_mode_superultrawide_3440x1440(self):
        """Glyph mode handles super ultrawide 21:9 aspect ratio."""
        # 3440 / 80 = 43px width, 1440 / 50 = 28.8 -> 28px height
        result = TileDimensionCalculator.calculate_from_window((3440, 1440), "glyph")

        assert result[0] == 3440 // GameConfig.SCREEN_WIDTH
        assert result[1] == 1440 // GameConfig.SCREEN_HEIGHT


class TestTileDimensionValidationAndClamping:
    """Test tile dimension validation and minimum size enforcement."""

    def test_validate_and_clamp_normal_sizes(self):
        """Normal tile sizes pass through unchanged."""
        # Typical sizes that are above minimums
        result = TileDimensionCalculator.validate_and_clamp(20, 20)
        assert result == (20, 20)

        result = TileDimensionCalculator.validate_and_clamp(64, 64)
        assert result == (64, 64)

    def test_validate_and_clamp_enforces_minimum_width(self):
        """Tile width is clamped to minimum."""
        min_width = GameConfig.MIN_TILE_WIDTH()

        # Test width below minimum
        result = TileDimensionCalculator.validate_and_clamp(1, 20)
        assert result[0] == min_width
        assert result[1] == 20

    def test_validate_and_clamp_enforces_minimum_height(self):
        """Tile height is clamped to minimum."""
        min_height = GameConfig.MIN_TILE_HEIGHT()

        # Test height below minimum
        result = TileDimensionCalculator.validate_and_clamp(20, 1)
        assert result[0] == 20
        assert result[1] == min_height

    def test_validate_and_clamp_enforces_both_minimums(self):
        """Both dimensions are clamped to minimums when too small."""
        min_width = GameConfig.MIN_TILE_WIDTH()
        min_height = GameConfig.MIN_TILE_HEIGHT()

        # Test both dimensions below minimum
        result = TileDimensionCalculator.validate_and_clamp(1, 1)
        assert result == (min_width, min_height)

    def test_validate_and_clamp_zero_dimensions(self):
        """Zero dimensions are clamped to minimums."""
        min_width = GameConfig.MIN_TILE_WIDTH()
        min_height = GameConfig.MIN_TILE_HEIGHT()

        result = TileDimensionCalculator.validate_and_clamp(0, 0)
        assert result == (min_width, min_height)

    def test_validate_and_clamp_negative_dimensions(self):
        """Negative dimensions are clamped to minimums."""
        min_width = GameConfig.MIN_TILE_WIDTH()
        min_height = GameConfig.MIN_TILE_HEIGHT()

        result = TileDimensionCalculator.validate_and_clamp(-10, -10)
        assert result == (min_width, min_height)


class TestTileDimensionTinyWindows:
    """Test tile calculations for very small windows."""

    def test_tiny_window_400x300(self):
        """Very small window enforces minimum tile sizes."""
        # 400 / 80 = 5px width, 300 / 50 = 6px height
        result = TileDimensionCalculator.calculate_from_window((400, 300), "glyph")

        # Should be clamped to minimums
        min_width = GameConfig.MIN_TILE_WIDTH()
        min_height = GameConfig.MIN_TILE_HEIGHT()

        assert result[0] >= min_width
        assert result[1] >= min_height

    def test_tiny_window_200x200(self):
        """Extremely small window enforces minimum tile sizes."""
        # 200 / 80 = 2.5 -> 2px width, 200 / 50 = 4px height
        result = TileDimensionCalculator.calculate_from_window((200, 200), "glyph")

        # Should be clamped to minimums
        min_width = GameConfig.MIN_TILE_WIDTH()
        min_height = GameConfig.MIN_TILE_HEIGHT()

        assert result[0] >= min_width
        assert result[1] >= min_height

    def test_tiny_window_100x100(self):
        """Absurdly small window enforces minimum tile sizes."""
        # 100 / 80 = 1.25 -> 1px width, 100 / 50 = 2px height
        result = TileDimensionCalculator.calculate_from_window((100, 100), "glyph")

        # Should be clamped to minimums
        min_width = GameConfig.MIN_TILE_WIDTH()
        min_height = GameConfig.MIN_TILE_HEIGHT()

        assert result[0] >= min_width
        assert result[1] >= min_height


class TestFallbackDimensions:
    """Test fallback dimension handling."""

    def test_get_fallback_dimensions(self):
        """Fallback dimensions are retrieved from config."""
        result = TileDimensionCalculator.get_fallback_dimensions()

        expected_width = GameConfig.FALLBACK_TILE_WIDTH()
        expected_height = GameConfig.FALLBACK_TILE_HEIGHT()

        assert result == (expected_width, expected_height)

    def test_fallback_dimensions_are_valid(self):
        """Fallback dimensions meet minimum requirements."""
        width, height = TileDimensionCalculator.get_fallback_dimensions()

        min_width = GameConfig.MIN_TILE_WIDTH()
        min_height = GameConfig.MIN_TILE_HEIGHT()

        assert width >= min_width
        assert height >= min_height


class TestTileDimensionEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_square_window_1000x1000(self):
        """Square aspect ratio window."""
        result = TileDimensionCalculator.calculate_from_window((1000, 1000), "glyph")

        # 1000 / 80 = 12.5 -> 12px width, 1000 / 50 = 20px height
        assert result[0] == 1000 // GameConfig.SCREEN_WIDTH
        assert result[1] == 1000 // GameConfig.SCREEN_HEIGHT

    def test_extreme_ultrawide_5120x1440(self):
        """Extreme ultrawide 32:9 aspect ratio."""
        result = TileDimensionCalculator.calculate_from_window((5120, 1440), "glyph")

        # 5120 / 80 = 64px width, 1440 / 50 = 28.8 -> 28px height
        assert result[0] == 5120 // GameConfig.SCREEN_WIDTH
        assert result[1] == 1440 // GameConfig.SCREEN_HEIGHT

    def test_portrait_orientation_1080x1920(self):
        """Portrait orientation (height > width)."""
        result = TileDimensionCalculator.calculate_from_window((1080, 1920), "glyph")

        # 1080 / 80 = 13.5 -> 13px width, 1920 / 50 = 38.4 -> 38px height
        assert result[0] == 1080 // GameConfig.SCREEN_WIDTH
        assert result[1] == 1920 // GameConfig.SCREEN_HEIGHT

    def test_calculate_from_window_unknown_mode_defaults_to_glyph(self):
        """Unknown graphics mode defaults to glyph mode behavior."""
        # Test with an invalid mode string
        result = TileDimensionCalculator.calculate_from_window((1920, 1080), "unknown_mode")

        # Should behave like glyph mode (not graphics mode which returns 64x64)
        expected = TileDimensionCalculator.calculate_from_window((1920, 1080), "glyph")

        assert result == expected

    def test_calculate_from_window_empty_string_mode(self):
        """Empty string mode defaults to glyph mode behavior."""
        result = TileDimensionCalculator.calculate_from_window((1920, 1080), "")

        # Should behave like glyph mode
        expected = TileDimensionCalculator.calculate_from_window((1920, 1080), "glyph")

        assert result == expected


class TestTileDimensionScaling:
    """Test tile dimension scaling relationships."""

    def test_doubling_resolution_doubles_tile_size_glyph_mode(self):
        """Doubling window size doubles tile dimensions in glyph mode."""
        # Base resolution
        base_width, base_height = 1280, 720
        result_base = TileDimensionCalculator.calculate_from_window(
            (base_width, base_height), "glyph"
        )

        # Doubled resolution
        doubled_width, doubled_height = base_width * 2, base_height * 2
        result_doubled = TileDimensionCalculator.calculate_from_window(
            (doubled_width, doubled_height), "glyph"
        )

        # Tiles should also double (approximately, due to integer division)
        # Allow some tolerance for integer division rounding
        assert result_doubled[0] >= result_base[0] * 1.9
        assert result_doubled[1] >= result_base[1] * 1.9

    def test_graphics_mode_unaffected_by_resolution_scaling(self):
        """Graphics mode tiles don't scale with resolution."""
        result_1x = TileDimensionCalculator.calculate_from_window((1280, 720), "graphics")
        result_2x = TileDimensionCalculator.calculate_from_window((2560, 1440), "graphics")
        result_4x = TileDimensionCalculator.calculate_from_window((5120, 2880), "graphics")

        # All should be fixed at 64x64
        assert result_1x == result_2x == result_4x == (64, 64)


class TestTileDimensionConsistency:
    """Test consistency across different calculation paths."""

    def test_calculate_from_window_matches_direct_call_glyph(self):
        """calculate_from_window with 'glyph' matches _calc_glyph_mode."""
        window_size = (1920, 1080)

        result_wrapper = TileDimensionCalculator.calculate_from_window(window_size, "glyph")
        result_direct = TileDimensionCalculator._calc_glyph_mode(*window_size)

        assert result_wrapper == result_direct

    def test_calculate_from_window_matches_direct_call_graphics(self):
        """calculate_from_window with 'graphics' matches _calc_graphics_mode."""
        window_size = (1920, 1080)

        result_wrapper = TileDimensionCalculator.calculate_from_window(window_size, "graphics")
        result_direct = TileDimensionCalculator._calc_graphics_mode(*window_size)

        assert result_wrapper == result_direct

    def test_all_methods_return_tuples(self):
        """All calculation methods return tuples of two integers."""
        test_cases = [
            TileDimensionCalculator.calculate_from_window((1920, 1080), "glyph"),
            TileDimensionCalculator.calculate_from_window((1920, 1080), "graphics"),
            TileDimensionCalculator._calc_glyph_mode(1920, 1080),
            TileDimensionCalculator._calc_graphics_mode(1920, 1080),
            TileDimensionCalculator.validate_and_clamp(20, 20),
            TileDimensionCalculator.get_fallback_dimensions(),
        ]

        for result in test_cases:
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], int)
            assert isinstance(result[1], int)
