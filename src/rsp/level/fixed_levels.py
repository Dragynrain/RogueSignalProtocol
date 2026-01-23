"""
Fixed level layouts for tutorial and special levels.

Provides hand-designed maps that bypass procedural generation.
Uses ASCII art format for easy level design and modification.

INTEGRATION: Called from coordinator.py generate_procedural_level() when
network_config has fixed_layout=true. Returns spawn position and skips
all procedural generation.
"""

from dataclasses import dataclass, field

from rsp.entities.base import Position

# Map legend:
# '#' = Wall
# '.' = Floor
# 's' = Blind spot
# '@' = Player spawn
# '>' = Gateway (exit)
# 'c' = Cooling node
# 'r' = CPU recovery node
# 'g' = Ghost node
# 'X' = Damaged Scanner (5 HP, 0 damage - melee teaching)
# 'S' = Scanner enemy (STATIC, vision 5)
# 'P' = Patrol enemy (PATROL routes) - used for all mobile enemies in prologue
# 'e' = Exploit pickup (Code Injection - ranged combat)
# 'E' = Exploit pickup (Threat Scan - utility, not combat)
# 'd' = Code hack (data code)
# '+' = Door/passage marker (floor tile, visual only)


@dataclass
class PrologueLayoutData:
    """Container for prologue level layout data.

    Named specifically for prologue to clarify this is not a generic fixed level system.
    """

    layout: list[str]  # ASCII map rows (y=0 is top)
    name: str = "Fixed Level"  # Display name
    tutorial_triggers: dict[str, Position] = field(default_factory=dict)
    enemy_overrides: dict[str, dict] = field(default_factory=dict)
    # Patrol routes keyed by spawn position (x,y) tuple -> list of waypoint positions
    # If a patrol enemy spawns at a position in this dict, use these waypoints
    # instead of random route generation
    patrol_routes: dict[tuple[int, int], list[Position]] = field(default_factory=dict)

    @property
    def width(self) -> int:
        return len(self.layout[0]) if self.layout else 0

    @property
    def height(self) -> int:
        return len(self.layout)

    def get_char(self, x: int, y: int) -> str:
        """Get character at (x, y), '#' if out of bounds."""
        if 0 <= y < len(self.layout) and 0 <= x < len(self.layout[y]):
            return self.layout[y][x]
        return "#"

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a position is walkable (not a wall)."""
        char = self.get_char(x, y)
        return char != "#"

    def validate_patrol_routes(self) -> list[str]:
        """Validate that all patrol route positions are walkable floor tiles.

        Returns:
            List of error messages (empty if all routes are valid)
        """
        errors = []
        for spawn_pos, waypoints in self.patrol_routes.items():
            spawn_x, spawn_y = spawn_pos
            if not self.is_walkable(spawn_x, spawn_y):
                errors.append(
                    f"Patrol spawn at ({spawn_x},{spawn_y}) is not walkable"
                )

            for i, waypoint in enumerate(waypoints):
                if not self.is_walkable(waypoint.x, waypoint.y):
                    errors.append(
                        f"Patrol waypoint {i} at ({waypoint.x},{waypoint.y}) "
                        f"for spawn ({spawn_x},{spawn_y}) is not walkable"
                    )

        return errors


# Backwards compatibility alias
FixedLevelData = PrologueLayoutData


# Prologue section boundaries (Y coordinate ranges for each teaching section)
# These MUST stay in sync with the layout below and death hints in narrative_content.json.
# Used by death handler to provide contextual hints.
#
# Layout structure (doors as natural section dividers):
#   Rows 0-4:   Spawn + X enemy + door (melee teaching)
#   Rows 5-8:   First patrol corridor + door (timing/wait teaching)
#   Rows 9-12:  Scanner + blind spots + patrol + door (FOV/stealth teaching)
#   Rows 13-16: Exploit pickup + wall + patrol behind + door (ranged combat)
#   Rows 17-23: Ghost node + blind spots + final patrol + gateway (synthesis)
#
PROLOGUE_SECTION_BOUNDARIES = {
    1: (0, 4),    # Section 1: rows 0-4 (melee - X enemy blocks first door)
    2: (5, 8),    # Section 2: rows 5-8 (patrol timing - wait for opening)
    3: (9, 12),   # Section 3: rows 9-12 (FOV + blindspots - distance matters)
    4: (13, 16),  # Section 4: rows 13-16 (ranged combat - wall blocks melee)
    5: (17, 23),  # Section 5: rows 17-23 (synthesis - final patrol + gateway)
}


def get_prologue_section(y: int) -> int:
    """Get prologue section number for a given Y coordinate.

    Args:
        y: Player's Y coordinate

    Returns:
        Section number (1-5), or 5 if beyond last section
    """
    for section, (min_y, max_y) in PROLOGUE_SECTION_BOUNDARIES.items():
        if min_y <= y <= max_y:
            return section
    return 5  # Default to last section if beyond boundaries


# Prologue layout: 28x24 tiles - Linear tutorial with forced paths
#
# DESIGN: Right side is walled off - player MUST traverse left corridor.
# Each section forces player through the teaching content, no bypassing.
# Doors act as natural section dividers.
#
# Section 1 (rows 0-4): MELEE - X blocks the first door, must bump-attack to pass
# Section 2 (rows 5-8): TIMING - P patrols corridor, wait for opening to cross
# Section 3 (rows 9-12): FOV + BLINDSPOTS - S has vision, blind spots at range > 1
# Section 4 (rows 13-16): RANGED - Wall blocks melee, exploit required for P behind
# Section 5 (rows 17-23): SYNTHESIS - Ghost node, stealth path, final P, gateway
#
PROLOGUE_LAYOUT_RAW = """
############################
#@..########################
#...########################
#.X.########################
###+########################
#...........################
#...P.......################
#...........################
###+########################
#ss.S.......################
#sss........################
#sss########################
#...P.r.....################
###+########################
#c.e........################
#...#.P.....################
###+########################
#sss........################
#sss.g......################
#sss........################
#sss........################
#sss.P..........+.........>#
#...........################
############################
""".strip()


def get_prologue_layout() -> FixedLevelData:
    """Get the prologue level layout data.

    Linear tutorial with forced path through left corridor:
    - X at (2,3): Damaged scanner blocks door - teaches melee
    - P at (4,6): Patrol in corridor - teaches turn timing
    - S at (4,9): Scanner with blindspots at (1-3,10) - teaches FOV/stealth
    - P at (4,12): Patrol + recovery at (6,12) - teaches alert/escape
    - P at (6,15): Behind wall at (4,15) - teaches ranged combat
    - P at (5,21): Guards gateway path - final challenge
    """
    lines = PROLOGUE_LAYOUT_RAW.split("\n")

    # Fixed patrol routes for deterministic teaching
    # Key: spawn position (x,y), Value: list of patrol waypoints
    #
    # IMPORTANT: Routes avoid door positions (x=3) to create safe crossing windows.
    # Patrols start from x=5+ so player can cross at x=1-3 when patrol is right.
    patrol_routes = {
        # Section 2: P at (4,6) patrols RIGHT side of corridor (x=5-11)
        # Player crosses on LEFT (x=1-2) when patrol is far right
        (4, 6): [Position(5, 6), Position(11, 6)],
        # Section 4: P at (4,12) patrols RIGHT side, avoiding door at x=3
        # Recovery node at (6,12) is still reachable
        (4, 12): [Position(5, 12), Position(11, 12)],
        # Section 5: P at (6,15) behind wall - player must use ranged
        (6, 15): [Position(6, 15), Position(11, 15)],
        # Section 6: P at (5,21) patrols further right to create safe window
        (5, 21): [Position(6, 21), Position(14, 21)],
    }

    layout_data = PrologueLayoutData(
        layout=lines,
        name="First Infiltration",
        tutorial_triggers={},
        enemy_overrides={},
        patrol_routes=patrol_routes,
    )

    # Validate patrol routes at load time (fail-fast on config errors)
    errors = layout_data.validate_patrol_routes()
    if errors:
        import logging

        for error in errors:
            logging.error(f"PROLOGUE LAYOUT ERROR: {error}")
        raise ValueError(
            f"Invalid patrol routes in prologue layout: {len(errors)} errors. "
            "Check logs for details."
        )

    return layout_data
