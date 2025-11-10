#!/usr/bin/env python3
"""
Chaos Agent - Keyboard Fuzzing to Find Crashes

A true chaos agent that randomly presses ANY valid game keys with random modifiers
and hold durations. This is "monkey on a typewriter" testing - great for finding
edge cases, race conditions, and unexpected state transitions.

Safety: This agent runs in headless mode and only simulates game input through
the input handler. It cannot:
- Send OS-level keyboard events
- Execute shell commands
- Close the application window (no window in headless mode)
- Escape the Python process

What it DOES do:
- Press random valid game keys (movement, exploits, inventory, help, etc.)
- Hold keys for random durations (simulating key repeats)
- Use random modifiers (shift, ctrl, shift+ctrl)
- Try to break the game by finding unexpected input sequences
"""

import pytest
import random
import sys
import os
import tcod.event

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.test_agent import GameTestAgent


class ChaosAgent:
    """
    True chaos agent that fuzzes keyboard input to find crashes.

    Simulates a monkey randomly pressing keys on the keyboard, including:
    - All movement keys (WASD, arrows, numpad)
    - Exploit keys (1-5)
    - UI toggles (I, L, F, V, H, ?)
    - Wait/rest keys (Space, Period)
    - Escape key
    - Random modifiers (Shift, Ctrl, Shift+Ctrl)

    This is MUCH more aggressive than the drunk agent - it tries EVERYTHING.
    """

    # All valid game keys (safe to test)
    GAME_KEYS = [
        # Movement - WASD
        tcod.event.KeySym.W, tcod.event.KeySym.A, tcod.event.KeySym.S, tcod.event.KeySym.D,
        tcod.event.KeySym.Q, tcod.event.KeySym.E, tcod.event.KeySym.Z, tcod.event.KeySym.C,
        # Movement - Arrows
        tcod.event.KeySym.UP, tcod.event.KeySym.DOWN, tcod.event.KeySym.LEFT, tcod.event.KeySym.RIGHT,
        # Movement - Numpad
        tcod.event.KeySym.KP_8, tcod.event.KeySym.KP_2, tcod.event.KeySym.KP_4, tcod.event.KeySym.KP_6,
        tcod.event.KeySym.KP_7, tcod.event.KeySym.KP_9, tcod.event.KeySym.KP_1, tcod.event.KeySym.KP_3,
        tcod.event.KeySym.KP_5,  # Wait/center
        # Exploit keys
        tcod.event.KeySym.N1, tcod.event.KeySym.N2, tcod.event.KeySym.N3,
        tcod.event.KeySym.N4, tcod.event.KeySym.N5,
        # UI toggles
        tcod.event.KeySym.I,  # Inventory
        tcod.event.KeySym.L,  # Look mode
        tcod.event.KeySym.F,  # Lore/fragments
        tcod.event.KeySym.V,  # Achievements
        tcod.event.KeySym.SLASH,  # Help (with shift)
        # Wait/rest
        tcod.event.KeySym.SPACE, tcod.event.KeySym.PERIOD,
        # Escape (close menus)
        tcod.event.KeySym.ESCAPE,
        # Dialogue responses
        tcod.event.KeySym.Y, tcod.event.KeySym.N,
        # Random other keys that might do something
        tcod.event.KeySym.RETURN, tcod.event.KeySym.TAB,
        # Letters that might trigger hidden features
        tcod.event.KeySym.H, tcod.event.KeySym.M, tcod.event.KeySym.P,
        tcod.event.KeySym.G, tcod.event.KeySym.T, tcod.event.KeySym.R,
    ]

    # Modifiers to randomly apply
    MODIFIERS = [
        0,  # No modifier (80% chance)
        0,  # No modifier
        0,  # No modifier
        0,  # No modifier
        tcod.event.Modifier.SHIFT,  # Shift (10% chance)
        tcod.event.Modifier.CTRL,  # Ctrl (5% chance)
        tcod.event.Modifier.SHIFT | tcod.event.Modifier.CTRL,  # Shift+Ctrl (5% chance)
    ]

    def __init__(self, agent: GameTestAgent):
        self.agent = agent
        self.actions_taken = []
        self.key_presses = 0
        self.menu_toggles = 0
        self.exploits_used = 0

    def _simulate_keypress(self, key_sym: int, modifier: int = 0, hold_duration: int = 1):
        """
        Simulate a key press through the game's input handler.

        Args:
            key_sym: The tcod.event.KeySym to press
            modifier: Modifier flags (KMOD_SHIFT, KMOD_CTRL, etc.)
            hold_duration: How many times to repeat the key (simulating hold)

        Returns:
            True if game should continue, False if exited
        """
        # Create a fake KeyDown event
        from game_input import InputHandler

        for _ in range(hold_duration):
            # Create mock event with the key and modifier
            class MockKeyEvent:
                def __init__(self, sym, mod):
                    self.sym = sym
                    self.mod = mod

            event = MockKeyEvent(key_sym, modifier)

            # Check if game has an input handler
            if hasattr(self.agent.engine, 'input_handler'):
                # Use the actual input handler
                try:
                    result = self.agent.engine.input_handler.handle_keydown(event)
                    if not result:
                        return False  # Game wants to exit
                except Exception as e:
                    # Log but don't crash - we're trying to find bugs!
                    print(f"Key press caused exception: {e}")
                    raise  # Re-raise for test framework to catch

            # Game might be over
            if self.agent.engine.game_over:
                return False

        return True

    def run_chaos(self, max_actions: int = 200) -> dict:
        """
        Run chaotic keyboard fuzzing for N actions or until death/crash.

        Args:
            max_actions: Maximum number of key presses to attempt

        Returns:
            Statistics about the chaos session
        """
        stats = {
            'actions_taken': 0,
            'key_presses': 0,
            'unique_keys_pressed': set(),
            'modifiers_used': {
                'none': 0,
                'shift': 0,
                'ctrl': 0,
                'shift_ctrl': 0,
            },
            'crashed': False,
            'crash_reason': None,
            'final_state': None,
            'menus_toggled': 0,
        }

        try:
            for action in range(max_actions):
                if self.agent.engine.game_over:
                    break

                stats['actions_taken'] = action

                # Pick random key and modifier
                key_sym = random.choice(self.GAME_KEYS)
                modifier = random.choice(self.MODIFIERS)

                # Random hold duration (1-3 taps, weighted toward 1)
                hold_duration = random.choices([1, 2, 3], weights=[70, 20, 10])[0]

                # Track stats
                stats['unique_keys_pressed'].add(key_sym)
                stats['key_presses'] += hold_duration

                if modifier == 0:
                    stats['modifiers_used']['none'] += 1
                elif modifier == tcod.event.Modifier.SHIFT:
                    stats['modifiers_used']['shift'] += 1
                elif modifier == tcod.event.Modifier.CTRL:
                    stats['modifiers_used']['ctrl'] += 1
                else:
                    stats['modifiers_used']['shift_ctrl'] += 1

                # Track menu toggles (I, L, F, V, ESC)
                if key_sym in [tcod.event.KeySym.I, tcod.event.KeySym.L,
                              tcod.event.KeySym.F, tcod.event.KeySym.V,
                              tcod.event.KeySym.ESCAPE]:
                    stats['menus_toggled'] += 1

                # Simulate the key press
                should_continue = self._simulate_keypress(key_sym, modifier, hold_duration)
                if not should_continue:
                    break

                # Record action
                self.actions_taken.append({
                    'action': action,
                    'key': key_sym,
                    'modifier': modifier,
                    'hold': hold_duration,
                    'player_pos': (self.agent.player.x, self.agent.player.y),
                    'player_hp': self.agent.player.cpu,
                })

        except Exception as e:
            stats['crashed'] = True
            stats['crash_reason'] = str(e)
            stats['crash_type'] = type(e).__name__
            # Re-raise so test framework catches it
            raise
        finally:
            stats['final_state'] = self.agent.get_state()
            # Convert set to count for JSON serialization
            stats['unique_keys_count'] = len(stats['unique_keys_pressed'])
            del stats['unique_keys_pressed']  # Remove set (not JSON serializable)

        return stats


class TestChaosAgent:
    """Tests using true chaos/keyboard fuzzing agents."""

    def test_random_keyspam_200_actions(self):
        """Random key spam for 200 actions should not crash."""
        agent = GameTestAgent(seed=42)
        chaos = ChaosAgent(agent)

        stats = chaos.run_chaos(max_actions=200)

        # We don't care about success, just that it didn't crash
        assert not stats['crashed'], f"Game crashed: {stats['crash_reason']}"

        # Log interesting stats
        print(f"\n=== Chaos Agent Test Results ===")
        print(f"Completed {stats['actions_taken']} actions")
        print(f"Pressed {stats['key_presses']} keys total")
        print(f"Used {stats['unique_keys_count']} unique keys")
        print(f"Modifiers: {stats['modifiers_used']}")
        print(f"Menu toggles: {stats['menus_toggled']}")
        print(f"Final HP: {stats['final_state']['player_hp']}")
        print(f"Game Over: {stats['final_state']['game_over']}")

    def test_chaos_with_different_seeds(self):
        """Run chaos tests on multiple random seeds to find seed-specific bugs."""
        crashes = []

        for seed in [1, 42, 123, 456, 789]:
            try:
                agent = GameTestAgent(seed=seed)
                chaos = ChaosAgent(agent)
                stats = chaos.run_chaos(max_actions=100)

                if stats['crashed']:
                    crashes.append({
                        'seed': seed,
                        'reason': stats['crash_reason']
                    })
            except Exception as e:
                crashes.append({
                    'seed': seed,
                    'reason': str(e),
                    'type': type(e).__name__
                })

        # Report crashes
        if crashes:
            print(f"\n=== Crashes Found ===")
            for crash in crashes:
                print(f"Seed {crash['seed']}: {crash.get('type', 'Unknown')} - {crash['reason']}")

        # We expect NO crashes
        assert len(crashes) == 0, f"Found {len(crashes)} crashes across seeds"

    def test_long_chaos_session(self):
        """Run a very long chaos session (1000 actions) to find rare bugs."""
        agent = GameTestAgent(seed=999)
        chaos = ChaosAgent(agent)

        # This is an endurance test
        stats = chaos.run_chaos(max_actions=1000)

        assert not stats['crashed'], f"Long session crashed: {stats['crash_reason']}"

        print(f"\n=== Long Chaos Session ===")
        print(f"Completed {stats['actions_taken']}/1000 actions")
        print(f"Total key presses: {stats['key_presses']}")
        print(f"Unique keys used: {stats['unique_keys_count']}")
        print(f"Final state: HP={stats['final_state']['player_hp']}, Game Over={stats['final_state']['game_over']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s shows print output

