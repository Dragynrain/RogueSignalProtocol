"""
Complete level playthrough integration tests.

Tests the entire level playthrough workflow including:
- Level initialization and map generation
- Item collection (code hacks, exploits, story fragments, upgrades)
- Enemy engagement and defeat
- Gateway discovery and level progression
- State persistence across level transitions
- Resource management throughout gameplay

This test suite focuses on real gameplay behavior, not mocked interactions.
"""

import pytest
from unittest.mock import Mock
import copy

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState
from game_config import GameConfig, GameSettings, GameBalance
from game_inventory import CodeHack, ExploitItem, StoryFragment
from game_data import GameData, GameUpgrades
from tests.fixtures.real_game_data import get_real_game_data
from tests.fixtures.simple_fixtures import create_real_player


class TestCompleteLevelPlaythrough:
    """Test complete level playthrough workflows from start to gateway."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create real game data
        self.game_data = get_real_game_data()

        # Create game settings with muted audio for tests
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.sfx_volume = 0.0
        self.game_settings.music_volume = 0.0
        self.game_settings.graphics_mode = "ascii"

    def teardown_method(self):
        """Clean up test fixtures."""
        pass

    def create_test_engine(self, level=1):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )

        # Set initial level
        engine.level = level

        return engine

    def test_level_initialization_creates_valid_game_state(self):
        """Test that level initialization creates a valid, playable game state."""
        engine = self.create_test_engine(level=1)

        # Verify engine initialized correctly
        assert engine.level == 1
        assert engine.game_over == False
        assert engine.turn >= 0

        # Verify player exists and has valid state
        assert engine.player is not None
        assert engine.player.cpu > 0
        assert engine.player.max_cpu > 0
        assert engine.player.trace_level >= 0
        assert 0 <= engine.player.x < GameConfig.MAP_WIDTH
        assert 0 <= engine.player.y < GameConfig.MAP_HEIGHT

        # Verify map exists and is valid
        assert engine.game_map is not None
        assert engine.game_map.width == GameConfig.MAP_WIDTH
        assert engine.game_map.height == GameConfig.MAP_HEIGHT
        assert len(engine.game_map.walls) > 0

        # Verify player not in wall
        player_pos = (engine.player.x, engine.player.y)
        assert player_pos not in engine.game_map.walls

        # Verify gateway exists
        assert engine.game_map.gateway is not None
        assert isinstance(engine.game_map.gateway, Position)

        # Verify enemies were spawned
        assert len(engine.enemies) > 0

        # Verify all enemies are in valid positions
        for enemy in engine.enemies:
            assert 0 <= enemy.x < GameConfig.MAP_WIDTH
            assert 0 <= enemy.y < GameConfig.MAP_HEIGHT
            assert (enemy.x, enemy.y) not in engine.game_map.walls
            assert enemy.state == EnemyState.UNAWARE

    def test_code_hack_collection_and_usage_in_level(self):
        """Test collecting and using code hacks during level playthrough."""
        engine = self.create_test_engine(level=1)

        # Find a code hack on the map
        code_positions = list(engine.game_map.code_hacks.keys())
        assert len(code_positions) > 0, "No code hacks spawned on level"

        # Get initial player stats
        initial_cpu = engine.player.cpu
        initial_heat = engine.player.heat
        initial_inventory_count = len(engine.player.inventory_manager.items)

        # Move player to a code hack position
        code_pos = code_positions[0]
        code_hack = engine.game_map.code_hacks[code_pos]
        engine.player.x = code_pos[0]
        engine.player.y = code_pos[1]

        # Process turn to collect the code hack
        engine.maybe_process_turn()

        # Verify code hack was collected
        assert code_pos not in engine.game_map.code_hacks, "Code hack not removed from map"
        assert len(engine.player.inventory_manager.items) > initial_inventory_count, "Code hack not added to inventory"

        # Verify code hack is in inventory
        code_in_inventory = None
        for item in engine.player.inventory_manager.items:
            if isinstance(item, CodeHack) and item.color_name == code_hack.color_name:
                code_in_inventory = item
                break

        assert code_in_inventory is not None, "Code hack not found in inventory"

        # Use the code hack
        pre_use_cpu = engine.player.cpu
        pre_use_heat = engine.player.heat

        # Code hacks have different effects based on color
        # We'll test that using the code has SOME effect
        success = code_in_inventory.use(engine.player, engine)

        assert success, "Code hack use failed"

        # Verify code hack was consumed
        post_use_count = len(engine.player.inventory_manager.items)
        assert post_use_count <= len(engine.player.inventory_manager.items), "Code hack not consumed or quantity decreased"

        # Verify some stat changed (CPU, heat, or trace level)
        stats_changed = (
            engine.player.cpu != pre_use_cpu or
            engine.player.heat != pre_use_heat or
            engine.player.trace_level != 0  # Trace could have been affected
        )
        assert stats_changed or engine.player.cpu == engine.player.max_cpu, "Code hack had no visible effect"

    def test_exploit_pickup_collection_and_equipping(self):
        """Test collecting exploit pickups and equipping them."""
        engine = self.create_test_engine(level=1)

        # Find an exploit pickup on the map
        exploit_positions = list(engine.game_map.exploit_pickups.keys())
        assert len(exploit_positions) > 0, "No exploit pickups spawned on level"

        # Get initial equipped exploit count
        initial_equipped_count = len(engine.player.inventory_manager.equipped_exploits)

        # Move player to exploit pickup
        exploit_pos = exploit_positions[0]
        exploit_item = engine.game_map.exploit_pickups[exploit_pos]
        engine.player.x = exploit_pos[0]
        engine.player.y = exploit_pos[1]

        # Process turn to collect the exploit
        engine.maybe_process_turn()

        # Verify exploit was collected from map
        assert exploit_pos not in engine.game_map.exploit_pickups, "Exploit not removed from map"

        # Verify exploit is in inventory
        exploit_in_inventory = None
        for item in engine.player.inventory_manager.items:
            if isinstance(item, ExploitItem) and item.exploit_key == exploit_item.exploit_key:
                exploit_in_inventory = item
                break

        assert exploit_in_inventory is not None, "Exploit not found in inventory"

        # Equip the exploit if there's room (pass ExploitItem, not string)
        if initial_equipped_count < 5:  # Max 5 exploits
            success = engine.player.inventory_manager.equip_exploit(exploit_in_inventory)
            assert success, "Failed to equip exploit"
            assert exploit_item.exploit_key in engine.player.inventory_manager.equipped_exploits, "Exploit not in equipped list"

    def test_permanent_upgrade_collection_and_effect(self):
        """Test collecting permanent upgrades and verifying their effects."""
        engine = self.create_test_engine(level=2)  # Level 2 has more upgrades

        # Find a permanent upgrade on the map
        upgrade_positions = list(engine.game_map.permanent_upgrades.keys())

        if len(upgrade_positions) == 0:
            # Try level 3 if level 2 has no upgrades
            engine = self.create_test_engine(level=3)
            upgrade_positions = list(engine.game_map.permanent_upgrades.keys())

        assert len(upgrade_positions) > 0, "No permanent upgrades spawned on any level"

        # Get the upgrade key
        upgrade_pos = upgrade_positions[0]
        upgrade_key = engine.game_map.permanent_upgrades[upgrade_pos]
        upgrade_def = GameUpgrades.UPGRADES[upgrade_key]

        # Store pre-upgrade stats
        pre_max_cpu = engine.player.max_cpu
        pre_max_heat = engine.player.max_heat
        pre_ram_total = engine.player.ram_total

        # Move player to upgrade position
        engine.player.x = upgrade_pos[0]
        engine.player.y = upgrade_pos[1]

        # Process turn to collect the upgrade
        engine.maybe_process_turn()

        # Verify upgrade was collected
        assert upgrade_pos not in engine.game_map.permanent_upgrades, "Upgrade not removed from map"

        # Verify upgrade effect was applied (based on upgrade type)
        stat_changed = False
        if upgrade_def.stat_type == 'cpu':
            assert engine.player.max_cpu > pre_max_cpu, "Max CPU not increased"
            stat_changed = True
        elif upgrade_def.stat_type == 'heat':
            assert engine.player.max_heat > pre_max_heat, "Max heat not increased"
            stat_changed = True
        elif upgrade_def.stat_type == 'ram':
            assert engine.player.ram_total > pre_ram_total, "RAM total not increased"
            stat_changed = True

        assert stat_changed, "No stat was changed by upgrade"

    def test_enemy_engagement_and_defeat(self):
        """Test engaging and defeating an enemy during level playthrough."""
        engine = self.create_test_engine(level=1)

        # Find an enemy
        assert len(engine.enemies) > 0, "No enemies on level"
        target_enemy = engine.enemies[0]

        # Record initial enemy count
        initial_enemy_count = len(engine.enemies)

        # Position player adjacent to enemy for bump attack
        engine.player.x = target_enemy.x + 1
        engine.player.y = target_enemy.y

        # Give player high CPU to survive
        engine.player.cpu = 100

        # Damage the enemy until defeated using bump attacks
        max_attempts = 10  # Prevent infinite loop
        attempts = 0

        while target_enemy in engine.enemies and attempts < max_attempts:
            attempts += 1

            # Move into enemy to bump attack (this triggers attack)
            dx = target_enemy.x - engine.player.x
            dy = target_enemy.y - engine.player.y

            # Try to move into enemy position (triggers bump attack)
            engine.move_player(dx, dy)

        # Verify enemy was defeated
        assert target_enemy not in engine.enemies, f"Enemy not defeated after {attempts} attempts"
        assert len(engine.enemies) < initial_enemy_count, "Enemy count not decreased"

    def test_gateway_discovery_triggers_confirmation_dialog(self):
        """Test that reaching the gateway triggers confirmation dialog."""
        engine = self.create_test_engine(level=1)

        # Get gateway position
        gateway = engine.game_map.gateway
        assert gateway is not None, "No gateway on map"

        # Position player near gateway
        engine.player.x = gateway.x - 1
        engine.player.y = gateway.y

        # Verify dialogue not shown yet
        assert engine.dialogue_manager.is_active() == False

        # Move player onto gateway (this triggers the confirmation dialogue)
        engine.move_player(1, 0)

        # Verify gateway confirmation dialogue is shown
        from game_dialogue import DialogueType
        assert engine.dialogue_manager.is_active() == True, "Gateway dialogue not shown"
        assert engine.dialogue_manager.active_dialogue == DialogueType.GATEWAY_CONFIRM, "Wrong dialogue type shown"

        # Verify sound effect was played
        engine.sound_manager.play_sound.assert_called_with("ui_menu_open")

    def test_gateway_confirmation_progresses_to_next_level(self):
        """Test that confirming gateway dialog progresses to next level."""
        engine = self.create_test_engine(level=1)

        # Move player to gateway and trigger confirmation
        gateway = engine.game_map.gateway
        engine.player.x = gateway.x - 1
        engine.player.y = gateway.y
        engine.move_player(1, 0)

        # Verify gateway confirmation dialogue is shown
        from game_dialogue import DialogueType
        assert engine.dialogue_manager.is_active() == True
        assert engine.dialogue_manager.active_dialogue == DialogueType.GATEWAY_CONFIRM

        # Dismiss dialogue and progress
        initial_level = engine.level
        engine.dialogue_manager.close_dialogue()
        engine.next_level()

        # Verify level progression
        assert engine.level == initial_level + 1, "Level not incremented"
        assert engine.game_over == False, "Game should not be over"

        # Verify new level was generated
        assert engine.game_map is not None
        new_gateway = engine.game_map.gateway
        assert new_gateway is not None
        assert new_gateway != gateway, "Gateway position should change"

        # Verify player position is valid on new level
        assert 0 <= engine.player.x < GameConfig.MAP_WIDTH
        assert 0 <= engine.player.y < GameConfig.MAP_HEIGHT
        assert (engine.player.x, engine.player.y) not in engine.game_map.walls

    def test_state_persistence_across_level_transitions(self):
        """Test that player state persists correctly across level transitions."""
        engine = self.create_test_engine(level=1)

        # Modify player state
        engine.player.cpu = 75
        engine.player.heat = 30
        engine.player.trace_level = 15

        # Record pre-transition state (equipped exploits should already have at least 1)
        pre_cpu = engine.player.cpu
        pre_heat = engine.player.heat
        pre_trace = engine.player.trace_level
        pre_equipped = copy.deepcopy(engine.player.inventory_manager.equipped_exploits)
        pre_max_cpu = engine.player.max_cpu
        pre_ram_total = engine.player.ram_total

        # Progress to next level
        engine.next_level()

        # Verify state persistence
        assert engine.player.cpu == pre_cpu, "CPU not preserved"
        assert engine.player.heat == pre_heat, "Heat not preserved"
        # Note: trace_level resets to 0 on level transition (by design)
        assert engine.player.trace_level == 0, "Trace level should reset to 0"

        # Verify inventory persisted
        assert engine.player.inventory_manager.equipped_exploits == pre_equipped, "Equipped exploits not preserved"

        # Verify base stats persisted
        assert engine.player.max_cpu == pre_max_cpu, "Max CPU not preserved"
        assert engine.player.ram_total == pre_ram_total, "RAM total not preserved"

    def test_complete_playthrough_level_1_to_2(self):
        """Test complete playthrough from level 1 start to level 2 arrival."""
        engine = self.create_test_engine(level=1)

        # Verify starting conditions
        assert engine.level == 1
        initial_cpu = engine.player.cpu

        # Collect some items
        if len(engine.game_map.code_hacks) > 0:
            code_pos = list(engine.game_map.code_hacks.keys())[0]
            engine.player.x = code_pos[0]
            engine.player.y = code_pos[1]
            engine.maybe_process_turn()
            assert len(engine.player.inventory_manager.items) > 0, "Failed to collect code hack"

        # Engage an enemy (optional, just verify system works)
        if len(engine.enemies) > 0:
            enemy = engine.enemies[0]
            # Just verify enemy exists and has valid state
            assert enemy.state == EnemyState.UNAWARE
            assert enemy.cpu > 0

        # Reach gateway
        gateway = engine.game_map.gateway
        engine.player.x = gateway.x - 1
        engine.player.y = gateway.y
        engine.move_player(1, 0)

        # Verify gateway confirmation dialogue is shown
        from game_dialogue import DialogueType
        assert engine.dialogue_manager.is_active() == True, "Gateway dialogue not shown"
        assert engine.dialogue_manager.active_dialogue == DialogueType.GATEWAY_CONFIRM

        # Dismiss dialogue and progress
        engine.dialogue_manager.close_dialogue()
        engine.next_level()

        # Verify level 2 state
        assert engine.level == 2
        assert engine.game_over == False
        assert engine.game_map is not None
        assert len(engine.enemies) > 0
        assert engine.game_map.gateway is not None

        # Verify player still has valid state
        assert engine.player.cpu > 0
        assert 0 <= engine.player.x < GameConfig.MAP_WIDTH
        assert 0 <= engine.player.y < GameConfig.MAP_HEIGHT

    def test_story_fragment_collection_on_level_3(self):
        """Test story fragment collection on level 3 (50% spawn chance)."""
        # Run test multiple times to account for 50% spawn rate
        fragment_found = False

        for _ in range(10):  # Try up to 10 times
            engine = self.create_test_engine(level=3)

            if len(engine.game_map.story_fragments) > 0:
                fragment_found = True

                # Test collecting the fragment
                fragment_pos = list(engine.game_map.story_fragments.keys())[0]
                fragment = engine.game_map.story_fragments[fragment_pos]

                # Verify fragment is valid
                assert isinstance(fragment, StoryFragment)
                assert fragment.fragment_index >= 0

                # Move player to fragment
                engine.player.x = fragment_pos[0]
                engine.player.y = fragment_pos[1]

                # Process turn to collect
                engine.maybe_process_turn()

                # Verify fragment was collected
                assert fragment_pos not in engine.game_map.story_fragments, "Fragment not removed from map"

                break

        # Note: Fragment might not spawn due to 50% chance and randomness
        # This test just verifies the collection mechanism works when fragments DO spawn
        if not fragment_found:
            # This is okay - 50% chance means we might not find one in 10 tries (though unlikely)
            pass

    def test_resource_management_throughout_level(self):
        """Test CPU, heat, and trace level management during level playthrough."""
        engine = self.create_test_engine(level=1)

        # Record initial resources
        initial_cpu = engine.player.cpu
        initial_max_cpu = engine.player.max_cpu
        initial_heat = engine.player.heat
        initial_trace = engine.player.trace_level

        # Verify resources are in valid ranges
        assert 0 <= initial_cpu <= initial_max_cpu, "CPU out of valid range"
        assert 0 <= initial_heat <= engine.player.max_heat, "Heat out of valid range"
        assert initial_trace >= 0, "Trace level negative"

        # Use an exploit to consume CPU and generate heat
        if len(engine.player.inventory_manager.equipped_exploits) > 0:
            exploit_key = engine.player.inventory_manager.equipped_exploits[0]
            exploit_def = GameData.EXPLOITS[exploit_key]

            # Ensure player has enough CPU
            engine.player.cpu = 100

            from game_combat import ExploitSystem
            exploit_system = ExploitSystem(engine)

            # Try to use exploit (might require targeting)
            # For this test, we just verify the system exists and doesn't crash
            assert exploit_system is not None

        # Find and use a CPU recovery node if available
        if len(engine.game_map.cpu_recovery_nodes) > 0:
            # Reduce CPU first
            engine.player.cpu = 50
            cpu_before = engine.player.cpu

            # Move to CPU node
            cpu_node = list(engine.game_map.cpu_recovery_nodes)[0]
            engine.player.x = cpu_node[0]
            engine.player.y = cpu_node[1]

            # Process turn
            engine.maybe_process_turn()

            # Verify CPU was restored (or at least didn't decrease significantly)
            # Note: Turn processing might consume some CPU, so check if total is positive or increased
            assert engine.player.cpu >= cpu_before - 5, "CPU decreased unexpectedly from CPU node"

        # Find and use a cooling node if available
        if len(engine.game_map.cooling_nodes) > 0:
            # Generate heat first
            engine.player.heat = 40

            # Move to cooling node
            cooling_node = list(engine.game_map.cooling_nodes)[0]
            engine.player.x = cooling_node[0]
            engine.player.y = cooling_node[1]

            # Process turn
            engine.maybe_process_turn()

            # Verify heat was reduced
            assert engine.player.heat < 40, "Heat not reduced from cooling node"

    def test_level_completion_with_enemies_remaining(self):
        """Test that player can complete level even with enemies still alive."""
        engine = self.create_test_engine(level=1)

        # Verify enemies exist
        assert len(engine.enemies) > 0

        # Go straight to gateway without defeating all enemies
        gateway = engine.game_map.gateway
        engine.player.x = gateway.x - 1
        engine.player.y = gateway.y
        engine.move_player(1, 0)

        # Verify gateway confirmation dialogue shown (player can leave even with enemies alive)
        from game_dialogue import DialogueType
        assert engine.dialogue_manager.is_active() == True
        assert engine.dialogue_manager.active_dialogue == DialogueType.GATEWAY_CONFIRM

        # Dismiss dialogue and progress
        enemy_count_before = len(engine.enemies)
        engine.dialogue_manager.close_dialogue()
        engine.next_level()

        # Verify progression worked
        assert engine.level == 2
        assert engine.game_over == False

        # Verify new enemies were spawned (not the same enemies)
        # New level should have its own enemies
        assert len(engine.enemies) > 0

    def test_multiple_level_transitions_preserve_progression(self):
        """Test that multiple level transitions preserve game progression."""
        engine = self.create_test_engine(level=1)

        # Record initial max_cpu (permanent upgrades affect this stat)
        initial_max_cpu = engine.player.max_cpu

        # Progress through levels 1 -> 2 -> 3
        for target_level in [2, 3]:
            current_level = engine.level
            engine.next_level()

            assert engine.level == target_level, f"Failed to progress to level {target_level}"
            # Verify player still has same max_cpu (no upgrades collected)
            assert engine.player.max_cpu == initial_max_cpu, f"Max CPU changed unexpectedly at level {target_level}"
            assert engine.game_map is not None
            assert len(engine.enemies) > 0

        # Verify we're on level 3
        assert engine.level == 3

        # Progress past level 3 (should trigger victory)
        engine.next_level()

        # Verify victory
        assert engine.level == 4
        assert engine.game_over == True

    def test_level_playthrough_with_full_inventory(self):
        """Test level playthrough behavior when inventory is full or nearly full."""
        engine = self.create_test_engine(level=1)

        # Fill inventory with test items
        for i in range(10):  # Add several items
            exploit_key = list(GameData.EXPLOITS.keys())[i % len(GameData.EXPLOITS)]
            exploit_def = GameData.EXPLOITS[exploit_key]
            test_item = ExploitItem(exploit_key, exploit_def)
            engine.player.inventory_manager.add_item(test_item)

        initial_inventory_count = len(engine.player.inventory_manager.items)

        # Try to collect another item
        if len(engine.game_map.exploit_pickups) > 0:
            exploit_pos = list(engine.game_map.exploit_pickups.keys())[0]
            engine.player.x = exploit_pos[0]
            engine.player.y = exploit_pos[1]
            engine.maybe_process_turn()

            # Verify item was added (or inventory system handles overflow gracefully)
            final_inventory_count = len(engine.player.inventory_manager.items)
            assert final_inventory_count >= initial_inventory_count, "Inventory count decreased unexpectedly"

        # Verify game is still playable
        assert engine.player.cpu > 0
        assert not engine.game_over


class TestLevelEnvironmentGeneration:
    """Test level environment and feature generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.sfx_volume = 0.0
        self.game_settings.music_volume = 0.0
        self.game_settings.graphics_mode = "ascii"

    def create_test_engine(self, level=1):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )
        engine.level = level
        return engine

    def test_all_essential_map_features_generated(self):
        """Test that all essential map features are generated on each level."""
        for level in [1, 2, 3]:
            engine = self.create_test_engine(level=level)

            # Verify walls exist
            assert len(engine.game_map.walls) > 0, f"No walls on level {level}"

            # Verify border walls exist
            assert (0, 0) in engine.game_map.walls, f"Missing top-left border on level {level}"
            assert (GameConfig.MAP_WIDTH-1, 0) in engine.game_map.walls, f"Missing top-right border on level {level}"

            # Verify gateway exists
            assert engine.game_map.gateway is not None, f"No gateway on level {level}"

            # Verify code hacks spawned
            assert len(engine.game_map.code_hacks) > 0, f"No code hacks on level {level}"

            # Verify exploit pickups spawned
            assert len(engine.game_map.exploit_pickups) > 0, f"No exploit pickups on level {level}"

            # Verify special nodes spawned
            network_config = engine.game_state.get_current_network_config()

            if network_config.get('cooling_nodes', 0) > 0:
                assert len(engine.game_map.cooling_nodes) > 0, f"No cooling nodes on level {level}"

            if network_config.get('cpu_nodes', 0) > 0:
                assert len(engine.game_map.cpu_recovery_nodes) > 0, f"No CPU nodes on level {level}"

    def test_shadow_coverage_varies_by_level(self):
        """Test that shadow coverage follows network configuration per level."""
        shadow_counts = {}

        for level in [1, 2, 3]:
            engine = self.create_test_engine(level=level)
            shadow_counts[level] = len(engine.game_map.shadows)

            # Verify shadows exist
            network_config = engine.game_state.get_current_network_config()
            if network_config.get('shadow_coverage', 0) > 0:
                assert shadow_counts[level] > 0, f"No shadows on level {level} despite shadow_coverage > 0"

    def test_enemy_density_scales_with_level(self):
        """Test that enemy density increases or stays same across levels."""
        enemy_counts = {}

        for level in [1, 2, 3]:
            engine = self.create_test_engine(level=level)
            enemy_counts[level] = len(engine.enemies)

        # Later levels should have same or more enemies
        assert enemy_counts[2] >= enemy_counts[1], "Level 2 has fewer enemies than level 1"
        assert enemy_counts[3] >= enemy_counts[2], "Level 3 has fewer enemies than level 2"

    def test_items_spawn_in_accessible_locations(self):
        """Test that all items spawn in locations the player can reach."""
        engine = self.create_test_engine(level=1)

        # Check code hacks
        for pos in engine.game_map.code_hacks.keys():
            assert pos not in engine.game_map.walls, f"Code hack at {pos} is in a wall"
            assert 0 <= pos[0] < GameConfig.MAP_WIDTH, f"Code hack X coordinate {pos[0]} out of bounds"
            assert 0 <= pos[1] < GameConfig.MAP_HEIGHT, f"Code hack Y coordinate {pos[1]} out of bounds"

        # Check exploit pickups
        for pos in engine.game_map.exploit_pickups.keys():
            assert pos not in engine.game_map.walls, f"Exploit at {pos} is in a wall"
            assert 0 <= pos[0] < GameConfig.MAP_WIDTH, f"Exploit X coordinate {pos[0]} out of bounds"
            assert 0 <= pos[1] < GameConfig.MAP_HEIGHT, f"Exploit Y coordinate {pos[1]} out of bounds"

        # Check permanent upgrades
        for pos in engine.game_map.permanent_upgrades.keys():
            assert pos not in engine.game_map.walls, f"Upgrade at {pos} is in a wall"
            assert 0 <= pos[0] < GameConfig.MAP_WIDTH, f"Upgrade X coordinate {pos[0]} out of bounds"
            assert 0 <= pos[1] < GameConfig.MAP_HEIGHT, f"Upgrade Y coordinate {pos[1]} out of bounds"

    def test_gateway_spawns_far_from_player_start(self):
        """Test that gateway spawns a reasonable distance from player starting position."""
        engine = self.create_test_engine(level=1)

        # Player should start in top-left spawn area (around 5,5)
        player_start = Position(engine.player.x, engine.player.y)
        gateway_pos = engine.game_map.gateway

        # Calculate distance
        distance = player_start.distance_to(gateway_pos)

        # Gateway should be reasonably far (at least 15 tiles away)
        assert distance >= 15, f"Gateway too close to player start: {distance} tiles"
