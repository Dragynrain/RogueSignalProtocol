"""
Balance Relationships Tests

Validates that game balance values have sensible relationships:
- MIN values are less than MAX values
- Difficulty scaling is progressive
- Resource costs and rewards are balanced
- Stat caps and limits are reasonable
- Game progression values make sense

These tests catch configuration errors that could break game balance.
"""

import pytest
import json
from pathlib import Path


class TestMinMaxRelationships:
    """Test that MIN/MAX value pairs have correct relationships."""

    def setup_method(self):
        """Load config files."""
        self.game_config = self._load_json('game_rules.json')
        self.game_data = self._load_json('game_content.json')

    def _load_json(self, filename):
        """Load a JSON file from project root."""
        path = Path(__file__).parent.parent.parent / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_cpu_restore_min_less_than_max(self):
        """Test that cpu_restore_min < cpu_restore_max."""
        # Check both files since this value is duplicated (see consistency tests)
        balance_config = self.game_config.get('balance', {})
        balance_data = self.game_data.get('balance', {})

        # Check game_config
        if 'cpu_restore_min' in balance_config and 'cpu_restore_max' in balance_config:
            min_val = balance_config['cpu_restore_min']
            max_val = balance_config['cpu_restore_max']
            assert min_val < max_val, (
                f"game_rules.json: cpu_restore_min ({min_val}) must be less than "
                f"cpu_restore_max ({max_val})"
            )
            assert min_val > 0, "cpu_restore_min must be positive"
            assert max_val > 0, "cpu_restore_max must be positive"

        # Check game_data
        if 'cpu_restore_min' in balance_data and 'cpu_restore_max' in balance_data:
            min_val = balance_data['cpu_restore_min']
            max_val = balance_data['cpu_restore_max']
            assert min_val < max_val, (
                f"game_content.json: cpu_restore_min ({min_val}) must be less than "
                f"cpu_restore_max ({max_val})"
            )

    def test_room_size_min_less_than_max(self):
        """Test that min_room_size < max_room_size."""
        room_gen = self.game_config.get('room_generation', {})

        min_size = room_gen.get('min_room_size', 0)
        max_size = room_gen.get('max_room_size', 0)

        assert min_size < max_size, (
            f"min_room_size ({min_size}) must be less than max_room_size ({max_size})"
        )
        assert min_size >= 3, "min_room_size should be at least 3 for playable rooms"
        assert max_size <= 15, "max_room_size should be reasonable (<= 15)"

    def test_heat_values_positive(self):
        """Test that all heat-related values are positive."""
        balance = self.game_config.get('balance', {})

        heat_values = {
            'heat_reduction_normal': balance.get('heat_reduction_normal'),
            'heat_reduction_boosted': balance.get('heat_reduction_boosted'),
            'heat_reduction_instant': balance.get('heat_reduction_instant'),
        }

        for name, value in heat_values.items():
            assert value > 0, f"{name} must be positive, got {value}"

    def test_heat_reduction_boosted_greater_than_normal(self):
        """Test that boosted cooling is better than normal cooling."""
        balance = self.game_config.get('balance', {})

        normal = balance.get('heat_reduction_normal', 0)
        boosted = balance.get('heat_reduction_boosted', 0)

        assert boosted > normal, (
            f"heat_reduction_boosted ({boosted}) must be greater than "
            f"heat_reduction_normal ({normal})"
        )

    def test_max_capacities_reasonable(self):
        """Test that max capacity values are reasonable."""
        gameplay = self.game_config.get('gameplay', {})

        max_heat = gameplay.get('max_heat', 0)
        max_trace = gameplay.get('max_trace_level', 0)
        max_ram = gameplay.get('max_ram_capacity', 0)
        max_cpu = gameplay.get('max_cpu_capacity', 0)

        # All should be positive
        assert max_heat > 0, "max_heat must be positive"
        assert max_trace > 0, "max_trace_level must be positive"
        assert max_ram > 0, "max_ram_capacity must be positive"
        assert max_cpu > 0, "max_cpu_capacity must be positive"

        # Reasonable ranges
        assert max_heat == 100, "max_heat should be 100 for percentage-based system"
        assert max_trace == 100, "max_trace_level should be 100 for percentage-based system"
        assert max_ram >= 8, "max_ram_capacity should be at least 8"
        assert max_cpu >= 100, "max_cpu_capacity should be at least 100"


class TestDifficultyScaling:
    """Test that difficulty multipliers scale correctly."""

    def setup_method(self):
        """Load game data."""
        self.game_data = self._load_json('game_content.json')

    def _load_json(self, filename):
        """Load a JSON file from project root."""
        path = Path(__file__).parent.parent.parent / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_difficulty_multipliers_ascending(self):
        """Test that difficulty multipliers increase progressively."""
        multipliers = self.game_data.get('difficulty_multipliers', {})

        easy = multipliers.get('easy', 0)
        normal = multipliers.get('normal', 0)
        hard = multipliers.get('hard', 0)
        nightmare = multipliers.get('nightmare', 0)

        # Progressive difficulty
        assert easy < normal, f"easy ({easy}) must be less than normal ({normal})"
        assert normal < hard, f"normal ({normal}) must be less than hard ({hard})"
        assert hard < nightmare, f"hard ({hard}) must be less than nightmare ({nightmare})"

        # Reasonable ranges
        assert easy >= 0.5, "easy difficulty should not be too easy (>= 0.5)"
        assert easy <= 1.0, "easy difficulty should be at or below normal"
        assert normal == 1.0, "normal difficulty should be baseline (1.0)"
        assert nightmare <= 2.0, "nightmare difficulty should not be impossible (<= 2.0)"

    def test_level_progression_difficulty(self):
        """Test that level configs show progressive difficulty."""
        networks = self.game_data.get('network_configs', {})

        # Extract level data
        level_1 = networks.get('1', {})
        level_2 = networks.get('2', {})
        level_3 = networks.get('3', {})

        # Enemy count should increase
        enemies_1 = level_1.get('enemies', 0)
        enemies_2 = level_2.get('enemies', 0)
        enemies_3 = level_3.get('enemies', 0)

        assert enemies_1 < enemies_2, "Level 2 should have more enemies than Level 1"
        assert enemies_2 < enemies_3, "Level 3 should have more enemies than Level 2"

        # Background trace should increase
        trace_1 = level_1.get('background_trace', 0)
        trace_2 = level_2.get('background_trace', 0)
        trace_3 = level_3.get('background_trace', 0)

        assert trace_1 <= trace_2, "Level 2 trace should be >= Level 1"
        assert trace_2 <= trace_3, "Level 3 trace should be >= Level 2"

    def test_resource_scarcity_progression(self):
        """Test that resource nodes become scarcer at higher levels."""
        networks = self.game_data.get('network_configs', {})

        level_1 = networks.get('1', {})
        level_2 = networks.get('2', {})
        level_3 = networks.get('3', {})

        # Cooling nodes should decrease or stay same
        cooling_1 = level_1.get('cooling_nodes', 0)
        cooling_2 = level_2.get('cooling_nodes', 0)
        cooling_3 = level_3.get('cooling_nodes', 0)

        assert cooling_1 >= cooling_2, "Level 2 should have same or fewer cooling nodes"
        assert cooling_2 >= cooling_3, "Level 3 should have same or fewer cooling nodes"

        # CPU nodes should decrease
        cpu_1 = level_1.get('cpu_nodes', 0)
        cpu_2 = level_2.get('cpu_nodes', 0)
        cpu_3 = level_3.get('cpu_nodes', 0)

        assert cpu_1 >= cpu_2, "Level 2 should have same or fewer CPU nodes"
        assert cpu_2 >= cpu_3, "Level 3 should have same or fewer CPU nodes"


class TestResourceBalance:
    """Test that resource costs and rewards are balanced."""

    def setup_method(self):
        """Load config files."""
        self.game_config = self._load_json('game_rules.json')
        self.game_data = self._load_json('game_content.json')

    def _load_json(self, filename):
        """Load a JSON file from project root."""
        path = Path(__file__).parent.parent.parent / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_exploit_heat_costs_reasonable(self):
        """Test that exploit heat costs are reasonable."""
        exploits = self.game_data.get('exploits', {})

        for exploit_id, data in exploits.items():
            heat_cost = data.get('heat', 0)
            category = data.get('category', 'unknown')

            assert heat_cost >= 0, f"Exploit '{exploit_id}' heat cost cannot be negative"
            assert heat_cost <= 100, f"Exploit '{exploit_id}' heat cost ({heat_cost}) exceeds max heat"

            # Emergency exploits should have high heat
            if category == 'emergency':
                assert heat_cost >= 40, f"Emergency exploit '{exploit_id}' should have high heat cost"

    def test_exploit_ram_costs_within_capacity(self):
        """Test that exploit RAM costs don't exceed max capacity."""
        exploits = self.game_data.get('exploits', {})
        max_ram = self.game_config.get('gameplay', {}).get('max_ram_capacity', 32)

        for exploit_id, data in exploits.items():
            ram_cost = data.get('ram', 0)

            assert ram_cost > 0, f"Exploit '{exploit_id}' should have positive RAM cost"
            assert ram_cost <= max_ram, (
                f"Exploit '{exploit_id}' RAM cost ({ram_cost}) exceeds max RAM ({max_ram})"
            )

    def test_enemy_rewards_reasonable(self):
        """Test that enemy elimination rewards are reasonable."""
        balance = self.game_config.get('balance', {})
        reward = balance.get('enemy_elimination_cpu_reward', 0)

        assert reward > 0, "Enemy elimination should reward CPU"
        assert reward <= 20, f"Enemy reward ({reward}) seems too generous"

    def test_node_effects_meaningful(self):
        """Test that special node effects are meaningful."""
        balance = self.game_config.get('balance', {})

        cooling_effect = balance.get('cooling_node_effect', 0)
        cpu_recovery = balance.get('cpu_recovery_amount', 0)
        ghost_trace_reduction = balance.get('ghost_node_trace_reduction_percent', 0)

        assert cooling_effect > 0, "Cooling node should reduce heat"
        assert cooling_effect <= 50, "Cooling node effect seems too powerful"

        assert cpu_recovery > 0, "CPU node should restore CPU"
        assert cpu_recovery <= 50, "CPU recovery seems too generous"

        assert ghost_trace_reduction > 0, "Ghost node should reduce trace"
        assert ghost_trace_reduction <= 50, "Ghost node trace reduction seems too powerful"


class TestEnemyBalance:
    """Test that enemy stats are balanced."""

    def setup_method(self):
        """Load game data."""
        self.game_data = self._load_json('game_content.json')

    def _load_json(self, filename):
        """Load a JSON file from project root."""
        path = Path(__file__).parent.parent.parent / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_enemy_cpu_values_positive(self):
        """Test that all enemies have positive CPU."""
        enemies = self.game_data.get('enemy_types', {})

        for enemy_id, data in enemies.items():
            cpu = data.get('cpu', 0)
            assert cpu > 0, f"Enemy '{enemy_id}' must have positive CPU, got {cpu}"

    def test_enemy_vision_reasonable(self):
        """Test that enemy vision ranges are reasonable."""
        enemies = self.game_data.get('enemy_types', {})

        for enemy_id, data in enemies.items():
            vision = data.get('vision', 0)
            assert vision > 0, f"Enemy '{enemy_id}' must have positive vision"
            assert vision <= 10, f"Enemy '{enemy_id}' vision ({vision}) seems too high"

    def test_enemy_damage_non_negative(self):
        """Test that enemy damage values are non-negative."""
        enemies = self.game_data.get('enemy_types', {})

        for enemy_id, data in enemies.items():
            damage = data.get('damage', -1)
            assert damage >= 0, f"Enemy '{enemy_id}' damage cannot be negative, got {damage}"

    def test_admin_is_strongest(self):
        """Test that admin enemy has highest stats."""
        enemies = self.game_data.get('enemy_types', {})

        admin = enemies.get('admin', {})
        admin_cpu = admin.get('cpu', 0)
        admin_damage = admin.get('damage', 0)
        admin_vision = admin.get('vision', 0)

        # Admin should have highest CPU
        for enemy_id, data in enemies.items():
            if enemy_id != 'admin':
                enemy_cpu = data.get('cpu', 0)
                assert admin_cpu > enemy_cpu, (
                    f"Admin CPU ({admin_cpu}) should exceed {enemy_id} CPU ({enemy_cpu})"
                )

        # Admin should have highest or tied damage
        for enemy_id, data in enemies.items():
            if enemy_id != 'admin':
                enemy_damage = data.get('damage', 0)
                assert admin_damage >= enemy_damage, (
                    f"Admin damage ({admin_damage}) should be >= {enemy_id} damage ({enemy_damage})"
                )

        # Admin should have highest vision
        for enemy_id, data in enemies.items():
            if enemy_id != 'admin':
                enemy_vision = data.get('vision', 0)
                assert admin_vision >= enemy_vision, (
                    f"Admin vision ({admin_vision}) should be >= {enemy_id} vision ({enemy_vision})"
                )

    def test_scanner_no_damage(self):
        """Test that scanner enemy has no attack (pure detection)."""
        enemies = self.game_data.get('enemy_types', {})
        scanner = enemies.get('scanner', {})

        damage = scanner.get('damage', -1)
        assert damage == 0, f"Scanner should have 0 damage (detection only), got {damage}"

    def test_firewall_light_damage(self):
        """Test that firewall enemy has light damage (obstacle with light attack)."""
        enemies = self.game_data.get('enemy_types', {})
        firewall = enemies.get('firewall', {})

        damage = firewall.get('damage', -1)
        assert damage >= 0, f"Firewall damage cannot be negative, got {damage}"
        assert damage <= 10, f"Firewall should have light damage (<= 10), got {damage}"


class TestExploitBalance:
    """Test that exploit stats are balanced."""

    def setup_method(self):
        """Load game data."""
        self.game_data = self._load_json('game_content.json')

    def _load_json(self, filename):
        """Load a JSON file from project root."""
        path = Path(__file__).parent.parent.parent / filename
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_combat_exploits_have_damage(self):
        """Test that combat category exploits have damage > 0."""
        exploits = self.game_data.get('exploits', {})

        combat_exploits = {k: v for k, v in exploits.items() if v.get('category') == 'combat'}

        for exploit_id, data in combat_exploits.items():
            damage = data.get('damage', 0)
            # memory_leak is combat but has no direct damage (confuses enemies)
            if exploit_id != 'memory_leak':
                assert damage > 0, (
                    f"Combat exploit '{exploit_id}' should have damage > 0, got {damage}"
                )

    def test_stealth_exploits_no_damage(self):
        """Test that stealth exploits don't deal direct damage."""
        exploits = self.game_data.get('exploits', {})

        stealth_exploits = {k: v for k, v in exploits.items() if v.get('category') == 'stealth'}

        for exploit_id, data in stealth_exploits.items():
            damage = data.get('damage', -1)
            assert damage == 0, (
                f"Stealth exploit '{exploit_id}' should have 0 damage, got {damage}"
            )

    def test_utility_exploits_no_damage(self):
        """Test that utility exploits don't deal direct damage."""
        exploits = self.game_data.get('exploits', {})

        utility_exploits = {k: v for k, v in exploits.items() if v.get('category') == 'utility'}

        for exploit_id, data in utility_exploits.items():
            damage = data.get('damage', -1)
            assert damage == 0, (
                f"Utility exploit '{exploit_id}' should have 0 damage, got {damage}"
            )

    def test_melee_exploits_range_one(self):
        """Test that melee exploits have range == 1."""
        exploits = self.game_data.get('exploits', {})

        # Buffer overflow is explicitly melee
        buffer_overflow = exploits.get('buffer_overflow', {})
        assert buffer_overflow.get('range') == 1, "buffer_overflow should be melee (range 1)"

    def test_area_exploits_have_reasonable_range(self):
        """Test that area effect exploits have reasonable ranges."""
        exploits = self.game_data.get('exploits', {})

        area_exploits = {k: v for k, v in exploits.items() if v.get('targeting') == 'AREA'}

        for exploit_id, data in area_exploits.items():
            range_val = data.get('range', 0)
            assert range_val > 0, f"Area exploit '{exploit_id}' should have positive range"
            assert range_val <= 5, f"Area exploit '{exploit_id}' range ({range_val}) seems too large"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
