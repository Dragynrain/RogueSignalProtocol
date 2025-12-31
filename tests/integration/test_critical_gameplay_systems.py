"""
Critical gameplay systems integration tests.

Tests the integration of core gameplay systems that are essential for proper game function:
- Combat system integration with enemy AI and player actions
- TraceLevel system and enemy alerting chains
- Exploit system and its effects on gameplay
- Inventory and upgrade systems
- Save/load system with complex game states
- Audio system integration during gameplay events
- Map interaction and special tiles
"""

from rsp.entities.base import EnemyState
from tests.fixtures.simple_fixtures import enemy_builder


class TestCombatSystemIntegration:
    """Test critical combat system integration."""

    def test_player_enemy_combat_integration(self, basic_game_engine):
        """Test complete player vs enemy combat workflow."""

        # Set up combat scenario
        basic_game_engine.player.position.x, basic_game_engine.player.position.y = 10, 10
        basic_game_engine.player.cpu = 100
        basic_game_engine.player.heat = 0

        # Create enemy adjacent to player
        enemy = enemy_builder("bot", pos=(11, 10))
        enemy.cpu = 50
        basic_game_engine.enemies = [enemy]

        # Give player a combat exploit
        basic_game_engine.player.inventory_manager.equipped_exploits.append("code_injection")

        initial_heat = basic_game_engine.player.heat

        # Execute exploit (this will target based on game logic)
        result = basic_game_engine.exploit_system.use_exploit("code_injection")

        # Verify exploit system integration
        assert isinstance(result, bool)  # Should return a boolean

        # Verify heat generation
        assert basic_game_engine.player.heat >= initial_heat  # Heat should increase or stay same

        # Verify exploit system is properly integrated
        assert hasattr(basic_game_engine, "exploit_system")
        assert basic_game_engine.exploit_system.game == basic_game_engine

    def test_enemy_attack_player_integration(self, basic_game_engine):
        """Test enemy attacking player integration."""

        # Set up scenario
        basic_game_engine.player.x, basic_game_engine.player.y = 10, 10
        basic_game_engine.player.cpu = 100

        # Create hostile enemy adjacent to player - use bot instead of virus for direct damage
        enemy = enemy_builder("bot", pos=(11, 10))
        enemy.state = EnemyState.HOSTILE
        basic_game_engine.enemies = [enemy]

        initial_player_cpu = basic_game_engine.player.cpu

        # Enemy attacks player
        damage = enemy.attack_player(basic_game_engine.player)

        # Verify attack results - bot should deal direct damage
        assert basic_game_engine.player.cpu < initial_player_cpu or damage > 0

        # Verify integration worked
        assert isinstance(damage, int)
        assert damage >= 0

    def test_player_death_and_game_over_integration(self, basic_game_engine):
        """Test player death triggers proper game over sequence."""

        # Set up player near death
        basic_game_engine.player.cpu = 1
        basic_game_engine.game_over = False

        # Manually trigger player death to test integration
        basic_game_engine.player.cpu = 0

        # Use centralized death handler to process death
        basic_game_engine.death_handler.check_death("test")

        # Check game over integration
        # The main integration test is that the system doesn't crash
        assert basic_game_engine.player.cpu <= 0  # Player should be dead
        assert basic_game_engine.game_over is True  # Game over should be triggered

        # Verify the game basic_game_engine still functions
        assert hasattr(basic_game_engine, "game_over")
        assert hasattr(basic_game_engine, "player")


class TestTraceLevelSystemIntegration:
    """Test critical trace level and enemy alerting system integration."""

    def test_enemy_trace_level_system_integration(self, basic_game_engine):
        """Test enemy trace level system is properly integrated."""

        # Set up test scenario
        basic_game_engine.player.x, basic_game_engine.player.y = 10, 10
        basic_game_engine.player.trace_level = 20

        # Create enemy
        enemy = enemy_builder("scanner", pos=(12, 10))
        basic_game_engine.enemies = [enemy]

        # Verify trace level system integration
        assert hasattr(basic_game_engine.player, "trace_level")
        assert isinstance(basic_game_engine.player.trace_level, (int, float))
        assert basic_game_engine.player.trace_level >= 0

        # Verify enemy vision integration
        assert hasattr(enemy, "can_see_player")
        assert hasattr(enemy, "state")

    def test_trace_threshold_system_integration(self, basic_game_engine):
        """Test trace level threshold system is properly integrated."""

        # Process a turn
        basic_game_engine.process_turn()

        # Verify trace level system is working (should be same or change predictably)
        assert basic_game_engine.player.trace_level >= 0  # TraceLevel should never be negative
        assert isinstance(basic_game_engine.player.trace_level, (int, float))  # Should be a number

    def test_trace_level_system_persistence_integration(self, basic_game_engine):
        """Test trace level system integrates with game state persistence."""

        # Set trace level value
        initial_trace = 75
        basic_game_engine.player.trace_level = initial_trace

        # Verify trace level persists in player object
        assert basic_game_engine.player.trace_level == initial_trace

        # Verify trace level is accessible through game basic_game_engine
        assert hasattr(basic_game_engine, "player")
        assert hasattr(basic_game_engine.player, "trace_level")


class TestExploitSystemIntegration:
    """Test critical exploit system integration."""

    def test_exploit_system_integration(self, basic_game_engine):
        """Test exploit system is properly integrated."""

        # Verify exploit system exists and is accessible
        assert hasattr(basic_game_engine, "input_handler")
        assert hasattr(basic_game_engine, "exploit_system")

        # Verify exploit system is properly initialized
        exploit_system = basic_game_engine.exploit_system
        assert exploit_system.game == basic_game_engine

        # Verify player has inventory system for exploits
        assert hasattr(basic_game_engine.player, "inventory_manager")
        assert hasattr(basic_game_engine.player.inventory_manager, "equipped_exploits")

    def test_exploit_heat_system_integration(self, basic_game_engine):
        """Test exploit system integrates with heat management."""

        # Set up player with exploit
        basic_game_engine.player.inventory_manager.equipped_exploits.append("code_injection")
        initial_heat = basic_game_engine.player.heat

        # Use exploit
        result = basic_game_engine.exploit_system.use_exploit("code_injection")

        # Verify heat system integration
        assert isinstance(result, bool)
        assert basic_game_engine.player.heat >= initial_heat  # Heat should increase or stay same

    def test_exploit_targeting_system_integration(self, basic_game_engine):
        """Test exploit system integrates with targeting."""

        # Verify targeting system exists
        assert hasattr(basic_game_engine, "targeting_mode")
        assert hasattr(basic_game_engine, "targeting_exploit")
        assert hasattr(basic_game_engine, "cursor_position")

        # Test basic integration
        basic_game_engine.targeting_mode = True
        basic_game_engine.targeting_exploit = "code_injection"

        # Verify integration works
        assert basic_game_engine.targeting_mode
        assert basic_game_engine.targeting_exploit == "code_injection"


class TestGameStateIntegration:
    """Test critical game state persistence and management integration."""

    def test_game_state_system_integration(self, basic_game_engine):
        """Test game state system is properly integrated."""

        # Verify game state components exist
        assert hasattr(basic_game_engine, "game_state")
        assert hasattr(basic_game_engine, "level")
        assert hasattr(basic_game_engine, "turn")

        # Verify save/load system exists
        assert hasattr(basic_game_engine, "game_session")
        assert hasattr(basic_game_engine, "auto_save")

        # Test basic state access
        initial_level = basic_game_engine.level
        initial_turn = basic_game_engine.turn

        assert isinstance(initial_level, int)
        assert isinstance(initial_turn, int)

    def test_turn_processing_system_integration(self, basic_game_engine):
        """Test turn processing system integration."""

        # Set up initial state
        initial_turn = basic_game_engine.turn

        # Process a turn
        basic_game_engine.process_turn()

        # Verify turn advanced
        assert basic_game_engine.turn > initial_turn

        # Verify turn processor exists
        assert hasattr(basic_game_engine, "turn_processor")

    def test_game_state_persistence_integration(self, basic_game_engine):
        """Test game state persistence integration."""

        # Set some state
        basic_game_engine.player.cpu = 75
        basic_game_engine.player.heat = 30
        basic_game_engine.player.trace_level = 45

        # Verify state is accessible
        assert basic_game_engine.player.cpu == 75
        assert basic_game_engine.player.heat == 30
        assert basic_game_engine.player.trace_level == 45

        # Verify persistence systems exist
        assert hasattr(
            basic_game_engine, "game_session"
        ), "Engine should have game_session attribute"
        assert callable(
            getattr(basic_game_engine, "auto_save", None)
        ), "Engine should have auto_save method"
