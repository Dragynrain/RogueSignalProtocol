"""
Tests for visibility manager vision bonus handling.

Verifies that enemy vision caching correctly uses vision_range property
which includes ascension bonuses, not the base type_data.vision.
"""

from game_ascension import AscensionModifiers
from game_entities import Position


class TestVisionBonusInCaching:
    """Tests that vision bonuses are correctly applied in visibility caching."""

    def test_enemy_vision_uses_vision_range_property(self):
        """Vision caching should use vision_range, not type_data.vision."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)
        game_map = agent.engine.game_map
        visibility_manager = agent.engine.visibility_manager

        # Find a floor position near the player
        player = agent.engine.player
        spawn_pos = Position(player.x + 3, player.y + 3)
        # Ensure it's a floor tile
        if game_map.is_wall(spawn_pos):
            # Find any floor position
            for x in range(game_map.width):
                for y in range(game_map.height):
                    if not game_map.is_wall(Position(x, y)):
                        spawn_pos = Position(x, y)
                        break

        # Create a scanner enemy in the game
        scanner = agent.engine.enemy_manager.spawn_enemy(spawn_pos, "scanner")

        # Base scanner vision from type_data
        base_vision = scanner.type_data.vision

        # Apply A1 ascension modifier (scanner vision bonus)
        modifiers = AscensionModifiers()
        modifiers.scanner_vision_bonus = 2  # A1 bonus
        scanner.apply_ascension_modifiers(modifiers)

        # vision_range should now be base + bonus
        assert scanner.vision_range == base_vision + 2

        # Trigger cache population by calling can_enemy_see_player
        visibility_manager.can_enemy_see_player(scanner, agent.engine.player, current_turn=1)

        # Check that cache key uses vision_range, not type_data.vision
        expected_vision = scanner.vision_range
        expected_key = (scanner.x, scanner.y, expected_vision)

        assert expected_key in visibility_manager._enemy_fov_cache, (
            f"Cache key should use vision_range={expected_vision}, "
            f"not base vision={scanner.type_data.vision}"
        )

    def test_enemy_vision_cache_key_includes_bonus(self):
        """Cache key should use vision_range, not type_data.vision."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)
        game_map = agent.engine.game_map
        visibility_manager = agent.engine.visibility_manager

        # Find a floor position
        player = agent.engine.player
        spawn_pos = Position(player.x + 3, player.y + 3)
        if game_map.is_wall(spawn_pos):
            for x in range(game_map.width):
                for y in range(game_map.height):
                    if not game_map.is_wall(Position(x, y)):
                        spawn_pos = Position(x, y)
                        break

        # Create a scanner enemy
        scanner = agent.engine.enemy_manager.spawn_enemy(spawn_pos, "scanner")

        # Apply vision bonus
        modifiers = AscensionModifiers()
        modifiers.scanner_vision_bonus = 3
        scanner.apply_ascension_modifiers(modifiers)

        # Trigger cache population
        visibility_manager.can_enemy_see_player(scanner, agent.engine.player, current_turn=1)

        # Check that cache key uses vision_range, not type_data.vision
        expected_vision = scanner.vision_range
        expected_key = (scanner.x, scanner.y, expected_vision)

        assert expected_key in visibility_manager._enemy_fov_cache, (
            f"Cache key should use vision_range={expected_vision}, "
            f"not base vision={scanner.type_data.vision}"
        )

    def test_a5_all_enemy_vision_bonus(self):
        """A5 all-enemy vision bonus should affect visibility calculations."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)
        game_map = agent.engine.game_map
        visibility_manager = agent.engine.visibility_manager

        # Find a floor position
        player = agent.engine.player
        spawn_pos = Position(player.x + 3, player.y + 3)
        if game_map.is_wall(spawn_pos):
            for x in range(game_map.width):
                for y in range(game_map.height):
                    if not game_map.is_wall(Position(x, y)):
                        spawn_pos = Position(x, y)
                        break

        # Create a bot (not a scanner, to test A5)
        bot = agent.engine.enemy_manager.spawn_enemy(spawn_pos, "bot")
        base_vision = bot.type_data.vision

        # Apply A5 modifier
        modifiers = AscensionModifiers()
        modifiers.enemy_vision_bonus = 1  # A5 bonus
        bot.apply_ascension_modifiers(modifiers)

        assert bot.vision_range == base_vision + 1

        # Trigger cache population
        visibility_manager.can_enemy_see_player(bot, agent.engine.player, current_turn=1)

        # Check that cache key uses vision_range, not type_data.vision
        expected_vision = bot.vision_range
        expected_key = (bot.x, bot.y, expected_vision)

        assert expected_key in visibility_manager._enemy_fov_cache, (
            f"Cache key should use vision_range={expected_vision}, "
            f"not base vision={bot.type_data.vision}"
        )
