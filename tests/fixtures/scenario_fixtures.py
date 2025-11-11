"""
Scenario Fixtures - Advanced Test Scenarios

Additional fixture library for complex test scenarios:
- Full inventory fixture (max items, all exploits)
- Level 2/3 fixtures (skip level progression)
- Victory scenario fixture (one step from victory)
- Surrounded fixture variants (different enemy types/counts)
- Performance stress fixture (many enemies + particles)

These fixtures enable testing edge cases and complex gameplay scenarios
without tedious manual setup.
"""

from unittest.mock import Mock
from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState
from game_config import GameSettings
from tests.fixtures.standard_patterns import create_basic_game_environment


def create_full_inventory_fixture():
    """
    Player with maximum items and all exploits equipped.

    Returns a GameEngine with:
    - Player with 50+ items in inventory
    - All 3 exploit slots filled with different exploits
    - Various code hacks (stacked by color)
    - Full CPU, moderate heat

    Perfect for: Inventory overflow tests, item management edge cases
    """
    engine = create_basic_game_environment()

    # Clear existing enemies for clean test
    engine.enemies = []

    # Set player to full resources
    engine.player.cpu = 100
    engine.player.max_cpu = 100
    engine.player.heat = 30
    engine.player.ram_total = 8

    # Fill inventory with items
    from game_data import GameData

    # Add 10 of each code hack color (stacks)
    for color in ["red", "green", "blue", "yellow", "purple"]:
        for _ in range(10):
            code_hack = {
                "id": f"code_hack_{color}",
                "name": f"{color.capitalize()} Code Hack",
                "type": "code_hack",
                "color": color,
                "ram_bonus": 1
            }
            engine.player.inventory.append(code_hack)

    # Add all exploits to inventory (not equipped yet)
    exploit_types = ["buffer_overflow", "packet_storm", "system_hop",
                     "traffic_masquerade", "data_spike", "logic_bomb",
                     "memory_leak", "exploit_scanner"]

    for i, exploit_name in enumerate(exploit_types[:8]):
        if exploit_name in GameData.EXPLOITS:
            exploit_data = GameData.EXPLOITS[exploit_name]
            exploit_item = {
                "id": f"exploit_{exploit_name}",
                "name": exploit_data.name,
                "type": "exploit",
                "exploit_type": exploit_name,
                "ram": exploit_data.ram,
                "heat": exploit_data.heat
            }
            engine.player.inventory.append(exploit_item)

    # Equip 3 exploits to slots
    if len([i for i in engine.player.inventory if i.get("type") == "exploit"]) >= 3:
        exploit_items = [i for i in engine.player.inventory if i.get("type") == "exploit"]
        engine.player.equipped_exploits = [
            exploit_items[0]["exploit_type"],
            exploit_items[1]["exploit_type"],
            exploit_items[2]["exploit_type"]
        ]

    return engine


def create_level_2_start_fixture():
    """
    Player starting level 2 with level 1 progress carried over.

    Returns a GameEngine with:
    - Level set to 2
    - Player with some items/upgrades from level 1
    - Moderate CPU (80/100), some heat (40)
    - 2-3 exploits equipped
    - Trace level reset to 0 (per level transition rules)

    Perfect for: Level progression tests, level 2 specific mechanics
    """
    engine = create_basic_game_environment()

    # Set to level 2
    engine.level = 2

    # Level 2 stats (carried from level 1)
    engine.player.cpu = 80
    engine.player.max_cpu = 100
    engine.player.heat = 40
    engine.player.trace_level = 0  # Resets on level transition

    # Add some code hacks (5 reds, 3 blues)
    for _ in range(5):
        engine.player.inventory.append({
            "id": "code_hack_red",
            "name": "Red Code Hack",
            "type": "code_hack",
            "color": "red",
            "ram_bonus": 1
        })

    for _ in range(3):
        engine.player.inventory.append({
            "id": "code_hack_blue",
            "name": "Blue Code Hack",
            "type": "code_hack",
            "color": "blue",
            "ram_bonus": 1
        })

    # Equip 2 exploits
    from game_data import GameData
    if "buffer_overflow" in GameData.EXPLOITS and "packet_storm" in GameData.EXPLOITS:
        engine.player.equipped_exploits = ["buffer_overflow", "packet_storm", None]

    return engine


def create_level_3_start_fixture():
    """
    Player starting level 3 (final level).

    Returns a GameEngine with:
    - Level set to 3
    - Player with accumulated items from levels 1-2
    - Good CPU (90/100), higher heat (50)
    - 3 exploits equipped
    - Trace level reset to 0

    Perfect for: Final level tests, victory scenario setup
    """
    engine = create_basic_game_environment()

    # Set to level 3
    engine.level = 3

    # Level 3 stats (strong from progression)
    engine.player.cpu = 90
    engine.player.max_cpu = 100
    engine.player.heat = 50
    engine.player.trace_level = 0  # Resets on level transition

    # Add many code hacks (10 reds, 5 blues, 5 greens)
    for _ in range(10):
        engine.player.inventory.append({
            "id": "code_hack_red",
            "name": "Red Code Hack",
            "type": "code_hack",
            "color": "red",
            "ram_bonus": 1
        })

    for _ in range(5):
        engine.player.inventory.append({
            "id": "code_hack_blue",
            "name": "Blue Code Hack",
            "type": "code_hack",
            "color": "blue",
            "ram_bonus": 1
        })

    for _ in range(5):
        engine.player.inventory.append({
            "id": "code_hack_green",
            "name": "Green Code Hack",
            "type": "code_hack",
            "color": "green",
            "ram_bonus": 1
        })

    # Equip 3 strong exploits
    from game_data import GameData
    exploits_to_equip = ["buffer_overflow", "packet_storm", "data_spike"]
    if all(e in GameData.EXPLOITS for e in exploits_to_equip):
        engine.player.equipped_exploits = exploits_to_equip

    return engine


def create_victory_ready_fixture():
    """
    Player at level 3 gateway, one step from victory.

    Returns a GameEngine with:
    - Level 3
    - Player positioned adjacent to gateway
    - Strong stats (near full HP, low heat)
    - Victory achievable in next move

    Perfect for: Victory screen tests, endgame validation
    """
    engine = create_level_3_start_fixture()

    # Find gateway on map
    gateway_pos = None
    for y in range(engine.game_map.height):
        for x in range(engine.game_map.width):
            if engine.game_map.tiles[y][x] == 11:  # Gateway tile
                gateway_pos = (x, y)
                break
        if gateway_pos:
            break

    # Position player adjacent to gateway if found
    if gateway_pos:
        # Try to place player next to gateway
        adjacent_positions = [
            (gateway_pos[0] + 1, gateway_pos[1]),
            (gateway_pos[0] - 1, gateway_pos[1]),
            (gateway_pos[0], gateway_pos[1] + 1),
            (gateway_pos[0], gateway_pos[1] - 1),
        ]

        for pos in adjacent_positions:
            if (0 <= pos[0] < engine.game_map.width and
                0 <= pos[1] < engine.game_map.height and
                (pos[0], pos[1]) not in engine.game_map.walls):
                engine.player.position.x = pos[0]
                engine.player.position.y = pos[1]
                break

    # Set player to strong stats (ready for victory)
    engine.player.cpu = 95
    engine.player.max_cpu = 100
    engine.player.heat = 20
    engine.player.trace_level = 10

    # Clear enemies near gateway to ensure clean victory
    engine.enemies = [e for e in engine.enemies
                      if abs(e.x - gateway_pos[0]) > 5 or abs(e.y - gateway_pos[1]) > 5]

    return engine


def create_surrounded_by_enemy_type_fixture(enemy_type: str = "bot", count: int = 4):
    """
    Player surrounded by N enemies of specific type.

    Args:
        enemy_type: Type of enemy ("bot", "scanner", "hunter", etc.)
        count: Number of enemies to surround player with (4, 6, or 8)

    Returns a GameEngine with:
    - Player at center position
    - {count} enemies of {enemy_type} surrounding player
    - All enemies in HOSTILE state
    - Player at moderate HP

    Perfect for: Combat stress tests, multi-enemy scenarios
    """
    engine = create_basic_game_environment()

    # Clear existing enemies
    engine.enemies = []

    # Position player at center
    player_x, player_y = 15, 15
    engine.player.position.x = player_x
    engine.player.position.y = player_y
    engine.player.cpu = 70  # Moderate HP (under pressure)
    engine.player.heat = 50

    # Surround positions (up to 8 surrounding tiles)
    surround_offsets = [
        (-1, -1), (0, -1), (1, -1),
        (-1,  0),          (1,  0),
        (-1,  1), (0,  1), (1,  1)
    ]

    # Create enemies at surrounding positions
    from tests.fixtures.real_game_data import create_real_enemy

    for i in range(min(count, 8)):
        offset = surround_offsets[i]
        enemy_x = player_x + offset[0]
        enemy_y = player_y + offset[1]

        # Verify position is valid (not in wall)
        if (enemy_x, enemy_y) not in engine.game_map.walls:
            enemy = create_real_enemy(enemy_type, enemy_x, enemy_y)
            enemy.state = EnemyState.HOSTILE  # Make immediately hostile
            engine.enemies.append(enemy)

    return engine


def create_performance_stress_fixture():
    """
    Scenario designed to stress test performance.

    Returns a GameEngine with:
    - 20+ enemies scattered across map
    - Player with full resources
    - Large explored area (500+ tiles)
    - Multiple particle sources active

    Perfect for: Performance tests, memory leak detection, long session validation
    """
    engine = create_basic_game_environment()

    # Clear existing enemies
    engine.enemies = []

    # Position player
    engine.player.position.x = 15
    engine.player.position.y = 15
    engine.player.cpu = 100
    engine.player.max_cpu = 100
    engine.player.heat = 0

    # Spawn 25 enemies across map (mix of types)
    from tests.fixtures.real_game_data import create_real_enemy

    enemy_types = ["bot", "scanner", "patrol", "hunter", "firewall"]
    positions = []

    # Generate 25 valid positions for enemies
    import random
    random.seed(42)  # Deterministic for testing

    for _ in range(25):
        for attempt in range(100):  # Try up to 100 times to find valid position
            x = random.randint(5, engine.game_map.width - 5)
            y = random.randint(5, engine.game_map.height - 5)

            if ((x, y) not in engine.game_map.walls and
                (x, y) not in positions and
                (x, y) != (engine.player.x, engine.player.y)):
                positions.append((x, y))
                break

    # Create enemies
    for i, pos in enumerate(positions[:25]):
        enemy_type = enemy_types[i % len(enemy_types)]
        enemy = create_real_enemy(enemy_type, pos[0], pos[1])
        engine.enemies.append(enemy)

    # Mark large area as explored (500+ tiles)
    for y in range(max(0, engine.player.y - 15), min(engine.game_map.height, engine.player.y + 15)):
        for x in range(max(0, engine.player.x - 15), min(engine.game_map.width, engine.player.x + 15)):
            engine.explored_tiles.add((x, y))

    return engine
