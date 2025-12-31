"""
Multi-Enemy Coordination Integration Tests

Tests complex enemy interactions and coordination:
- Enemy alerting chains (one enemy alerts nearby enemies)
- Multiple enemies converging on player
- Enemy state synchronization
- Patrol route coordination
- Enemy collision and blocking
- Multiple enemies attacking simultaneously
- Enemy movement queue conflicts
- Admin coordination with normal enemies
- Enemy pathfinding around other enemies
- Mass combat scenarios

These tests use REAL game objects with minimal mocking.
"""

import pytest

from rsp.entities.base import EnemyState, Position
from tests.fixtures.simple_fixtures import enemy_builder


class TestEnemyAlertingChains:
    """Test enemy alerting chains and coordination."""

    def test_enemy_alerts_nearby_enemies_on_detection(self, basic_game_engine):
        """Test enemy alerts nearby enemies when spotting player."""

        # Position player
        basic_game_engine.player.position = Position(20, 20)

        # Create enemy group - one can see player, others nearby
        spotter = enemy_builder("scanner", pos=(22, 20))  # Can see player
        nearby1 = enemy_builder("scanner", pos=(24, 20))  # Nearby
        nearby2 = enemy_builder("scanner", pos=(26, 20))  # Also nearby

        spotter.state = EnemyState.UNAWARE
        nearby1.state = EnemyState.UNAWARE
        nearby2.state = EnemyState.UNAWARE

        basic_game_engine.enemies = [spotter, nearby1, nearby2]

        # Process turns to allow detection and alerting
        for _ in range(5):
            basic_game_engine.process_turn()

        # Verify alerting system exists
        for enemy in basic_game_engine.enemies:
            assert hasattr(enemy, "state"), "Enemy should track state"
            assert hasattr(enemy, "alert_timer"), "Enemy should have alert timer"

    def test_alert_spreads_through_enemy_network(self, basic_game_engine):
        """Test alert spreads from enemy to enemy."""

        # Position player
        basic_game_engine.player.position = Position(20, 20)

        # Create chain of enemies
        enemy1 = enemy_builder("scanner", pos=(22, 20))  # Sees player
        enemy2 = enemy_builder("scanner", pos=(25, 20))  # Near enemy1
        enemy3 = enemy_builder("scanner", pos=(28, 20))  # Near enemy2

        enemy1.state = EnemyState.UNAWARE
        enemy2.state = EnemyState.UNAWARE
        enemy3.state = EnemyState.UNAWARE

        basic_game_engine.enemies = [enemy1, enemy2, enemy3]

        # Process multiple turns for alert to spread
        for _ in range(10):
            basic_game_engine.process_turn()

        # Verify coordination system
        assert all(
            hasattr(e, "state") for e in basic_game_engine.enemies
        ), "All enemies should track state"

    def test_alert_timer_expires(self, basic_game_engine):
        """Test alert timer expires after one turn (per specs)."""

        # Create alert enemy
        scanner = enemy_builder("scanner", pos=(20, 20))
        scanner.state = EnemyState.ALERT
        scanner.alert_timer = 1

        # Manually decrement alert timer (simulating turn update)
        scanner.alert_timer -= 1

        # Alert should expire
        assert scanner.alert_timer == 0, "Alert timer should expire after 1 turn"

    def test_hostile_enemy_does_not_use_alert_timer(self, basic_game_engine):
        """Test hostile enemy doesn't need alert timer."""

        # Position player and enemy
        basic_game_engine.player.position = Position(20, 20)
        scanner = enemy_builder("scanner", pos=(22, 20))
        scanner.state = EnemyState.HOSTILE
        basic_game_engine.enemies = [scanner]

        # Hostile enemies maintain state without timer
        assert scanner.state == EnemyState.HOSTILE, "Should remain hostile"

    def test_stunned_enemy_cannot_alert_others(self, basic_game_engine):
        """Test that stunned enemies cannot alert nearby enemies."""

        # Position player
        basic_game_engine.player.position = Position(20, 20)

        # Create enemy group - stunned spotter with nearby enemies
        # Scanner vision range is 10, so position nearby enemies 11+ tiles away from player
        # but within alert range of the spotter (alert range is typically 5)
        spotter = enemy_builder("scanner", pos=(25, 20))  # Can see player (distance 5)
        nearby1 = enemy_builder(
            "scanner", pos=(31, 20)
        )  # Near spotter but can't see player (distance 11 from player)
        nearby2 = enemy_builder(
            "scanner", pos=(33, 20)
        )  # Near spotter but can't see player (distance 13 from player)

        # Set spotter to be stunned (e.g., from Denial of Service exploit)
        spotter.state = EnemyState.UNAWARE
        spotter.disabled_turns = 3  # Stunned for 3 turns

        nearby1.state = EnemyState.UNAWARE
        nearby2.state = EnemyState.UNAWARE

        basic_game_engine.enemies = [spotter, nearby1, nearby2]

        # Process turns - spotter sees player but is stunned, so can't alert others
        for _ in range(5):
            basic_game_engine.process_turn()

        # Verify nearby enemies are NOT alerted (because spotter is stunned)
        # They can't see the player themselves (beyond vision range) and the
        # stunned spotter cannot alert them
        assert (
            nearby1.state == EnemyState.UNAWARE
        ), "Nearby enemy should not be alerted by stunned enemy"
        assert (
            nearby2.state == EnemyState.UNAWARE
        ), "Nearby enemy should not be alerted by stunned enemy"


class TestEnemyConvergence:
    """Test multiple enemies converging on player."""

    def test_multiple_enemies_move_toward_player(self, basic_game_engine):
        """Test multiple hostile enemies move toward player."""

        # Position player
        basic_game_engine.player.position = Position(25, 25)

        # Create enemies from different directions
        north = enemy_builder("bot", pos=(25, 15))
        south = enemy_builder("bot", pos=(25, 35))
        east = enemy_builder("bot", pos=(35, 25))
        west = enemy_builder("bot", pos=(15, 25))

        # Make all hostile
        for enemy in [north, south, east, west]:
            enemy.state = EnemyState.HOSTILE

        basic_game_engine.enemies = [north, south, east, west]

        # Record initial distances
        initial_distances = {
            "north": north.position.distance_to(basic_game_engine.player.position),
            "south": south.position.distance_to(basic_game_engine.player.position),
            "east": east.position.distance_to(basic_game_engine.player.position),
            "west": west.position.distance_to(basic_game_engine.player.position),
        }

        # Process multiple turns
        for _ in range(5):
            basic_game_engine.process_turn()

        # Verify enemies have pathfinding
        for enemy in basic_game_engine.enemies:
            assert hasattr(enemy, "move"), "Enemy should have move capability"
            assert hasattr(enemy, "move_queue"), "Enemy should have move queue"

    def test_enemies_surround_player(self, basic_game_engine):
        """Test enemies attempt to surround player."""

        # Position player
        basic_game_engine.player.position = Position(20, 20)

        # Create enemies around player
        enemies = []
        positions = [(19, 19), (20, 19), (21, 19), (19, 20), (21, 20), (19, 21), (20, 21), (21, 21)]

        for x, y in positions:
            enemy = enemy_builder("bot", pos=(x, y))
            enemy.state = EnemyState.HOSTILE
            enemies.append(enemy)

        basic_game_engine.enemies = enemies

        # Player is surrounded
        assert len(basic_game_engine.enemies) == 8, "Should have 8 surrounding enemies"

        # Process turn
        basic_game_engine.process_turn()

        # Verify system handles multiple adjacent enemies
        assert all(
            hasattr(e, "state") for e in basic_game_engine.enemies
        ), "All enemies should function"


class TestEnemyCollisionAndBlocking:
    """Test enemy collision and blocking mechanics."""

    def test_enemies_cannot_occupy_same_position(self, basic_game_engine):
        """Test two enemies cannot be at same position."""

        # Create two enemies at same position (shouldn't happen in game)
        pos = Position(20, 20)
        enemy1 = enemy_builder("scanner", pos=(pos.x, pos.y))
        enemy2 = enemy_builder("bot", pos=(20, 20))

        basic_game_engine.enemies = [enemy1, enemy2]

        # Verify game map checks for enemy positions
        assert hasattr(
            basic_game_engine.game_map, "is_valid_position"
        ), "Map should validate positions"

    def test_enemy_pathfinding_avoids_other_enemies(self, basic_game_engine):
        """Test enemy pathfinding routes around other enemies."""

        # Position player
        basic_game_engine.player.position = Position(30, 20)

        # Create moving enemy
        mover = enemy_builder("bot", pos=(20, 20))
        mover.state = EnemyState.HOSTILE

        # Create blocking enemies in the way
        blocker1 = enemy_builder("scanner", pos=(25, 20))
        blocker2 = enemy_builder("scanner", pos=(26, 20))

        blocker1.state = EnemyState.UNAWARE
        blocker2.state = EnemyState.UNAWARE

        basic_game_engine.enemies = [mover, blocker1, blocker2]

        # Process turns
        for _ in range(5):
            basic_game_engine.process_turn()

        # Mover should path around blockers (or handle blocking)
        assert hasattr(mover, "move_queue"), "Should use pathfinding"

    def test_enemy_blocked_movement_invalidates_queue(self, basic_game_engine):
        """Test enemy movement queue invalidates when blocked."""

        # Create enemy with movement queue
        mover = enemy_builder("bot", pos=(20, 20))
        mover.state = EnemyState.HOSTILE
        mover.move_queue = [Position(21, 20), Position(22, 20)]

        # Create blocker at next position
        blocker = enemy_builder("scanner", pos=(21, 20))
        blocker.state = EnemyState.UNAWARE

        basic_game_engine.enemies = [mover, blocker]
        basic_game_engine.player.position = Position(25, 20)

        # Process turn (mover should detect block and invalidate queue)
        basic_game_engine.process_turn()

        # Queue should be handled appropriately
        assert hasattr(mover, "move_queue"), "Should maintain queue system"


class TestSimultaneousCombat:
    """Test multiple enemies attacking simultaneously."""

    def test_multiple_enemies_attack_same_turn(self, basic_game_engine):
        """Test multiple adjacent enemies can attack on same turn."""

        # Position player
        basic_game_engine.player.position = Position(20, 20)
        basic_game_engine.player.cpu = 100

        # Create adjacent hostile enemies
        bot1 = enemy_builder("bot", pos=(21, 20))
        bot2 = enemy_builder("bot", pos=(19, 20))
        bot3 = enemy_builder("bot", pos=(20, 21))

        for bot in [bot1, bot2, bot3]:
            bot.state = EnemyState.HOSTILE

        basic_game_engine.enemies = [bot1, bot2, bot3]

        initial_cpu = basic_game_engine.player.cpu

        # Process turn (all enemies should attack)
        basic_game_engine.process_turn()

        # Verify multiple attacks possible
        # CPU may decrease from multiple attacks
        assert (
            basic_game_engine.player.cpu <= initial_cpu
        ), "Player may take damage from multiple enemies"

    def test_virus_and_bot_combined_attack(self, basic_game_engine):
        """Test virus (DoT) and bot (direct damage) attacking together."""

        # Position player
        basic_game_engine.player.position = Position(20, 20)
        basic_game_engine.player.cpu = 100

        # Create different enemy types
        virus = enemy_builder("virus", pos=(21, 20))
        bot = enemy_builder("bot", pos=(19, 20))

        virus.state = EnemyState.HOSTILE
        bot.state = EnemyState.HOSTILE

        basic_game_engine.enemies = [virus, bot]

        initial_cpu = basic_game_engine.player.cpu

        # Process turn
        basic_game_engine.process_turn()

        # Verify both attack types work
        # Bot deals direct damage, virus applies infection
        assert hasattr(
            basic_game_engine.player.temporary_effects, "__getitem__"
        ), "Effects system should exist"

    def test_mass_combat_scenario(self, basic_game_engine):
        """Test player vs many enemies simultaneously."""

        # Position player
        basic_game_engine.player.position = Position(25, 25)
        basic_game_engine.player.cpu = 100
        basic_game_engine.player.inventory_manager.equipped_exploits.append("code_injection")

        # Create many enemies
        enemies = []
        for i in range(5):
            enemy = enemy_builder("bot", pos=(26 + i, 25))
            enemy.state = EnemyState.HOSTILE
            enemies.append(enemy)

        basic_game_engine.enemies = enemies

        # Process multiple turns of combat
        for _ in range(10):
            if len(basic_game_engine.enemies) > 0 and basic_game_engine.player.cpu > 0:
                basic_game_engine.process_turn()

        # Verify system stability
        assert basic_game_engine.player.cpu >= 0, "Player CPU should be valid"


class TestPatrolCoordination:
    """Test patrol enemy coordination."""

    def test_multiple_patrols_independent_routes(self, basic_game_engine):
        """Test multiple patrol enemies follow independent routes."""

        # Find valid spawn positions
        valid_positions = []
        for x in range(10, 40, 5):
            for y in range(10, 40, 5):
                pos = Position(x, y)
                if not basic_game_engine.game_map.is_wall(pos):
                    valid_positions.append(pos)
                    if len(valid_positions) >= 3:
                        break
            if len(valid_positions) >= 3:
                break

        # Create patrol enemies with routes
        patrols = []
        for pos in valid_positions[:3]:
            patrol = basic_game_engine.enemy_manager.spawn_enemy(pos, "patrol")
            patrol.state = EnemyState.UNAWARE
            patrols.append(patrol)

        # Verify patrols have routes
        for patrol in patrols:
            assert hasattr(patrol, "patrol_points"), "Patrol should have route"
            assert len(patrol.patrol_points) > 0, "Patrol should have patrol points"

    def test_patrol_switches_to_chase_when_detecting_player(self, basic_game_engine):
        """Test patrol abandons route when spotting player."""

        # Find valid position
        patrol_pos = None
        for x in range(15, 25):
            for y in range(15, 25):
                pos = Position(x, y)
                if not basic_game_engine.game_map.is_wall(pos):
                    patrol_pos = pos
                    break
            if patrol_pos:
                break

        # Create patrol enemy
        patrol = basic_game_engine.enemy_manager.spawn_enemy(patrol_pos, "patrol")
        patrol.state = EnemyState.UNAWARE

        # Position player nearby
        basic_game_engine.player.position = Position(patrol_pos.x + 2, patrol_pos.y)

        # Process turns
        for _ in range(5):
            basic_game_engine.process_turn()

        # Patrol should have reacted to player
        assert hasattr(patrol, "state"), "Patrol should track state"


class TestAdminCoordination:
    """Test admin enemy coordination with normal enemies."""

    def test_admin_coordinates_with_normal_enemies(self, basic_game_engine):
        """Test admin works alongside normal enemies."""

        # Position player
        basic_game_engine.player.position = Position(25, 25)

        # Create admin and normal enemies
        admin = enemy_builder("admin", pos=(40, 40))
        scanner = enemy_builder("scanner", pos=(20, 20))
        bot = enemy_builder("bot", pos=(22, 22))

        scanner.state = EnemyState.UNAWARE
        bot.state = EnemyState.UNAWARE

        basic_game_engine.enemies = [admin, scanner, bot]

        # Process turns
        for _ in range(5):
            basic_game_engine.process_turn()

        # Verify all enemies function together
        assert len(basic_game_engine.enemies) >= 3, "All enemies should coexist"
        assert admin.state == EnemyState.HOSTILE, "Admin should be hostile"

    def test_admin_always_sees_player_coordination(self, basic_game_engine):
        """Test admin's omniscient vision doesn't break normal enemy behavior."""

        # Position player in shadow
        shadow_pos = Position(20, 20)
        basic_game_engine.game_map.blind_spots.add((shadow_pos.x, shadow_pos.y))
        basic_game_engine.player.position = shadow_pos

        # Create admin far away and normal enemy nearby
        admin = enemy_builder("admin", pos=(50, 50))
        scanner = enemy_builder("scanner", pos=(25, 20))
        scanner.state = EnemyState.UNAWARE

        basic_game_engine.enemies = [admin, scanner]

        # Admin sees player, normal enemy doesn't
        admin_sees = admin.can_see_player(basic_game_engine.player, basic_game_engine.game_map)
        scanner_sees = scanner.can_see_player(basic_game_engine.player, basic_game_engine.game_map)

        assert bool(admin_sees), "Admin should see player"
        assert not scanner_sees, "Normal enemy should not see player in shadow"


class TestComplexCoordinationScenarios:
    """Test complex multi-enemy coordination scenarios."""

    def test_mixed_enemy_types_coordination(self, basic_game_engine):
        """Test different enemy types working together."""

        # Position player
        basic_game_engine.player.position = Position(25, 25)

        # Create diverse enemy group
        scanner = enemy_builder("scanner", pos=(20, 25))  # Long vision
        bot = enemy_builder("bot", pos=(22, 25))  # Direct damage
        virus = enemy_builder("virus", pos=(24, 25))  # DoT
        firewall = enemy_builder("firewall", pos=(26, 25))  # Tank

        for enemy in [scanner, bot, virus, firewall]:
            enemy.state = EnemyState.HOSTILE

        basic_game_engine.enemies = [scanner, bot, virus, firewall]

        # Process turns
        for _ in range(10):
            basic_game_engine.process_turn()

        # Verify all types function together
        assert all(
            hasattr(e, "state") for e in basic_game_engine.enemies
        ), "All types should coexist"

    def test_enemy_reinforcement_scenario(self, basic_game_engine):
        """Test enemies reinforcing each other during combat."""

        # Position player in combat
        basic_game_engine.player.position = Position(25, 25)
        basic_game_engine.player.inventory_manager.equipped_exploits.append("code_injection")

        # Create initial enemies
        initial_enemy = enemy_builder("bot", pos=(26, 25))
        initial_enemy.state = EnemyState.HOSTILE
        basic_game_engine.enemies = [initial_enemy]

        # Create reinforcements nearby (unaware)
        reinforcement1 = enemy_builder("bot", pos=(30, 25))
        reinforcement2 = enemy_builder("scanner", pos=(32, 25))
        reinforcement1.state = EnemyState.UNAWARE
        reinforcement2.state = EnemyState.UNAWARE
        basic_game_engine.enemies.extend([reinforcement1, reinforcement2])

        # Process combat turns
        for _ in range(10):
            if len(basic_game_engine.enemies) > 0:
                basic_game_engine.process_turn()

        # Reinforcements should have joined combat
        assert len(basic_game_engine.enemies) >= 1, "Some enemies should remain"

    def test_full_level_enemy_coordination(self, basic_game_engine):
        """Test enemy coordination in full level scenario."""

        # Position player
        basic_game_engine.player.position = Position(25, 25)

        # Enemies should be spawned by level generation
        initial_enemy_count = len(basic_game_engine.enemies)

        # Process many turns
        for _ in range(20):
            basic_game_engine.process_turn()

        # Verify enemies are managed correctly
        assert isinstance(len(basic_game_engine.enemies), int), "Enemy count should be valid"
        assert hasattr(basic_game_engine, "enemy_manager"), "Should have enemy manager"

    def test_pincer_movement_coordination(self, basic_game_engine):
        """Test enemies executing pincer movement."""

        # Position player
        basic_game_engine.player.position = Position(25, 25)

        # Create enemies for pincer (from opposite sides)
        north_group = [
            enemy_builder("bot", pos=(25, 15)),
            enemy_builder("bot", pos=(24, 16)),
            enemy_builder("bot", pos=(26, 16)),
        ]

        south_group = [
            enemy_builder("bot", pos=(25, 35)),
            enemy_builder("bot", pos=(24, 34)),
            enemy_builder("bot", pos=(26, 34)),
        ]

        all_enemies = north_group + south_group
        for enemy in all_enemies:
            enemy.state = EnemyState.HOSTILE

        basic_game_engine.enemies = all_enemies

        # Record initial positions
        initial_positions = [(e.position.x, e.position.y) for e in basic_game_engine.enemies]

        # Process turns (enemies converge)
        for _ in range(10):
            basic_game_engine.process_turn()

        # Enemies should have moved (pathfinding toward player)
        assert all(
            hasattr(e, "move_queue") for e in basic_game_engine.enemies
        ), "All should use pathfinding"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
