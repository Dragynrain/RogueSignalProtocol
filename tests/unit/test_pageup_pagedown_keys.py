"""
Test PageUp/PageDown keyboard key mappings.

Design: PageUp/PageDown map to DIAGONAL MOVEMENT (laptop-friendly roguelike layout),
NOT to page navigation. This matches standard roguelike conventions where the
navigation cluster mirrors numpad diagonals:

    Physical:  [Home][PgUp]     Roguelike:  [NW][NE]
               [End ][PgDn]                 [SW][SE]

Fast scrolling in menus is handled by:
- Mouse wheel
- Gamepad shoulder buttons (LB/RB)
- Custom key bindings (user can rebind)
"""

import tcod.event

from rsp.input.actions import InputAction, InputContext
from rsp.input.mappings import InputMapper


class TestPageUpDownKeyboardMappings:
    """Test PageUp/PageDown keyboard key mappings match laptop-friendly roguelike design."""

    def test_pageup_maps_to_diagonal_movement(self):
        """PageUp key maps to MOVE_NORTHEAST (laptop diagonal, not page nav)."""
        mapper = InputMapper()

        action = mapper.get_action_for_key(tcod.event.KeySym.PAGEUP)

        assert (
            action == InputAction.MOVE_NORTHEAST
        ), "PageUp should map to MOVE_NORTHEAST (laptop-friendly diagonal)"

    def test_pagedown_maps_to_diagonal_movement(self):
        """PageDown key maps to MOVE_SOUTHEAST (laptop diagonal, not page nav)."""
        mapper = InputMapper()

        action = mapper.get_action_for_key(tcod.event.KeySym.PAGEDOWN)

        assert (
            action == InputAction.MOVE_SOUTHEAST
        ), "PageDown should map to MOVE_SOUTHEAST (laptop-friendly diagonal)"

    def test_home_maps_to_northwest(self):
        """Home key maps to MOVE_NORTHWEST (completes laptop diagonal cluster)."""
        mapper = InputMapper()

        action = mapper.get_action_for_key(tcod.event.KeySym.HOME)

        assert action == InputAction.MOVE_NORTHWEST, "Home should map to MOVE_NORTHWEST"

    def test_end_maps_to_southwest(self):
        """End key maps to MOVE_SOUTHWEST (completes laptop diagonal cluster)."""
        mapper = InputMapper()

        action = mapper.get_action_for_key(tcod.event.KeySym.END)

        assert action == InputAction.MOVE_SOUTHWEST, "End should map to MOVE_SOUTHWEST"

    def test_laptop_diagonal_cluster_complete(self):
        """All four laptop diagonal keys form a complete movement cluster."""
        mapper = InputMapper()

        # Verify the complete laptop diagonal cluster
        assert mapper.get_action_for_key(tcod.event.KeySym.HOME) == InputAction.MOVE_NORTHWEST
        assert mapper.get_action_for_key(tcod.event.KeySym.PAGEUP) == InputAction.MOVE_NORTHEAST
        assert mapper.get_action_for_key(tcod.event.KeySym.END) == InputAction.MOVE_SOUTHWEST
        assert mapper.get_action_for_key(tcod.event.KeySym.PAGEDOWN) == InputAction.MOVE_SOUTHEAST

    def test_context_does_not_change_keyboard_mapping(self):
        """Keyboard mappings are global - context doesn't change PageUp/PageDown behavior.

        Unlike gamepad bindings which are context-sensitive, keyboard mappings
        are consistent across all contexts. PageUp always means diagonal movement.
        """
        mapper = InputMapper()

        # Same mapping in gameplay and menu contexts
        gameplay_action = mapper.get_action_for_key(tcod.event.KeySym.PAGEUP, InputContext.GAMEPLAY)
        menu_action = mapper.get_action_for_key(
            tcod.event.KeySym.PAGEUP, InputContext.ACHIEVEMENTS_SCREEN
        )

        assert gameplay_action == menu_action == InputAction.MOVE_NORTHEAST
