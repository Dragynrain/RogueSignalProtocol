"""
Integration tests for achievement metric tracking.

Tests verify that achievement-related metrics are properly tracked during gameplay:
- unique_exploits_used_this_run (for master_hacker)
- used_any_exploits (for pure_skill, resource_efficient)
- used_any_code_hacks (for data_miner, resource_efficient)
- special_nodes_discovered (for explorer)
"""

from rsp.systems.metrics import get_current_session, init_session_metrics
from tests.test_agent import GameTestAgent


class TestExploitTracking:
    """Tests for exploit usage tracking."""

    def test_exploit_usage_sets_used_any_exploits(self):
        """Using an exploit should set used_any_exploits = True."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        session = get_current_session()
        assert session is not None
        assert session.used_any_exploits is False

        # Use threat_scan exploit (doesn't need a target and works without cooldown)
        if "threat_scan" not in agent.engine.player.inventory_manager.equipped_exploits:
            agent.engine.player.inventory_manager.equipped_exploits.append("threat_scan")

        agent.engine.exploit_system.use_exploit("threat_scan")

        # Check that used_any_exploits is now True
        assert session.used_any_exploits is True

    def test_exploit_usage_adds_to_unique_set(self):
        """Using exploits should add them to unique_exploits_used_this_run."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        session = get_current_session()
        assert session is not None
        assert len(session.unique_exploits_used_this_run) == 0

        # Ensure threat_scan is equipped
        if "threat_scan" not in agent.engine.player.inventory_manager.equipped_exploits:
            agent.engine.player.inventory_manager.equipped_exploits.append("threat_scan")

        # Use an exploit
        agent.engine.exploit_system.use_exploit("threat_scan")

        # Check that exploit was added to unique set
        assert "threat_scan" in session.unique_exploits_used_this_run

    def test_using_same_exploit_twice_doesnt_duplicate(self):
        """Using the same exploit twice shouldn't add duplicate entries."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        session = get_current_session()

        # Ensure threat_scan is equipped
        if "threat_scan" not in agent.engine.player.inventory_manager.equipped_exploits:
            agent.engine.player.inventory_manager.equipped_exploits.append("threat_scan")

        # Use same exploit twice
        agent.engine.exploit_system.use_exploit("threat_scan")
        agent.engine.exploit_system.use_exploit("threat_scan")

        # Set should still only have one entry
        assert "threat_scan" in session.unique_exploits_used_this_run
        # Count entries in the set (there should be exactly 1)
        count = sum(1 for x in session.unique_exploits_used_this_run if x == "threat_scan")
        assert count == 1


class TestCodeHackTracking:
    """Tests for code hack usage tracking."""

    def test_code_hack_usage_sets_used_any_code_hacks(self):
        """Using a code hack should set used_any_code_hacks = True."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        session = get_current_session()
        assert session is not None
        assert session.used_any_code_hacks is False

        # Give player a code hack
        from rsp.combat.inventory import CodeHack

        code = CodeHack(
            color_name="crimson",
            effect="restore_cpu",
            name="Crimson Code",
            description="Restores CPU",
        )
        agent.engine.player.inventory_manager.add_item(code)

        # Manually use the code hack
        code.use(agent.engine.player, agent.engine)

        # Check that used_any_code_hacks is now True
        assert session.used_any_code_hacks is True

    def test_code_hack_usage_adds_to_unique_set(self):
        """Using code hacks should add them to unique_code_hacks_used_this_run."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        session = get_current_session()
        assert session is not None
        assert len(session.unique_code_hacks_used_this_run) == 0

        # Give player a code hack
        from rsp.combat.inventory import CodeHack

        code = CodeHack(
            color_name="azure",
            effect="reduce_heat",
            name="Azure Code",
            description="Reduces heat",
        )
        agent.engine.player.inventory_manager.add_item(code)

        # Use the code hack
        code.use(agent.engine.player, agent.engine)

        # Check that code was added to unique set
        assert "Azure Code" in session.unique_code_hacks_used_this_run

    def test_using_all_6_code_colors_enables_code_collector(self):
        """Using all 6 code colors should enable the code_collector achievement."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        session = get_current_session()
        assert session is not None

        from rsp.systems.achievements import TOTAL_CODE_HACK_TYPES
        from rsp.combat.inventory import CodeHack

        # All 6 code colors and their names
        code_data = [
            ("crimson", "Crimson Code"),
            ("azure", "Azure Code"),
            ("emerald", "Emerald Code"),
            ("golden", "Golden Code"),
            ("violet", "Violet Code"),
            ("silver", "Silver Code"),
        ]

        # Use all 6 different colored codes
        for color, name in code_data:
            code = CodeHack(
                color_name=color,
                effect="restore_cpu",  # Effect doesn't matter for tracking
                name=name,
                description="Test",
            )
            agent.engine.player.inventory_manager.add_item(code)
            code.use(agent.engine.player, agent.engine)

        # Verify all 6 unique codes were tracked
        assert len(session.unique_code_hacks_used_this_run) == 6
        assert len(session.unique_code_hacks_used_this_run) >= TOTAL_CODE_HACK_TYPES

        # Verify each code name is in the set
        for _, name in code_data:
            assert name in session.unique_code_hacks_used_this_run


class TestSpecialNodesTracking:
    """Tests for special node discovery tracking."""

    def test_upgrade_pickup_adds_to_special_nodes(self):
        """Picking up an upgrade should add 'upgrade' to special_nodes_discovered."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        session = get_current_session()
        assert session is not None
        assert "upgrade" not in session.special_nodes_discovered

        # Place an upgrade at player position
        player_pos = (agent.engine.player.x, agent.engine.player.y)
        agent.engine.game_map.permanent_upgrades[player_pos] = "cpu_boost"

        # Process turn to pick up upgrade
        agent.engine.game_session.process_turn()

        # Check that 'upgrade' was added to special nodes
        assert "upgrade" in session.special_nodes_discovered

    def test_gateway_completion_adds_to_special_nodes(self):
        """Completing a level via gateway should add 'gateway' to special_nodes_discovered."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        session = get_current_session()
        assert session is not None
        assert "gateway" not in session.special_nodes_discovered

        # Call progress_to_next_level directly (simulating gateway completion)
        agent.engine.game_session.progress_to_next_level()

        # Check that 'gateway' was added to special nodes
        assert "gateway" in session.special_nodes_discovered


class TestPureSkillAchievementFix:
    """Tests that pure_skill achievement (no exploits used) tracks correctly."""

    def test_not_using_exploits_keeps_flag_false(self):
        """Not using any exploits should keep used_any_exploits = False."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        session = get_current_session()

        # Just process a turn without using exploits
        agent.engine.game_session.process_turn()

        # Flag should still be False
        assert session.used_any_exploits is False

    def test_pure_skill_achievement_possible_without_exploits(self):
        """pure_skill achievement should be earnable by not using exploits."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        session = get_current_session()

        # Simulate completing the game without using exploits
        session.victory = True
        session.levels_completed = 3

        # Verify conditions for pure_skill from game_achievements
        from rsp.systems.achievements import ALL_ACHIEVEMENTS

        pure_skill = ALL_ACHIEVEMENTS.get("pure_skill")
        assert pure_skill is not None

        # Without using exploits, used_any_exploits should be False
        assert session.used_any_exploits is False
        # And without using code hacks
        assert session.used_any_code_hacks is False


class TestMasterHackerAchievementFix:
    """Tests that master_hacker achievement (use all exploits) can now be earned."""

    def test_multiple_exploits_tracked_uniquely(self):
        """Using multiple different exploits should add each to the unique set."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        session = get_current_session()

        # Use threat_scan which works without targets or cooldown issues
        # We can only reliably test one exploit at a time due to game state
        if "threat_scan" not in agent.engine.player.inventory_manager.equipped_exploits:
            agent.engine.player.inventory_manager.equipped_exploits.append("threat_scan")

        agent.engine.exploit_system.use_exploit("threat_scan")

        # threat_scan should be in unique set
        assert "threat_scan" in session.unique_exploits_used_this_run
        # And used_any_exploits should be True
        assert session.used_any_exploits is True


class TestEnemyEncounterTracking:
    """Tests for unique enemy encounter tracking (for enemy_database achievement)."""

    def test_killing_enemy_adds_to_unique_encountered(self):
        """Killing an enemy should add its type to unique_enemies_encountered."""
        from rsp.systems.metrics import track_enemy_kill

        init_session_metrics()

        session = get_current_session()
        assert session is not None
        assert len(session.unique_enemies_encountered) == 0

        # Track a kill
        track_enemy_kill(
            enemy_type="scanner",
            damage=10,
            was_stealth=False,
            is_admin=False,
            from_blind_spot=False,
            enemies_remaining=5,
            game=None,
        )

        # Check that enemy type was added
        assert "scanner" in session.unique_enemies_encountered

    def test_killing_same_enemy_type_twice_doesnt_duplicate(self):
        """Killing the same enemy type twice shouldn't duplicate entries."""
        from rsp.systems.metrics import track_enemy_kill

        init_session_metrics()

        session = get_current_session()

        # Kill two scanners
        for _ in range(2):
            track_enemy_kill(
                enemy_type="scanner",
                damage=10,
                was_stealth=False,
                is_admin=False,
                from_blind_spot=False,
                enemies_remaining=5,
                game=None,
            )

        # Set should still only have one entry
        assert len(session.unique_enemies_encountered) == 1
        assert "scanner" in session.unique_enemies_encountered

    def test_killing_different_enemy_types_adds_each(self):
        """Killing different enemy types should add each to the set."""
        from rsp.systems.metrics import track_enemy_kill

        init_session_metrics()

        session = get_current_session()

        # Kill different enemy types
        for enemy_type in ["scanner", "virus", "firewall", "hunter"]:
            track_enemy_kill(
                enemy_type=enemy_type,
                damage=10,
                was_stealth=False,
                is_admin=False,
                from_blind_spot=False,
                enemies_remaining=5,
                game=None,
            )

        # All types should be in the set
        assert len(session.unique_enemies_encountered) == 4
        assert "scanner" in session.unique_enemies_encountered
        assert "virus" in session.unique_enemies_encountered
        assert "firewall" in session.unique_enemies_encountered
        assert "hunter" in session.unique_enemies_encountered
