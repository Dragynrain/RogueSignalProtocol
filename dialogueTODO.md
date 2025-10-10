# Dialogue System Implementation Plan

## ⭐ CONFIRMED DESIGN DECISIONS ⭐

Based on user feedback, here are the finalized design decisions:

### 1. **Inventory Attack Warning Timing**
- Show warning **when the player takes damage from an attack** (not when enemy merely gets in range)
- Show dialogue **every time the player takes damage** while inventory is open
- **Only once per turn** even if attacked multiple times in that turn

### 2. **Dialogue Stacking/Queuing**
- **Stack and queue with priority system**
- Higher priority dialogues (attack warnings) override lower priority ones
- Show dialogues sequentially after dismissal when multiple are queued

### 3. **Overclock Warning Details**
- **DO the math for the player** - show exact damage calculation
- Display: "Using this exploit will exceed heat capacity by X. You will take X damage (current CPU: Y/Z)"
- Make it clear what the consequence will be with specific numbers

### 4. **"Don't Show Again" Option**
- ✅ **Overclock warning**: Include "don't show this again" option
- ❌ **Inventory attack warning**: NO "don't show this again" option (always important)
- **Configurable per dialogue type** via `DialogueConfig.has_dont_show_option: bool`
- **Save to user_settings.json** under a new `dialogue_preferences` section:
  ```json
  "dialogue_preferences": {
    "show_overclock_warning": true,
    "show_inventory_attack_warning": true
  }
  ```

### 5. **Movement While Dialogue Active**
- **Make it configurable** per dialogue type
- **Default for both current dialogues: Block movement**
- Movement key presses should be ignored while dialogue is active
- Add `DialogueConfig.blocks_movement: bool` attribute

### 6. **Visual Integration**
- **Solid color blocks** (no semi-transparency) for maximum terminal compatibility
- **Use the existing box drawing system** in the codebase for nice bordered boxes
- **Pause the game** - dialogues should freeze enemy movement and game time

### 7. **Priority Levels**
```python
class DialoguePriority(Enum):
    LOW = 0      # Informational messages
    MEDIUM = 1   # Warnings (overclock)
    HIGH = 2     # Urgent warnings (under attack)
    CRITICAL = 3 # Game-ending confirmations
```

## Overview
Create a flexible, reusable popup dialogue system for warning players about dangerous actions (taking damage while in inventory, overclocking exploits, etc.).

## Current State Analysis
- **Existing Overclock Confirmation**: The game already has a basic overclock confirmation system in `game_engine.py` and `game_input.py`
  - Uses `game.overclock_confirmation` flag
  - Uses `game.overclock_exploit` to track which exploit is being confirmed
  - Renders confirmation UI in `game_rendering.py`
- **Attack While In Inventory**: Currently no warning when enemies attack while player is in inventory

## Design Goals
1. **Unified System**: Single dialogue manager that handles all popup confirmations/warnings
2. **Reusable**: Easy to add new dialogue types without duplicating code
3. **Non-Blocking**: Player can dismiss or confirm dialogues with key presses
4. **Informative**: Clearly communicate risk and consequences
5. **Consistent**: Same look and feel across all dialogues

## Architecture

### Core Components

#### 1. DialogueManager Class (`game_dialogue.py`)
```python
class DialogueType(Enum):
    """Types of dialogues that can be displayed."""
    OVERCLOCK_WARNING = "overclock"      # Exploit use over heat capacity
    INVENTORY_ATTACK = "inventory_attack"  # Attacked while in inventory
    GATEWAY_CONFIRM = "gateway"          # Already exists, migrate to new system
    # Future: SAVE_OVERWRITE, QUIT_CONFIRM, etc.

@dataclass
class DialogueConfig:
    """Configuration for a specific dialogue type."""
    title: str                          # e.g., "OVERCLOCK WARNING"
    message: str                        # Main message text
    options: List[str]                  # e.g., ["[Y] Confirm", "[N] Cancel"]
    default_action: str                 # Which option is selected by default
    color_scheme: Dict[str, Tuple[int, int, int]]  # Colors for different parts
    requires_confirmation: bool         # If False, just shows info (press any key)
    can_dismiss: bool                   # Can player press ESC to dismiss?
    priority: DialoguePriority          # Priority level for queuing (HIGH = attack, MEDIUM = overclock)
    blocks_movement: bool               # If True, movement keys are ignored while dialogue active
    has_dont_show_option: bool          # If True, includes "Don't show this again" checkbox
    user_pref_key: Optional[str]        # Key in user_settings.json for "don't show" preference

class DialogueManager:
    """Manages all game dialogues and warnings."""

    def __init__(self, user_settings):
        self.active_dialogue: Optional[DialogueType] = None
        self.dialogue_data: Dict[str, Any] = {}  # Context data for current dialogue
        self.dialogue_configs: Dict[DialogueType, DialogueConfig] = {}
        self.dialogue_queue: List[Tuple[DialogueType, Dict[str, Any]]] = []  # Priority queue
        self.user_settings = user_settings  # Reference to user settings for "don't show" prefs
        self._register_default_dialogues()

    def _register_default_dialogues(self):
        """Register all default dialogue configurations."""
        # Overclock warning
        # NOTE: Message will be formatted with context data showing exact calculations
        self.dialogue_configs[DialogueType.OVERCLOCK_WARNING] = DialogueConfig(
            title="⚠ OVERCLOCK WARNING ⚠",
            message="Using {exploit_name} will exceed heat capacity by {overheat_amount}. You will take {damage} CPU damage (current: {current_cpu}/{max_cpu})",
            options=["[Y] Use exploit anyway", "[N] Cancel", "[D] Don't show again"],
            default_action="N",
            color_scheme={
                "title": Colors.RED,
                "message": Colors.YELLOW,
                "border": Colors.RED,
                "background": (30, 0, 0),
            },
            requires_confirmation=True,
            can_dismiss=True,
            priority=DialoguePriority.MEDIUM,
            blocks_movement=True,
            has_dont_show_option=True,
            user_pref_key="show_overclock_warning"
        )

        # Inventory attack warning
        self.dialogue_configs[DialogueType.INVENTORY_ATTACK] = DialogueConfig(
            title="⚠ UNDER ATTACK ⚠",
            message="Enemies are attacking! Close inventory immediately!",
            options=["[ESC] Close Inventory"],
            default_action="ESC",
            color_scheme={
                "title": Colors.RED,
                "message": Colors.BRIGHT_RED,
                "border": Colors.RED,
                "background": (30, 0, 0),
            },
            requires_confirmation=False,
            can_dismiss=True,
            priority=DialoguePriority.HIGH,
            blocks_movement=True,
            has_dont_show_option=False,
            user_pref_key=None
        )

    def show_dialogue(self, dialogue_type: DialogueType, **context_data):
        """
        Show a dialogue to the player.
        Checks user preferences and handles queuing based on priority.
        """
        config = self.dialogue_configs.get(dialogue_type)
        if not config:
            return

        # Check if user has disabled this dialogue
        if config.user_pref_key:
            dialogue_prefs = self.user_settings.get('dialogue_preferences', {})
            if not dialogue_prefs.get(config.user_pref_key, True):
                return  # User disabled this dialogue

        # If a dialogue is already active, add to queue
        if self.active_dialogue:
            self._queue_dialogue(dialogue_type, context_data)
            return

        # Show dialogue immediately
        self.active_dialogue = dialogue_type
        self.dialogue_data = context_data

    def _queue_dialogue(self, dialogue_type: DialogueType, context_data: Dict[str, Any]):
        """Add dialogue to priority queue."""
        new_priority = self.dialogue_configs[dialogue_type].priority

        # Insert into queue based on priority (higher priority = closer to front)
        inserted = False
        for i, (queued_type, _) in enumerate(self.dialogue_queue):
            queued_priority = self.dialogue_configs[queued_type].priority
            if new_priority.value > queued_priority.value:
                self.dialogue_queue.insert(i, (dialogue_type, context_data))
                inserted = True
                break

        if not inserted:
            self.dialogue_queue.append((dialogue_type, context_data))

    def _show_next_queued_dialogue(self):
        """Show the next dialogue from the queue if available."""
        if self.dialogue_queue:
            next_type, next_data = self.dialogue_queue.pop(0)
            self.active_dialogue = next_type
            self.dialogue_data = next_data

    def handle_input(self, key) -> Optional[str]:
        """
        Handle player input for active dialogue.
        Returns: Action to take ("confirm", "cancel", "dismiss", "dont_show_again", None)
        """
        if not self.active_dialogue:
            return None

        config = self.dialogue_configs[self.active_dialogue]

        # Handle ESC
        if key == tcod.event.K_ESCAPE and config.can_dismiss:
            return "dismiss"

        # Handle confirmation dialogues
        if config.requires_confirmation:
            if key == tcod.event.K_y:
                return "confirm"
            elif key == tcod.event.K_n:
                return "cancel"
            elif key == tcod.event.K_d and config.has_dont_show_option:
                return "dont_show_again"
        else:
            # Info-only dialogue - any key closes it
            return "dismiss"

        return None

    def close_dialogue(self):
        """Close the current dialogue and show next queued dialogue if any."""
        self.active_dialogue = None
        self.dialogue_data = {}

        # Show next queued dialogue if available
        self._show_next_queued_dialogue()

    def disable_dialogue(self, dialogue_type: DialogueType):
        """Disable a dialogue type by saving preference to user settings."""
        config = self.dialogue_configs.get(dialogue_type)
        if config and config.user_pref_key:
            if 'dialogue_preferences' not in self.user_settings:
                self.user_settings['dialogue_preferences'] = {}
            self.user_settings['dialogue_preferences'][config.user_pref_key] = False
            # Save user settings immediately
            self._save_user_settings()

    def is_active(self) -> bool:
        """Check if a dialogue is currently active."""
        return self.active_dialogue is not None

    def get_active_config(self) -> Optional[DialogueConfig]:
        """Get configuration for currently active dialogue."""
        if self.active_dialogue:
            return self.dialogue_configs[self.active_dialogue]
        return None
```

#### 2. Rendering Integration (`game_rendering.py`)
```python
def render_dialogue(self, console: tcod.console.Console):
    """Render active dialogue popup."""
    if not self.game.dialogue_manager.is_active():
        return

    config = self.game.dialogue_manager.get_active_config()
    if not config:
        return

    # Calculate dialogue box dimensions
    box_width = 60
    box_height = 10
    box_x = (GameConfig.SCREEN_WIDTH - box_width) // 2
    box_y = (GameConfig.SCREEN_HEIGHT - box_height) // 2

    # Draw semi-transparent background overlay
    for y in range(GameConfig.SCREEN_HEIGHT):
        for x in range(GameConfig.SCREEN_WIDTH):
            current_bg = console.bg[y, x]
            darkened = tuple(c // 2 for c in current_bg)
            console.bg[y, x] = darkened

    # Draw dialogue box
    self._draw_bordered_box(console, box_x, box_y, box_width, box_height,
                           config.color_scheme["border"], config.color_scheme["background"])

    # Render title (centered)
    title_x = box_x + (box_width - len(config.title)) // 2
    console.print(title_x, box_y + 1, config.title, fg=config.color_scheme["title"])

    # Render message (word-wrapped, formatted with context data)
    formatted_message = config.message.format(**self.game.dialogue_manager.dialogue_data)
    message_lines = self._wrap_text(formatted_message, box_width - 4)
    message_y = box_y + 3
    for i, line in enumerate(message_lines):
        console.print(box_x + 2, message_y + i, line, fg=config.color_scheme["message"])

    # Render options (centered at bottom)
    options_y = box_y + box_height - 2
    options_text = "  ".join(config.options)
    options_x = box_x + (box_width - len(options_text)) // 2
    console.print(options_x, options_y, options_text, fg=Colors.WHITE)

    # Add context-specific information if available
    dialogue_data = self.game.dialogue_manager.dialogue_data
    if self.game.dialogue_manager.active_dialogue == DialogueType.OVERCLOCK_WARNING:
        exploit_name = dialogue_data.get("exploit_name", "Unknown")
        damage = dialogue_data.get("damage", 0)
        info = f"Exploit: {exploit_name} | Damage: {damage} CPU"
        console.print(box_x + 2, message_y + len(message_lines) + 1, info,
                     fg=Colors.YELLOW)
    elif self.game.dialogue_manager.active_dialogue == DialogueType.INVENTORY_ATTACK:
        damage = dialogue_data.get("damage", 0)
        enemy_count = dialogue_data.get("enemy_count", 0)
        info = f"Damage taken: {damage} CPU from {enemy_count} enemies"
        console.print(box_x + 2, message_y + len(message_lines) + 1, info,
                     fg=Colors.BRIGHT_RED)

def _draw_bordered_box(self, console, x, y, width, height, border_color, bg_color):
    """Draw a bordered box for dialogues."""
    # Fill background
    for dy in range(height):
        for dx in range(width):
            console.bg[y + dy, x + dx] = bg_color

    # Draw borders (ASCII box drawing)
    # Top and bottom
    for dx in range(width):
        console.print(x + dx, y, "─", fg=border_color)
        console.print(x + dx, y + height - 1, "─", fg=border_color)

    # Left and right
    for dy in range(height):
        console.print(x, y + dy, "│", fg=border_color)
        console.print(x + width - 1, y + dy, "│", fg=border_color)

    # Corners
    console.print(x, y, "┌", fg=border_color)
    console.print(x + width - 1, y, "┐", fg=border_color)
    console.print(x, y + height - 1, "└", fg=border_color)
    console.print(x + width - 1, y + height - 1, "┘", fg=border_color)

def _wrap_text(self, text: str, max_width: int) -> List[str]:
    """Wrap text to fit within max_width characters."""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        word_length = len(word)
        if current_length + word_length + len(current_line) <= max_width:
            current_line.append(word)
            current_length += word_length
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_length

    if current_line:
        lines.append(" ".join(current_line))

    return lines
```

#### 3. Input Handling Integration (`game_input.py`)
```python
def handle_keys(self, key: int):
    """Main input handler - check dialogue first."""
    # Priority 1: Active dialogue
    if self.game.dialogue_manager.is_active():
        # Block movement keys if dialogue blocks movement
        config = self.game.dialogue_manager.get_active_config()
        if config and config.blocks_movement:
            # Check if this is a movement key (arrows, WASD, numpad, vim keys)
            movement_keys = {
                tcod.event.K_UP, tcod.event.K_DOWN, tcod.event.K_LEFT, tcod.event.K_RIGHT,
                tcod.event.K_w, tcod.event.K_a, tcod.event.K_s, tcod.event.K_d,
                tcod.event.K_KP_8, tcod.event.K_KP_2, tcod.event.K_KP_4, tcod.event.K_KP_6,
                tcod.event.K_h, tcod.event.K_j, tcod.event.K_k, tcod.event.K_l
            }
            if key in movement_keys:
                return  # Ignore movement while dialogue active

        action = self.game.dialogue_manager.handle_input(key)

        if action == "confirm":
            self._handle_dialogue_confirm()
        elif action in ["cancel", "dismiss"]:
            self._handle_dialogue_dismiss()
        elif action == "dont_show_again":
            self._handle_dialogue_dont_show_again()

        # Dialogue is active - don't process other inputs
        return

    # Priority 2: Inventory open
    if self.game.show_inventory:
        # Normal inventory input handling
        self._handle_inventory_keys(key)
        return

    # Priority 3: Normal gameplay
    self._handle_gameplay_keys(key)

def _handle_dialogue_confirm(self):
    """Handle dialogue confirmation."""
    dialogue_type = self.game.dialogue_manager.active_dialogue

    if dialogue_type == DialogueType.OVERCLOCK_WARNING:
        # Player confirmed overclock - execute exploit with damage
        exploit_key = self.game.dialogue_manager.dialogue_data.get("exploit_key")
        if exploit_key:
            self._execute_overclock_exploit(exploit_key)

    self.game.dialogue_manager.close_dialogue()

def _handle_dialogue_dismiss(self):
    """Handle dialogue dismissal/cancellation."""
    dialogue_type = self.game.dialogue_manager.active_dialogue

    if dialogue_type == DialogueType.INVENTORY_ATTACK:
        # Close inventory automatically
        self.game.show_inventory = False
    elif dialogue_type == DialogueType.OVERCLOCK_WARNING:
        # Cancel exploit use
        pass  # Just close dialogue

    self.game.dialogue_manager.close_dialogue()

def _handle_dialogue_dont_show_again(self):
    """Handle 'don't show this again' option."""
    dialogue_type = self.game.dialogue_manager.active_dialogue

    # Disable this dialogue type
    self.game.dialogue_manager.disable_dialogue(dialogue_type)

    # Close dialogue
    self.game.dialogue_manager.close_dialogue()

    # Add message to log
    self.game.message_log.add_message(
        "Dialogue disabled. Re-enable in settings if needed.",
        Colors.YELLOW
    )

def _check_inventory_attack(self) -> bool:
    """Check if player is being attacked while in inventory."""
    for enemy in self.game.enemies:
        if enemy.can_attack_player(self.game.player):
            return True
    return False

def _calculate_attack_info(self) -> Tuple[int, int]:
    """Calculate total damage and enemy count for inventory attack."""
    total_damage = 0
    enemy_count = 0

    for enemy in self.game.enemies:
        if enemy.can_attack_player(self.game.player):
            total_damage += enemy.type_data.damage
            enemy_count += 1

    return total_damage, enemy_count
```

#### 4. Turn Manager Integration for Inventory Attack Warning (`game_turn_manager.py`)
```python
# In _process_enemy_attacks() or wherever enemies deal damage to player:

def _process_enemy_attacks(self):
    """Process enemy attacks on the player."""
    # Track if player was attacked this turn while in inventory
    player_attacked_in_inventory = False
    total_damage_taken = 0
    attacking_enemies = []

    for enemy in self.game_engine.enemies:
        if enemy.can_attack_player(self.game_engine.player):
            damage = enemy.attack_player(self.game_engine.player)
            if damage > 0:
                total_damage_taken += damage
                attacking_enemies.append(enemy)

                # Check if inventory is open
                if self.game_engine.show_inventory:
                    player_attacked_in_inventory = True

    # If player was attacked while in inventory, show warning dialogue
    if player_attacked_in_inventory:
        self.game_engine.dialogue_manager.show_dialogue(
            DialogueType.INVENTORY_ATTACK,
            damage=total_damage_taken,
            enemy_count=len(attacking_enemies),
            attacking_enemies=[e.type for e in attacking_enemies]
        )
```

#### 5. Game Engine Integration (`game_engine.py`)
```python
# In GameEngine.__init__():
from game_dialogue import DialogueManager

self.dialogue_manager = DialogueManager()

# Modify overclock exploit usage:
def try_use_exploit(self, exploit_key: str):
    """Try to use an exploit, checking for overclock."""
    exploit_def = GameData.EXPLOITS.get(exploit_key)
    if not exploit_def:
        return

    # Check if this will cause overclock
    if self.player.heat + exploit_def.heat > self.player.max_heat:
        # Show overclock warning dialogue with exact damage calculation
        overheat_amount = (self.player.heat + exploit_def.heat) - self.player.max_heat
        cpu_damage = overheat_amount  # 1:1 ratio

        self.dialogue_manager.show_dialogue(
            DialogueType.OVERCLOCK_WARNING,
            exploit_key=exploit_key,
            exploit_name=exploit_def.name,
            damage=cpu_damage,
            overheat_amount=overheat_amount,
            current_cpu=self.player.cpu,
            max_cpu=self.player.max_cpu
        )
        return  # Wait for player confirmation

    # Normal exploit usage
    self._execute_exploit(exploit_key)
```

## Implementation Steps

### Phase 1: Core Dialogue System (Priority: HIGH)
1. ✅ Create `game_dialogue.py` with `DialogueManager` class
2. ✅ Define `DialogueType` enum and `DialogueConfig` dataclass
3. ✅ Implement dialogue registration system
4. ✅ Add dialogue manager to `GameEngine`

### Phase 2: Rendering (Priority: HIGH)
1. ✅ Add `render_dialogue()` method to `GameRenderer`
2. ✅ Implement bordered box drawing helper
3. ✅ Implement text wrapping helper
4. ✅ Add dialogue rendering to main render loop (render last, on top of everything)

### Phase 3: Input Handling (Priority: HIGH)
1. ✅ Modify `game_input.py` to check dialogue state first
2. ✅ Implement `_handle_dialogue_confirm()` and `_handle_dialogue_dismiss()`
3. ✅ Add dialogue input priority system

### Phase 4: Overclock Warning Integration (Priority: HIGH)
1. ✅ Register overclock warning dialogue config
2. ✅ Modify exploit usage code to show dialogue instead of immediate execution
3. ✅ Move overclock execution logic to confirmation handler
4. ✅ Remove old `overclock_confirmation` flag system
5. ✅ Test with various exploits

### Phase 5: Inventory Attack Warning (Priority: MEDIUM)
1. ✅ Register inventory attack dialogue config
2. ✅ Add `_check_inventory_attack()` method
3. ✅ Show dialogue when attack detected in inventory
4. ✅ Auto-close inventory on dialogue dismiss
5. ✅ Test with multiple enemies

### Phase 6: Migration & Cleanup (Priority: LOW)
1. ⬜ Migrate gateway confirmation to new system (optional)
2. ⬜ Remove old overclock confirmation code
3. ⬜ Update tests to use new dialogue system
4. ⬜ Add dialogue system tests

### Phase 7: Future Enhancements (Priority: LOW)
1. ⬜ Add dialogue history/log
2. ⬜ Add support for custom dialogue templates
3. ⬜ Add animation effects (fade in/out)
4. ⬜ Add sound effects for different dialogue types
5. ⬜ Support for multi-page dialogues
6. ⬜ Add dialogue positioning options (center, top, bottom)

## Technical Considerations

### Rendering Order
1. Game world
2. UI elements (stats, inventory, etc.)
3. **Dialogue overlay** (render last - highest priority)

### Input Priority
1. **Active dialogue** (highest priority - blocks all other input)
2. Inventory/Help screens
3. Targeting mode
4. Normal gameplay

### State Management
- Dialogue state is stored in `DialogueManager`
- Game state (inventory open, targeting, etc.) remains unchanged when dialogue appears
- Dialogue can query game state to customize messages
- Dialogue actions can modify game state (close inventory, execute exploit, etc.)

### Testing Strategy
1. Unit tests for `DialogueManager` (registration, state transitions)
2. Integration tests for dialogue + input handling
3. Manual testing for visual appearance
4. Test edge cases:
   - Multiple dialogues triggered in sequence
   - Dialogue shown while another is active (should queue or replace)
   - Input handling during dialogue
   - Game state changes while dialogue active

## File Changes Summary

### New Files
- `game_dialogue.py` - Core dialogue system

### Modified Files
- `game_engine.py` - Add DialogueManager, integrate with exploit usage
- `game_input.py` - Add dialogue input priority, attack detection
- `game_rendering.py` - Add dialogue rendering methods
- `game_entities.py` - Add DialogueType enum (or keep in game_dialogue.py)

### Files to Eventually Remove/Refactor
- Old overclock confirmation code in `game_engine.py`
- Old gateway confirmation code (migrate to new system)

## Configuration Examples

### Overclock Warning Dialogue (with exact damage calculation)
```
┌─────────────────────────────────────────────────────────┐
│              ⚠ OVERCLOCK WARNING ⚠                     │
│                                                          │
│  Using Buffer Overflow will exceed heat capacity by 15. │
│  You will take 15 CPU damage (current: 85/100)          │
│                                                          │
│  [Y] Use exploit anyway  [N] Cancel  [D] Don't show again│
└─────────────────────────────────────────────────────────┘
```

### Inventory Attack Warning (triggered when damage is taken)
```
┌─────────────────────────────────────────────────────────┐
│                ⚠ UNDER ATTACK ⚠                        │
│                                                          │
│  Enemies are attacking! Close inventory immediately!    │
│                                                          │
│  Damage taken: 23 CPU from 3 enemies                   │
│                                                          │
│                   [ESC] Close Inventory                  │
└─────────────────────────────────────────────────────────┘
```

**Note**: Inventory attack warning appears ONLY when player takes damage while in inventory, not just when enemies are nearby. Shows once per turn even if multiple attacks occur.

## Notes
- Keep dialogue system simple and focused
- Don't over-engineer - start with basics, add features as needed
- Maintain consistent visual style with rest of game
- All dialogue text should be clear and actionable
- Consider accessibility - clear language, obvious controls
- Test with keyboard input only (no mouse required)
