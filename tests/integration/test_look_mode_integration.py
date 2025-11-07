#!/usr/bin/env python3
"""
Integration tests for Look Mode functionality.
Tests the complete look mode workflow without heavy mocking.
"""

import pytest
import tcod.event
from game_engine import GameEngine
from game_entities import Position
from game_inspection import EntityInspector
from game_characters import Player, Enemy
from game_data import GameData
from game_inventory import CodeHack, ExploitItem


class TestLookModeIntegration:
    """Integration tests for look mode system."""

    def test_enter_look_mode_with_l_key(self):
        """Test entering look mode with L key."""
        game = GameEngine(load_save=False)

        # Dismiss intro dialogue (new games show intro)
        if game.dialogue_state.is_active():
            game.dialogue_state.close()

        # Verify initially not in look mode
        assert not game.look_mode

        # Simulate pressing L
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.L,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )

        game.input_handler.handle_keydown(event)

        # Verify look mode is active
        assert game.look_mode
        # Cursor should start at player position
        assert game.look_cursor_position.x == game.player.x
        assert game.look_cursor_position.y == game.player.y

    def test_exit_look_mode_with_esc(self):
        """Test exiting look mode with ESC key."""
        game = GameEngine(load_save=False)

        # Dismiss intro dialogue (new games show intro)
        if game.dialogue_state.is_active():
            game.dialogue_state.close()

        # Enter look mode
        game.look_mode = True
        game.look_cursor_position = Position(game.player.x, game.player.y)

        # Simulate pressing ESC
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )

        game.input_handler.handle_keydown(event)

        # Verify look mode is inactive
        assert not game.look_mode

    def test_exit_look_mode_with_l_key(self):
        """Test exiting look mode with L key."""
        game = GameEngine(load_save=False)

        # Dismiss intro dialogue (new games show intro)
        if game.dialogue_state.is_active():
            game.dialogue_state.close()

        # Enter look mode
        game.look_mode = True
        game.look_cursor_position = Position(game.player.x, game.player.y)

        # Simulate pressing L again
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.L,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )

        game.input_handler.handle_keydown(event)

        # Verify look mode is inactive
        assert not game.look_mode

    def test_move_cursor_with_arrow_keys(self):
        """Test moving look mode cursor with arrow keys."""
        game = GameEngine(load_save=False)

        # Dismiss intro dialogue (new games show intro)
        if game.dialogue_state.is_active():
            game.dialogue_state.close()

        # Enter look mode
        game.look_mode = True
        initial_x = game.player.x
        initial_y = game.player.y
        game.look_cursor_position = Position(initial_x, initial_y)

        # Move right
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RIGHT,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event)
        assert game.look_cursor_position.x == initial_x + 1
        assert game.look_cursor_position.y == initial_y

        # Move down
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event)
        assert game.look_cursor_position.x == initial_x + 1
        assert game.look_cursor_position.y == initial_y + 1

    def test_move_cursor_with_wasd_keys(self):
        """Test moving look mode cursor with WASD keys."""
        game = GameEngine(load_save=False)

        # Dismiss intro dialogue (new games show intro)
        if game.dialogue_state.is_active():
            game.dialogue_state.close()

        # Enter look mode
        game.look_mode = True
        initial_x = game.player.x
        initial_y = game.player.y
        game.look_cursor_position = Position(initial_x, initial_y)

        # Move right with D
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.D,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event)
        assert game.look_cursor_position.x == initial_x + 1

        # Move up with W
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.W,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event)
        assert game.look_cursor_position.y == initial_y - 1

    def test_move_cursor_with_numpad_keys(self):
        """Test moving look mode cursor with numpad keys."""
        game = GameEngine(load_save=False)

        # Dismiss intro dialogue (new games show intro)
        if game.dialogue_state.is_active():
            game.dialogue_state.close()

        # Enter look mode
        game.look_mode = True
        initial_x = game.player.x
        initial_y = game.player.y
        game.look_cursor_position = Position(initial_x, initial_y)

        # Move right with numpad 6
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.KP_6,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event)
        assert game.look_cursor_position.x == initial_x + 1

    def test_cursor_bounds_checking(self):
        """Test that cursor stays within map bounds."""
        game = GameEngine(load_save=False)
        from game_config import GameConfig

        # Enter look mode at edge of map
        game.look_mode = True
        game.look_cursor_position = Position(0, 0)

        # Try to move left (should stay at 0)
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.LEFT,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event)
        assert game.look_cursor_position.x == 0

        # Try to move up (should stay at 0)
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.UP,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event)
        assert game.look_cursor_position.y == 0

        # Move to far edge
        game.look_cursor_position = Position(GameConfig.MAP_WIDTH - 1, GameConfig.MAP_HEIGHT - 1)

        # Try to move right (should stay at max)
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RIGHT,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event)
        assert game.look_cursor_position.x == GameConfig.MAP_WIDTH - 1

        # Try to move down (should stay at max)
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event)
        assert game.look_cursor_position.y == GameConfig.MAP_HEIGHT - 1


class TestEntityInspection:
    """Integration tests for entity inspection system."""

    def test_inspect_player(self):
        """Test inspecting the player."""
        game = GameEngine(load_save=False)

        player_pos = Position(game.player.x, game.player.y)
        entity_info = EntityInspector.get_entity_at_position(game, player_pos)

        assert entity_info['entity_type'] == 'player'
        assert 'Player' in entity_info['name']
        assert entity_info['description'] != ''
        assert 'CPU:' in entity_info['details']
        assert 'Heat:' in entity_info['details']

    def test_inspect_enemy(self):
        """Test inspecting an enemy."""
        game = GameEngine(load_save=False)

        # Add an enemy to the game
        if len(game.enemies) > 0:
            enemy = game.enemies[0]
            enemy_pos = Position(enemy.x, enemy.y)
            entity_info = EntityInspector.get_entity_at_position(game, enemy_pos)

            assert entity_info['entity_type'] == 'enemy'
            assert entity_info['name'] != ''
            # Description may be empty if not loaded from JSON yet, just check it exists
            assert 'description' in entity_info
            assert 'State:' in entity_info['details']
            assert 'CPU:' in entity_info['details']

    def test_inspect_wall(self):
        """Test inspecting a wall."""
        game = GameEngine(load_save=False)

        # Find a wall tile
        wall_pos = None
        for (x, y) in game.game_map.walls:
            wall_pos = Position(x, y)
            break

        if wall_pos:
            entity_info = EntityInspector.get_entity_at_position(game, wall_pos)

            assert entity_info['entity_type'] == 'wall'
            assert 'Barrier' in entity_info['name'] or 'Security' in entity_info['name']

    def test_inspect_floor(self):
        """Test inspecting empty floor."""
        game = GameEngine(load_save=False)

        # Find an empty floor tile (not wall, not entity)
        for x in range(game.game_map.width):
            for y in range(game.game_map.height):
                pos = Position(x, y)
                if (not game.game_map.is_wall(pos) and
                    not game.enemy_manager.get_enemy_at_position(pos) and
                    pos.x != game.player.x and pos.y != game.player.y):
                    entity_info = EntityInspector.get_entity_at_position(game, pos)

                    # Should return floor or shadow
                    assert entity_info['entity_type'] in ['floor', 'blind_spot']
                    assert entity_info['name'] != ''
                    return

    def test_inspect_code_hack(self):
        """Test inspecting a code hack."""
        game = GameEngine(load_save=False)

        # Add a code hack to the map
        test_pos = Position(10, 10)
        if not game.game_map.is_wall(test_pos):
            code_hack = CodeHack('crimson', 'restore_cpu', 'Crimson Code', 'Restores CPU', quantity=1)
            game.game_map.code_hacks[(test_pos.x, test_pos.y)] = code_hack

            entity_info = EntityInspector.get_entity_at_position(game, test_pos)

            assert entity_info['entity_type'] == 'code_hack'
            assert 'Code' in entity_info['name'] or 'Data' in entity_info['name']

    def test_inspect_exploit_pickup(self):
        """Test inspecting an exploit pickup."""
        game = GameEngine(load_save=False)

        # Add an exploit pickup to the map
        test_pos = Position(12, 12)
        if not game.game_map.is_wall(test_pos):
            exploit_def = list(GameData.EXPLOITS.values())[0]
            exploit_key = list(GameData.EXPLOITS.keys())[0]
            exploit_item = ExploitItem(exploit_key, exploit_def)
            game.game_map.exploit_pickups[(test_pos.x, test_pos.y)] = exploit_item

            entity_info = EntityInspector.get_entity_at_position(game, test_pos)

            assert entity_info['entity_type'] == 'exploit_pickup'
            assert entity_info['name'] != ''
            assert 'RAM:' in entity_info['details'] or 'Heat:' in entity_info['details']

    def test_inspect_cooling_node(self):
        """Test inspecting a cooling node."""
        game = GameEngine(load_save=False)

        # Find or add a cooling node
        if len(game.game_map.cooling_nodes) > 0:
            node_pos_tuple = list(game.game_map.cooling_nodes)[0]
            node_pos = Position(node_pos_tuple[0], node_pos_tuple[1])

            entity_info = EntityInspector.get_entity_at_position(game, node_pos)

            assert entity_info['entity_type'] == 'cooling_node'
            assert 'Cooling' in entity_info['name']

    def test_inspect_gateway(self):
        """Test inspecting the gateway."""
        game = GameEngine(load_save=False)

        if game.game_map.gateway:
            entity_info = EntityInspector.get_entity_at_position(game, game.game_map.gateway)

            assert entity_info['entity_type'] == 'gateway'
            assert 'Gateway' in entity_info['name']
            assert 'Level' in entity_info['details']


class TestLookModeWorkflow:
    """Integration tests for complete look mode workflows."""

    def test_complete_look_mode_workflow(self):
        """Test complete workflow: enter, move, inspect, exit."""
        game = GameEngine(load_save=False)

        # Dismiss intro dialogue (new games show intro)
        if game.dialogue_state.is_active():
            game.dialogue_state.close()

        # 1. Enter look mode
        event_l = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.L,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event_l)
        assert game.look_mode

        initial_pos = Position(game.look_cursor_position.x, game.look_cursor_position.y)

        # 2. Move cursor
        event_right = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RIGHT,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event_right)
        assert game.look_cursor_position.x == initial_pos.x + 1

        # 3. Inspect current position
        entity_info = EntityInspector.get_entity_at_position(game, game.look_cursor_position)
        assert entity_info is not None
        assert 'name' in entity_info
        assert 'description' in entity_info

        # 4. Exit look mode
        event_esc = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event_esc)
        assert not game.look_mode

    def test_look_mode_does_not_process_turns(self):
        """Test that looking around doesn't consume turns."""
        game = GameEngine(load_save=False)

        initial_turn = game.turn

        # Enter look mode and move cursor
        game.look_mode = True
        game.look_cursor_position = Position(game.player.x, game.player.y)

        # Move cursor multiple times
        for _ in range(5):
            event = tcod.event.KeyDown(
                scancode=0,
                sym=tcod.event.KeySym.RIGHT,
                mod=tcod.event.Modifier.NONE,
                repeat=False
            )
            game.input_handler.handle_keydown(event)

        # Verify turn counter hasn't changed
        assert game.turn == initial_turn

        # Exit look mode
        game.look_mode = False

    def test_look_mode_doesnt_interfere_with_dialogue(self):
        """Test that dialogue takes priority over look mode."""
        game = GameEngine(load_save=False)

        # Activate a dialogue
        from game_dialogue_system import create_death_dialogue
        game.dialogue_state.show(create_death_dialogue())

        # Try to enter look mode
        event_l = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.L,
            mod=tcod.event.Modifier.NONE,
            repeat=False
        )
        game.input_handler.handle_keydown(event_l)

        # Should still be in dialogue, not look mode
        assert game.dialogue_state.is_active()
        assert not game.look_mode

    def test_look_mode_camera_scrolling(self):
        """Test that camera follows cursor in look mode for map exploration."""
        from game_rendering_glyphs import GlyphsMapRenderer
        from game_config import GameConfig

        game = GameEngine(load_save=False)
        renderer = GlyphsMapRenderer(settings=game.settings)

        # Get viewport dimensions
        viewport_width = GameConfig.VIEWPORT_WIDTH(game.settings.graphics_mode)
        viewport_height = GameConfig.VIEWPORT_HEIGHT(game.settings.graphics_mode)

        # Check if camera can actually scroll (map must be larger than viewport)
        can_scroll_x = GameConfig.MAP_WIDTH > viewport_width
        can_scroll_y = GameConfig.MAP_HEIGHT > viewport_height

        # Position player in center of map
        game.player.position.x = 25
        game.player.position.y = 25

        # Enter look mode
        game.look_mode = True
        game.look_cursor_position = Position(game.player.x, game.player.y)

        # Initial camera should center on player/cursor
        initial_camera = renderer._calculate_camera_offset(game.player, game)

        # Calculate expected camera position (handles cases where viewport > map)
        if viewport_width >= GameConfig.MAP_WIDTH:
            expected_x = -(viewport_width - GameConfig.MAP_WIDTH) // 2
        else:
            expected_x = max(0, min(GameConfig.MAP_WIDTH - viewport_width,
                                   game.player.x - viewport_width // 2))

        if viewport_height >= GameConfig.MAP_HEIGHT:
            expected_y = -(viewport_height - GameConfig.MAP_HEIGHT) // 2
        else:
            expected_y = max(0, min(GameConfig.MAP_HEIGHT - viewport_height,
                                   game.player.y - viewport_height // 2))

        assert initial_camera.x == expected_x
        assert initial_camera.y == expected_y

        # Move cursor far away from player
        distance = viewport_width // 2 + 5
        game.look_cursor_position = Position(
            min(GameConfig.MAP_WIDTH - 1, game.player.x + distance),
            game.player.y
        )

        # Camera should follow cursor if scrolling is possible, otherwise stay at origin
        new_camera = renderer._calculate_camera_offset(game.player, game)

        if can_scroll_x:
            # If map is larger than viewport, camera should move to follow cursor
            assert new_camera.x != initial_camera.x, "Camera should scroll when cursor moves away from player"
        else:
            # If map fits entirely in viewport, camera stays centered (may be negative to center map)
            assert new_camera.x == expected_x, "Camera should stay centered when map fits in viewport"

        # Exit look mode
        game.look_mode = False

        # Camera should return to centering on player
        final_camera = renderer._calculate_camera_offset(game.player, game)
        assert final_camera == initial_camera, "Camera should return to player when exiting look mode"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
