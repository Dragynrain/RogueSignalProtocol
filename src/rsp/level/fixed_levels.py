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


# Prologue layout: 28x24 tiles - Linear tutorial with clear teaching sections
#
# DESIGN: Each section teaches 1-2 mechanics before player moves on.
# Linear flow (railroaded) ensures lessons happen in order.
#
# Section 1 (rows 1-3): MELEE - X blocks only exit, must bump-attack
# Section 2 (rows 4-7): TURN-BASED + WAIT - vertical patrol, time crossing
# Section 3 (rows 8-11): BLIND SPOTS - reachable via side path, not through Scanner
# Section 4 (rows 12-15): ALERT + ESCAPE - get spotted, learn to run
# Section 5 (rows 16-20): EXPLOITS + HEAT - ranged combat, cooling node
# Section 6 (rows 21-22): SYNTHESIS - choose stealth or combat path to gateway
#
PROLOGUE_LAYOUT_RAW = """
############################
#@..+#.....................#
#..X##.....................#
#...+#.....................#
####+#######################
#....#.....................#
#..P.+.....................#
#....#.....................#
####+#######################
#....+.....S...............#
#sss.#.....................#
#sss.+.....................#
####+#######################
#....+.......P.............#
#....#.....................#
#..r.+.....................#
####+#######################
#..c.+..e.....#............#
#....#........#............#
#....+........+.....P......#
####+##########+.......#+###
#sss.+........g........+..>#
#sss.#........P........#sss#
############################
""".strip()


def get_prologue_layout() -> FixedLevelData:
    """Get the prologue level layout data.

    Linear tutorial with clear teaching sections:
    - Section 2 P at (3,6): VERTICAL patrol - player times horizontal crossing
    - Section 4 P at (13,13): HORIZONTAL patrol - triggers alert lesson
    - Section 5 P at (20,19): Stationary ranged target for exploit practice
    - Section 6 P at (14,22): Guards center - player chooses stealth or combat
    """
    lines = PROLOGUE_LAYOUT_RAW.split("\n")

    # Fixed patrol routes for deterministic teaching
    # Key: spawn position (x,y), Value: list of patrol waypoints
    patrol_routes = {
        # Section 2: P at (3,6) patrols VERTICALLY (perpendicular to player path)
        # Player enters from north (door at 4,4), needs to cross east through door (5,6)
        # Vertical patrol creates timing window for horizontal crossing
        (3, 6): [Position(3, 5), Position(3, 7)],
        # Section 4: P at (13,13) patrols HORIZONTALLY across player's path
        # Likely to spot player - teaches alert escape mechanic
        (13, 13): [Position(11, 13), Position(15, 13)],
        # Section 5: P at (20,19) - minimal movement, ranged target
        # Wall at x=14 creates gap - encourages using exploit at range
        (20, 19): [Position(19, 19), Position(21, 19)],
        # Section 6: P at (14,22) guards center between stealth/combat paths
        (14, 22): [Position(12, 22), Position(16, 22)],
    }

    return FixedLevelData(
        layout=lines,
        name="First Infiltration",
        tutorial_triggers={},
        enemy_overrides={},
        patrol_routes=patrol_routes,
    )
