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
# Section 2: Blind spot range trap (rows 6-12)
# Section 3: Alert grace period + escape (rows 13-17)
# Section 4: Ranged combat + Heat (rows 18-21)
# Section 5: Synthesis - choice of paths (rows 21-23)
PROLOGUE_LAYOUT_RAW = """
############################
#@..##..P.+.e.............#
#..X##....#...............#
#...+.....#...............#
#...#.....#...............#
####+#####################
#....+....................#
#....#.....sssssS.........#
#....#....................#
#....#..sss...............#
#....#..sss...............#
#....#....................#
####+#########+###########
#....+.........+....sss...#
#....#....P....#....sss...#
#....#....+....#..Edrss...#
#....#....+....+....sss...#
################....###+###
#....#..c..############...#
#....#.....####P####......#
#....+.....####.####......#
####+########.....##..+.###
#sss.+.....g.......#....+>#
#sss.#.........P...#..sss.#
############################
""".strip()


def get_prologue_layout() -> FixedLevelData:
    """Get the prologue level layout data."""
    lines = PROLOGUE_LAYOUT_RAW.split("\n")
    return FixedLevelData(
        layout=lines,
        name="First Infiltration",
        tutorial_triggers={},
        enemy_overrides={},
    )
