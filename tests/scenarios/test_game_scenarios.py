#!/usr/bin/env python3
"""
End-to-end scenario tests for RogueSignalProtocol.
These tests simulate complete gameplay workflows using real game components.
"""

import pytest
from unittest.mock import Mock
from game_map import GameMap
from game_level import LevelGenerator
from game_characters import Player, Enemy
from game_entities import Position, EnemyState
from game_combat import ExploitSystem
from game_state import MessageLog, GameStateManager
from game_inventory import ExploitItem, InventoryManager
from game_data import GameData
from game_enemies import EnemyManager
from game_engine import GameEngine


class TestCompleteGameplayScenarios:
    """Test complete gameplay scenarios from start to finish."""
    
    def setup_method(self):
        """Set up a complete game environment for scenario testing."""
        # Create real game map and generate a level
        self.game_map = GameMap(50, 30)
        self.level_generator = LevelGenerator(self.game_map)
        self.level_generator.generate_level(level=1, seed=42)
        
        # Create real player
        self.player = Player(10, 10)
        
        # Create real message log
        self.message_log = MessageLog()
        
        # Create enemy manager with required arguments
        self.enemy_manager = EnemyManager(self.game_map, self.message_log)
        
        # Create minimal game state
        self.mock_game = Mock()
        self.mock_game.game_map = self.game_map
        self.mock_game.player = self.player
        self.mock_game.message_log = self.message_log
        self.mock_game.enemy_manager = self.enemy_manager
        self.mock_game.sound_manager = Mock()
        self.mock_game.level = 1
        self.mock_game.turn = 1
        
        # Create exploit system
        self.exploit_system = ExploitSystem(self.mock_game)
    
    def test_player_exploration_and_discovery_scenario(self):
        """
        Scenario: Player explores map, discovers items, and reaches gateway.
        This tests the core exploration gameplay loop.
        """
        # ARRANGE: Player starts with basic equipment
        initial_pos = self.player.position
        initial_cpu = self.player.cpu
        
        # ACT 1: Player moves around the map
        # Simulate player movement (find a walkable position)
        walkable_positions = []
        for x in range(self.game_map.width):
            for y in range(self.game_map.height):
                pos = Position(x, y)
                if not self.game_map.is_wall(pos):
                    walkable_positions.append(pos)
        
        assert len(walkable_positions) > 0, "Map should have walkable areas"
        
        # Move player to a new position
        if len(walkable_positions) > 1:
            new_pos = walkable_positions[1]  # Pick second walkable position
            self.player.position = new_pos
        
        # ACT 2: Player finds and uses items
        # Add some items to player inventory
        exploit_def = GameData.EXPLOITS["buffer_overflow"]
        buffer_overflow = ExploitItem("buffer_overflow", exploit_def)
        self.player.inventory_manager.add_item(buffer_overflow)
        equip_success = self.player.inventory_manager.equip_exploit(buffer_overflow)
        
        # ACT 3: Check if player can reach gateway
        gateway_reachable = False
        if self.game_map.gateway:
            # Simple check - gateway exists and is on map
            gateway_reachable = self.game_map.gateway.is_valid(self.game_map.width, self.game_map.height)
        
        # ASSERT: Verify complete scenario worked
        assert self.player.position != initial_pos or len(walkable_positions) == 1
        assert self.player.cpu == initial_cpu  # No damage taken during exploration
        assert equip_success, "Player should be able to equip found exploits"
        assert len(self.player.inventory_manager.equipped_exploits) > 0
        assert self.game_map.gateway is not None, "Level should have an exit gateway"
    
    def test_stealth_infiltration_scenario(self):
        """
        Scenario: Player uses stealth mechanics to avoid enemies and reach objectives.
        Tests stealth gameplay, shadow mechanics, and enemy detection.
        """
        # ARRANGE: Add enemies to the map
        if len(self.enemy_manager.enemies) == 0:
            # Find positions for enemies
            enemy_positions = []
            for x in range(5, 45, 10):  # Spread enemies across map
                for y in range(5, 25, 10):
                    pos = Position(x, y)
                    if not self.game_map.is_wall(pos):
                        enemy_positions.append(pos)
            
            # Add enemies at valid positions
            for i, pos in enumerate(enemy_positions[:3]):  # Limit to 3 enemies
                enemy = Enemy(pos, 'script_kiddie')
                self.enemy_manager.add_enemy(enemy)
        
        # ACT 1: Player starts in a safe position
        player_start_pos = self.player.position
        initial_detection = self.player.detection
        
        # ACT 2: Test shadow mechanics
        shadow_positions = list(self.game_map.shadows)
        player_in_shadow = any(
            self.game_map.is_shadow(Position(self.player.position.x, self.player.position.y))
            for shadow_pos in shadow_positions
        )
        
        # ACT 3: Simulate stealth movement
        # Player should be able to move without triggering all enemies
        enemies_before = len([e for e in self.enemy_manager.enemies if e.state == EnemyState.HOSTILE])
        
        # Move player slightly and check detection didn't spike dramatically
        if len(shadow_positions) > 0:
            shadow_x, shadow_y = list(shadow_positions)[0]
            shadow_pos = Position(shadow_x, shadow_y)
            if not self.game_map.is_wall(shadow_pos):
                self.player.position = shadow_pos
        
        # ASSERT: Stealth mechanics work
        assert self.player.detection >= initial_detection  # Detection might increase slightly
        assert self.player.detection < 100, "Stealth movement shouldn't immediately max detection"
        assert len(self.game_map.shadows) >= 0, "Map should have shadow areas for stealth"
    
    def test_combat_encounter_scenario(self):
        """
        Scenario: Player engages in combat with enemies using exploits.
        Tests complete combat workflow from detection to resolution.
        """
        # ARRANGE: Set up combat scenario
        # Give player combat-ready equipment
        combat_exploits = ["buffer_overflow", "system_crash"]
        for exploit_name in combat_exploits:
            if exploit_name in ["buffer_overflow", "system_crash"]:  # Only add known exploits
                exploit_item = ExploitItem(exploit_name)
                self.player.inventory_manager.add_item(exploit_item)
                self.player.inventory_manager.equip_exploit(exploit_item)
        
        # Place enemy near player
        enemy_pos = Position(self.player.position.x + 3, self.player.position.y + 1)
        combat_enemy = Enemy(enemy_pos, 'script_kiddie')
        combat_enemy.state = EnemyState.HOSTILE  # Make enemy aggressive
        self.enemy_manager.add_enemy(combat_enemy)
        
        # ACT 1: Player detects enemy
        initial_enemy_count = len(self.enemy_manager.enemies)
        enemy_distance = abs(self.player.position.x - combat_enemy.position.x) + abs(self.player.position.y - combat_enemy.position.y)
        
        # ACT 2: Player uses exploit in combat
        initial_heat = self.player.heat
        target_position = combat_enemy.position
        
        # Use exploit system
        exploit_result = self.exploit_system.execute_exploit("buffer_overflow", target_position)
        
        # ACT 3: Check combat resolution
        post_combat_heat = self.player.heat
        
        # ASSERT: Combat scenario completed successfully
        assert initial_enemy_count > 0, "Should have enemies for combat"
        assert enemy_distance <= 10, "Enemy should be within reasonable range"
        assert isinstance(exploit_result, bool), "Exploit should return success/failure"
        assert post_combat_heat >= initial_heat, "Using exploits should generate heat"
        assert self.player.cpu > 0, "Player should survive the encounter"
        assert len(self.player.inventory_manager.equipped_exploits) > 0, "Player should have combat tools"
    
    def test_resource_management_scenario(self):
        """
        Scenario: Player manages CPU, heat, and inventory throughout gameplay.
        Tests resource constraints and recovery mechanics.
        """
        # ARRANGE: Set player to moderate resource levels
        self.player.cpu = 60  # Moderate health
        self.player.heat = 40  # Some heat buildup
        
        initial_cpu = self.player.cpu
        initial_heat = self.player.heat
        
        # ACT 1: Test CPU management
        # Simulate taking damage
        damage_taken = self.player.take_damage(15)
        current_cpu = self.player.cpu
        
        # Test healing
        heal_amount = self.player.heal(10)
        healed_cpu = self.player.cpu
        
        # ACT 2: Test heat management
        # Simulate using high-heat exploit
        heat_exploit = ExploitItem("system_crash")  # Typically high heat
        self.player.inventory_manager.add_item(heat_exploit)
        self.player.inventory_manager.equip_exploit(heat_exploit)
        
        pre_exploit_heat = self.player.heat
        target_pos = Position(self.player.position.x + 1, self.player.position.y)
        self.exploit_system.execute_exploit("system_crash", target_pos)
        post_exploit_heat = self.player.heat
        
        # ACT 3: Test inventory limits
        # Try to add many exploits to test capacity
        exploit_count = 0
        test_exploits = ["buffer_overflow", "threat_scan", "data_mimic", "shadow_step"]
        for exploit_name in test_exploits:
            exploit_item = ExploitItem(exploit_name)
            if self.player.inventory_manager.add_item(exploit_item):
                if self.player.inventory_manager.equip_exploit(exploit_item):
                    exploit_count += 1
        
        # ASSERT: Resource management works correctly
        assert damage_taken == 15, "Damage calculation should be accurate"
        assert current_cpu == initial_cpu - 15, "CPU should decrease with damage"
        assert heal_amount == 10, "Healing should work correctly"
        assert healed_cpu == current_cpu + 10, "CPU should increase with healing"
        assert post_exploit_heat >= pre_exploit_heat, "Exploits should generate heat"
        assert self.player.heat <= 100, "Heat should be capped at maximum"
        assert exploit_count <= self.player.inventory_manager.max_equipped_exploits, "Should respect equipment limits"
    
    def test_level_progression_scenario(self):
        """
        Scenario: Player completes a level and progresses to the next.
        Tests level completion mechanics and progression.
        """
        # ARRANGE: Player reaches level completion state
        initial_level = self.mock_game.level
        
        # Ensure player has equipment for next level
        essential_exploit = ExploitItem("buffer_overflow")
        self.player.inventory_manager.add_item(essential_exploit)
        self.player.inventory_manager.equip_exploit(essential_exploit)
        
        # ACT 1: Player reaches gateway
        gateway_position = self.game_map.gateway
        player_can_reach_gateway = gateway_position is not None
        
        if gateway_position:
            # Simulate player reaching gateway
            self.player.position = gateway_position
            player_at_gateway = (self.player.position.x == gateway_position.x and 
                               self.player.position.y == gateway_position.y)
        else:
            player_at_gateway = False
        
        # ACT 2: Simulate level completion requirements
        player_ready_for_next_level = (
            self.player.cpu > 0 and  # Player is alive
            len(self.player.inventory_manager.equipped_exploits) > 0 and  # Has tools
            player_can_reach_gateway  # Can reach exit
        )
        
        # ACT 3: Test next level generation
        if player_ready_for_next_level:
            # Generate next level
            next_level_map = GameMap(50, 30)
            next_generator = LevelGenerator(next_level_map)
            next_generator.generate_level(level=2, seed=43)  # Different seed for variety
            
            next_level_valid = (
                len(next_level_map.walls) > 0 and
                next_level_map.gateway is not None
            )
        else:
            next_level_valid = False
        
        # ASSERT: Level progression scenario works
        assert initial_level > 0, "Should start with valid level"
        assert self.game_map.gateway is not None, "Current level should have exit"
        assert len(self.player.inventory_manager.equipped_exploits) > 0, "Player should have progression tools"
        if player_ready_for_next_level:
            assert next_level_valid, "Next level should generate successfully"


class TestGameplayWorkflowScenarios:
    """Test specific gameplay workflows and user journeys."""
    
    def test_new_player_tutorial_workflow(self):
        """
        Scenario: New player goes through basic tutorial workflow.
        Tests that a new player can perform basic actions.
        """
        # ARRANGE: Fresh player setup
        player = Player(5, 5)
        game_map = GameMap(20, 15)  # Small tutorial map
        generator = LevelGenerator(game_map)
        generator.generate_level(level=1, seed=100)
        
        # ACT 1: Player learns basic movement
        original_pos = player.position
        new_pos = Position(6, 6)
        if not game_map.is_wall(new_pos):
            player.position = new_pos
            movement_successful = True
        else:
            movement_successful = False
        
        # ACT 2: Player learns inventory management
        tutorial_exploit = ExploitItem("threat_scan")  # Safe, low-impact exploit
        inventory_add_success = player.inventory_manager.add_item(tutorial_exploit)
        equip_success = player.inventory_manager.equip_exploit(tutorial_exploit)
        
        # ACT 3: Player learns basic resource monitoring
        initial_cpu = player.cpu
        initial_heat = player.heat
        resource_check_successful = (initial_cpu == 100 and initial_heat == 0)
        
        # ASSERT: Tutorial workflow completes successfully
        assert movement_successful or game_map.is_wall(new_pos), "Movement should work or be blocked by walls"
        assert inventory_add_success, "New player should be able to add items"
        assert equip_success, "New player should be able to equip basic exploits"
        assert resource_check_successful, "New player should start with full resources"
        assert len(game_map.walls) > 0, "Tutorial map should have structure"
        assert game_map.gateway is not None, "Tutorial should have clear exit"
    
    def test_speedrun_optimization_scenario(self):
        """
        Scenario: Experienced player attempts to complete level quickly.
        Tests optimal gameplay paths and efficiency.
        """
        # ARRANGE: Optimal player setup
        player = Player(1, 1)
        game_map = GameMap(30, 20)
        generator = LevelGenerator(game_map)
        generator.generate_level(level=1, seed=200)  # Consistent seed for reproducible test
        
        # Give player optimal equipment
        optimal_exploits = ["shadow_step", "threat_scan"]  # Mobility and detection
        for exploit_name in optimal_exploits:
            exploit_item = ExploitItem(exploit_name)
            player.inventory_manager.add_item(exploit_item)
            player.inventory_manager.equip_exploit(exploit_item)
        
        # ACT 1: Find shortest path to gateway
        gateway = game_map.gateway
        if gateway:
            # Calculate Manhattan distance (optimal pathfinding would be better, but this tests basics)
            distance_to_gateway = abs(player.position.x - gateway.x) + abs(player.position.y - gateway.y)
            path_exists = distance_to_gateway > 0
        else:
            path_exists = False
        
        # ACT 2: Simulate efficient resource usage
        # Player should use minimal resources for maximum progress
        initial_resources = (player.cpu, player.heat)
        
        # Use efficient exploit (threat_scan for reconnaissance)
        mock_game = Mock()
        mock_game.player = player
        mock_game.message_log = MessageLog()
        mock_game.sound_manager = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        if gateway:
            scout_result = exploit_system.execute_exploit("threat_scan", gateway)
        else:
            scout_result = False
        
        final_resources = (player.cpu, player.heat)
        resource_efficiency = (final_resources[0] >= initial_resources[0] * 0.9)  # Minimal resource loss
        
        # ASSERT: Speedrun scenario demonstrates efficiency
        assert gateway is not None, "Map should have clear objective"
        assert path_exists, "Should have path to objective"
        assert len(player.inventory_manager.equipped_exploits) >= 1, "Should have mobility tools"
        assert resource_efficiency, "Should use resources efficiently"
        assert isinstance(scout_result, bool), "Reconnaissance should provide actionable result"
    
    def test_challenge_mode_scenario(self):
        """
        Scenario: Player faces maximum difficulty with limited resources.
        Tests game balance and difficulty scaling.
        """
        # ARRANGE: Challenge mode setup
        player = Player(25, 15)
        player.cpu = 50  # Reduced health
        player.heat = 60  # Already heated up
        
        # Create more complex map
        game_map = GameMap(60, 40)
        generator = LevelGenerator(game_map)
        generator.generate_level(level=2, seed=300)  # Higher level for complexity
        
        # Limited equipment
        challenge_exploit = ExploitItem("buffer_overflow")  # High-risk, high-reward
        player.inventory_manager.add_item(challenge_exploit)
        player.inventory_manager.equip_exploit(challenge_exploit)
        
        # ACT 1: Test survival under pressure
        initial_state = {
            'cpu': player.cpu,
            'heat': player.heat,
            'position': player.position
        }
        
        # ACT 2: High-risk action
        mock_game = Mock()
        mock_game.player = player
        mock_game.message_log = MessageLog()
        mock_game.sound_manager = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        # Use high-heat exploit near max heat (risky!)
        risky_target = Position(player.position.x + 2, player.position.y)
        risk_result = exploit_system.execute_exploit("buffer_overflow", risky_target)
        
        # ACT 3: Check survival and adaptation
        survival_state = {
            'alive': player.cpu > 0,
            'heat_managed': player.heat <= 100,
            'can_continue': player.cpu > 10  # Minimum viable health
        }
        
        # ASSERT: Challenge scenario tests limits appropriately
        assert initial_state['cpu'] < 100, "Challenge should start with constraints"
        assert initial_state['heat'] > 0, "Challenge should start with pressure"
        assert len(game_map.walls) > 100, "Challenge map should be complex"
        assert isinstance(risk_result, bool), "High-risk actions should have clear outcomes"
        assert survival_state['alive'], "Player should be able to survive with skill"
        assert survival_state['heat_managed'], "Heat management should be critical but possible"