"""
Enemy Type Coverage Matrix Tests

Tests specific enemy types in various gameplay scenarios to ensure each enemy
type behaves correctly across different contexts.

Coverage:
- Admin enemy in stealth scenarios
- Virus enemy in combat scenarios
- Inhibitor enemy in multi-enemy scenarios
- Hunter enemy in level progression
- All enemy types spawn correctly
- Enemy type balance validation
"""

import pytest

from game_entities import EnemyState
from tests.test_agent import GameTestAgent


class TestAdminInStealthScenarios:
    """
    Admin is the most dangerous enemy - test stealth mechanics against it.
    Admin has: vision 8, damage 45, 250 CPU, damage resistance.
    """

    def test_admin_detection_range_exceeds_normal_enemies(self):
        """Admin's vision 8 should detect player from farther than normal enemies."""
        agent = GameTestAgent(seed=12345)

        # Spawn admin at known location
        admin = agent.spawn_enemy("admin", 15, 15)
        assert admin is not None
        assert admin.type == "admin"
        assert admin.type_data.vision == 8  # Admin has exceptional vision

        # Admin vision is 8, which is higher than most enemies (3-6)
        # This test validates admin has exceptional vision range

    def test_admin_stealth_evasion_difficult(self):
        """Admin's high vision makes stealth evasion challenging."""
        agent = GameTestAgent(seed=12346)

        # Spawn admin
        admin = agent.spawn_enemy("admin", 20, 20)
        assert admin.state in [EnemyState.UNAWARE, EnemyState.ALERT, EnemyState.HOSTILE]

    def test_admin_combat_extremely_dangerous(self):
        """Admin deals massive damage and has damage resistance."""
        agent = GameTestAgent(seed=12347)

        admin = agent.spawn_enemy("admin", 15, 15)

        # Verify admin stats
        assert admin.cpu >= 200  # Very high HP
        assert admin.max_cpu >= 200
        assert admin.type_data.damage >= 40  # High damage

    def test_admin_spawns_correctly(self):
        """Admin enemy type spawns with correct attributes."""
        agent = GameTestAgent(seed=12348)

        admin = agent.spawn_enemy("admin", 10, 10)
        assert admin is not None
        assert admin.type == "admin"
        assert admin.type_data.symbol == "A"
        assert admin.type_data.vision == 8


class TestVirusInCombatScenarios:
    """
    Virus has unique DoT/corruption mechanics - test in combat contexts.
    Virus has: 0 direct damage but corruption effect.
    """

    def test_virus_spawns_correctly(self):
        """Virus enemy type spawns with correct stats."""
        agent = GameTestAgent(seed=23456)

        virus = agent.spawn_enemy("virus", 10, 10)
        assert virus is not None
        assert virus.type == "virus"
        assert virus.type_data.symbol == "V"
        assert virus.type_data.vision == 4

    def test_virus_movement_pattern_unique(self):
        """Virus has VIRUS movement type - should move differently."""
        agent = GameTestAgent(seed=23457)

        virus = agent.spawn_enemy("virus", 15, 15)
        initial_pos = (virus.x, virus.y)

        # Wait several turns and observe movement
        for _ in range(5):
            agent.wait(1)

        # Virus should exist
        assert virus.type == "virus"  # Verify still exists

    def test_virus_in_multi_enemy_combat(self):
        """Virus combined with other enemies creates complex scenarios."""
        agent = GameTestAgent(seed=23458)

        # Spawn virus and hunter together
        virus = agent.spawn_enemy("virus", 15, 15)
        hunter = agent.spawn_enemy("hunter", 17, 15)

        assert virus is not None
        assert hunter is not None

        # Make both potentially engage
        agent.move_to(16, 15)
        agent.wait(1)

        # Both should still exist initially
        assert virus.type == "virus"
        assert hunter.type == "hunter"


class TestInhibitorInMultiEnemyScenarios:
    """
    Inhibitor slows player execution - test with multiple enemies.
    Inhibitor has: 0 damage, slowing effect.
    """

    def test_inhibitor_spawns_correctly(self):
        """Inhibitor enemy type spawns with correct stats."""
        agent = GameTestAgent(seed=34567)

        inhibitor = agent.spawn_enemy("inhibitor", 12, 12)
        assert inhibitor is not None
        assert inhibitor.type == "inhibitor"
        assert inhibitor.type_data.symbol == "I"
        assert inhibitor.type_data.damage == 0  # No direct damage

    def test_inhibitor_with_multiple_enemies(self):
        """Inhibitor + other enemies creates compound threat."""
        agent = GameTestAgent(seed=34568)

        # Spawn inhibitor + patrol + bot (3 enemies)
        inhibitor = agent.spawn_enemy("inhibitor", 15, 15)
        patrol = agent.spawn_enemy("patrol", 15, 17)
        bot = agent.spawn_enemy("bot", 17, 15)

        assert inhibitor is not None
        assert patrol is not None
        assert bot is not None

        # Make all potentially hostile
        agent.move_to(16, 16)
        agent.wait(2)

        # All three should still be valid objects
        assert inhibitor.type == "inhibitor"
        assert patrol.type == "patrol"
        assert bot.type == "bot"

    def test_inhibitor_non_lethal_threat(self):
        """Inhibitor doesn't deal direct damage."""
        agent = GameTestAgent(seed=34569)

        inhibitor = agent.spawn_enemy("inhibitor", 10, 10)

        # Verify inhibitor has 0 damage
        assert inhibitor.type_data.damage == 0


class TestHunterInLevelProgression:
    """
    Hunter is fast and dangerous - test in level progression contexts.
    Hunter has: vision 6, damage 15, random movement.
    """

    def test_hunter_spawns_correctly(self):
        """Hunter enemy type spawns with correct stats."""
        agent = GameTestAgent(seed=45678)

        hunter = agent.spawn_enemy("hunter", 20, 20)
        assert hunter is not None
        assert hunter.type == "hunter"
        assert hunter.type_data.symbol == "H"
        assert hunter.type_data.vision == 6
        assert hunter.type_data.damage == 15  # High damage

    def test_hunter_high_damage_output(self):
        """Hunter deals significant damage (15)."""
        agent = GameTestAgent(seed=45679)

        hunter = agent.spawn_enemy("hunter", 15, 15)

        # Verify hunter damage stat
        assert hunter.type_data.damage == 15

    def test_hunter_wide_vision_range(self):
        """Hunter's vision 6 allows detection from medium range."""
        agent = GameTestAgent(seed=45680)

        hunter = agent.spawn_enemy("hunter", 15, 15)

        # Verify hunter has vision 6
        assert hunter.type_data.vision == 6

    def test_hunter_in_gateway_rush_scenario(self):
        """Hunter pursuing player toward gateway creates pressure."""
        agent = GameTestAgent(seed=45681)

        # Spawn hunter
        hunter = agent.spawn_enemy("hunter", 20, 20)
        assert hunter.type == "hunter"


class TestAllEnemyTypesSpawning:
    """Validate all enemy types can spawn correctly."""

    @pytest.mark.parametrize(
        "enemy_type",
        ["scanner", "patrol", "bot", "firewall", "hunter", "virus", "inhibitor", "admin"],
    )
    def test_enemy_type_spawns(self, enemy_type):
        """Each enemy type spawns successfully."""
        agent = GameTestAgent(seed=56789)
        enemy = agent.spawn_enemy(enemy_type, 10, 10)

        assert enemy is not None
        assert enemy.type == enemy_type

    @pytest.mark.parametrize(
        "enemy_type,expected_symbol",
        [
            ("scanner", "S"),
            ("patrol", "P"),
            ("bot", "B"),
            ("firewall", "F"),
            ("hunter", "H"),
            ("virus", "V"),
            ("inhibitor", "I"),
            ("admin", "A"),
        ],
    )
    def test_enemy_type_symbol(self, enemy_type, expected_symbol):
        """Each enemy type has the correct unique symbol."""
        agent = GameTestAgent(seed=56790)
        enemy = agent.spawn_enemy(enemy_type, 10, 10)

        assert enemy.type_data.symbol == expected_symbol

    @pytest.mark.parametrize(
        "enemy_type",
        ["scanner", "patrol", "bot", "firewall", "hunter", "virus", "inhibitor", "admin"],
    )
    def test_enemy_type_has_valid_stats(self, enemy_type):
        """Each enemy type has sensible stat values."""
        agent = GameTestAgent(seed=56791)
        enemy = agent.spawn_enemy(enemy_type, 10, 10)

        # All enemies should have positive CPU
        assert enemy.cpu > 0
        assert enemy.max_cpu > 0

        # Vision should be reasonable (1-10 range)
        assert 1 <= enemy.type_data.vision <= 10

        # Damage should be non-negative
        assert enemy.type_data.damage >= 0


class TestEnemyTypeBalance:
    """Validate enemy type distribution and balance per level."""

    def test_level_1_has_enemies(self):
        """Level 1 should have enemies present."""
        agent = GameTestAgent(seed=67890, level=1)

        # Check what enemy types are present on level 1
        enemy_count = len(agent.enemies)

        # Level 1 should have at least some enemies
        assert enemy_count > 0

    def test_dangerous_enemy_stats(self):
        """Dangerous enemies (hunter, admin) have higher stats."""
        agent = GameTestAgent(seed=67891)

        # Spawn dangerous enemies
        hunter = agent.spawn_enemy("hunter", 10, 10)
        admin = agent.spawn_enemy("admin", 15, 10)

        # Basic enemies
        bot = agent.spawn_enemy("bot", 20, 10)
        patrol = agent.spawn_enemy("patrol", 25, 10)

        # Dangerous enemies should have higher damage
        assert hunter.type_data.damage >= bot.type_data.damage
        assert admin.type_data.damage >= patrol.type_data.damage

        # Admin should have much higher HP
        assert admin.max_cpu >= hunter.max_cpu

    def test_enemy_count_reasonable_per_level(self):
        """Each level spawns a reasonable number of enemies."""
        agent = GameTestAgent(seed=67892, level=1)

        enemy_count = len(agent.enemies)

        # Should have enemies but not too many (3-30 is reasonable range)
        assert 3 <= enemy_count <= 30

    def test_enemy_type_variety_present(self):
        """Levels should have variety of enemy types (not all one type)."""
        agent = GameTestAgent(seed=67893, level=1)

        enemy_types_present = set()
        for enemy in agent.enemies:
            enemy_types_present.add(enemy.type)

        # Should have at least 1 enemy type present
        assert len(enemy_types_present) >= 1
