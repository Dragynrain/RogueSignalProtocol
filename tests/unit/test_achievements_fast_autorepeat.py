"""
Test that auto-repeat is faster in achievements screen for better scrolling.

The achievements screen has many items to scroll through, so holding down
arrow keys/dpad should repeat ~2x faster than in other contexts.
"""

from rsp.core.config import GameConfig
from rsp.input.actions import InputContext
from rsp.input.gamepad import GamepadInputHandler
from rsp.input.mappings import InputMapper


class TestAchievementsFastAutoRepeat:
    """Test achievements screen has faster auto-repeat rate."""

    def test_achievements_repeat_rate_is_faster(self):
        """Achievements screen should have ~2x faster repeat rate than normal."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Get repeat rate for achievements context
        achievements_rate = handler.get_repeat_rate(InputContext.ACHIEVEMENTS_SCREEN)

        # Get default repeat rate
        default_rate = handler.get_repeat_rate(InputContext.GAMEPLAY)

        # Achievements should be ~2x faster (smaller number = faster repeat)
        assert (
            achievements_rate < default_rate
        ), "Achievements repeat rate should be faster than default"

        # Should be approximately half (within 10ms tolerance)
        expected_achievements_rate = default_rate / 2.0
        assert (
            abs(achievements_rate - expected_achievements_rate) < 0.01
        ), f"Expected {expected_achievements_rate}s, got {achievements_rate}s"

    def test_achievements_repeat_rate_value(self):
        """Achievements repeat rate should match BUTTON_REPEAT_RATE_FAST config."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        achievements_rate = handler.get_repeat_rate(InputContext.ACHIEVEMENTS_SCREEN)

        # Should match fast repeat rate from config
        assert (
            achievements_rate == GameConfig.BUTTON_REPEAT_RATE_FAST
        ), f"Expected {GameConfig.BUTTON_REPEAT_RATE_FAST}s repeat rate, got {achievements_rate}s"

    def test_default_repeat_rate_unchanged(self):
        """Default repeat rate should match BUTTON_REPEAT_RATE config."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        default_rate = handler.get_repeat_rate(InputContext.GAMEPLAY)

        assert (
            default_rate == GameConfig.BUTTON_REPEAT_RATE
        ), f"Default repeat rate should be {GameConfig.BUTTON_REPEAT_RATE}s, got {default_rate}s"

    def test_lore_viewer_has_normal_repeat(self):
        """Lore viewer should have normal repeat rate (not sped up)."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        lore_rate = handler.get_repeat_rate(InputContext.LORE_VIEWER)

        # Should be normal speed
        assert (
            lore_rate == GameConfig.BUTTON_REPEAT_RATE
        ), f"Lore viewer should have normal repeat rate ({GameConfig.BUTTON_REPEAT_RATE}s), got {lore_rate}s"

    def test_initial_delay_unchanged(self):
        """Initial delay before repeat starts should match config."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Initial delay should be the same across all contexts
        initial_delay = handler.get_initial_delay(InputContext.ACHIEVEMENTS_SCREEN)

        assert (
            initial_delay == GameConfig.BUTTON_REPEAT_INITIAL_DELAY
        ), f"Initial delay should be {GameConfig.BUTTON_REPEAT_INITIAL_DELAY}s, got {initial_delay}s"
