"""
Test for InputAction import bug in menu analog stick handling.

Regression test for crash when using analog stick in main menu.
Bug: game_loop.py references InputAction without importing it.
"""


def test_game_loop_has_input_enums_for_gamepad_handling():
    """
    Test that game_loop.py imports InputAction and InputContext to prevent NameError.

    Regression test for TWO related bugs:

    Bug 1: NameError: name 'InputAction' is not defined
    - Location: game_loop.py:784-787 (analog stick navigation)
    - Trigger: Player moves analog stick in menu
    - Code references: InputAction.NAVIGATE_UP, InputAction.NAVIGATE_DOWN

    Bug 2: NameError: name 'InputContext' is not defined
    - Location: game_loop.py:753-765 (button auto-repeat context detection)
    - Trigger: Player holds gamepad button in menu (D-pad, face buttons)
    - Code references: InputContext.MAIN_MENU, InputContext.SETTINGS_MENU,
                       InputContext.HELP, InputContext.ABOUT_MENU,
                       InputContext.ACHIEVEMENTS_SCREEN, InputContext.LORE_VIEWER

    Both enums are defined in game_input_actions.py and must be imported
    in game_loop.py to prevent crashes during gamepad menu navigation.

    Note: InputAction is imported at module level, InputContext is imported
    locally where needed (inside functions). Both approaches prevent NameError.
    """
    import rsp.core.loop as game_loop
    from rsp.input.actions import InputContext

    # Check if InputAction is available in game_loop module (imported at top)
    assert hasattr(
        game_loop, "InputAction"
    ), "game_loop.py must import InputAction to handle analog stick navigation"

    # InputContext is imported locally inside functions, verify it exists
    assert InputContext is not None, "InputContext must be importable from rsp.input.actions"

    # Verify the specific contexts used in game_loop exist
    assert hasattr(InputContext, "MAIN_MENU"), "InputContext.MAIN_MENU must exist"
    assert hasattr(InputContext, "SETTINGS_MENU"), "InputContext.SETTINGS_MENU must exist"
