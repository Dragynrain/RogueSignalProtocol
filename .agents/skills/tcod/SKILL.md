# python-tcod API Expert Skill

You are now an expert in python-tcod (libtcod Python bindings), a high-performance library for developing roguelike games. This skill provides comprehensive knowledge of the latest python-tcod API (version 19.x), best practices, and common usage patterns.

## Core Knowledge

### Current Version
- **Latest Version**: python-tcod 19.5.0 (as of 2025)
- **Installation**: `pip install tcod`
- **Official Documentation**: https://python-tcod.readthedocs.io/
- **GitHub**: https://github.com/libtcod/python-tcod

### Key Modules

1. **tcod.console** - Console/terminal rendering
2. **tcod.map** - Field of View (FOV) calculations
3. **tcod.path** - Pathfinding algorithms
4. **tcod.event** - Input event handling
5. **tcod.context** - Window management and rendering contexts
6. **tcod.tileset** - Font and tileset management
7. **tcod.noise** - Procedural noise generation
8. **tcod.bsp** - Binary Space Partitioning for dungeon generation

---

## Field of View (FOV) - tcod.map

### Primary Function: `tcod.map.compute_fov()`

Computes field of view and returns a boolean numpy array indicating visible tiles.

```python
import tcod
import numpy as np

# Create transparency map (True = transparent, False = opaque/wall)
transparency = np.ones((map_height, map_width), dtype=bool)
for y in range(map_height):
    for x in range(map_width):
        transparency[y, x] = not is_wall(x, y)

# Compute FOV from point-of-view (POV)
fov = tcod.map.compute_fov(
    transparency=transparency,  # 2D bool array
    pov=(pov_y, pov_x),        # IMPORTANT: (y, x) order!
    radius=10,                  # Vision range (0 = infinite)
    light_walls=True,          # Include walls in visible area
    algorithm=tcod.FOV_RESTRICTIVE  # or FOV_SYMMETRIC_SHADOWCAST, etc.
)

# Check if position is visible (array indexed as [y, x])
is_visible = fov[target_y, target_x]
```

### FOV Algorithms
- `tcod.FOV_RESTRICTIVE` - Default, most conservative (recommended)
- `tcod.FOV_SYMMETRIC_SHADOWCAST` - Symmetric, good for most games
- `tcod.FOV_PERMISSIVE_0` through `tcod.FOV_PERMISSIVE_8` - Increasingly permissive
- `tcod.libtcodpy.FOV_SYMMETRIC_SHADOWCAST` - Legacy access (still works)

### Critical Notes
- **Coordinate Order**: TCOD uses **(y, x)** order, not (x, y)!
- **Array Indexing**: Results are indexed as `fov[y, x]`
- **Transparency Map**: Non-zero values = transparent, zero = opaque
- **Performance**: Cache transparency maps to avoid recreation
- **Light Walls**: `True` makes wall tiles visible, `False` only shows walkable tiles

### FOV Caching Pattern (Performance Optimization)

```python
class GameMap:
    def __init__(self):
        self._fov_cache = {}
        self._transparency_cache = None

    def _get_transparency_map(self):
        """Cache transparency map to avoid recreation."""
        if self._transparency_cache is None:
            self._transparency_cache = np.ones((self.height, self.width), dtype=bool)
            for y in range(self.height):
                for x in range(self.width):
                    self._transparency_cache[y, x] = not self.is_wall(x, y)
        return self._transparency_cache

    def can_see_position(self, start_pos, end_pos, vision_range):
        """Check visibility with caching."""
        # Check distance first (fast early exit)
        if start_pos.distance_to(end_pos) > vision_range:
            return False

        # Cache FOV computations
        cache_key = (start_pos.x, start_pos.y, vision_range)
        if cache_key not in self._fov_cache:
            transparency = self._get_transparency_map()
            fov = tcod.map.compute_fov(
                transparency=transparency,
                pov=(start_pos.y, start_pos.x),  # y, x order!
                radius=vision_range,
                algorithm=tcod.FOV_SYMMETRIC_SHADOWCAST
            )

            # Limit cache size to prevent memory bloat
            if len(self._fov_cache) > 50:
                self._fov_cache.clear()
            self._fov_cache[cache_key] = fov

        return self._fov_cache[cache_key][end_pos.y, end_pos.x]

    def invalidate_caches(self):
        """Call when map changes (e.g., doors open/close)."""
        self._transparency_cache = None
        self._fov_cache.clear()
```

---

## Pathfinding - tcod.path

### Primary Classes: `SimpleGraph` and `Pathfinder`

TCOD provides fast, efficient pathfinding using Dijkstra's algorithm with configurable costs.

```python
import tcod
import numpy as np

# 1. Create cost map (0 = impassable, higher = more expensive)
cost_map = np.zeros((map_width, map_height), dtype=np.int32)
for x in range(map_width):
    for y in range(map_height):
        if is_walkable(x, y):
            cost_map[x, y] = 10  # Base movement cost
            if is_difficult_terrain(x, y):
                cost_map[x, y] = 20  # Higher cost for difficult terrain
        # Walls/impassable stay at 0

# 2. Create graph with movement costs
graph = tcod.path.SimpleGraph(
    cost=cost_map,
    cardinal=2,    # Cost multiplier for N/S/E/W movement
    diagonal=3     # Cost multiplier for diagonal movement
)

# 3. Create pathfinder and set starting point
pathfinder = tcod.path.Pathfinder(graph)
pathfinder.add_root((start_x, start_y))  # (x, y) order for pathfinding!

# 4. Get path to target
path = pathfinder.path_to((target_x, target_y))

# 5. Check and use path
if len(path) >= 2:  # At least start and one move
    next_step = path[1]  # First step after current position
    next_x, next_y = next_step
else:
    # No path found
    pass
```

### SimpleGraph Parameters
- `cost`: 2D numpy array (int32) - movement cost per tile (0 = blocked)
- `cardinal`: Cost multiplier for cardinal directions (N/S/E/W)
- `diagonal`: Cost multiplier for diagonal directions
- Common values: `cardinal=2, diagonal=3` (approximates sqrt(2) for diagonals)

### Pathfinder Methods
- `add_root((x, y))` - Set starting position for pathfinding
- `path_to((x, y))` - Get path array to target (returns numpy array)
- `path_from((x, y))` - Get path array from target to root
- `distance` - 2D array of distances from root to all positions

### Cost Map Design Patterns

```python
def create_pathfinding_cost_map(game_map, enemy=None):
    """Create cost map with smart avoidance."""
    cost_map = np.zeros((game_map.width, game_map.height), dtype=np.int32)

    for x in range(game_map.width):
        for y in range(game_map.height):
            if game_map.is_wall(x, y):
                cost_map[x, y] = 0  # Impassable
            elif game_map.has_enemy(x, y) and enemy:
                # High cost to avoid other enemies (but not impossible)
                cost_map[x, y] = 50
            elif game_map.is_shadow(x, y):
                # Enemies prefer shadows for stealth
                cost_map[x, y] = 5
            else:
                cost_map[x, y] = 10  # Normal walkable

    return cost_map
```

### Path Validation

Always check path length before using:

```python
# Get path
path = pathfinder.path_to((target_x, target_y))

# Validate path exists and is reasonable
if len(path) < 2:
    # No path found (either blocked or already at target)
    return None

# Check path isn't unreasonably long (stuck/inefficient)
max_reasonable_length = direct_distance * 3
if len(path) > max_reasonable_length:
    # Path is too long, probably stuck or going around huge obstacle
    return None

# Get next step (path[0] is current position, path[1] is next step)
next_step = path[1]
```

### Coordinate Order: CRITICAL!
- **Pathfinding uses (x, y) order** - opposite of FOV!
- FOV: `pov=(y, x)` and `fov[y, x]`
- Path: `add_root((x, y))` and `path_to((x, y))`

---

## Console Rendering - tcod.console

### Basic Console Operations

```python
import tcod

# Create console (usually done once)
console = tcod.console.Console(width=80, height=50)

# Clear console
console.clear()

# Print single character
console.print(x=10, y=5, string="@", fg=(255, 255, 255), bg=(0, 0, 0))

# Print string
console.print(x=10, y=5, string="Hello World", fg=(255, 255, 255))

# Draw rectangle
console.draw_rect(x=0, y=0, width=10, height=5, ch=ord(' '), fg=(255,255,255), bg=(0,0,0))

# Draw frame (box border)
console.draw_frame(
    x=0, y=0, width=40, height=20,
    title="Inventory",  # Optional
    fg=(255, 255, 255),
    bg=(0, 0, 0),
    clear=False  # Don't clear contents inside frame
)
```

### Character Rendering

```python
# Direct character placement
console.ch[y, x] = ord('@')       # Set character (note: y, x order!)
console.fg[y, x] = (255, 255, 255)  # Set foreground color
console.bg[y, x] = (0, 0, 0)        # Set background color

# Using tiles_rgb (structured array - fastest method)
console.tiles_rgb[y, x] = (ord('@'), (255,255,255), (0,0,0))
```

### Color Handling

Colors can be specified as:
- Tuples: `(r, g, b)` with values 0-255
- Named colors from `tcod.color`: `tcod.color.white`, `tcod.color.red`
- NEVER pass ColorRGB objects directly - convert to tuple if needed

```python
# Good - tuple
fg_color = (255, 255, 255)

# Good - named color (is a tuple)
fg_color = tcod.color.white

# Bad - ColorRGB object (can cause issues)
# fg_color = tcod.ColorRGB(255, 255, 255)  # Avoid this

# Convert ColorRGB to tuple if necessary
def ensure_color_tuple(color):
    if hasattr(color, '__iter__') and not isinstance(color, (str, tcod.ColorRGB)):
        return tuple(color)
    return (color.r, color.g, color.b) if hasattr(color, 'r') else color
```

---

## Context and Rendering - tcod.context

### Basic Window Setup

```python
import tcod

# Load tileset/font
tileset = tcod.tileset.load_tilesheet(
    "dejavu10x10_gs_tc.png",
    columns=32,
    rows=8,
    charmap=tcod.tileset.CHARMAP_TCOD
)

# Create rendering context
with tcod.context.new(
    columns=80,     # Console width
    rows=50,        # Console height
    tileset=tileset,
    title="My Roguelike",
    vsync=True
) as context:
    console = tcod.console.Console(80, 50)

    # Game loop
    while True:
        console.clear()
        # ... render game ...
        context.present(console)  # Display console

        # Handle events
        for event in tcod.event.wait():
            if isinstance(event, tcod.event.Quit):
                raise SystemExit()
```

### Advanced SDL Rendering (Graphics Mode)

For mixing console text with SDL2 graphics (tiles, images):

```python
# In initialization
context = tcod.context.new(...)

# Setup SDL renderer for graphics
if hasattr(context, 'sdl_renderer'):
    console_render = context.new_console_render(scaling=1)

    # Game loop
    while True:
        # Clear SDL renderer
        context.sdl_renderer.clear()

        # Render console as texture
        console.clear()
        # ... draw to console ...
        console_texture = console_render.render(console)

        # Copy console texture to renderer
        context.sdl_renderer.copy(console_texture)

        # Draw additional graphics (tiles, sprites, etc.)
        # ... SDL rendering code ...

        # Present everything
        context.sdl_renderer.present()
```

---

## Event Handling - tcod.event

### Overview

TCOD uses SDL event handling through the `tcod.event` module. **Important**: As of version 19.0+, SDL was updated to 3.x, which renamed some enums. **Single letter keys are now UPPERCASE** in KeySym.

### Key Event Attributes

- `event.sym` - A `KeySym` representing the key symbol (use for command inputs)
- `event.scancode` - Physical location of key on keyboard
- `event.mod` - Modifier keys (Shift, Ctrl, Alt, etc.)
- For text input, use `TextInput.text` instead of key symbols

### Event Loop Patterns

```python
import tcod

# Pattern 1: Wait for events (turn-based games, most efficient)
for event in tcod.event.wait():
    if isinstance(event, tcod.event.Quit):
        raise SystemExit()
    elif isinstance(event, tcod.event.KeyDown):
        if event.sym == tcod.event.KeySym.UP:
            # Handle up arrow
            pass

# Pattern 2: Poll events (real-time games with animations)
for event in tcod.event.get():
    # Process all pending events
    pass

# Pattern 3: Event handler class (recommended for complex games)
class EventHandler(tcod.event.EventDispatch[None]):
    def ev_quit(self, event: tcod.event.Quit) -> None:
        raise SystemExit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        if event.sym == tcod.event.KeySym.ESCAPE:
            raise SystemExit()
        elif event.sym == tcod.event.KeySym.UP:
            return ("move", 0, -1)
        elif event.sym == tcod.event.KeySym.DOWN:
            return ("move", 0, 1)
        # ... more key handling ...
        return None

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> None:
        # Handle mouse clicks
        print(f"Clicked at tile: {event.tile}")

handler = EventHandler()
for event in tcod.event.wait():
    action = handler.dispatch(event)
    if action:
        # Process action
        pass
```

### Complete KeySym Reference (v19.x)

**CRITICAL: Letter keys are UPPERCASE in v19+!**

```python
# Arrow keys (navigation)
tcod.event.KeySym.UP
tcod.event.KeySym.DOWN
tcod.event.KeySym.LEFT
tcod.event.KeySym.RIGHT

# Letter keys (UPPERCASE in v19+!)
tcod.event.KeySym.A  # The 'A' key
tcod.event.KeySym.B  # The 'B' key
# ... through ...
tcod.event.KeySym.Z  # The 'Z' key

# Number keys (top row)
tcod.event.KeySym.N0, N1, N2, N3, N4, N5, N6, N7, N8, N9
# Or with Python 3.13+: tcod.event.KeySym["0"] through KeySym["9"]

# Numpad keys
tcod.event.KeySym.KP_0, KP_1, KP_2, KP_3, KP_4, KP_5, KP_6, KP_7, KP_8, KP_9
tcod.event.KeySym.KP_ENTER
tcod.event.KeySym.KP_PLUS, KP_MINUS, KP_MULTIPLY, KP_DIVIDE

# Function keys
tcod.event.KeySym.F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12

# Special/control keys
tcod.event.KeySym.ESCAPE
tcod.event.KeySym.RETURN  # Enter key
tcod.event.KeySym.SPACE
tcod.event.KeySym.TAB
tcod.event.KeySym.BACKSPACE
tcod.event.KeySym.DELETE
tcod.event.KeySym.INSERT
tcod.event.KeySym.HOME
tcod.event.KeySym.END
tcod.event.KeySym.PAGEUP
tcod.event.KeySym.PAGEDOWN

# Modifier keys
tcod.event.KeySym.LSHIFT, RSHIFT
tcod.event.KeySym.LCTRL, RCTRL
tcod.event.KeySym.LALT, RALT

# Punctuation/symbols
tcod.event.KeySym.MINUS
tcod.event.KeySym.EQUALS
tcod.event.KeySym.LEFTBRACKET, RIGHTBRACKET
tcod.event.KeySym.BACKSLASH
tcod.event.KeySym.SEMICOLON
tcod.event.KeySym.QUOTE
tcod.event.KeySym.COMMA, PERIOD, SLASH
```

### Modifier Key Handling

```python
# Modifier constants
tcod.event.KMOD_SHIFT   # Either shift key
tcod.event.KMOD_CTRL    # Either ctrl key
tcod.event.KMOD_ALT     # Either alt key
tcod.event.KMOD_LSHIFT  # Left shift specifically
tcod.event.KMOD_RSHIFT  # Right shift specifically

# Check if modifiers are pressed
def ev_keydown(self, event: tcod.event.KeyDown):
    # Check single modifier
    if event.mod & tcod.event.KMOD_SHIFT:
        print("Shift is held")

    # Check multiple modifiers
    if (event.mod & tcod.event.KMOD_CTRL) and (event.mod & tcod.event.KMOD_SHIFT):
        print("Ctrl+Shift held")

    # Distinguish uppercase from modifier
    if event.sym == tcod.event.KeySym.A:
        if event.mod & tcod.event.KMOD_SHIFT:
            return self.handle_uppercase_a()
        else:
            return self.handle_lowercase_a()
```

### Mouse Event Handling

```python
class EventHandler(tcod.event.EventDispatch[None]):
    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        """Mouse moved."""
        # event.tile = (x, y) tile coordinates
        # event.position = (x, y) pixel coordinates
        print(f"Mouse over tile: {event.tile}")

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> None:
        """Mouse button pressed."""
        # event.button = 1 (left), 2 (middle), 3 (right)
        if event.button == 1:  # Left click
            print(f"Left clicked tile: {event.tile}")
        elif event.button == 3:  # Right click
            print(f"Right clicked tile: {event.tile}")

    def ev_mousebuttonup(self, event: tcod.event.MouseButtonUp) -> None:
        """Mouse button released."""
        pass

    def ev_mousewheel(self, event: tcod.event.MouseWheel) -> None:
        """Mouse wheel scrolled."""
        # event.y > 0 = scroll up, < 0 = scroll down
        if event.y > 0:
            self.scroll_up()
        elif event.y < 0:
            self.scroll_down()
```

### Context Event Conversion

For accurate tile coordinates, convert events through context:

```python
for event in tcod.event.wait():
    # Convert to get accurate tile coordinates
    event = context.convert_event(event)

    if isinstance(event, tcod.event.MouseMotion):
        # Now event.tile is accurate to your console size
        print(f"Mouse at tile: {event.tile}")
```

---

## Community Examples and Patterns

### Example 1: Complete EventHandler from Roguelike Tutorial

A production-ready event handler pattern from "Yet Another Roguelike Tutorial":

```python
from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import tcod.event

if TYPE_CHECKING:
    from engine import Engine

class Action:
    """Base action class."""
    def perform(self, engine: Engine) -> None:
        raise NotImplementedError()

class MovementAction(Action):
    def __init__(self, dx: int, dy: int):
        self.dx = dx
        self.dy = dy

    def perform(self, engine: Engine) -> None:
        dest_x = engine.player.x + self.dx
        dest_y = engine.player.y + self.dy
        if engine.game_map.in_bounds(dest_x, dest_y):
            if not engine.game_map.tiles["walkable"][dest_x, dest_y]:
                return  # Blocked by wall
            if engine.game_map.get_blocking_entity_at(dest_x, dest_y):
                return  # Blocked by entity
            engine.player.move(self.dx, self.dy)

class EscapeAction(Action):
    def perform(self, engine: Engine) -> None:
        raise SystemExit()

class EventHandler(tcod.event.EventDispatch[Optional[Action]]):
    """Main event handler - returns Actions based on input."""

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        return EscapeAction()

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None
        key = event.sym

        # Movement keys (vi keys + arrows)
        if key == tcod.event.KeySym.UP or key == tcod.event.KeySym.K:
            action = MovementAction(dx=0, dy=-1)
        elif key == tcod.event.KeySym.DOWN or key == tcod.event.KeySym.J:
            action = MovementAction(dx=0, dy=1)
        elif key == tcod.event.KeySym.LEFT or key == tcod.event.KeySym.H:
            action = MovementAction(dx=-1, dy=0)
        elif key == tcod.event.KeySym.RIGHT or key == tcod.event.KeySym.L:
            action = MovementAction(dx=1, dy=0)
        # Diagonal movement (vi keys)
        elif key == tcod.event.KeySym.Y:
            action = MovementAction(dx=-1, dy=-1)
        elif key == tcod.event.KeySym.U:
            action = MovementAction(dx=1, dy=-1)
        elif key == tcod.event.KeySym.B:
            action = MovementAction(dx=-1, dy=1)
        elif key == tcod.event.KeySym.N:
            action = MovementAction(dx=1, dy=1)
        elif key == tcod.event.KeySym.ESCAPE:
            action = EscapeAction()

        return action

# Usage in game loop
engine = Engine(player=player, game_map=game_map)
event_handler = EventHandler()

while True:
    engine.render(console, context)

    for event in tcod.event.wait():
        action = event_handler.dispatch(event)
        if action:
            action.perform(engine)
```

### Example 2: Multi-State Event System

Advanced pattern for handling different game states (from RogueBasin tutorials):

```python
from typing import Optional
import tcod.event

class BaseEventHandler(tcod.event.EventDispatch["BaseEventHandler"]):
    """Base class that returns itself or a new handler."""

    def handle_events(self, event: tcod.event.Event) -> "BaseEventHandler":
        """Handle event and return next active handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        return self

class MainGameEventHandler(BaseEventHandler):
    """Handler for main gameplay."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        if event.sym == tcod.event.KeySym.I:
            return InventoryEventHandler()  # Switch to inventory mode
        elif event.sym == tcod.event.KeySym.ESCAPE:
            return MainMenuEventHandler()  # Switch to main menu
        # ... handle game movement ...
        return None

class InventoryEventHandler(BaseEventHandler):
    """Handler for inventory screen."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        if event.sym == tcod.event.KeySym.ESCAPE or event.sym == tcod.event.KeySym.I:
            return MainGameEventHandler()  # Return to game
        # Handle item selection with letter keys
        if event.sym >= tcod.event.KeySym.A and event.sym <= tcod.event.KeySym.Z:
            index = event.sym - tcod.event.KeySym.A
            self.use_item(index)
        return None

class MainMenuEventHandler(BaseEventHandler):
    """Handler for main menu."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        if event.sym == tcod.event.KeySym.N:  # New game
            return MainGameEventHandler()
        elif event.sym == tcod.event.KeySym.Q:  # Quit
            raise SystemExit()
        return None

# Usage
event_handler = MainMenuEventHandler()
while True:
    render(console, context, event_handler)
    for event in tcod.event.wait():
        event_handler = event_handler.handle_events(event)
```

### Example 3: FOV-based Entity Rendering (Official TCOD Pattern)

Complete example showing FOV integration with entity rendering:

```python
import tcod
import numpy as np
from typing import List, Tuple

class Entity:
    def __init__(self, x: int, y: int, char: str, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.char = char
        self.color = color

class GameMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # Tiles: structured array with walkable and transparent
        self.tiles = np.zeros((width, height),
            dtype=[("walkable", bool), ("transparent", bool)])

    def compute_fov(self, pov_x: int, pov_y: int, radius: int = 8) -> np.ndarray:
        """Compute FOV and return visible tiles array."""
        # Extract transparency data (note: y,x indexing for TCOD)
        transparency = self.tiles["transparent"].T  # Transpose for (y,x) order

        return tcod.map.compute_fov(
            transparency=transparency,
            pov=(pov_y, pov_x),
            radius=radius,
            light_walls=True,
            algorithm=tcod.FOV_SYMMETRIC_SHADOWCAST
        )

    def render(self, console: tcod.console.Console, fov: np.ndarray,
               entities: List[Entity]) -> None:
        """Render map and entities within FOV."""
        for x in range(self.width):
            for y in range(self.height):
                # Check if in FOV (remember: fov uses [y, x] indexing)
                visible = fov[y, x]

                if self.tiles["walkable"][x, y]:
                    if visible:
                        console.print(x, y, ".", fg=(255, 255, 255))
                    else:
                        console.print(x, y, ".", fg=(100, 100, 100))
                else:
                    if visible:
                        console.print(x, y, "#", fg=(255, 255, 255))
                    else:
                        console.print(x, y, "#", fg=(80, 80, 80))

        # Render entities only if in FOV
        for entity in entities:
            if fov[entity.y, entity.x]:  # Note: [y, x] indexing!
                console.print(entity.x, entity.y, entity.char, fg=entity.color)

# Usage
game_map = GameMap(80, 50)
player = Entity(40, 25, "@", (255, 255, 255))
enemies = [Entity(45, 25, "G", (0, 255, 0)), Entity(35, 20, "O", (255, 0, 0))]

fov = game_map.compute_fov(player.x, player.y, radius=10)
game_map.render(console, fov, [player] + enemies)
```

### Example 4: Advanced Pathfinding with Dijkstra Maps (Community Pattern)

Using TCOD pathfinding for smarter AI (flee, ambush, etc.):

```python
import tcod
import numpy as np

def create_dijkstra_map(game_map, goals: list, max_cost: int = 100):
    """Create Dijkstra map showing cost to reach any goal."""
    cost_map = np.ones((game_map.width, game_map.height), dtype=np.int32)
    for x in range(game_map.width):
        for y in range(game_map.height):
            if not game_map.walkable[x, y]:
                cost_map[x, y] = 0  # Walls impassable

    graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
    pathfinder = tcod.path.Pathfinder(graph)

    # Add all goals as roots
    for goal_x, goal_y in goals:
        pathfinder.add_root((goal_x, goal_y))

    # Distance map shows cost to reach nearest goal from any position
    return pathfinder.distance

def enemy_chase_behavior(enemy, player, game_map):
    """Enemy moves toward player using pathfinding."""
    dijkstra = create_dijkstra_map(game_map, [(player.x, player.y)])

    # Find lowest cost neighbor
    best_move = None
    best_cost = dijkstra[enemy.x, enemy.y]

    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = enemy.x + dx, enemy.y + dy
        if game_map.in_bounds(nx, ny) and game_map.walkable[nx, ny]:
            cost = dijkstra[nx, ny]
            if cost < best_cost:
                best_cost = cost
                best_move = (dx, dy)

    return best_move

def enemy_flee_behavior(enemy, player, game_map):
    """Enemy flees from player - moves to highest cost neighbor."""
    dijkstra = create_dijkstra_map(game_map, [(player.x, player.y)])

    # Find HIGHEST cost neighbor (furthest from player)
    best_move = None
    best_cost = dijkstra[enemy.x, enemy.y]

    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = enemy.x + dx, enemy.y + dy
        if game_map.in_bounds(nx, ny) and game_map.walkable[nx, ny]:
            cost = dijkstra[nx, ny]
            if cost > best_cost:
                best_cost = cost
                best_move = (dx, dy)

    return best_move
```

### Example 5: Hello World - Official TCOD Getting Started

The canonical minimal TCOD program (from official docs):

```python
#!/usr/bin/env python3
"""Hello World example from python-tcod docs."""
import tcod

# Load font
tileset = tcod.tileset.load_tilesheet(
    "dejavu10x10_gs_tc.png",
    columns=32,
    rows=8,
    charmap=tcod.tileset.CHARMAP_TCOD
)

# Create console and context
with tcod.context.new(
    columns=80,
    rows=60,
    tileset=tileset,
    title="Hello World",
    vsync=True,
) as context:
    console = tcod.console.Console(80, 60)

    # Main loop
    while True:
        console.clear()
        console.print(x=1, y=1, string="Hello World")
        context.present(console)

        # Event loop
        for event in tcod.event.wait():
            if isinstance(event, tcod.event.Quit):
                raise SystemExit()
```

### Example 6: Procedural Generation with BSP (Binary Space Partitioning)

Using TCOD's BSP for dungeon generation:

```python
import tcod
import numpy as np

class DungeonGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles = np.zeros((width, height), dtype=bool)  # False = wall

    def generate(self):
        """Generate dungeon using BSP."""
        # Create BSP tree
        bsp = tcod.bsp.BSP(0, 0, self.width, self.height)
        bsp.split_recursive(
            depth=5,
            min_width=6,
            min_height=6,
            max_horizontal_ratio=1.5,
            max_vertical_ratio=1.5,
        )

        # Create rooms and corridors
        for node in bsp.pre_order():
            if node.children:
                # Node has children - connect them with corridor
                node1, node2 = node.children
                self._create_corridor(node1.center, node2.center)
            else:
                # Leaf node - create room
                self._create_room(node)

    def _create_room(self, node: tcod.bsp.BSP):
        """Create a room within BSP node."""
        # Leave 1 tile border for walls
        x1, y1 = node.x + 1, node.y + 1
        x2, y2 = node.x + node.width - 1, node.y + node.height - 1

        for x in range(x1, x2):
            for y in range(y1, y2):
                self.tiles[x, y] = True  # Walkable

    def _create_corridor(self, start: tuple, end: tuple):
        """Connect two points with L-shaped corridor."""
        x1, y1 = start
        x2, y2 = end

        # Horizontal then vertical
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x, y1] = True
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x2, y] = True

# Usage
dungeon = DungeonGenerator(80, 50)
dungeon.generate()
```

---

## Best Practices

### 1. Coordinate Order Consistency
- **FOV**: Use (y, x) for `pov` and array indexing
- **Pathfinding**: Use (x, y) for positions
- **Console**: Direct array access uses [y, x]
- **Your code**: Pick one convention and convert at boundaries

### 2. Performance Optimization
- **Cache transparency maps** - only rebuild when map changes
- **Cache FOV results** - especially for multiple queries from same position
- **Limit cache size** - clear old entries to prevent memory bloat
- **Use numpy arrays** - much faster than Python lists
- **Pre-allocate arrays** - don't recreate cost/transparency maps each frame

### 3. Pathfinding Tips
- Always validate path length > 1 before using
- Check path length isn't unreasonably long (stuck detection)
- Use cost maps to create smart AI behavior (prefer shadows, avoid enemies)
- Set diagonal cost ≈ 1.4x cardinal cost for realistic movement

### 4. FOV Tips
- Use `FOV_RESTRICTIVE` or `FOV_SYMMETRIC_SHADOWCAST` for best results
- Set `light_walls=True` to include walls in visible area
- Cache FOV computations - they're expensive
- Use distance checks before FOV for early exit optimization

### 5. Console Rendering
- Clear console at start of each frame
- Use `console.tiles_rgb` for fastest direct access
- Always use color tuples, not ColorRGB objects
- Use `draw_frame` for boxes/borders - it's optimized

### 6. Common Pitfalls to Avoid
- **Mixing (x,y) and (y,x)** - most common TCOD mistake!
- **Not checking path length** - can cause index errors
- **Recreating arrays every frame** - terrible performance
- **Zero-cost tiles in pathfinding** - means impassable, not free
- **Forgetting to clear caches** - can cause stale FOV after map changes

---

## Real-World Code Examples (from this project)

### FOV with Caching
```python
def can_see_position(self, start: Position, end: Position, vision_range: int) -> bool:
    """Check visibility using TCOD FOV with caching."""
    # Early distance check
    if start.distance_to(end) > vision_range:
        return False

    # Cache FOV computations
    cache_key = (start.x, start.y, vision_range)
    if cache_key not in self._fov_cache:
        transparency = self._get_transparency_map()
        fov = tcod.map.compute_fov(
            transparency=transparency,
            pov=(start.y, start.x),  # y, x order!
            radius=vision_range,
            algorithm=tcod.libtcodpy.FOV_SYMMETRIC_SHADOWCAST
        )

        if len(self._fov_cache) > 50:
            self._fov_cache.clear()
        self._fov_cache[cache_key] = fov

    return self._fov_cache[cache_key][end.y, end.x]
```

### Pathfinding for Enemy AI
```python
def find_path_to_player(self, game_map, player_pos):
    """Find path using TCOD pathfinding."""
    # Create cost map
    cost_map = np.zeros((game_map.width, game_map.height), dtype=np.int32)
    for x in range(game_map.width):
        for y in range(game_map.height):
            cost_map[x, y] = 10 if game_map.is_walkable(x, y) else 0

    # Setup pathfinding
    graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
    pathfinder = tcod.path.Pathfinder(graph)
    pathfinder.add_root((self.x, self.y))

    # Get path
    path = pathfinder.path_to((player_pos.x, player_pos.y))

    # Validate path
    if len(path) >= 2:
        return path[1]  # Next step
    return None
```

### Console Rendering with Safe Colors
```python
def draw_bordered_box(console: tcod.console.Console, x: int, y: int,
                     width: int, height: int, border_color: tuple, bg_color: tuple):
    """Draw box with proper color handling."""
    # Ensure colors are tuples
    border_color = tuple(border_color) if hasattr(border_color, '__iter__') else border_color
    bg_color = tuple(bg_color) if hasattr(bg_color, '__iter__') else bg_color

    # Fill background
    console.draw_rect(x, y, width, height, ord(' '), fg=(255,255,255), bg=bg_color)

    # Draw border
    console.draw_frame(x, y, width, height, fg=border_color, bg=bg_color, clear=False)
```

---

## Additional Resources

### Official Documentation
- Main docs: https://python-tcod.readthedocs.io/en/latest/
- Tutorial: https://python-tcod.readthedocs.io/en/latest/tutorial/index.html
- API Reference (FOV): https://python-tcod.readthedocs.io/en/latest/tcod/map.html
- API Reference (Pathfinding): https://python-tcod.readthedocs.io/en/latest/tcod/path.html

### Tutorials
- Yet Another Roguelike Tutorial: https://rogueliketutorials.com/tutorials/tcod/v2/
- Official Getting Started: https://python-tcod.readthedocs.io/en/latest/tcod/getting-started.html

### GitHub
- python-tcod repo: https://github.com/libtcod/python-tcod
- Examples: https://github.com/libtcod/python-tcod/tree/main/examples

---

## When to Use This Skill

Invoke this skill when:
- Working with TCOD pathfinding or FOV systems
- **Debugging event handling or KeySym issues** (especially v19+ uppercase letter keys!)
- Debugging coordinate order issues (x,y vs y,x)
- Optimizing TCOD performance (caching, numpy arrays)
- Implementing new AI behaviors using pathfinding
- Setting up rendering pipelines with TCOD contexts
- Troubleshooting TCOD-related errors or crashes
- Questions about TCOD API usage or best practices
- Implementing new vision/detection systems
- Creating procedural generation with TCOD tools
- **Need examples of production-ready event handler patterns**
- **Want to see community-tested approaches** to common roguelike problems

This skill provides deep expertise in python-tcod 19.x with focus on practical, production-ready patterns used in real roguelike games. Includes official examples, community patterns from popular tutorials (Yet Another Roguelike Tutorial, RogueBasin), and proven architectural approaches.
