#!/usr/bin/env python3
"""
Complete gateway and level generation analysis.
Tracks gateway distances, code hacks, exploit pickups, and enemies for each strategy.
"""

import sys
import logging
from typing import Dict, List
import random

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
from game_data import GameData

def count_enemies_on_map(game_map):
    """Count how many enemies can be placed based on floor space."""
    # Get network config for level 1
    config = GameConfig.get_network_configs()[1]
    return config['enemies']

def analyze_strategy(strategy_name: str, iterations: int = 100) -> Dict:
    """Analyze a gateway strategy comprehensively."""

    results = {
        'strategy': strategy_name,
        'iterations': iterations,
        'warnings': 0,
        'distances': [],
        'code_hacks': [],
        'exploit_pickups': [],
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
            # Create fresh map and generator
            game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
            level_generator = LevelGenerator(game_map)

            # Set up warning capture
            warning_capture = WarningCapture()
            logger = logging.getLogger()
            logger.addHandler(warning_capture)

            try:
                # Generate level (this creates gateway, but not items/enemies)
                seed = random.randint(1, 1000000)
                level_generator.generate_level(1, seed)

                # Calculate distance
                spawn = Position(5, 5)
                if game_map.gateway:
                    distance = spawn.distance_to(game_map.gateway)
                    results['distances'].append(distance)

                # Count code hacks (placed by level generator)
                results['code_hacks'].append(len(game_map.code_hacks))

                # Count exploit pickups
                results['exploit_pickups'].append(len(game_map.exploit_pickups))

                # Get enemy count from config (enemies aren't placed by level generator)
                enemy_count = count_enemies_on_map(game_map)
                results['enemies'].append(enemy_count)

                # Check for warnings
                if warning_capture.warnings:
                    results['warnings'] += 1
                    if not results['warning_messages']:
                        results['warning_messages'] = warning_capture.warnings[:1]

            finally:
                logger.removeHandler(warning_capture)

    finally:
        # Restore original weights
        config_data['room_generation']['gateway_strategy_weights'] = original_weights

    return results

def print_results(all_results: List[Dict]):
    """Print formatted results table."""

    print("\n" + "="*120)
    print("COMPREHENSIVE LEVEL GENERATION ANALYSIS - 100 ITERATIONS PER STRATEGY")
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

    # Enemies Table
    print("ENEMIES (FROM CONFIG - NOT PLACED BY LEVEL GENERATOR):")
    print("-" * 120)
    print(f"{'Strategy':<20} | {'Config Count':<12} | {'Note':<50}")
    print("-" * 120)

    for result in all_results:
        strategy = result['strategy'].replace('_', ' ').title()
        if result['enemies']:
            enemy_count = result['enemies'][0]  # All will be same from config
            print(f"{strategy:<20} | {enemy_count:<12} | {'Same for all - from network config, not level gen':<50}")

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
    print("Starting comprehensive level generation analysis...")
    print("Testing 100 iterations of each gateway strategy...")
    print("(This may take 30-60 seconds)")
    print()

    strategies = ['far_corner', 'central_hub', 'hidden_dead_end', 'gauntlet']
    all_results = []

    for strategy in strategies:
        print(f"Testing {strategy.replace('_', ' ').title()}... ", end='', flush=True)
        result = analyze_strategy(strategy, iterations=100)
        all_results.append(result)
        print("Done!")

    print_results(all_results)

if __name__ == '__main__':
    # Suppress pygame welcome message
    import os
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
    main()
