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
- Display: "Using this exploit will exceed heat capacity by X. You will have remaining CPU: Y/Z)" or "... by X. This will kill you!"
- Make it clear what the consequence will be with specific numbers

### 4. **"Don't Show Again" Option**
- ✅ **Overclock warning**: Include "don't show this again" option
- ❌ **Inventory attack warning**: NO "don't show this again" option (always important)
- **Configurable per dialogue type** via `DialogueConfig.has_dont_show_option: bool`
- **Save to user_settings.json** under a new `dialogue_preferences` section:
  ```json
  "dialogue_preferences": {
    "show_overclock_warning": true
  }
  ```
- **Settings Screen**: Add a "Dialogue Settings" section to Settings menu that allows users to re-enable any hidden dialogues. Only show dialogues that have the `has_dont_show_option` flag enabled. Display with checkboxes that toggle the visibility preference.

### 5. **Movement While Dialogue Active**
- **Make it configurable** per dialogue type
- **Default for both current dialogues: Block movement**
- Movement key presses should be ignored while dialogue is active
- Add `DialogueConfig.blocks_movement: bool` attribute

### 6. **Visual Integration**
- **Solid color blocks** (no semi-transparency) for maximum terminal compatibility
- **ASCII-ONLY box drawing** - Use simple ASCII characters (+-|) for borders, NO Unicode box chars
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

    def __init__(self, settings: GameSettings):
        self.active_dialogue: Optional[DialogueType] = None
        self.dialogue_data: Dict[str, Any] = {}  # Context data for current dialogue
        self.dialogue_configs: Dict[DialogueType, DialogueConfig] = {}
        self.dialogue_queue: List[Tuple[DialogueType, Dict[str, Any]]] = []  # Priority queue
        self.settings = settings  # Reference to GameSettings for "don't show" prefs
        self._register_default_dialogues()

    def _register_default_dialogues(self):
        """Register all default dialogue configurations."""
        # Overclock warning
        # NOTE: Message will be formatted with context data showing exact calculations
        self.dialogue_configs[DialogueType.OVERCLOCK_WARNING] = DialogueConfig(
            title="*** OVERCLOCK WARNING ***",
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
            title="*** UNDER ATTACK ***",
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
            dialogue_prefs = getattr(self.settings, 'dialogue_preferences', {})
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
            if not hasattr(self.settings, 'dialogue_preferences'):
                self.settings.dialogue_preferences = {}
            self.settings.dialogue_preferences[config.user_pref_key] = False
            # Save user settings immediately
            self.settings.save_settings()

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

    # NOTE: No semi-transparent overlay - just draw solid dialogue box on top
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
    """Draw a bordered box for dialogues using ASCII-only characters."""
    # Fill background
    for dy in range(height):
        for dx in range(width):
            console.bg[y + dy, x + dx] = bg_color

    # Draw borders (ASCII ONLY - no Unicode)
    # Top and bottom
    for dx in range(width):
        console.print(x + dx, y, "-", fg=border_color)
        console.print(x + dx, y + height - 1, "-", fg=border_color)

    # Left and right
    for dy in range(height):
        console.print(x, y + dy, "|", fg=border_color)
        console.print(x + width - 1, y + dy, "|", fg=border_color)

    # Corners
    console.print(x, y, "+", fg=border_color)
    console.print(x + width - 1, y, "+", fg=border_color)
    console.print(x, y + height - 1, "+", fg=border_color)
    console.print(x + width - 1, y + height - 1, "+", fg=border_color)

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

#### 5. GameSettings Persistence Integration (`game_config.py`)
```python
# Add to GameSettings class:

class GameSettings:
    """Manages game settings with persistent storage."""

    SETTINGS_FILE = "user_settings.json"

    def __init__(self):
        self.master_volume = 0.7
        self.sfx_volume = 0.8
        self.music_volume = 0.5
        self.graphics_mode = "ascii"  # "ascii" or "graphics"
        self.dialogue_preferences = {}  # NEW: Dictionary for dialogue preferences
        self.load_settings()

    def load_settings(self) -> None:
        """Load settings from file."""
        try:
            if os.path.exists(self.SETTINGS_FILE):
                # Read file content first to check for corruption
                with open(self.SETTINGS_FILE, 'r') as f:
                    content = f.read().strip()

                if not content:
                    logging.warning("Settings file is empty, using defaults")
                    self._create_default_settings_file()
                    return

                try:
                    settings_data = json.loads(content)
                    self.master_volume = settings_data.get("master_volume", 0.7)
                    self.sfx_volume = settings_data.get("sfx_volume", 0.8)
                    self.music_volume = settings_data.get("music_volume", 0.5)
                    self.graphics_mode = settings_data.get("graphics_mode", "ascii")
                    # NEW: Load dialogue preferences with default empty dict
                    self.dialogue_preferences = settings_data.get("dialogue_preferences", {})
                except json.JSONDecodeError as e:
                    logging.warning(f"Settings file corrupted, recreating with defaults")
                    self._create_default_settings_file()
        except Exception as e:
            logging.warning(f"Failed to load settings: {e}")
            self._create_default_settings_file()

    def save_settings(self) -> None:
        """Save settings to file."""
        try:
            settings_data = {
                "master_volume": self.master_volume,
                "sfx_volume": self.sfx_volume,
                "music_volume": self.music_volume,
                "graphics_mode": self.graphics_mode,
                "dialogue_preferences": self.dialogue_preferences  # NEW: Save dialogue prefs
            }
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings_data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
```

#### 6. Game Engine Integration (`game_engine.py`)
```python
# In GameEngine.__init__():
from game_dialogue import DialogueManager

# Pass settings instance to DialogueManager (settings should be passed to __init__ or created)
self.dialogue_manager = DialogueManager(settings or GameSettings())

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
1. ⬜ Create `game_dialogue.py` with `DialogueManager` class
2. ⬜ Define `DialogueType` enum and `DialogueConfig` dataclass
3. ⬜ Implement dialogue registration system
4. ⬜ Add dialogue manager to `GameEngine`
5. ⬜ Add `dialogue_preferences` dict attribute to `GameSettings` class
6. ⬜ Update `GameSettings.load_settings()` to load `dialogue_preferences` from JSON
7. ⬜ Update `GameSettings.save_settings()` to save `dialogue_preferences` to JSON
8. ⬜ Implement "don't show again" preference persistence via GameSettings

### Phase 2: Rendering (Priority: HIGH)
1. ⬜ Add `render_dialogue()` method to `GameRenderer`
2. ⬜ Implement ASCII-only bordered box drawing helper (use +-| characters, NO Unicode)
3. ⬜ Implement text wrapping helper with edge case handling (long words)
4. ⬜ Add dialogue rendering to main render loop (render last, on top of everything)
5. ⬜ Ensure solid color blocks (no semi-transparency) for terminal compatibility
6. ⬜ Test rendering in both ASCII and graphics modes

### Phase 3: Input Handling (Priority: HIGH)
1. ⬜ Modify `game_input.py` to check dialogue state first
2. ⬜ Implement `_handle_dialogue_confirm()` and `_handle_dialogue_dismiss()`
3. ⬜ Implement `_handle_dialogue_dont_show_again()`
4. ⬜ Add dialogue input priority system (dialogue > inventory > gameplay)
5. ⬜ Add movement key blocking when `DialogueConfig.blocks_movement` is true

### Phase 4: Overclock Warning Integration (Priority: HIGH)
1. ⬜ Locate exploit execution code (search game_combat.py and game_engine.py)
2. ⬜ Register overclock warning dialogue config with exact damage calculations
3. ⬜ Modify exploit usage code to show dialogue instead of immediate execution
4. ⬜ Move overclock execution logic to confirmation handler in game_input.py
5. ⬜ Remove old `overclock_confirmation` flag system
6. ⬜ Test with various exploits and damage scenarios
7. ⬜ Verify "don't show again" functionality works correctly
8. ⬜ Verify settings persist across game restarts

### Phase 5: Inventory Attack Warning (Priority: MEDIUM)
1. ⬜ Register inventory attack dialogue config (no "don't show again" option)
2. ⬜ Integrate with `game_turn_manager.py` `_process_enemy_attacks()` method
3. ⬜ Show dialogue when player takes damage while inventory is open
4. ⬜ Ensure dialogue only shows once per turn even with multiple attackers
5. ⬜ Auto-close inventory on dialogue dismiss
6. ⬜ Test with multiple enemies attacking simultaneously

### Phase 6: Settings Screen Integration (Priority: MEDIUM)
1. ⬜ Check available space in SettingsMenu for integrated dialogue options
2. ⬜ Add dialogue preference options to SettingsMenu (below existing settings)
3. ⬜ Implement for BOTH ASCII and graphics mode settings screens
4. ⬜ Display only dialogues with `has_dont_show_option=True`
5. ⬜ Implement checkbox/toggle UI for each hideable dialogue
6. ⬜ Ensure changes save immediately via GameSettings.save_settings()
7. ⬜ Test re-enabling hidden dialogues through settings
8. ⬜ Verify layout works in both narrow (graphics) and wide (ASCII) layouts

### Phase 7: Migration & Cleanup (Priority: LOW)
1. ⬜ Migrate gateway confirmation to new system (optional)
2. ⬜ Remove old overclock confirmation code from `game_engine.py` and `game_rendering.py`
3. ⬜ Update tests to use new dialogue system
4. ⬜ Add dialogue system unit tests
5. ⬜ Add integration tests for dialogue priority and queuing

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
+------------------------------------------------------------+
|              *** OVERCLOCK WARNING ***                     |
|                                                            |
|  Using Buffer Overflow will exceed heat capacity by 15.   |
|  You will take 15 CPU damage and have 85/100 remaining.   |
|                                                            |
|  [Y] Use exploit anyway  [N] Cancel  [D] Don't show again |
+------------------------------------------------------------+
```

### Inventory Attack Warning (triggered when damage is taken)
```
+--------------------------------------------------------+
|                *** UNDER ATTACK ***                    |
|                                                        |
|  Enemies are attacking! Close inventory immediately!  |
|                                                        |
|  Damage taken: 23 CPU from 3 enemies                  |
|                                                        |
|                   [ESC] Close Inventory               |
+--------------------------------------------------------+
```

**Note**: Inventory attack warning appears ONLY when player takes damage while in inventory, not just when enemies are nearby. Shows once per turn even if multiple attacks occur.

## Code Audit & Verification

### ✅ Verified Code Assumptions
1. **GameEngine Structure** (game_engine.py:113-115):
   - `overclock_confirmation` flag exists and needs migration
   - `overclock_exploit` tracks which exploit is being confirmed
   - These will be replaced by DialogueManager system

2. **GameSettings & user_settings.json** (game_config.py:16-26):
   - GameSettings class exists with proper save/load functionality
   - user_settings.json currently has: master_volume, sfx_volume, music_volume, graphics_mode
   - Perfect place to add `dialogue_preferences` section

3. **SettingsMenu** (game_menus.py:544-861):
   - Existing SettingsMenu in game_menus.py with proper rendering
   - Uses options list with type-based rendering (volume, toggle, action)
   - Can easily add new "dialogue" type for checkbox list
   - Already has left/right adjustment and background-aware layouts

4. **Box Drawing System** (game_menus.py:591-695):
   - `_render_right_side_box()` method exists for bordered boxes
   - **IMPORTANT**: Will need to create ASCII-only version using +-| characters
   - Returns box dict with positioning info for content rendering
   - Cannot reuse existing box drawing due to Unicode characters

5. **Enemy Attack Detection** (game_turn_manager.py:392-422):
   - `_process_enemy_attacks()` method processes all enemy attacks
   - Perfect integration point for inventory attack warning
   - Already tracks damage and enemy types
   - Need to check `game_engine.show_inventory` flag

6. **Input Priority** (game_input.py):
   - Input handling needs to be updated to check dialogue first
   - Current priority seems to be: inventory > gameplay
   - Need to add: dialogue > inventory > gameplay

### ⚠️ Issues Found & Fixes Needed

1. **CRITICAL: Box Drawing Unicode vs ASCII**
   - **Issue**: Plan originally specified Unicode box chars (┌┐└┘─│) but game uses specific tileset
   - **Resolution**: NO Unicode anywhere - strict ASCII only including UI elements
   - **Fix**: Use simple ASCII characters (+-|) for all box drawing in dialogues
   - **Updated Plan**: Implement ASCII-only box drawing (+ for corners, - for horizontal, | for vertical)

2. **Semi-Transparency Warning**
   - **Issue**: Plan shows semi-transparent background overlay in rendering code
   - **Resolution**: Design spec says "solid color blocks (no semi-transparency)"
   - **Fix**: Remove semi-transparency, use solid black background for dialogue boxes

3. **Settings Integration Unclear**
   - **Issue**: Plan doesn't specify exact UI for dialogue settings section
   - **Resolution**: Add clear spec for checkbox-style toggle list
   - **Fix**: Create new option type "dialogue_checkbox" with per-dialogue toggle

4. **GameSettings.save_settings() Integration**
   - **Issue**: DialogueManager needs to call save_settings() when preferences change
   - **Resolution**: DialogueManager should hold reference to GameSettings instance
   - **Fix**: Pass settings to DialogueManager.__init__ and call save_settings() after updating preferences
   - **Implementation**: Add dialogue_preferences dict attribute to GameSettings, update load/save methods

5. **Message Text Wrapping**
   - **Issue**: Plan shows basic word wrapping but doesn't handle long words
   - **Resolution**: Need to handle edge cases (words longer than box width)
   - **Fix**: Add character-level breaking for words that exceed max_width

### 📋 Additional Considerations

1. **Exploit System Integration Point**
   - Current overclock code is likely in `game_combat.py` or `game_engine.py`
   - Need to verify exact location of exploit execution logic
   - Ensure dialogue shows BEFORE any CPU damage is applied

2. **Inventory Attack Timing**
   - Show dialogue WHEN player takes damage (not when enemy gets in range)
   - Only show ONCE per turn even if multiple enemies attack
   - Need flag to track "shown_attack_warning_this_turn"

3. **Dialogue Queuing Edge Cases**
   - **DECISION**: If same dialogue type queued twice, only show once (de-duplicate or update context)
   - What if player dismisses high-priority dialogue while low-priority queued? (still show low-priority)
   - What if player closes inventory while attack warning active? (auto-dismiss dialogue)

4. **Save/Load Compatibility**
   - Don't save dialogue_manager state (recreate on load)
   - DO save dialogue_preferences in user_settings.json
   - Old saves without dialogue_preferences should work fine (defaults to True)

5. **Testing Strategy**
   - Unit tests for DialogueManager (registration, queuing, state)
   - Integration tests for overclock workflow
   - Integration tests for inventory attack workflow
   - Manual tests for UI rendering and input handling

### 🔧 Recommended Implementation Improvements

1. **Simplified Rendering** - Instead of darkening entire screen, just draw dialogue box on top with solid background
2. **Cleaner Message Formatting** - Use f-strings with named parameters for clarity
3. **Type Safety** - Add type hints to all DialogueManager methods
4. **Error Handling** - Gracefully handle missing dialogue configs (log warning, don't crash)
5. **Accessibility** - Ensure high contrast colors (red warning on dark background)

## Notes
- Keep dialogue system simple and focused
- Don't over-engineer - start with basics, add features as needed
- Maintain consistent visual style with rest of game
- All dialogue text should be clear and actionable
- Consider accessibility - clear language, obvious controls
- Test with keyboard input only (no mouse required)
- **STRICT ASCII-ONLY for all UI elements** - game uses specific tileset, no Unicode anywhere

## Implementation Answers (from user)
1. **GameSettings.dialogue_preferences**: Dict attribute with JSON persistence (load/save in GameSettings)
2. **Dialogue Queue De-duplication**: Only show same dialogue type once (de-duplicate)
3. **Settings UI Layout**: Integrated into main Settings screen below existing options (both ASCII/graphics)
4. **Exploit Execution Location**: Search game_combat.py and game_engine.py (found in both via grep)
5. **Implementation Order**: Follow exact phase order (1→2→3→4→5→6→7)
