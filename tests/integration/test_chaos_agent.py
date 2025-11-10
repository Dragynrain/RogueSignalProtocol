#!/usr/bin/env python3
"""
Chaos Agent - Random Actions to Find Crashes

The dumbest agent that just randomly explores the state space.
Great for finding unexpected crashes, edge cases, and assertions.
"""

import pytest
import random
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.test_agent import GameTestAgent


class ChaosAgent:
    """
    Agent that makes completely random decisions.

    This is actually one of the BEST testing approaches because:
    - Finds edge cases humans wouldn't think of
    - No bias in test design
    - Explores the full state space randomly
    - Great for finding crashes and assertion failures
    """

    def __init__(self, agent: GameTestAgent):
        self.agent = agent
        self.actions_taken = []

    def run_chaos(self, max_turns: int = 100) -> dict:
        """
        Run random actions for N turns or until death/crash.

        Returns:
            Statistics about the chaos session
        """
        stats = {
            'turns_survived': 0,
            'moves_made': 0,
            'walls_hit': 0,
            'enemies_encountered': 0,
            'crashed': False,
            'crash_reason': None,
            'final_state': None
        }

        directions = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0),           (1, 0),
            (-1, 1),  (0, 1),  (1, 1)
        ]

        try:
            for turn in range(max_turns):
                if self.agent.engine.game_over:
                    break

                stats['turns_survived'] = turn

                # Random action: 80% move, 20% wait
                if random.random() < 0.8:
                    # Pick random direction
                    dx, dy = random.choice(directions)

                    old_pos = (self.agent.player.x, self.agent.player.y)
                    success = self.agent.move_player(dx, dy)
                    new_pos = (self.agent.player.x, self.agent.player.y)

                    if success:
                        stats['moves_made'] += 1
                    else:
                        stats['walls_hit'] += 1

                    # Check if we bumped an enemy
                    enemy = self.agent.get_enemy_at(new_pos[0], new_pos[1])
                    if enemy or old_pos != new_pos:
                        # Check if there WAS an enemy there
                        if old_pos != new_pos:
                            # We moved - check destination
                            enemy_at_dest = self.agent.get_enemy_at(new_pos[0], new_pos[1])
                            if enemy_at_dest:
                                stats['enemies_encountered'] += 1
                else:
                    # Wait
                    self.agent.wait(1)

                self.actions_taken.append({
                    'turn': turn,
                    'player_pos': (self.agent.player.x, self.agent.player.y),
                    'player_hp': self.agent.player.cpu,
                    'num_enemies': len(self.agent.enemies)
                })

        except Exception as e:
            stats['crashed'] = True
            stats['crash_reason'] = str(e)
            stats['crash_type'] = type(e).__name__
            # Re-raise so test framework catches it
            raise
        finally:
            stats['final_state'] = self.agent.get_state()

        return stats


class TestChaosAgent:
    """Tests using chaos/random agents."""

    def test_random_walk_100_turns(self):
        """Random walking for 100 turns should not crash."""
        agent = GameTestAgent(seed=42)
        chaos = ChaosAgent(agent)

        stats = chaos.run_chaos(max_turns=100)

        # We don't care about success, just that it didn't crash
        assert not stats['crashed'], f"Game crashed: {stats['crash_reason']}"

        # Log interesting stats
        print(f"\n=== Chaos Test Results ===")
        print(f"Survived {stats['turns_survived']} turns")
        print(f"Made {stats['moves_made']} successful moves")
        print(f"Hit {stats['walls_hit']} walls")
        print(f"Encountered {stats['enemies_encountered']} enemies")
        print(f"Final HP: {stats['final_state']['player_hp']}")
        print(f"Game Over: {stats['final_state']['game_over']}")

    def test_chaos_on_multiple_seeds(self):
        """Run chaos tests on multiple random seeds to find seed-specific bugs."""
        crashes = []

        for seed in [1, 42, 123, 456, 789]:
            try:
                agent = GameTestAgent(seed=seed)
                chaos = ChaosAgent(agent)
                stats = chaos.run_chaos(max_turns=50)

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
        """Run a very long random session (500 turns) to find rare bugs."""
        agent = GameTestAgent(seed=999)
        chaos = ChaosAgent(agent)

        # This is more of a stress test
        stats = chaos.run_chaos(max_turns=500)

        assert not stats['crashed'], f"Long session crashed: {stats['crash_reason']}"

        print(f"\n=== Long Chaos Session ===")
        print(f"Survived {stats['turns_survived']}/500 turns")
        print(f"Total moves: {stats['moves_made']}")
        print(f"Wall collisions: {stats['walls_hit']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s shows print output
