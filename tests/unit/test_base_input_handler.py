"""
Unit tests for BaseInputHandler (game_input_base.py)

Tests the unified input handling architecture.
Target: ≥90% line coverage, ≥80% branch coverage
"""

from unittest.mock import Mock, patch

import pytest
import tcod.event

from rsp.input.actions import InputAction, InputContext
from rsp.input.base import BaseInputHandler
from rsp.input.gamepad import GamepadInputHandler
from rsp.input.mappings import InputMapper

# ============================================================================
# Test Fixtures
# ============================================================================


class ConcreteInputHandler(BaseInputHandler):
    """Concrete implementation for testing abstract BaseInputHandler"""

    def __init__(self, game=None, renderer=None, test_context=InputContext.MAIN_MENU):
        super().__init__(game, renderer)
        self.test_context = test_context
        self.executed_actions = []

    def get_context(self) -> InputContext:
        return self.test_context

    def execute_action(self, action: InputAction) -> str:
        """Returns str for testing (menu-like behavior)"""
        self.executed_actions.append(action)
        if action == InputAction.CONFIRM:
            return "confirmed"
        elif action == InputAction.CANCEL:
            return "cancelled"
        elif action == InputAction.NAVIGATE_UP:
            return "up"
        elif action == InputAction.NAVIGATE_DOWN:
            return "down"
        return "action_executed"

    def get_default_return(self) -> str:
        return ""


class GameplayTestHandler(BaseInputHandler):
    """Test handler that returns bool (gameplay-like behavior)"""

    def __init__(self, game=None, renderer=None):
        super().__init__(game, renderer)
        self.executed_actions = []

    def get_context(self) -> InputContext:
        return InputContext.GAMEPLAY

    def execute_action(self, action: InputAction) -> bool:
        self.executed_actions.append(action)
        return True

    def get_default_return(self) -> bool:
        return True


@pytest.fixture
def mock_game():
    """Create a mock game instance"""
    game = Mock()
    game.settings = Mock()
    game.settings.custom_keyboard_bindings = {}
    game.settings.custom_gamepad_bindings = {}
    return game


@pytest.fixture
def mock_renderer():
    """Create a mock renderer instance"""
    return Mock()


@pytest.fixture
def handler(mock_game, mock_renderer):
    """Create a concrete test handler"""
    return ConcreteInputHandler(mock_game, mock_renderer)


@pytest.fixture
def gameplay_handler(mock_game, mock_renderer):
    """Create a gameplay test handler"""
    return GameplayTestHandler(mock_game, mock_renderer)


# ============================================================================
# Test BaseInputHandler Initialization
# ============================================================================


def test_initialization_creates_per_handler_instances(mock_game, mock_renderer):
    """Each handler should get its own InputMapper and GamepadHandler"""
    handler1 = ConcreteInputHandler(mock_game, mock_renderer)
    handler2 = ConcreteInputHandler(mock_game, mock_renderer)

    # Each handler has its own instances
    assert handler1.input_mapper is not handler2.input_mapper
    assert handler1.gamepad_handler is not handler2.gamepad_handler

    # Each instance is properly created
    assert isinstance(handler1.input_mapper, InputMapper)
    assert isinstance(handler1.gamepad_handler, GamepadInputHandler)
    assert isinstance(handler2.input_mapper, InputMapper)
    assert isinstance(handler2.gamepad_handler, GamepadInputHandler)


def test_initialization_without_game():
    """Handler should work without game (for menus)"""
    handler = ConcreteInputHandler(game=None, renderer=None)

    assert handler.game is None
    assert handler.renderer is None
    assert isinstance(handler.input_mapper, InputMapper)
    assert isinstance(handler.gamepad_handler, GamepadInputHandler)


def test_initialization_loads_custom_bindings(mock_game, mock_renderer):
    """Handler should load custom bindings from game.settings"""
    mock_game.settings.custom_keyboard_bindings = {tcod.event.KeySym.W: InputAction.MOVE_NORTH}
    mock_game.settings.custom_gamepad_bindings = {0: InputAction.CONFIRM}

    with patch.object(InputMapper, "load_custom_bindings") as mock_load:
        handler = ConcreteInputHandler(mock_game, mock_renderer)
        mock_load.assert_called_once()


def test_gamepad_handler_gets_game_ref(mock_game, mock_renderer):
    """GamepadHandler should receive the game reference"""
    handler = ConcreteInputHandler(mock_game, mock_renderer)

    # Verify gamepad_handler has correct game reference
    assert handler.gamepad_handler.game is mock_game


# ============================================================================
# Test Keyboard Input Handling
# ============================================================================


def test_handle_input_keyboard_event(handler):
    """KeyDown event should map to InputAction and execute"""
    # Simulate pressing ESC (mapped to CANCEL)
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.ESCAPE,
        sym=tcod.event.KeySym.ESCAPE,
        mod=tcod.event.Modifier.NONE,
    )

    # Mock the action mapping
    handler.input_mapper.get_action_for_key = Mock(return_value=InputAction.CANCEL)

    result = handler.handle_input(event)

    # Verify action was mapped with context and modifier, then executed
    handler.input_mapper.get_action_for_key.assert_called_once_with(
        event.sym, InputContext.MAIN_MENU, tcod.event.Modifier.NONE
    )
    assert InputAction.CANCEL in handler.executed_actions
    assert result == "cancelled"


def test_handle_input_keyboard_unmapped_key(handler):
    """Unmapped key should return default value"""
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.F12, sym=tcod.event.KeySym.F12, mod=tcod.event.Modifier.NONE
    )

    # Mock returning None (unmapped key)
    handler.input_mapper.get_action_for_key = Mock(return_value=None)

    result = handler.handle_input(event)

    # Should return default without executing action
    assert len(handler.executed_actions) == 0
    assert result == ""


# ============================================================================
# Test Gamepad Button Input Handling
# ============================================================================


def test_handle_input_gamepad_button(handler):
    """ControllerButton event should map to InputAction and execute"""
    # Simulate pressing A button
    import tcod.sdl.joystick

    event = tcod.event.ControllerButton(
        type="CONTROLLERBUTTONDOWN",
        which=0,
        button=tcod.sdl.joystick.ControllerButton.A,
        pressed=True,
    )

    # Mock the gamepad handler
    handler.gamepad_handler.handle_button_event = Mock(return_value=InputAction.CONFIRM)

    result = handler.handle_input(event)

    # Verify action was mapped and executed
    handler.gamepad_handler.handle_button_event.assert_called_once_with(
        event, InputContext.MAIN_MENU
    )
    assert InputAction.CONFIRM in handler.executed_actions
    assert result == "confirmed"


def test_handle_input_gamepad_buttonup(handler):
    """BUTTONUP events should be processed (no action returned)"""
    import tcod.sdl.joystick

    event = tcod.event.ControllerButton(
        type="CONTROLLERBUTTONUP",
        which=0,
        button=tcod.sdl.joystick.ControllerButton.A,
        pressed=False,
    )

    # Mock returning None (BUTTONUP clears state, doesn't generate action)
    handler.gamepad_handler.handle_button_event = Mock(return_value=None)

    result = handler.handle_input(event)

    # BUTTONUP should be processed but not execute action
    handler.gamepad_handler.handle_button_event.assert_called_once()
    assert len(handler.executed_actions) == 0
    assert result == ""


# ============================================================================
# Test Gamepad Axis Input Handling
# ============================================================================


def test_handle_input_gamepad_axis(handler):
    """ControllerAxis event should map to InputAction and execute"""
    # Simulate left stick up
    import tcod.sdl.joystick

    event = tcod.event.ControllerAxis(
        type="CONTROLLERAXISMOTION",
        which=0,
        axis=tcod.sdl.joystick.ControllerAxis.LEFTY,
        value=-32000,
    )

    # Mock the axis handler
    handler.gamepad_handler.handle_axis_event = Mock(return_value=InputAction.NAVIGATE_UP)

    result = handler.handle_input(event)

    # Verify action was mapped and executed
    handler.gamepad_handler.handle_axis_event.assert_called_once_with(event, InputContext.MAIN_MENU)
    assert InputAction.NAVIGATE_UP in handler.executed_actions
    assert result == "up"


def test_handle_input_gamepad_axis_no_action(handler):
    """Axis events below threshold should not generate action"""
    import tcod.sdl.joystick

    event = tcod.event.ControllerAxis(
        type="CONTROLLERAXISMOTION",
        which=0,
        axis=tcod.sdl.joystick.ControllerAxis.LEFTX,
        value=100,  # Below threshold
    )

    # Mock returning None (below threshold)
    handler.gamepad_handler.handle_axis_event = Mock(return_value=None)

    result = handler.handle_input(event)

    # Should return default without executing action
    assert len(handler.executed_actions) == 0
    assert result == ""


# ============================================================================
# Test Mouse Input Handling
# ============================================================================


def test_handle_input_mouse_motion(handler):
    """MouseMotion event should call handle_mouse_motion()"""
    event = Mock(spec=tcod.event.MouseMotion)
    event.position = Mock()
    event.position.x = 100
    event.position.y = 200

    # Override handle_mouse_motion to track calls
    handler.handle_mouse_motion = Mock(return_value="mouse_moved")

    result = handler.handle_input(event)

    handler.handle_mouse_motion.assert_called_once_with(event)
    assert result == "mouse_moved"


def test_handle_input_mouse_click_left(handler):
    """Left click should call handle_left_click()"""
    event = Mock(spec=tcod.event.MouseButtonDown)
    event.button = tcod.event.MouseButton.LEFT
    event.position = Mock()
    event.position.x = 100
    event.position.y = 200

    # Override to track calls
    handler.handle_left_click = Mock(return_value="clicked")

    result = handler.handle_input(event)

    handler.handle_left_click.assert_called_once_with(event)
    assert result == "clicked"


def test_handle_input_mouse_click_right(handler):
    """Right click should call handle_right_click()"""
    event = Mock(spec=tcod.event.MouseButtonDown)
    event.button = tcod.event.MouseButton.RIGHT
    event.position = Mock()
    event.position.x = 100
    event.position.y = 200

    # Override to track calls
    handler.handle_right_click = Mock(return_value="right_clicked")

    result = handler.handle_input(event)

    handler.handle_right_click.assert_called_once_with(event)
    assert result == "right_clicked"


def test_handle_input_mouse_wheel(handler):
    """Mouse wheel should call handle_mouse_wheel()"""
    event = Mock(spec=tcod.event.MouseWheel)
    event.x = 0
    event.y = -1  # Scroll down

    # Override to track calls
    handler.handle_mouse_wheel = Mock(return_value="scrolled")

    result = handler.handle_input(event)

    handler.handle_mouse_wheel.assert_called_once_with(event)
    assert result == "scrolled"


# ============================================================================
# Test Mouse Handling in Headless Mode
# ============================================================================


def test_handle_mouse_motion_headless_mode():
    """Mouse motion in headless mode should return default"""
    handler = ConcreteInputHandler(game=None, renderer=None)

    event = Mock(spec=tcod.event.MouseMotion)
    event.position = Mock()
    event.position.x = 100
    event.position.y = 200

    result = handler.handle_mouse_motion(event)

    # Should return default without crashing
    assert result == ""


def test_handle_left_click_headless_mode():
    """Left click in headless mode should return default"""
    handler = ConcreteInputHandler(game=None, renderer=None)

    event = Mock(spec=tcod.event.MouseButtonDown)
    event.button = tcod.event.MouseButton.LEFT
    event.position = Mock()
    event.position.x = 100
    event.position.y = 200

    result = handler.handle_left_click(event)
    assert result == ""


def test_handle_right_click_headless_mode():
    """Right click in headless mode should return default"""
    handler = ConcreteInputHandler(game=None, renderer=None)

    event = Mock(spec=tcod.event.MouseButtonDown)
    event.button = tcod.event.MouseButton.RIGHT
    event.position = Mock()
    event.position.x = 100
    event.position.y = 200

    result = handler.handle_right_click(event)
    assert result == ""


def test_handle_mouse_wheel_headless_mode():
    """Mouse wheel in headless mode should return default"""
    handler = ConcreteInputHandler(game=None, renderer=None)

    event = Mock(spec=tcod.event.MouseWheel)
    event.x = 0
    event.y = -1

    result = handler.handle_mouse_wheel(event)
    assert result == ""


# ============================================================================
# Test Error Handling
# ============================================================================


def test_execute_action_attribute_error_handling(handler):
    """AttributeError in execute_action should be caught and logged"""

    def raising_execute_action(action):
        raise AttributeError("Wrong context")

    handler.execute_action = raising_execute_action

    # Mock keyboard event
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.ESCAPE,
        sym=tcod.event.KeySym.ESCAPE,
        mod=tcod.event.Modifier.NONE,
    )
    handler.input_mapper.get_action_for_key = Mock(return_value=InputAction.CANCEL)

    with patch("logging.error") as mock_log:
        result = handler.handle_input(event)

        # Should log error and return default
        assert mock_log.called
        assert result == ""


def test_execute_action_exception_handling(handler):
    """General exception in execute_action should be caught and logged"""

    def raising_execute_action(action):
        raise RuntimeError("Unexpected error")

    handler.execute_action = raising_execute_action

    # Mock keyboard event
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.ESCAPE,
        sym=tcod.event.KeySym.ESCAPE,
        mod=tcod.event.Modifier.NONE,
    )
    handler.input_mapper.get_action_for_key = Mock(return_value=InputAction.CANCEL)

    with patch("logging.error") as mock_log:
        result = handler.handle_input(event)

        # Should log error with traceback and return default
        assert mock_log.called
        assert result == ""


# ============================================================================
# Test Unknown Event Types
# ============================================================================


def test_handle_input_unknown_event(handler):
    """Unknown event types should return default value"""
    # Create a mock event that doesn't match any isinstance checks
    event = Mock()
    event.__class__.__name__ = "UnknownEvent"

    result = handler.handle_input(event)

    # Should return default without crashing
    assert result == ""
    assert len(handler.executed_actions) == 0


def test_handle_input_none_event(handler):
    """None event should return default value"""
    result = handler.handle_input(None)

    assert result == ""
    assert len(handler.executed_actions) == 0


# ============================================================================
# Test Return Types (str vs bool)
# ============================================================================


def test_menu_handler_returns_str(handler):
    """Menu-like handlers should return str"""
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.ESCAPE,
        sym=tcod.event.KeySym.ESCAPE,
        mod=tcod.event.Modifier.NONE,
    )
    handler.input_mapper.get_action_for_key = Mock(return_value=InputAction.CANCEL)

    result = handler.handle_input(event)

    assert isinstance(result, str)
    assert result == "cancelled"


def test_gameplay_handler_returns_bool(gameplay_handler):
    """Gameplay-like handlers should return bool"""
    event = tcod.event.KeyDown(
        scancode=tcod.event.Scancode.W, sym=tcod.event.KeySym.W, mod=tcod.event.Modifier.NONE
    )
    gameplay_handler.input_mapper.get_action_for_key = Mock(return_value=InputAction.MOVE_NORTH)

    result = gameplay_handler.handle_input(event)

    assert isinstance(result, bool)
    assert result is True


# ============================================================================
# Test Context Switching
# ============================================================================


def test_get_context_called_for_gamepad_events(handler):
    """get_context() should be called for gamepad events"""
    import tcod.sdl.joystick

    handler.get_context = Mock(return_value=InputContext.MAIN_MENU)
    handler.gamepad_handler.handle_button_event = Mock(return_value=None)

    event = tcod.event.ControllerButton(
        type="CONTROLLERBUTTONDOWN",
        which=0,
        button=tcod.sdl.joystick.ControllerButton.A,
        pressed=True,
    )

    handler.handle_input(event)

    # get_context() should be called to pass to gamepad handler
    handler.get_context.assert_called_once()


def test_get_context_called_for_axis_events(handler):
    """get_context() should be called for axis events"""
    import tcod.sdl.joystick

    handler.get_context = Mock(return_value=InputContext.MAIN_MENU)
    handler.gamepad_handler.handle_axis_event = Mock(return_value=None)

    event = tcod.event.ControllerAxis(
        type="CONTROLLERAXISMOTION", which=0, axis=tcod.sdl.joystick.ControllerAxis.LEFTX, value=0
    )

    handler.handle_input(event)

    # get_context() should be called to pass to gamepad handler
    handler.get_context.assert_called_once()


# ============================================================================
# Test Abstract Methods
# ============================================================================


def test_abstract_get_context_must_be_implemented():
    """Subclasses must implement get_context() - ABC enforces at instantiation"""

    class IncompleteHandler(BaseInputHandler):
        def execute_action(self, action):
            return ""

        def get_default_return(self):
            return ""

    # ABC prevents instantiation without all abstract methods
    with pytest.raises(TypeError, match="get_context"):
        IncompleteHandler()


def test_abstract_execute_action_must_be_implemented():
    """Subclasses must implement execute_action() - ABC enforces at instantiation"""

    class IncompleteHandler(BaseInputHandler):
        def get_context(self):
            return InputContext.MAIN_MENU

        def get_default_return(self):
            return ""

    # ABC prevents instantiation without all abstract methods
    with pytest.raises(TypeError, match="execute_action"):
        IncompleteHandler()


def test_abstract_get_default_return_must_be_implemented():
    """Subclasses must implement get_default_return() - ABC enforces at instantiation"""

    class IncompleteHandler(BaseInputHandler):
        def get_context(self):
            return InputContext.MAIN_MENU

        def execute_action(self, action):
            return ""

    # ABC prevents instantiation without all abstract methods
    with pytest.raises(TypeError, match="get_default_return"):
        IncompleteHandler()
