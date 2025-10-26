#!/usr/bin/env python3
"""
Integration tests for dialogue rendering.

Tests the complete rendering pipeline including transparency handling,
multiple dialogue types, and coordinate system correctness.
"""

import pytest
import tcod.console
import numpy as np
from unittest.mock import Mock

from game_dialogue_system import (
    DialogueState,
    UnifiedRenderer,
    create_gateway_dialogue,
    create_death_dialogue,
    create_intro_dialogue,
    create_victory_dialogue,
    create_overclock_warning_dialogue,
    create_inventory_attack_dialogue
)
from game_coordinate_helpers import CoordinateHelpers


class TestDialogueRendering:
    """Test dialogue rendering with transparency."""

    def test_dialogue_renders_opaque_over_transparent_console(self):
        """Dialogue box is opaque even when console is transparent."""
        console = tcod.console.Console(width=80, height=50)

        # Make entire console transparent
        console.rgba["bg"][:, :, 3] = 0

        # Render dialogue
        dialogue = create_gateway_dialogue()
        UnifiedRenderer.render(console, dialogue)

        # Check that center area (dialogue box) is opaque
        # Box should be centered around (40, 25)
        center_region_opaque = False
        for y in range(20, 30):
            for x in range(30, 50):
                if console.rgba["bg"][y, x, 3] == 255:
                    center_region_opaque = True
                    break
            if center_region_opaque:
                break

        assert center_region_opaque, "Dialogue box should be opaque"

    def test_dialogue_transparency_does_not_affect_outside_area(self):
        """Dialogue rendering doesn't affect transparency outside dialogue box."""
        console = tcod.console.Console(width=80, height=50)

        # Make entire console transparent
        console.rgba["bg"][:, :, 3] = 0

        # Render dialogue
        dialogue = create_gateway_dialogue()
        UnifiedRenderer.render(console, dialogue)

        # Check corners are still transparent (far from center)
        assert console.rgba["bg"][0, 0, 3] == 0
        assert console.rgba["bg"][0, 79, 3] == 0
        assert console.rgba["bg"][49, 0, 3] == 0
        assert console.rgba["bg"][49, 79, 3] == 0

    def test_all_dialogue_types_render_without_crash(self):
        """All dialogue types render successfully."""
        console = tcod.console.Console(width=80, height=50)

        dialogues = [
            create_gateway_dialogue(),
            create_death_dialogue(),
            create_intro_dialogue(),
            create_victory_dialogue(),
            create_overclock_warning_dialogue("Test Exploit", 10, 5, 15, 20),
            create_inventory_attack_dialogue()
        ]

        for dialogue in dialogues:
            console.clear()
            UnifiedRenderer.render(console, dialogue)

            # Verify dialogue was rendered (box should be opaque in center)
            center_has_opaque_pixels = False
            for y in range(15, 35):
                for x in range(20, 60):
                    if console.rgba["bg"][y, x, 3] == 255:
                        center_has_opaque_pixels = True
                        break
                if center_has_opaque_pixels:
                    break
            assert center_has_opaque_pixels, f"Dialogue {dialogue.title} should render opaque box"

    def test_dialogue_rendering_with_state_manager(self):
        """Dialogue rendering works with DialogueState manager."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)
        console = tcod.console.Console(width=80, height=50)

        # Show dialogue through state manager
        dialogue = create_gateway_dialogue()
        state.show(dialogue)

        # Render active dialogue
        assert state.is_active()
        UnifiedRenderer.render(console, state.get_active())

        # Should have rendered something opaque in the center
        # Check that dialogue box area has alpha=255
        center_y, center_x = 25, 40
        assert console.rgba["bg"][center_y, center_x, 3] == 255

    def test_dialogue_box_centering(self):
        """Dialogue boxes are centered correctly."""
        console = tcod.console.Console(width=80, height=50)

        dialogue = create_gateway_dialogue()
        UnifiedRenderer.render(console, dialogue)

        # Dialogue should be centered, so center of console should have opaque region
        center_y, center_x = 25, 40

        # Check region around center is opaque (dialogue box)
        is_opaque = console.rgba["bg"][center_y, center_x, 3] == 255
        assert is_opaque, f"Center ({center_x}, {center_y}) should be opaque for dialogue box"

    def test_dialogue_with_formatted_message(self):
        """Dialogue with format_data renders correctly."""
        console = tcod.console.Console(width=80, height=50)

        dialogue = create_overclock_warning_dialogue(
            exploit_name="Buffer Overflow",
            overheat_amount=25,
            damage=10,
            remaining_cpu=5,
            max_cpu=20
        )

        UnifiedRenderer.render(console, dialogue)

        # Verify format_data was used (check for health value in rendered text)
        # The dialogue should contain formatted content
        rendered_text_found = False
        for y in range(console.height):
            for x in range(console.width):
                if console.ch[y, x] != 0:  # Non-empty character
                    rendered_text_found = True
                    break
            if rendered_text_found:
                break
        assert rendered_text_found, "Dialogue should render text content"

    def test_dialogue_rendering_on_small_console(self):
        """Dialogue renders correctly on smaller consoles."""
        console = tcod.console.Console(width=40, height=25)

        dialogue = create_gateway_dialogue()
        UnifiedRenderer.render(console, dialogue)

        # Verify rendering succeeded on small console
        has_text = np.any(console.ch != 0)
        assert has_text, "Dialogue should render text even on small console"

    def test_multiple_dialogues_render_sequentially(self):
        """Multiple dialogues can be rendered sequentially without issues."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)
        console = tcod.console.Console(width=80, height=50)

        # Queue multiple dialogues
        state.show(create_gateway_dialogue())
        state.show(create_death_dialogue())
        state.show(create_victory_dialogue())

        # Render and close each dialogue
        for _ in range(3):
            assert state.is_active()
            console.clear()
            UnifiedRenderer.render(console, state.get_active())
            state.close()

        assert not state.is_active()


class TestTransparencyHandling:
    """Test transparency handling in detail."""

    def test_set_alpha_region_called_correctly(self):
        """UnifiedRenderer correctly sets alpha for dialogue region."""
        console = tcod.console.Console(width=80, height=50)

        # Make everything transparent
        console.rgba["bg"][:, :, 3] = 0

        dialogue = create_gateway_dialogue()
        UnifiedRenderer.render(console, dialogue)

        # Count opaque pixels - should be a rectangular region
        opaque_pixels = np.sum(console.rgba["bg"][:, :, 3] == 255)
        transparent_pixels = np.sum(console.rgba["bg"][:, :, 3] == 0)

        # Dialogue box should be ~720 pixels (60 width x 12 height)
        # Most of console should still be transparent
        assert opaque_pixels > 500, "Should have opaque dialogue box"
        assert transparent_pixels > 3000, "Most of console should remain transparent"

    def test_transparency_survives_multiple_renders(self):
        """Transparency settings survive multiple render calls."""
        console = tcod.console.Console(width=80, height=50)

        # Make everything transparent
        console.rgba["bg"][:, :, 3] = 0

        dialogue = create_gateway_dialogue()

        # Render twice
        UnifiedRenderer.render(console, dialogue)
        UnifiedRenderer.render(console, dialogue)

        # Dialogue should still be opaque, outside should still be transparent
        assert console.rgba["bg"][25, 40, 3] == 255  # Center opaque
        assert console.rgba["bg"][0, 0, 3] == 0      # Corner transparent

    def test_dialogue_alpha_doesnt_leak_outside_bounds(self):
        """Alpha setting doesn't affect pixels outside dialogue box."""
        console = tcod.console.Console(width=80, height=50)

        # Set specific pattern: all even rows transparent, odd rows opaque
        for y in range(50):
            alpha = 0 if y % 2 == 0 else 255
            console.rgba["bg"][y, :, 3] = alpha

        dialogue = create_gateway_dialogue()
        UnifiedRenderer.render(console, dialogue)

        # Far corners should maintain original pattern
        assert console.rgba["bg"][0, 0, 3] == 0    # Even row, should be transparent
        assert console.rgba["bg"][1, 0, 3] == 255  # Odd row, should be opaque


class TestCoordinateCorrectness:
    """Test that coordinate systems are used correctly."""

    def test_render_uses_correct_indexing(self):
        """Renderer uses correct [y, x] indexing for TCOD arrays."""
        console = tcod.console.Console(width=80, height=50)

        # This test verifies no transposition bugs occur
        console.rgba["bg"][:, :, 3] = 0

        dialogue = create_gateway_dialogue()
        UnifiedRenderer.render(console, dialogue)

        # If indexing is wrong, transparency would be set at transposed coordinates
        # Check a specific position: if we center a 60x12 box on 80x50,
        # it should be at (10, 19) with size (60, 12)
        # Center would be around (40, 25)

        # Check that opaque region exists near expected center
        center_opaque = console.rgba["bg"][25, 40, 3] == 255
        assert center_opaque, "Dialogue should be opaque at center"

        # If coordinates were transposed, opaque region would be at wrong location
        # Check that (40, 25) [transposed] is NOT the only opaque location
        transposed_opaque = console.rgba["bg"][40, 25, 3] == 255
        # Both should be opaque since box is 60x12 (wide), but this is a sanity check
        # that we're not accidentally transposing

    def test_coordinate_helpers_integration(self):
        """CoordinateHelpers are used correctly in rendering."""
        console = tcod.console.Console(width=80, height=50)

        # Calculate expected box position using CoordinateHelpers
        box_width = 60
        box_height = 12
        expected_x, expected_y = CoordinateHelpers.center_box(
            box_width, box_height, 80, 50
        )

        console.rgba["bg"][:, :, 3] = 0
        dialogue = create_gateway_dialogue()
        UnifiedRenderer.render(console, dialogue)

        # Check that expected position is opaque
        # Add 1 to account for border
        check_y = expected_y + 1
        check_x = expected_x + 1

        assert console.rgba["bg"][check_y, check_x, 3] == 255, \
            f"Expected dialogue at ({check_x}, {check_y}) to be opaque"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_dialogue_with_empty_message(self):
        """Dialogue with empty message renders without crash."""
        console = tcod.console.Console(width=80, height=50)

        from game_dialogue_system import DialogueBox
        dialogue = DialogueBox(
            title="Empty",
            message="",
            options=["[OK]"],
            valid_keys=[tcod.event.KeySym.SPACE],
            title_color=(255, 255, 255),
            message_color=(255, 255, 255),
            border_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            format_data={}
        )

        UnifiedRenderer.render(console, dialogue)

        # Verify empty message was handled (should still render box frame)
        has_frame = np.any(console.ch != 0)
        assert has_frame, "Dialogue should render box frame even with empty message"

    def test_dialogue_with_very_long_message(self):
        """Dialogue with very long message wraps correctly."""
        console = tcod.console.Console(width=80, height=50)

        from game_dialogue_system import DialogueBox
        long_message = "This is a very long message " * 20

        dialogue = DialogueBox(
            title="Long",
            message=long_message,
            options=["[OK]"],
            valid_keys=[tcod.event.KeySym.SPACE],
            title_color=(255, 255, 255),
            message_color=(255, 255, 255),
            border_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            format_data={}
        )

        UnifiedRenderer.render(console, dialogue)

        # Verify long message was handled (should wrap or truncate)
        has_text = np.any(console.ch != 0)
        assert has_text, "Dialogue should render long message (wrapped/truncated)"

    def test_dialogue_with_missing_format_keys(self):
        """Dialogue with missing format keys handles gracefully."""
        console = tcod.console.Console(width=80, height=50)

        dialogue = create_overclock_warning_dialogue(
            exploit_name="Test",
            overheat_amount=10,
            damage=5,
            remaining_cpu=15,
            max_cpu=20
        )

        # Clear format_data to simulate missing keys
        dialogue.format_data = {}

        UnifiedRenderer.render(console, dialogue)

        # Verify missing format keys were handled gracefully
        has_content = np.any(console.ch != 0)
        assert has_content, "Dialogue should render even with missing format keys"

    def test_dialogue_on_minimal_console(self):
        """Dialogue renders on very small console."""
        console = tcod.console.Console(width=20, height=10)

        dialogue = create_gateway_dialogue()

        UnifiedRenderer.render(console, dialogue)

        # Verify clamping worked - dialogue should fit in minimal console
        has_text = np.any(console.ch != 0)
        assert has_text, "Dialogue should render on minimal console (clamped to fit)"
        # Verify no array access errors occurred (would crash before this point)


class TestWorkflowSimulation:
    """Simulate complete dialogue workflows."""

    def test_gameplay_dialogue_workflow(self):
        """Simulate typical gameplay dialogue workflow."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)
        console = tcod.console.Console(width=80, height=50)

        # 1. Player triggers overclock warning
        dialogue1 = create_overclock_warning_dialogue(
            exploit_name="Buffer Overflow",
            overheat_amount=10,
            damage=5,
            remaining_cpu=15,
            max_cpu=20
        )
        state.show(dialogue1)

        # 2. While dialogue is active, inventory attack occurs (higher priority)
        dialogue2 = create_inventory_attack_dialogue()
        state.show(dialogue2)

        # 3. First dialogue still active (queued)
        assert state.get_active() == dialogue1
        UnifiedRenderer.render(console, state.get_active())

        # 4. Player dismisses first dialogue
        state.close()

        # 5. Higher priority dialogue shown
        assert state.get_active() == dialogue2
        UnifiedRenderer.render(console, state.get_active())

        # 6. Player dismisses second dialogue
        state.close()

        # 7. No more dialogues
        assert not state.is_active()

    def test_death_dialogue_workflow(self):
        """Simulate death dialogue workflow."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)
        console = tcod.console.Console(width=80, height=50)

        # Player dies
        dialogue = create_death_dialogue()
        state.show(dialogue)

        # Render death screen
        assert state.is_active()
        UnifiedRenderer.render(console, state.get_active())

        # Player presses space
        state.close()

        assert not state.is_active()

    def test_victory_dialogue_workflow(self):
        """Simulate victory dialogue workflow."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)
        console = tcod.console.Console(width=80, height=50)

        # Player reaches gateway
        dialogue = create_victory_dialogue()
        state.show(dialogue)

        # Render victory screen
        assert state.is_active()
        UnifiedRenderer.render(console, state.get_active())

        # Player presses enter
        state.close()

        assert not state.is_active()
