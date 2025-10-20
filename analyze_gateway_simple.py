#!/usr/bin/env python3
"""
Analyze gateway placement strategies - simplified version.
Track warning rates and minimum distances for each strategy type.
"""

import sys
import logging
from collections import defaultdict
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

def analyze_strategy(strategy_name: str, iterations: int = 100) -> Dict:
    """Analyze a gateway strategy by forcing it to be used."""

    results = {
        'strategy': strategy_name,
        'iterations': iterations,
        'warnings': 0,
        'distances': [],
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
                # Generate level
                seed = random.randint(1, 1000000)
                level_generator.generate_level(1, seed)

                # Calculate distance
                spawn = Position(5, 5)
                if game_map.gateway:
                    distance = spawn.distance_to(game_map.gateway)
                    results['distances'].append(distance)

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

    print("\n" + "="*90)
    print("GATEWAY PLACEMENT ANALYSIS - 100 ITERATIONS PER STRATEGY")
    print("="*90)
    print()

    # Header
    print(f"{'Strategy':<20} | {'Warnings':<12} | {'Min Dist':<12} | {'Avg Dist':<12} | {'Max Dist':<12}")
    print(f"{'':20} | {'(count/%)':<12} | {'(tiles)':<12} | {'(tiles)':<12} | {'(tiles)':<12}")
    print("-" * 90)

    for result in all_results:
        strategy = result['strategy'].replace('_', ' ').title()

        # Warning stats
        warning_count = result['warnings']
        warning_pct = (warning_count / result['iterations']) * 100
        warning_str = f"{warning_count} ({warning_pct:.0f}%)"

        # Distance stats
        if result['distances']:
            min_dist = min(result['distances'])
            avg_dist = sum(result['distances']) / len(result['distances'])
            max_dist = max(result['distances'])
            min_dist_str = f"{min_dist:.1f}"
            avg_dist_str = f"{avg_dist:.1f}"
            max_dist_str = f"{max_dist:.1f}"
        else:
            min_dist_str = "N/A"
            avg_dist_str = "N/A"
            max_dist_str = "N/A"

        print(f"{strategy:<20} | {warning_str:<12} | {min_dist_str:<12} | {avg_dist_str:<12} | {max_dist_str:<12}")

    print("-" * 90)

    # Print warning messages
    print("\nWARNING MESSAGES:")
    print("-" * 90)
    for result in all_results:
        if result['warning_messages']:
            strategy = result['strategy'].replace('_', ' ').title()
            print(f"\n{strategy}:")
            for msg in result['warning_messages']:
                print(f"  {msg}")

    if not any(r['warning_messages'] for r in all_results):
        print("  (No warnings - all strategies met minimum distance requirements)")

    print("\n" + "="*90)
    print()

def main():
    """Run the analysis."""
    print("Starting gateway placement analysis...")
    print("Testing 100 iterations of each strategy type...")
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
