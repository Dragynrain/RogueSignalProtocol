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
class FixedLevelData:
    """Container for fixed level layout data."""

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


# Prologue layout: 28x24 tiles - Linear tutorial with forced paths
#
# DESIGN: Right side is walled off - player MUST traverse left corridor.
# Each section forces player through the teaching content, no bypassing.
#
# Section 1 (rows 1-3): MELEE - X blocks the only door, must kill to pass
# Section 2 (rows 4-8): TURN-BASED + WAIT - patrol in corridor, timing matters
# Section 3 (rows 9-12): FOV + BLINDSPOTS - Scanner blocks path, use blindspots
# Section 4 (rows 13-15): ALERT + ESCAPE - patrol, escape corridor to break LOS
# Section 5 (rows 16-18): EXPLOITS + HEAT - wall blocks melee, ranged needed
# Section 6 (rows 19-22): SYNTHESIS - stealth path via blindspots or fight
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
#...S.......################
#sss........################
###+########################
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
    patrol_routes = {
        # Section 2: P at (4,6) patrols horizontally in corridor
        (4, 6): [Position(2, 6), Position(9, 6)],
        # Section 4: P at (4,12) patrols in section with recovery node
        (4, 12): [Position(2, 12), Position(9, 12)],
        # Section 5: P at (6,15) behind wall - player must use ranged
        (6, 15): [Position(6, 15), Position(11, 15)],
        # Section 6: P at (5,21) guards long corridor to gateway
        (5, 21): [Position(5, 21), Position(14, 21)],
    }

    return FixedLevelData(
        layout=lines,
        name="First Infiltration",
        tutorial_triggers={},
        enemy_overrides={},
        patrol_routes=patrol_routes,
    )
