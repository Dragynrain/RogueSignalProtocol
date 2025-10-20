#!/usr/bin/env python3
"""
Full level generation analysis including coordinator placement.
Actually counts code hacks, exploits, and enemies after full generation.
"""

import sys
import logging
from typing import Dict, List
import random
import os

# Suppress pygame message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

# Set up logging to capture warnings
class WarningCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.warnings = []
        self.setLevel(logging.WARNING)

    def emit(self, record):
        if record.levelno == logging.WARNING:
            self.warnings.append(record.getMessage())

# Import game modules
from game_config import GameConfig
from game_map import GameMap
from game_level import LevelGenerator
from game_entities import Position
from game_level_coordinator import GameLevelCoordinator
from game_audio import SoundManager
from game_enemies import EnemyManager
from game_state import GameStateManager, MessageLog

def analyze_strategy_full(strategy_name: str, iterations: int = 100) -> Dict:
    """Analyze with FULL level generation including coordinator."""

    results = {
        'strategy': strategy_name,
        'iterations': iterations,
        'warnings': 0,
        'distances': [],
        'code_hacks': [],
        'exploit_pickups': [],
        'story_fragments': [],
        'permanent_upgrades': [],
        'enemies': [],
        'warning_messages': []
    }

    # Get original weights
    import game_config
    config_data = game_config.GameConfig._config_data
    original_weights = config_data['room_generation']['gateway_strategy_weights'].copy()

    # Force this strategy
    forced_weights = {k: 0.0 for k in original_weights.keys()}
    forced_weights[strategy_name] = 1.0
    config_data['room_generation']['gateway_strategy_weights'] = forced_weights

    try:
        for i in range(iterations):
            # Create minimal engine components
            game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
            message_log = MessageLog()
            sound_manager = SoundManager()
            enemy_manager = EnemyManager(game_map, message_log)
            game_state = GameStateManager()

            # Create minimal engine mock
            class MinimalEngine:
                def __init__(self):
                    self.game_map = game_map
                    self.message_log = message_log
                    self.sound_manager = sound_manager
                    self.enemy_manager = enemy_manager
                    self.game_state = game_state
                    self.level = 1
                    self.admin_spawned = False
                    self.game_over = False
                    self.level_generator = LevelGenerator(game_map)
                    self.code_hack_effects = {'dummy': True}  # Mock - coordinator needs non-empty

                    class MinimalPlayer:
                        def __init__(self):
                            self.x = 5
                            self.y = 5
                            self.trace_level = 0
                            self.cpu = 100
                            self.max_cpu = 100
                            self.heat = 0

                    self.player = MinimalPlayer()

                def auto_save(self):
                    pass  # Mock auto-save

            engine = MinimalEngine()
            coordinator = GameLevelCoordinator(engine)

            # Set up warning capture
            warning_capture = WarningCapture()
            logger = logging.getLogger()
            logger.addHandler(warning_capture)

            try:
                # Generate FULL level with coordinator
                seed = random.randint(1, 1000000)
                engine.game_state.dungeon_seed = seed
                coordinator.generate_procedural_level()

                # Calculate distance
                spawn = Position(5, 5)
                if game_map.gateway:
                    distance = spawn.distance_to(game_map.gateway)
                    results['distances'].append(distance)

                # Count items (NOW ACTUALLY PLACED!)
                results['code_hacks'].append(len(game_map.code_hacks))
                results['exploit_pickups'].append(len(game_map.exploit_pickups))
                results['story_fragments'].append(len(game_map.story_fragments))
                results['permanent_upgrades'].append(len(game_map.permanent_upgrades))

                # Count enemies (NOW ACTUALLY PLACED!)
                results['enemies'].append(len(enemy_manager.enemies))

                # Check for warnings
                if warning_capture.warnings:
                    results['warnings'] += 1
                    if not results['warning_messages']:
                        results['warning_messages'] = warning_capture.warnings[:1]

            except Exception as e:
                print(f"Error in {strategy_name} iteration {i}: {e}")
                import traceback
                traceback.print_exc()

            finally:
                logger.removeHandler(warning_capture)

    finally:
        # Restore original weights
        config_data['room_generation']['gateway_strategy_weights'] = original_weights

    return results

def print_results(all_results: List[Dict]):
    """Print formatted results table."""

    print("\n" + "="*120)
    print("FULL LEVEL GENERATION ANALYSIS - 100 ITERATIONS PER STRATEGY")
    print("="*120)
    print()

    # Gateway Distance Table
    print("GATEWAY PLACEMENT:")
    print("-" * 120)
    print(f"{'Strategy':<20} | {'Warnings':<12} | {'Min Dist':<12} | {'Avg Dist':<12} | {'Max Dist':<12}")
    print(f"{'':20} | {'(count/%)':<12} | {'(tiles)':<12} | {'(tiles)':<12} | {'(tiles)':<12}")
    print("-" * 120)

    for result in all_results:
        strategy = result['strategy'].replace('_', ' ').title()
        warning_count = result['warnings']
        warning_pct = (warning_count / result['iterations']) * 100
        warning_str = f"{warning_count} ({warning_pct:.0f}%)"

        if result['distances']:
            min_dist = min(result['distances'])
            avg_dist = sum(result['distances']) / len(result['distances'])
            max_dist = max(result['distances'])
            print(f"{strategy:<20} | {warning_str:<12} | {min_dist:<12.1f} | {avg_dist:<12.1f} | {max_dist:<12.1f}")

    print()

    # Code Hacks Table
    print("CODE HACKS PLACED:")
    print("-" * 120)
    print(f"{'Strategy':<20} | {'Min':<12} | {'Max':<12} | {'Average':<12} | {'Total Tested':<12}")
    print("-" * 120)

    for result in all_results:
        strategy = result['strategy'].replace('_', ' ').title()
        if result['code_hacks']:
            min_hacks = min(result['code_hacks'])
            max_hacks = max(result['code_hacks'])
            avg_hacks = sum(result['code_hacks']) / len(result['code_hacks'])
            print(f"{strategy:<20} | {min_hacks:<12} | {max_hacks:<12} | {avg_hacks:<12.1f} | {len(result['code_hacks']):<12}")

    print()

    # Exploit Pickups Table
    print("EXPLOIT PICKUPS PLACED:")
    print("-" * 120)
    print(f"{'Strategy':<20} | {'Min':<12} | {'Max':<12} | {'Average':<12} | {'Total Tested':<12}")
    print("-" * 120)

    for result in all_results:
        strategy = result['strategy'].replace('_', ' ').title()
        if result['exploit_pickups']:
            min_exploits = min(result['exploit_pickups'])
            max_exploits = max(result['exploit_pickups'])
            avg_exploits = sum(result['exploit_pickups']) / len(result['exploit_pickups'])
            print(f"{strategy:<20} | {min_exploits:<12} | {max_exploits:<12} | {avg_exploits:<12.1f} | {len(result['exploit_pickups']):<12}")

    print()

    # Story Fragments Table
    print("STORY FRAGMENTS PLACED:")
    print("-" * 120)
    print(f"{'Strategy':<20} | {'Min':<12} | {'Max':<12} | {'Average':<12} | {'Total Tested':<12}")
    print("-" * 120)

    for result in all_results:
        strategy = result['strategy'].replace('_', ' ').title()
        if result['story_fragments']:
            min_frags = min(result['story_fragments'])
            max_frags = max(result['story_fragments'])
            avg_frags = sum(result['story_fragments']) / len(result['story_fragments'])
            print(f"{strategy:<20} | {min_frags:<12} | {max_frags:<12} | {avg_frags:<12.1f} | {len(result['story_fragments']):<12}")

    print()

    # Permanent Upgrades Table
    print("PERMANENT UPGRADES PLACED:")
    print("-" * 120)
    print(f"{'Strategy':<20} | {'Min':<12} | {'Max':<12} | {'Average':<12} | {'Total Tested':<12}")
    print("-" * 120)

    for result in all_results:
        strategy = result['strategy'].replace('_', ' ').title()
        if result['permanent_upgrades']:
            min_ups = min(result['permanent_upgrades'])
            max_ups = max(result['permanent_upgrades'])
            avg_ups = sum(result['permanent_upgrades']) / len(result['permanent_upgrades'])
            print(f"{strategy:<20} | {min_ups:<12} | {max_ups:<12} | {avg_ups:<12.1f} | {len(result['permanent_upgrades']):<12}")

    print()

    # Enemies Table
    print("ENEMIES PLACED:")
    print("-" * 120)
    print(f"{'Strategy':<20} | {'Min':<12} | {'Max':<12} | {'Average':<12} | {'Total Tested':<12}")
    print("-" * 120)

    for result in all_results:
        strategy = result['strategy'].replace('_', ' ').title()
        if result['enemies']:
            min_enemies = min(result['enemies'])
            max_enemies = max(result['enemies'])
            avg_enemies = sum(result['enemies']) / len(result['enemies'])
            print(f"{strategy:<20} | {min_enemies:<12} | {max_enemies:<12} | {avg_enemies:<12.1f} | {len(result['enemies']):<12}")

    print()

    # Warning Messages
    print("WARNING MESSAGES:")
    print("-" * 120)
    for result in all_results:
        if result['warning_messages']:
            strategy = result['strategy'].replace('_', ' ').title()
            print(f"\n{strategy}:")
            for msg in result['warning_messages']:
                print(f"  {msg}")

    if not any(r['warning_messages'] for r in all_results):
        print("  (No warnings - all strategies met minimum distance requirements!)")

    print("\n" + "="*120)
    print()

def main():
    """Run the analysis."""
    print("Starting FULL level generation analysis with coordinator...")
    print("Testing 100 iterations of each gateway strategy...")
    print("This includes: gateway, code hacks, exploits, story fragments, upgrades, AND enemies")
    print("(This will take 1-2 minutes)")
    print()

    strategies = ['far_corner', 'central_hub', 'hidden_dead_end', 'gauntlet']
    all_results = []

    for strategy in strategies:
        print(f"Testing {strategy.replace('_', ' ').title()}... ", end='', flush=True)
        result = analyze_strategy_full(strategy, iterations=100)
        all_results.append(result)
        print("Done!")

    print_results(all_results)

if __name__ == '__main__':
    main()
