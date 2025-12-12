#!/usr/bin/env python3
"""
Gamepad Chaos Agent - Fuzz Testing for Gamepad Input

A chaos agent that randomly slams different buttons and analog sticks in random
combinations to uncover edge cases, race conditions, and crashes in the gamepad
input handling code.

Unlike the isolated handler tests, this drives the FULL game loop through
InputHandler.handle_controller_button() and InputHandler.handle_controller_axis(),
which triggers actual game state changes (movement, menu toggles, etc).

Tests scenarios that normal unit tests don't cover:
- Simultaneous button + stick input
- Rapid stick direction changes
- Both sticks at extreme positions simultaneously
- Button mashing during stick movement
- Edge cases around deadzone boundaries
- Real timing for auto-repeat mechanics

Includes behavioral assertions to verify:
- Player moves in expected direction when stick is pushed
- Game state stays consistent (no invalid positions, HP, etc.)
- Menu state toggles correctly
"""

import os
import random
import sys
import time

import pytest
import tcod.event
import tcod.sdl.joystick

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from game_config import GameConfig
from game_input import InputHandler
from tests.test_agent import GameTestAgent


class MockControllerButton:
    """Mock tcod.event.ControllerButton for testing."""

    def __init__(self, button: int, pressed: bool):
        self.button = button
        self.pressed = pressed
        self.type = "CONTROLLERBUTTONDOWN" if pressed else "CONTROLLERBUTTONUP"


class MockControllerAxis:
    """Mock tcod.event.ControllerAxis for testing."""

    def __init__(self, axis: int, value: int):
        self.axis = axis
        self.value = value
        self.type = "CONTROLLERAXISMOTION"


class GamepadChaosAgent:
    """
    Chaos agent that fuzzes gamepad input through the full input handler.

    Drives actual game state changes by calling InputHandler methods directly,
    just like the real game loop does.
    """

    # All gamepad buttons to test
    BUTTONS = [
        tcod.sdl.joystick.ControllerButton.A,
        tcod.sdl.joystick.ControllerButton.B,
        tcod.sdl.joystick.ControllerButton.X,
        tcod.sdl.joystick.ControllerButton.Y,
        tcod.sdl.joystick.ControllerButton.BACK,
        tcod.sdl.joystick.ControllerButton.START,
        tcod.sdl.joystick.ControllerButton.LEFTSHOULDER,
        tcod.sdl.joystick.ControllerButton.RIGHTSHOULDER,
        tcod.sdl.joystick.ControllerButton.DPAD_UP,
        tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
        tcod.sdl.joystick.ControllerButton.DPAD_LEFT,
        tcod.sdl.joystick.ControllerButton.DPAD_RIGHT,
        tcod.sdl.joystick.ControllerButton.LEFTSTICK,
        tcod.sdl.joystick.ControllerButton.RIGHTSTICK,
    ]

    # Interesting axis values to test (edge cases)
    INTERESTING_AXIS_VALUES = [
        0,  # Center
        -32768,  # Min
        32767,  # Max
        -16384,  # Half negative
        16384,  # Half positive
        -5000,  # Just past typical deadzone
        5000,  # Just past typical deadzone
        -3000,  # Right at typical deadzone edge
        3000,  # Right at typical deadzone edge
        -1000,  # Inside typical deadzone
        1000,  # Inside typical deadzone
        -32000,  # Near max
        32000,  # Near max
    ]

    def __init__(self, agent: GameTestAgent, seed: int | None = None):
        """
        Initialize gamepad chaos agent.

        Args:
            agent: GameTestAgent with initialized game engine
            seed: Random seed for reproducibility
        """
        self.agent = agent
        self.engine = agent.engine
        self.rng = random.Random(seed)

        # Create a real InputHandler connected to the game engine
        # This is what the actual game loop uses
        self.input_handler = InputHandler(self.engine, renderer=None, controllers=set())

        # Stats
        self.button_events = 0
        self.axis_events = 0
        self.actions_executed = 0
        self.menu_exits = 0
        self.exceptions = []
        self.state_violations = []  # Track behavioral violations

    def _validate_game_state(self) -> list[str]:
        """
        Check game state for consistency violations.

        Returns list of violation descriptions (empty if state is valid).
        """
        violations = []
        player = self.agent.player

        # Player position must be within map bounds
        if player.x < 0 or player.x >= GameConfig.MAP_WIDTH:
            violations.append(f"Player X out of bounds: {player.x}")
        if player.y < 0 or player.y >= GameConfig.MAP_HEIGHT:
            violations.append(f"Player Y out of bounds: {player.y}")

        # Player can't be inside a wall (unless game is over)
        if not self.engine.game_over:
            if (player.x, player.y) in self.engine.game_map.walls:
                violations.append(f"Player inside wall at ({player.x}, {player.y})")

        # HP consistency
        if player.cpu < 0:
            violations.append(f"Player HP negative: {player.cpu}")
        if player.cpu > player.max_cpu:
            violations.append(f"Player HP exceeds max: {player.cpu} > {player.max_cpu}")

        # If HP is 0, game should be over (or death pending)
        if player.cpu <= 0 and not self.engine.game_over:
            if not getattr(self.engine, "pending_death_dialogue", False):
                violations.append(f"Player dead (HP={player.cpu}) but game not over")

        # Turn counter should never be negative
        if self.engine.turn < 0:
            violations.append(f"Turn counter negative: {self.engine.turn}")

        return violations

    def _random_axis_value(self) -> int:
        """Generate random axis value, biased toward interesting values."""
        if self.rng.random() < 0.3:
            return self.rng.choice(self.INTERESTING_AXIS_VALUES)
        return self.rng.randint(-32768, 32767)

    def _random_trigger_value(self) -> int:
        """Generate random trigger value (0-32767)."""
        if self.rng.random() < 0.3:
            return self.rng.choice([0, 32767, 16384, 5000, 1000, 30000])
        return self.rng.randint(0, 32767)

    def _send_button(self, button: int, pressed: bool) -> bool | None:
        """Send button event through the real input handler."""
        event = MockControllerButton(button, pressed)
        try:
            result = self.input_handler.handle_controller_button(event)
            self.button_events += 1
            if result is True:
                self.actions_executed += 1
            elif result is False:
                self.menu_exits += 1
            return result
        except Exception as e:
            self.exceptions.append(
                {
                    "type": "button",
                    "button": button,
                    "pressed": pressed,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            raise

    def _send_axis(self, axis: int, value: int) -> bool | None:
        """Send axis event through the real input handler."""
        event = MockControllerAxis(axis, value)
        try:
            result = self.input_handler.handle_controller_axis(event)
            self.axis_events += 1
            if result is True:
                self.actions_executed += 1
            return result
        except Exception as e:
            self.exceptions.append(
                {
                    "type": "axis",
                    "axis": axis,
                    "value": value,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            raise

    def run_chaos(self, max_actions: int = 500, real_timing: bool = False) -> dict:
        """
        Run chaotic gamepad input for N actions.

        Args:
            max_actions: Maximum number of input events to generate
            real_timing: If True, use real delays to test auto-repeat (slower but more thorough)

        Returns:
            Statistics about the chaos session
        """
        stats = {
            "actions_attempted": 0,
            "button_events": 0,
            "axis_events": 0,
            "actions_executed": 0,
            "menu_exits": 0,
            "player_moved": False,
            "menus_opened": 0,
            "crashed": False,
            "crash_info": None,
            "final_player_pos": None,
            "final_player_hp": None,
            "game_over": False,
        }

        initial_pos = (self.agent.player.x, self.agent.player.y)
        CA = tcod.sdl.joystick.ControllerAxis

        try:
            for i in range(max_actions):
                if self.engine.game_over:
                    stats["game_over"] = True
                    break

                stats["actions_attempted"] = i + 1

                # Random action type: 35% button, 55% axis, 10% combo
                action_type = self.rng.random()

                if action_type < 0.35:
                    # Button press (and sometimes release)
                    button = self.rng.choice(self.BUTTONS)
                    self._send_button(button, True)
                    # 50% chance to release immediately
                    if self.rng.random() < 0.5:
                        self._send_button(button, False)

                elif action_type < 0.90:
                    # Axis event - pick stick or trigger
                    axis_choice = self.rng.random()
                    if axis_choice < 0.4:
                        # Left stick
                        self._send_axis(CA.LEFTX, self._random_axis_value())
                        self._send_axis(CA.LEFTY, self._random_axis_value())
                    elif axis_choice < 0.7:
                        # Right stick
                        self._send_axis(CA.RIGHTX, self._random_axis_value())
                        self._send_axis(CA.RIGHTY, self._random_axis_value())
                    else:
                        # Triggers
                        self._send_axis(CA.TRIGGERLEFT, self._random_trigger_value())
                        self._send_axis(CA.TRIGGERRIGHT, self._random_trigger_value())

                else:
                    # Combo: button + stick simultaneously
                    button = self.rng.choice(self.BUTTONS)
                    self._send_button(button, True)
                    self._send_axis(CA.LEFTX, self._random_axis_value())
                    self._send_axis(CA.LEFTY, self._random_axis_value())
                    self._send_button(button, False)

                # Real timing mode: add delays to trigger auto-repeat
                if real_timing and i % 10 == 0:
                    time.sleep(0.05)  # 50ms - enough for settling period

                # Track menu state changes
                if (
                    self.engine.show_help
                    or self.engine.show_inventory
                    or self.engine.show_achievements
                ):
                    stats["menus_opened"] += 1

                # Validate game state periodically (every 50 actions)
                if i % 50 == 0:
                    violations = self._validate_game_state()
                    if violations:
                        self.state_violations.extend(violations)

        except Exception as e:
            stats["crashed"] = True
            stats["crash_info"] = {
                "error": str(e),
                "error_type": type(e).__name__,
                "action_number": stats["actions_attempted"],
                "exceptions": self.exceptions,
            }
            raise
        finally:
            stats["button_events"] = self.button_events
            stats["axis_events"] = self.axis_events
            stats["actions_executed"] = self.actions_executed
            stats["menu_exits"] = self.menu_exits
            stats["final_player_pos"] = (self.agent.player.x, self.agent.player.y)
            stats["final_player_hp"] = self.agent.player.cpu
            stats["player_moved"] = stats["final_player_pos"] != initial_pos

            # Final state validation
            final_violations = self._validate_game_state()
            if final_violations:
                self.state_violations.extend(final_violations)
            stats["state_violations"] = self.state_violations

        return stats

    def run_directional_behavior_test(self) -> dict:
        """
        Test that stick input produces correct directional movement.

        Pushes stick in each cardinal direction and verifies player moves
        (or is blocked by wall/enemy) in the expected direction.
        """
        stats = {
            "directions_tested": 0,
            "correct_moves": 0,
            "blocked_moves": 0,  # Blocked by wall/enemy (valid)
            "wrong_moves": 0,  # Moved in wrong direction (bug!)
            "no_moves": 0,  # Didn't move when expected
            "violations": [],
        }

        CA = tcod.sdl.joystick.ControllerAxis

        # Test each cardinal direction
        directions = [
            ("north", 0, -25000, 0, -1),  # (name, x_axis, y_axis, expected_dx, expected_dy)
            ("south", 0, 25000, 0, 1),
            ("west", -25000, 0, -1, 0),
            ("east", 25000, 0, 1, 0),
        ]

        for name, axis_x, axis_y, expected_dx, expected_dy in directions:
            if self.engine.game_over:
                break

            stats["directions_tested"] += 1

            # Record position before
            old_x, old_y = self.agent.player.x, self.agent.player.y

            # Push stick in direction - need to send multiple events like real game loop
            # The settling period (30ms) requires sustained input before movement triggers
            start = time.time()
            while time.time() - start < 0.1:  # 100ms of sustained input
                self._send_axis(CA.LEFTX, axis_x)
                self._send_axis(CA.LEFTY, axis_y)
                time.sleep(0.01)  # 10ms between polls (like real 60fps game loop)

            # Check position after
            new_x, new_y = self.agent.player.x, self.agent.player.y
            actual_dx = new_x - old_x
            actual_dy = new_y - old_y

            # Release stick
            self._send_axis(CA.LEFTX, 0)
            self._send_axis(CA.LEFTY, 0)
            time.sleep(0.01)

            # Evaluate movement
            if actual_dx == expected_dx and actual_dy == expected_dy:
                stats["correct_moves"] += 1
            elif actual_dx == 0 and actual_dy == 0:
                # Didn't move - check if blocked
                target_x = old_x + expected_dx
                target_y = old_y + expected_dy
                if (target_x, target_y) in self.engine.game_map.walls:
                    stats["blocked_moves"] += 1  # Valid - wall blocked
                elif self.agent.get_enemy_at(target_x, target_y):
                    stats["blocked_moves"] += 1  # Valid - enemy blocked (bump attack)
                else:
                    stats["no_moves"] += 1
                    stats["violations"].append(
                        f"{name}: Expected move ({expected_dx},{expected_dy}) but didn't move"
                    )
            else:
                # Moved, but wrong direction
                stats["wrong_moves"] += 1
                stats["violations"].append(
                    f"{name}: Expected ({expected_dx},{expected_dy}) but got ({actual_dx},{actual_dy})"
                )

        return stats

    def run_stick_stress(self, iterations: int = 200) -> dict:
        """
        Stress test analog stick handling with rapid direction changes.

        This focuses on the analog stick state machine - settling periods,
        direction locking, deadzone crossings.
        """
        stats = {
            "iterations": 0,
            "direction_changes": 0,
            "deadzone_crossings": 0,
            "movements_triggered": 0,
            "crashed": False,
        }

        CA = tcod.sdl.joystick.ControllerAxis
        initial_pos = (self.agent.player.x, self.agent.player.y)

        try:
            for i in range(iterations):
                if self.engine.game_over:
                    break

                stats["iterations"] = i + 1

                test_type = i % 5

                if test_type == 0:
                    # Full-circle stick rotation (8 cardinal + diagonal directions)
                    import math

                    for angle in range(0, 360, 45):
                        x = int(32767 * math.cos(math.radians(angle)))
                        y = int(32767 * math.sin(math.radians(angle)))
                        self._send_axis(CA.LEFTX, x)
                        self._send_axis(CA.LEFTY, y)
                        stats["direction_changes"] += 1
                    # Release stick
                    self._send_axis(CA.LEFTX, 0)
                    self._send_axis(CA.LEFTY, 0)
                    # Small delay for settling
                    time.sleep(0.035)

                elif test_type == 1:
                    # Deadzone in-out-in transitions
                    # Inside deadzone
                    self._send_axis(CA.LEFTX, 1000)
                    self._send_axis(CA.LEFTY, 1000)
                    # Jump outside deadzone
                    self._send_axis(CA.LEFTX, 20000)
                    self._send_axis(CA.LEFTY, 20000)
                    stats["deadzone_crossings"] += 1
                    time.sleep(0.035)  # Wait for settling
                    # Back inside deadzone
                    self._send_axis(CA.LEFTX, 0)
                    self._send_axis(CA.LEFTY, 0)
                    stats["deadzone_crossings"] += 1

                elif test_type == 2:
                    # Instant opposite direction snap
                    self._send_axis(CA.LEFTX, -32768)
                    self._send_axis(CA.LEFTY, 0)
                    time.sleep(0.035)
                    # Snap to opposite
                    self._send_axis(CA.LEFTX, 32767)
                    stats["direction_changes"] += 1
                    time.sleep(0.035)
                    # Release
                    self._send_axis(CA.LEFTX, 0)

                elif test_type == 3:
                    # Both sticks at max, opposite directions
                    self._send_axis(CA.LEFTX, -32768)
                    self._send_axis(CA.LEFTY, -32768)
                    self._send_axis(CA.RIGHTX, 32767)
                    self._send_axis(CA.RIGHTY, 32767)
                    time.sleep(0.035)
                    # Release both
                    self._send_axis(CA.LEFTX, 0)
                    self._send_axis(CA.LEFTY, 0)
                    self._send_axis(CA.RIGHTX, 0)
                    self._send_axis(CA.RIGHTY, 0)

                else:
                    # Hold direction and wait for auto-repeat
                    self._send_axis(CA.LEFTX, 25000)
                    self._send_axis(CA.LEFTY, 0)
                    # Wait long enough for initial delay + one repeat
                    time.sleep(0.4)
                    self._send_axis(CA.LEFTX, 0)

                # Check if player moved
                current_pos = (self.agent.player.x, self.agent.player.y)
                if current_pos != initial_pos:
                    stats["movements_triggered"] += 1
                    initial_pos = current_pos

        except Exception as e:
            stats["crashed"] = True
            stats["crash_info"] = {"error": str(e), "error_type": type(e).__name__}
            raise

        return stats

    def run_button_mash(self, duration_seconds: float = 2.0) -> dict:
        """
        Rapid button mashing test - simulates aggressive menu navigation.

        Mashes buttons as fast as possible for a fixed duration.
        """
        stats = {
            "total_presses": 0,
            "duration": duration_seconds,
            "presses_per_second": 0,
            "crashed": False,
        }

        start_time = time.time()
        try:
            while time.time() - start_time < duration_seconds:
                if self.engine.game_over:
                    break

                # Mash a random button
                button = self.rng.choice(self.BUTTONS)
                self._send_button(button, True)
                self._send_button(button, False)
                stats["total_presses"] += 1

            stats["presses_per_second"] = stats["total_presses"] / duration_seconds

        except Exception as e:
            stats["crashed"] = True
            stats["crash_info"] = {"error": str(e), "error_type": type(e).__name__}
            raise

        return stats

    def run_mixed_input_chaos(self, iterations: int = 100) -> dict:
        """
        Test rapid switching between D-pad and analog stick.

        This can reveal conflicts in the input state machine.
        """
        stats = {
            "iterations": 0,
            "dpad_inputs": 0,
            "analog_inputs": 0,
            "crashed": False,
        }

        CA = tcod.sdl.joystick.ControllerAxis
        dpad_buttons = [
            tcod.sdl.joystick.ControllerButton.DPAD_UP,
            tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
            tcod.sdl.joystick.ControllerButton.DPAD_LEFT,
            tcod.sdl.joystick.ControllerButton.DPAD_RIGHT,
        ]

        try:
            for i in range(iterations):
                if self.engine.game_over:
                    break

                stats["iterations"] = i + 1

                # Alternate between D-pad and analog
                if i % 2 == 0:
                    # D-pad input
                    button = self.rng.choice(dpad_buttons)
                    self._send_button(button, True)
                    self._send_button(button, False)
                    stats["dpad_inputs"] += 1
                else:
                    # Analog stick input
                    self._send_axis(CA.LEFTX, self.rng.choice([-25000, 25000]))
                    self._send_axis(CA.LEFTY, self.rng.choice([-25000, 25000]))
                    time.sleep(0.035)
                    self._send_axis(CA.LEFTX, 0)
                    self._send_axis(CA.LEFTY, 0)
                    stats["analog_inputs"] += 1

        except Exception as e:
            stats["crashed"] = True
            stats["crash_info"] = {"error": str(e), "error_type": type(e).__name__}
            raise

        return stats


class TestGamepadChaosAgent:
    """Tests using gamepad chaos/fuzzing agent."""

    def test_random_gamepad_chaos_500_actions(self):
        """Random gamepad input for 500 actions should not crash or corrupt state."""
        agent = GameTestAgent(seed=42)
        chaos = GamepadChaosAgent(agent, seed=42)

        stats = chaos.run_chaos(max_actions=500)

        assert not stats["crashed"], f"Game crashed: {stats.get('crash_info')}"
        assert not stats["state_violations"], f"State violations: {stats['state_violations']}"

        print("\n=== Gamepad Chaos Results ===")
        print(f"Actions attempted: {stats['actions_attempted']}")
        print(f"Button events: {stats['button_events']}")
        print(f"Axis events: {stats['axis_events']}")
        print(f"Actions executed: {stats['actions_executed']}")
        print(f"Player moved: {stats['player_moved']}")
        print(f"Final position: {stats['final_player_pos']}")
        print(f"Final HP: {stats['final_player_hp']}")
        print(f"Game over: {stats['game_over']}")

    def test_chaos_with_real_timing(self):
        """Chaos test with real timing delays to test auto-repeat."""
        agent = GameTestAgent(seed=123)
        chaos = GamepadChaosAgent(agent, seed=123)

        stats = chaos.run_chaos(max_actions=100, real_timing=True)

        assert not stats["crashed"], f"Game crashed: {stats.get('crash_info')}"
        assert not stats["state_violations"], f"State violations: {stats['state_violations']}"
        # With real timing, we should see actual player movement
        print(f"\nReal timing test - Player moved: {stats['player_moved']}")

    def test_directional_movement_behavior(self):
        """Verify stick input produces correct directional movement."""
        agent = GameTestAgent(seed=42)
        chaos = GamepadChaosAgent(agent, seed=42)

        stats = chaos.run_directional_behavior_test()

        # Should have no wrong-direction moves
        assert stats["wrong_moves"] == 0, f"Wrong direction moves: {stats['violations']}"

        # Log results
        print("\n=== Directional Behavior Test ===")
        print(f"Directions tested: {stats['directions_tested']}")
        print(f"Correct moves: {stats['correct_moves']}")
        print(f"Blocked (valid): {stats['blocked_moves']}")
        print(f"No movement (suspicious): {stats['no_moves']}")
        print(f"Wrong direction (BUG): {stats['wrong_moves']}")

    def test_multiple_seeds(self):
        """Run chaos on multiple seeds to find seed-specific bugs."""
        crashes = []
        violations = []

        for seed in [1, 42, 123, 456, 789, 999, 1337]:
            try:
                agent = GameTestAgent(seed=seed)
                chaos = GamepadChaosAgent(agent, seed=seed)
                stats = chaos.run_chaos(max_actions=200)

                if stats["crashed"]:
                    crashes.append({"seed": seed, "info": stats["crash_info"]})
                if stats.get("state_violations"):
                    violations.append({"seed": seed, "violations": stats["state_violations"]})
            except Exception as e:
                crashes.append(
                    {
                        "seed": seed,
                        "info": {"error": str(e), "error_type": type(e).__name__},
                    }
                )

        if crashes:
            print("\n=== Crashes Found ===")
            for crash in crashes:
                print(f"Seed {crash['seed']}: {crash['info']}")

        if violations:
            print("\n=== State Violations Found ===")
            for v in violations:
                print(f"Seed {v['seed']}: {v['violations']}")

        assert len(crashes) == 0, f"Found {len(crashes)} crashes across seeds"
        assert len(violations) == 0, f"Found {len(violations)} seeds with state violations"

    def test_stick_stress(self):
        """Stress test analog stick with rapid direction changes."""
        agent = GameTestAgent(seed=42)
        chaos = GamepadChaosAgent(agent, seed=42)

        stats = chaos.run_stick_stress(iterations=50)

        assert not stats["crashed"], f"Stick stress crashed: {stats.get('crash_info')}"

        print("\n=== Stick Stress Results ===")
        print(f"Iterations: {stats['iterations']}")
        print(f"Direction changes: {stats['direction_changes']}")
        print(f"Deadzone crossings: {stats['deadzone_crossings']}")
        print(f"Movements triggered: {stats['movements_triggered']}")

    def test_button_mash(self):
        """Rapid button mashing should not crash."""
        agent = GameTestAgent(seed=42)
        chaos = GamepadChaosAgent(agent, seed=42)

        stats = chaos.run_button_mash(duration_seconds=1.0)

        assert not stats["crashed"], f"Button mash crashed: {stats.get('crash_info')}"

        print("\n=== Button Mash Results ===")
        print(f"Total presses: {stats['total_presses']}")
        print(f"Presses/second: {stats['presses_per_second']:.1f}")

    def test_mixed_dpad_analog(self):
        """Rapid D-pad/analog switching should not crash."""
        agent = GameTestAgent(seed=42)
        chaos = GamepadChaosAgent(agent, seed=42)

        stats = chaos.run_mixed_input_chaos(iterations=100)

        assert not stats["crashed"], f"Mixed input crashed: {stats.get('crash_info')}"

        print("\n=== Mixed Input Results ===")
        print(f"Iterations: {stats['iterations']}")
        print(f"D-pad inputs: {stats['dpad_inputs']}")
        print(f"Analog inputs: {stats['analog_inputs']}")

    def test_long_chaos_session(self):
        """Extended chaos session (2000 actions)."""
        agent = GameTestAgent(seed=999)
        chaos = GamepadChaosAgent(agent, seed=999)

        stats = chaos.run_chaos(max_actions=2000)

        assert not stats["crashed"], f"Long session crashed: {stats.get('crash_info')}"

        print("\n=== Long Chaos Session ===")
        print(f"Actions: {stats['actions_attempted']}")
        print(f"Total inputs: {stats['button_events'] + stats['axis_events']}")
        print(f"Player moved: {stats['player_moved']}")
        print(f"Game over: {stats['game_over']}")

    def test_extreme_axis_values(self):
        """Test only extreme axis values (-32768, 0, 32767)."""
        agent = GameTestAgent(seed=42)
        chaos = GamepadChaosAgent(agent, seed=42)

        # Override to only use extremes
        chaos._random_axis_value = lambda: chaos.rng.choice([-32768, 0, 32767])

        stats = chaos.run_chaos(max_actions=300)

        assert not stats["crashed"], f"Extreme values crashed: {stats.get('crash_info')}"

    def test_deadzone_boundary_values(self):
        """Focus on deadzone boundary values."""
        agent = GameTestAgent(seed=42)
        chaos = GamepadChaosAgent(agent, seed=42)

        # Values clustered around 15% deadzone (~4915 for 32767 max)
        boundary_values = [
            0,
            1000,
            2000,
            3000,
            4000,
            4500,
            4900,
            5000,
            5100,
            5500,
            6000,
            8000,
            -1000,
            -2000,
            -3000,
            -4000,
            -4500,
            -4900,
            -5000,
            -5100,
            -5500,
            -6000,
            -8000,
        ]
        chaos._random_axis_value = lambda: chaos.rng.choice(boundary_values)

        stats = chaos.run_chaos(max_actions=300)

        assert not stats["crashed"], f"Deadzone boundary crashed: {stats.get('crash_info')}"

    def test_swap_sticks_chaos(self):
        """Test chaos with swap_sticks enabled - uses RIGHT stick for movement."""
        agent = GameTestAgent(seed=42)

        # Enable swap_sticks in settings
        agent.engine.settings.gamepad_swap_sticks = True

        chaos = GamepadChaosAgent(agent, seed=42)

        # Sync the setting to the gamepad handler
        chaos.input_handler.gamepad_handler.sync_settings_to_analog_handler()

        stats = chaos.run_chaos(max_actions=300)

        assert not stats["crashed"], f"Swap sticks chaos crashed: {stats.get('crash_info')}"
        assert not stats["state_violations"], f"State violations: {stats['state_violations']}"

        print("\n=== Swap Sticks Chaos Results ===")
        print(f"Actions: {stats['actions_attempted']}")
        print(f"Player moved: {stats['player_moved']}")

    def test_swap_sticks_directional(self):
        """Verify RIGHT stick moves player when swap_sticks is enabled."""
        agent = GameTestAgent(seed=42)

        # Enable swap_sticks
        agent.engine.settings.gamepad_swap_sticks = True

        chaos = GamepadChaosAgent(agent, seed=42)
        chaos.input_handler.gamepad_handler.sync_settings_to_analog_handler()

        CA = tcod.sdl.joystick.ControllerAxis

        # Record initial position
        old_x, old_y = agent.player.x, agent.player.y

        # Push RIGHT stick (should move player when swap_sticks=True)
        start = time.time()
        while time.time() - start < 0.1:
            chaos._send_axis(CA.RIGHTX, 25000)  # Push right
            chaos._send_axis(CA.RIGHTY, 0)
            time.sleep(0.01)

        new_x, new_y = agent.player.x, agent.player.y

        # Release
        chaos._send_axis(CA.RIGHTX, 0)
        chaos._send_axis(CA.RIGHTY, 0)

        # Player should have moved east (or been blocked)
        moved = (new_x != old_x) or (new_y != old_y)
        target_blocked = (old_x + 1, old_y) in agent.engine.game_map.walls

        assert (
            moved or target_blocked
        ), f"RIGHT stick with swap_sticks=True didn't move player: ({old_x},{old_y}) -> ({new_x},{new_y})"

        print(f"\nSwap sticks directional: moved={moved}, blocked={target_blocked}")

    def test_dialogue_chaos(self):
        """Test gamepad input during active dialogue."""
        agent = GameTestAgent(seed=42)
        chaos = GamepadChaosAgent(agent, seed=42)

        # Create and show a test dialogue
        import tcod.event

        from game_dialogue_system import DialogueBox

        test_dialogue = DialogueBox(
            title="TEST DIALOGUE",
            message="This is a test dialogue for chaos testing.",
            options=["[Y] Yes", "[N] No"],
            valid_keys=[tcod.event.KeySym.Y, tcod.event.KeySym.N],
            title_color=(255, 255, 255),
            message_color=(200, 200, 200),
            border_color=(100, 100, 100),
            bg_color=(20, 20, 40),
            format_data={},
            priority=5,
            user_pref_key=None,
        )

        stats = {
            "dialogue_inputs": 0,
            "dialogue_closed": False,
            "crashed": False,
        }

        try:
            # Show dialogue
            agent.engine.dialogue_state.show(test_dialogue)
            assert agent.engine.dialogue_state.is_active(), "Dialogue should be active"

            # Spam gamepad buttons while dialogue is active
            for _ in range(50):
                button = chaos.rng.choice(chaos.BUTTONS)
                chaos._send_button(button, True)
                chaos._send_button(button, False)
                stats["dialogue_inputs"] += 1

                # Check if dialogue was closed
                if not agent.engine.dialogue_state.is_active():
                    stats["dialogue_closed"] = True
                    break

            # Also test axis events during dialogue
            CA = tcod.sdl.joystick.ControllerAxis
            for _ in range(20):
                chaos._send_axis(CA.LEFTX, chaos._random_axis_value())
                chaos._send_axis(CA.LEFTY, chaos._random_axis_value())

        except Exception as e:
            stats["crashed"] = True
            stats["error"] = str(e)
            raise

        assert not stats["crashed"], f"Dialogue chaos crashed: {stats.get('error')}"

        print("\n=== Dialogue Chaos Results ===")
        print(f"Inputs during dialogue: {stats['dialogue_inputs']}")
        print(f"Dialogue closed by input: {stats['dialogue_closed']}")

    def test_look_mode_transitions(self):
        """Test entering/exiting look mode with gamepad while moving."""
        agent = GameTestAgent(seed=42)
        chaos = GamepadChaosAgent(agent, seed=42)

        CA = tcod.sdl.joystick.ControllerAxis

        stats = {
            "transitions": 0,
            "look_mode_entered": 0,
            "look_mode_exited": 0,
            "crashed": False,
        }

        try:
            for i in range(30):
                if agent.engine.game_over:
                    break

                # Simulate gameplay with look mode toggling
                if i % 3 == 0:
                    # Enter look mode via right stick (auto-look)
                    chaos._send_axis(CA.RIGHTX, 25000)
                    chaos._send_axis(CA.RIGHTY, 25000)
                    time.sleep(0.02)

                    if agent.engine.look_mode:
                        stats["look_mode_entered"] += 1

                    # Move cursor around in look mode
                    for _ in range(5):
                        chaos._send_axis(CA.RIGHTX, chaos._random_axis_value())
                        chaos._send_axis(CA.RIGHTY, chaos._random_axis_value())
                        time.sleep(0.01)

                    # Exit look mode (B button or ESC equivalent)
                    chaos._send_button(tcod.sdl.joystick.ControllerButton.B, True)
                    chaos._send_button(tcod.sdl.joystick.ControllerButton.B, False)

                    if not agent.engine.look_mode:
                        stats["look_mode_exited"] += 1

                    stats["transitions"] += 1

                else:
                    # Normal movement
                    chaos._send_axis(CA.LEFTX, chaos._random_axis_value())
                    chaos._send_axis(CA.LEFTY, chaos._random_axis_value())
                    time.sleep(0.02)

                # Release sticks
                chaos._send_axis(CA.LEFTX, 0)
                chaos._send_axis(CA.LEFTY, 0)
                chaos._send_axis(CA.RIGHTX, 0)
                chaos._send_axis(CA.RIGHTY, 0)

        except Exception as e:
            stats["crashed"] = True
            stats["error"] = str(e)
            raise

        # Validate final state
        violations = chaos._validate_game_state()
        assert not violations, f"State violations after look mode: {violations}"
        assert not stats["crashed"], f"Look mode transitions crashed: {stats.get('error')}"

        print("\n=== Look Mode Transition Results ===")
        print(f"Transition cycles: {stats['transitions']}")
        print(f"Look mode entered: {stats['look_mode_entered']}")
        print(f"Look mode exited: {stats['look_mode_exited']}")

    def test_targeting_mode_chaos(self):
        """Test targeting mode with chaotic gamepad input."""
        agent = GameTestAgent(seed=42)
        chaos = GamepadChaosAgent(agent, seed=42)

        CA = tcod.sdl.joystick.ControllerAxis

        stats = {
            "targeting_attempts": 0,
            "crashed": False,
        }

        try:
            # Try to trigger targeting mode (typically via exploit keys/triggers)
            for i in range(20):
                if agent.engine.game_over:
                    break

                # Press trigger (might activate targeting for some exploits)
                chaos._send_axis(CA.TRIGGERRIGHT, 30000)
                time.sleep(0.01)
                chaos._send_axis(CA.TRIGGERRIGHT, 0)

                # If in targeting mode, move cursor chaotically
                if agent.engine.targeting_mode:
                    stats["targeting_attempts"] += 1
                    for _ in range(10):
                        chaos._send_axis(CA.RIGHTX, chaos._random_axis_value())
                        chaos._send_axis(CA.RIGHTY, chaos._random_axis_value())
                        time.sleep(0.01)

                    # Confirm or cancel randomly
                    if chaos.rng.random() < 0.5:
                        chaos._send_button(tcod.sdl.joystick.ControllerButton.A, True)
                        chaos._send_button(tcod.sdl.joystick.ControllerButton.A, False)
                    else:
                        chaos._send_button(tcod.sdl.joystick.ControllerButton.B, True)
                        chaos._send_button(tcod.sdl.joystick.ControllerButton.B, False)

                # Regular movement between attempts
                chaos._send_axis(CA.LEFTX, chaos._random_axis_value())
                chaos._send_axis(CA.LEFTY, chaos._random_axis_value())
                time.sleep(0.02)
                chaos._send_axis(CA.LEFTX, 0)
                chaos._send_axis(CA.LEFTY, 0)

        except Exception as e:
            stats["crashed"] = True
            stats["error"] = str(e)
            raise

        # Validate final state
        violations = chaos._validate_game_state()
        assert not violations, f"State violations after targeting: {violations}"
        assert not stats["crashed"], f"Targeting chaos crashed: {stats.get('error')}"

        print("\n=== Targeting Mode Chaos Results ===")
        print(f"Targeting mode attempts: {stats['targeting_attempts']}")

    def test_menu_state_chaos(self):
        """Test gamepad input while toggling various menu states."""
        agent = GameTestAgent(seed=42)
        chaos = GamepadChaosAgent(agent, seed=42)

        CA = tcod.sdl.joystick.ControllerAxis

        stats = {
            "menu_toggles": 0,
            "help_opened": 0,
            "inventory_opened": 0,
            "achievements_opened": 0,
            "crashed": False,
        }

        try:
            for i in range(40):
                if agent.engine.game_over:
                    break

                # Toggle different menus
                menu_type = i % 4

                if menu_type == 0:
                    # Toggle help (typically SELECT/BACK button)
                    agent.engine.show_help = not agent.engine.show_help
                    if agent.engine.show_help:
                        stats["help_opened"] += 1

                elif menu_type == 1:
                    # Toggle inventory
                    agent.engine.show_inventory = not agent.engine.show_inventory
                    if agent.engine.show_inventory:
                        stats["inventory_opened"] += 1

                elif menu_type == 2:
                    # Toggle achievements
                    agent.engine.show_achievements = not agent.engine.show_achievements
                    if agent.engine.show_achievements:
                        stats["achievements_opened"] += 1

                # Send gamepad input in whatever state we're in
                for _ in range(5):
                    # Random button
                    button = chaos.rng.choice(chaos.BUTTONS)
                    chaos._send_button(button, True)
                    chaos._send_button(button, False)

                    # Random stick movement
                    chaos._send_axis(CA.LEFTX, chaos._random_axis_value())
                    chaos._send_axis(CA.LEFTY, chaos._random_axis_value())

                stats["menu_toggles"] += 1

                # Close menus before next iteration
                agent.engine.show_help = False
                agent.engine.show_inventory = False
                agent.engine.show_achievements = False

        except Exception as e:
            stats["crashed"] = True
            stats["error"] = str(e)
            raise

        # Validate final state
        violations = chaos._validate_game_state()
        assert not violations, f"State violations after menu chaos: {violations}"
        assert not stats["crashed"], f"Menu state chaos crashed: {stats.get('error')}"

        print("\n=== Menu State Chaos Results ===")
        print(f"Menu toggles: {stats['menu_toggles']}")
        print(f"Help opened: {stats['help_opened']}")
        print(f"Inventory opened: {stats['inventory_opened']}")
        print(f"Achievements opened: {stats['achievements_opened']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
