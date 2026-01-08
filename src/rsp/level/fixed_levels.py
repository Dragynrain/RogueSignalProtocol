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


# Prologue layout: 28x24 tiles
# Section 1: Turn-based + Wait + Movement queue (rows 0-5)
#   - X blocks ONLY path to door (walls at (2,3) and (3,4) force melee)
#   - P patrols corridor player must cross after X - forces wait/timing
# Section 2: Blind spot range trap (rows 6-12)
#   - Wall at (5,6) blocks quick bypass - player MUST try blind spots
#   - Blind spots at (1-3,6) adjacent to S - triggers TOO CLOSE lesson
#   - Safe blind spots at (3-4,9-10) range 3+ for successful hiding
# Section 3: Alert grace period + escape (rows 13-17)
#   - Rewards (r,d) moved to main escape corridor for visibility
# Section 4: Ranged combat + Heat (rows 18-21)
#   - P visible from corridor at range 5 - encourages Code Injection use
#   - Wall at x=11 creates longer walking path, hinting at ranged option
#   - Cooling node on left side accessible via door
# Section 5: Synthesis - choice of paths (rows 22-23)
PROLOGUE_LAYOUT_RAW = """
############################
#@..##....+.e.............#
#..X##....#...............#
#.#.+..P..#...............#
#..##.....#...............#
####+#####################
#sssS#....................#
#....#....................#
#....#....................#
#..ss#....................#
#..ss#....................#
#....+....................#
####+#########+###########
#..r.+.........+....sss...#
#.d..#....P....#....sss...#
#....#....+....#..XE.ss...#
#....#....+....+....sss...#
################....###+###
#..c.+.....#..............#
#....#.....#......P.......#
#....+.....+..............#
####+######+..........+.###
#sss.+.....g.......#....+>#
#sss.#.........P...#..sss.#
############################
""".strip()


def get_prologue_layout() -> FixedLevelData:
    """Get the prologue level layout data.

    Defines fixed patrol routes to guarantee teaching moments:
    - Section 1 P: Blocks corridor after X - player must wait/time passage
    - Section 3 P: Crosses entry path - guaranteed encounter
    - Section 4 P: Visible at range 5 from corridor - ranged combat target
    - Section 5 P: Guards center - player chooses path around
    """
    lines = PROLOGUE_LAYOUT_RAW.split("\n")

    # Fixed patrol routes for deterministic behavior
    # Key: spawn position (x,y), Value: list of patrol waypoints
    patrol_routes = {
        # Section 1: P at (7,3) patrols corridor player must cross
        (7, 3): [Position(5, 3), Position(9, 3)],
        # Section 3: P at (10,14) crosses entry - east-west patrol
        (10, 14): [Position(6, 14), Position(13, 14)],
        # Section 4: P at (18,19) patrols open area - visible from corridor
        (18, 19): [Position(17, 19), Position(20, 19)],
        # Section 5: P at (15,23) guards center between paths
        (15, 23): [Position(12, 23), Position(18, 23)],
    }

    return FixedLevelData(
        layout=lines,
        name="First Infiltration",
        tutorial_triggers={},
        enemy_overrides={},
        patrol_routes=patrol_routes,
    )
