"""
game_help_hints.py - Dynamic Help Text Hints

Provides functions for generating dynamic help text that reflects current
key/button bindings. Used by menus and screens to show context-appropriate
navigation hints at the bottom of the screen.

FORMATTING RULES (CONSISTENT EVERYWHERE):
- Full format: "Label: Value" with colon+space (e.g., "Navigate: ↑↓")
- Compact format: "Label:Value" no space (e.g., "↑↓:Nav")
- Section separator: Double space "  "
- Key alternatives use "/" (e.g., "LB/RB" for same action)
- NEVER mix keyboard and gamepad in same string

WARNING: Unicode arrows (arrow symbols) are used in UI strings returned by
these functions. These are rendered via TCOD and are safe for display.
NEVER pass these strings to logging.debug/info/error() - Windows crashes
on Unicode in log output. Use ASCII alternatives like [UP], [DOWN] in logs.
"""

from rsp.input.actions import InputAction, InputContext
from rsp.input.device_tracker import InputDeviceType, get_last_device
from rsp.input.mappings import InputMapper

# Module-level mapper instance for use in static contexts
_default_mapper = None


def _get_mapper(mapper: InputMapper | None = None) -> InputMapper:
    """Get the InputMapper to use for hint generation."""
    global _default_mapper
    if mapper is not None:
        return mapper
    if _default_mapper is None:
        _default_mapper = InputMapper()
    return _default_mapper


# ============================================================================
# DEVICE-AWARE HINT PRIMITIVES
# ============================================================================


def get_confirm_hint_for_device(
    context: InputContext,
    device: InputDeviceType | None = None,
    mapper: InputMapper | None = None,
) -> str:
    """Get confirm key/button for current device."""
    m = _get_mapper(mapper)
    device = device or get_last_device()
    if device == InputDeviceType.GAMEPAD:
        return m.get_button_hint(InputAction.CONFIRM, context)
    return m.get_key_hint(InputAction.CONFIRM)


def get_cancel_hint_for_device(
    context: InputContext,
    device: InputDeviceType | None = None,
    mapper: InputMapper | None = None,
) -> str:
    """Get cancel key/button for current device."""
    m = _get_mapper(mapper)
    device = device or get_last_device()
    if device == InputDeviceType.GAMEPAD:
        return m.get_button_hint(InputAction.CANCEL, context)
    return m.get_key_hint(InputAction.CANCEL)


def get_nav_hint_for_device(device: InputDeviceType | None = None) -> str:
    """Get navigation hint for current device."""
    device = device or get_last_device()
    if device == InputDeviceType.GAMEPAD:
        return "D-Pad"
    return "\u2191\u2193"  # ↑↓


def get_page_hint_for_device(device: InputDeviceType | None = None) -> str:
    """Get page navigation hint for current device."""
    device = device or get_last_device()
    if device == InputDeviceType.GAMEPAD:
        return "LB/RB"
    return "\u2190\u2192"  # ←→


def get_scroll_hint_for_device(device: InputDeviceType | None = None) -> str:
    """Get scroll hint for current device (includes wheel for keyboard)."""
    device = device or get_last_device()
    if device == InputDeviceType.GAMEPAD:
        return "D-Pad"
    return "\u2191\u2193/Wheel"  # ↑↓/Wheel


# ============================================================================
# SCREEN HELP STRINGS (FULL FORMAT)
# Format: "Label: Value  Label: Value  Label: Value"
# ============================================================================


def get_menu_help(context: InputContext, mapper: InputMapper | None = None) -> str:
    """Standard menu help: Navigate/Select/Back."""
    nav = get_nav_hint_for_device()
    confirm = get_confirm_hint_for_device(context, mapper=mapper)
    cancel = get_cancel_hint_for_device(context, mapper=mapper)
    return f"Navigate: {nav}  Select: {confirm}  Back: {cancel}"


def get_main_menu_help(use_graphics_mode: bool, mapper: InputMapper | None = None) -> str:
    """Main menu help (no Back option)."""
    nav = get_nav_hint_for_device()
    confirm = get_confirm_hint_for_device(InputContext.MAIN_MENU, mapper=mapper)
    if use_graphics_mode:
        return f"Nav: {nav}  Select: {confirm}"
    return f"Navigate: {nav}  Select: {confirm}"


def get_about_menu_help(use_graphics_mode: bool, mapper: InputMapper | None = None) -> str:
    """About menu help: Navigate/Open/Back."""
    nav = get_nav_hint_for_device()
    confirm = get_confirm_hint_for_device(InputContext.ABOUT_MENU, mapper=mapper)
    cancel = get_cancel_hint_for_device(InputContext.ABOUT_MENU, mapper=mapper)
    if use_graphics_mode:
        # Compact: 26 char max - "↑↓ Open:Enter Back:ESC" = 22
        return f"{nav} Open:{confirm} Back:{cancel}"
    return f"Navigate: {nav}  Open: {confirm}  Back: {cancel}"


def get_settings_menu_help(use_graphics_mode: bool, mapper: InputMapper | None = None) -> str:
    """Settings menu help: Navigate/Adjust/Back."""
    nav = get_nav_hint_for_device()
    cancel = get_cancel_hint_for_device(InputContext.SETTINGS_MENU, mapper=mapper)
    adj = "\u2190\u2192"  # ←→ for both (d-pad left/right or arrow keys)
    if use_graphics_mode:
        # Compact: 26 char max - "↑↓ Adj:←→ Back:ESC" = 19
        return f"{nav} Adj:{adj} Back:{cancel}"
    return f"Navigate: {nav}  Adjust: {adj}  Back: {cancel}"


def get_controls_hub_help(use_graphics_mode: bool, mapper: InputMapper | None = None) -> str:
    """Controls menu hub help."""
    nav = get_nav_hint_for_device()
    confirm = get_confirm_hint_for_device(InputContext.CONTROLS_MENU, mapper=mapper)
    cancel = get_cancel_hint_for_device(InputContext.CONTROLS_MENU, mapper=mapper)
    if use_graphics_mode:
        # Compact: 26 char max - "↑↓ Sel:Enter Back:ESC" = 21
        return f"{nav} Sel:{confirm} Back:{cancel}"
    return f"Navigate: {nav}  Select: {confirm}  Back: {cancel}"


def get_inventory_help(mapper: InputMapper | None = None) -> str:
    """Inventory screen help."""
    nav = get_nav_hint_for_device()
    confirm = get_confirm_hint_for_device(InputContext.INVENTORY, mapper=mapper)
    cancel = get_cancel_hint_for_device(InputContext.INVENTORY, mapper=mapper)
    return f"Navigate: {nav}  Use: {confirm}  Close: {cancel}"


def get_achievements_help(mapper: InputMapper | None = None) -> str:
    """Achievements screen help."""
    scroll = get_scroll_hint_for_device()
    cancel = get_cancel_hint_for_device(InputContext.ACHIEVEMENTS_SCREEN, mapper=mapper)
    return f"Scroll: {scroll}  Back: {cancel}"


def get_help_screen_help(mapper: InputMapper | None = None) -> str:
    """Help screen (paged) help."""
    pages = get_page_hint_for_device()
    scroll = get_scroll_hint_for_device()
    cancel = get_cancel_hint_for_device(InputContext.HELP, mapper=mapper)
    return f"Pages: {pages}  Scroll: {scroll}  Back: {cancel}"


def get_lore_viewer_help(mode: str, mapper: InputMapper | None = None) -> str:
    """Lore viewer help for different modes."""
    cancel = get_cancel_hint_for_device(InputContext.LORE_VIEWER, mapper=mapper)
    confirm = get_confirm_hint_for_device(InputContext.LORE_VIEWER, mapper=mapper)
    nav = get_nav_hint_for_device()
    device = get_last_device()

    if mode == "empty":
        # Just back option when no lore entries
        if device == InputDeviceType.GAMEPAD:
            return f"Back: {cancel}"
        return f"Back: {cancel} or Right-Click"
    elif mode == "list":
        # List navigation mode
        if device == InputDeviceType.GAMEPAD:
            return f"Navigate: {nav}  Read: {confirm}  Back: {cancel}"
        return f"Navigate: {nav}  Read: {confirm}  Back: {cancel} or Right-Click"
    else:
        # Reading mode
        return f"Close: {confirm}  Back: {cancel}"


def get_scrollable_help(context: InputContext, mapper: InputMapper | None = None) -> str:
    """Generic scrollable list help."""
    scroll = get_scroll_hint_for_device()
    cancel = get_cancel_hint_for_device(context, mapper=mapper)
    return f"Scroll: {scroll}  Back: {cancel}"


def get_paged_help(context: InputContext, mapper: InputMapper | None = None) -> str:
    """Generic paged content help."""
    pages = get_page_hint_for_device()
    scroll = get_scroll_hint_for_device()
    cancel = get_cancel_hint_for_device(context, mapper=mapper)
    return f"Pages: {pages}  Scroll: {scroll}  Back: {cancel}"


# ============================================================================
# CONTROLS MENU SPECIFIC HELP
# ============================================================================


def get_keyboard_bindings_help(mapper: InputMapper | None = None) -> tuple[str, str]:
    """Help for keyboard bindings menu."""
    m = _get_mapper(mapper)
    device = get_last_device()
    ctx = InputContext.SETTINGS_MENU
    if device == InputDeviceType.GAMEPAD:
        confirm = m.get_button_hint(InputAction.CONFIRM, ctx)
        reset_default = m.get_button_hint(InputAction.CONTROLS_RESET_DEFAULT, ctx)
        reset_all = m.get_button_hint(InputAction.CONTROLS_RESET_ALL, ctx)
        cancel = m.get_button_hint(InputAction.CANCEL, ctx)
        main = f"{confirm}: Edit  {reset_default}: Default  {reset_all}: Reset All  {cancel}: Back"
        nav = "Navigate: D-Pad  Fast Scroll: LB/RB"
    else:
        main = "Enter: Edit  Del: Default  R: Reset All  ESC: Back"
        nav = "Navigate: \u2191\u2193  Fast Scroll: PgUp/PgDn"
    return main, nav


def get_gamepad_bindings_help(mapper: InputMapper | None = None) -> tuple[str, str]:
    """Help for gamepad bindings menu."""
    m = _get_mapper(mapper)
    device = get_last_device()
    ctx = InputContext.SETTINGS_MENU
    if device == InputDeviceType.GAMEPAD:
        confirm = m.get_button_hint(InputAction.CONFIRM, ctx)
        reset_default = m.get_button_hint(InputAction.CONTROLS_RESET_DEFAULT, ctx)
        reset_all = m.get_button_hint(InputAction.CONTROLS_RESET_ALL, ctx)
        cancel = m.get_button_hint(InputAction.CANCEL, ctx)
        main = f"{confirm}: Edit  {reset_default}: Default  {reset_all}: Reset All  {cancel}: Back"
        nav = "Navigate: D-Pad  Switch Tab: LB/RB"
    else:
        main = "Enter: Edit  Del: Default  R: Reset All  ESC: Back"
        nav = "Navigate: \u2191\u2193  Switch Tab: [/]"
    return main, nav


def get_gamepad_settings_help(mapper: InputMapper | None = None) -> str:
    """Help for gamepad settings menu."""
    nav = get_nav_hint_for_device()
    cancel = get_cancel_hint_for_device(InputContext.SETTINGS_MENU, mapper=mapper)
    return f"Navigate: {nav}  Adjust: \u2190\u2192  Back: {cancel}"


def get_edit_binding_help_keyboard() -> str:
    """Help for keyboard binding edit dialog."""
    return "Press any key to bind  |  ESC: Cancel  |  Del: Default"


def get_edit_binding_help_gamepad(mapper: InputMapper | None = None) -> str:
    """Help for gamepad binding edit dialog."""
    device = get_last_device()
    if device == InputDeviceType.GAMEPAD:
        m = _get_mapper(mapper)
        cancel = m.get_button_hint(InputAction.CANCEL, InputContext.SETTINGS_MENU)
        reset = m.get_button_hint(InputAction.CONTROLS_RESET_DEFAULT, InputContext.SETTINGS_MENU)
        return f"Press any button to bind  |  {cancel}: Cancel  |  {reset}: Default"
    return "Press any button to bind  |  ESC: Cancel  |  Del: Default"


# ============================================================================
# DIALOGUE OPTIONS
# ============================================================================


def get_dialogue_confirm_option_for_device(
    text: str,
    device: InputDeviceType | None = None,
    mapper: InputMapper | None = None,
) -> str:
    """Get dialogue confirm option (e.g., "[Y] Yes" or "[A] Yes")."""
    m = _get_mapper(mapper)
    device = device or get_last_device()
    if device == InputDeviceType.GAMEPAD:
        btn = m.get_button_hint(InputAction.CONFIRM, InputContext.DIALOGUE)
        return f"[{btn}] {text}"
    return f"[Y] {text}"


def get_dialogue_cancel_option_for_device(
    text: str,
    device: InputDeviceType | None = None,
    mapper: InputMapper | None = None,
) -> str:
    """Get dialogue cancel option (e.g., "[N] No" or "[B] No")."""
    m = _get_mapper(mapper)
    device = device or get_last_device()
    if device == InputDeviceType.GAMEPAD:
        btn = m.get_button_hint(InputAction.CANCEL, InputContext.DIALOGUE)
        return f"[{btn}] {text}"
    return f"[N] {text}"


def get_dialogue_skip_option_for_device(
    text: str,
    device: InputDeviceType | None = None,
    mapper: InputMapper | None = None,
) -> str:
    """Get dialogue skip option (e.g., "[D] Don't ask again")."""
    m = _get_mapper(mapper)
    device = device or get_last_device()
    if device == InputDeviceType.GAMEPAD:
        btn = m.get_button_hint(InputAction.DIALOGUE_SKIP_WARNING, InputContext.DIALOGUE)
        return f"[{btn}] {text}"
    return f"[D] {text}"


# Convenience aliases that auto-detect device
def get_dialogue_confirm_option(text: str, mapper: InputMapper | None = None) -> str:
    """Get dialogue confirm option, auto-detecting device."""
    return get_dialogue_confirm_option_for_device(text, mapper=mapper)


def get_dialogue_cancel_option(text: str, mapper: InputMapper | None = None) -> str:
    """Get dialogue cancel option, auto-detecting device."""
    return get_dialogue_cancel_option_for_device(text, mapper=mapper)


def get_dialogue_skip_option(text: str, mapper: InputMapper | None = None) -> str:
    """Get dialogue skip option, auto-detecting device."""
    return get_dialogue_skip_option_for_device(text, mapper=mapper)


def get_dialogue_dismiss_option(text: str, mapper: InputMapper | None = None) -> str:
    """Get dismiss option for single-button dialogues (death, victory, etc.)."""
    device = get_last_device()
    if device == InputDeviceType.GAMEPAD:
        m = _get_mapper(mapper)
        btn = m.get_button_hint(InputAction.CONFIRM, InputContext.DIALOGUE)
        return f"[{btn}] {text}"
    return f"[Space/Enter] {text}"


# ============================================================================
# COMPACT HELP STRINGS (for tight spaces)
# Format: "Key:Label  Key:Label"
# ============================================================================


def get_menu_help_compact(context: InputContext, mapper: InputMapper | None = None) -> str:
    """Compact menu help for narrow spaces."""
    nav = get_nav_hint_for_device()
    confirm = get_confirm_hint_for_device(context, mapper=mapper)
    cancel = get_cancel_hint_for_device(context, mapper=mapper)
    return f"{nav}:Nav  {confirm}:Sel  {cancel}:Back"


# ============================================================================
# ACHIEVEMENT POPUP HINTS
# ============================================================================


def get_achievement_dismiss_hint(mapper: InputMapper | None = None) -> str:
    """Get dismiss hint for achievement popup based on device."""
    device = get_last_device()
    if device == InputDeviceType.GAMEPAD:
        m = _get_mapper(mapper)
        btn = m.get_button_hint(InputAction.CONFIRM, InputContext.DIALOGUE)
        return f"({btn} to dismiss)"
    return "(Enter/Click to dismiss)"


# ============================================================================
# VICTORY SCREEN HINTS
# ============================================================================


def get_victory_continue_prompt(mapper: InputMapper | None = None) -> str:
    """Get continue prompt for victory screen based on device."""
    device = get_last_device()
    if device == InputDeviceType.GAMEPAD:
        m = _get_mapper(mapper)
        btn = m.get_button_hint(InputAction.CONFIRM, InputContext.DIALOGUE)
        return f"[{btn}] Continue"
    return "[SPACE/ENTER] Continue"


# ============================================================================
# GRAPHICS PREVIEW HINTS
# ============================================================================


def get_graphics_preview_instructions(mapper: InputMapper | None = None) -> str:
    """Get instructions for graphics preview screen based on device."""
    device = get_last_device()
    if device == InputDeviceType.GAMEPAD:
        m = _get_mapper(mapper)
        cancel = m.get_button_hint(InputAction.CANCEL, InputContext.SETTINGS_MENU)
        confirm = m.get_button_hint(InputAction.CONFIRM, InputContext.SETTINGS_MENU)
        return f"Select: D-Pad  Variant: \u2190\u2192  Ring: {confirm}  Exit: {cancel}"
    return "Select: \u2191\u2193  Variant: \u2190\u2192  Ring: Space  Exit: ESC"


# ============================================================================
# CONTROLS MENU BINDING EDITOR HINTS
# ============================================================================


def get_gamepad_binding_instructions(mapper: InputMapper | None = None) -> str:
    """Get instructions for gamepad button binding editor based on device."""
    device = get_last_device()
    if device == InputDeviceType.GAMEPAD:
        m = _get_mapper(mapper)
        cancel = m.get_button_hint(InputAction.CANCEL, InputContext.SETTINGS_MENU)
        reset = m.get_button_hint(InputAction.CONTROLS_RESET_DEFAULT, InputContext.SETTINGS_MENU)
        return f"{cancel}: Cancel  |  {reset}: Reset to default"
    return "ESC: Cancel  |  Del: Reset to default"
