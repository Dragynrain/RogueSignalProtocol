#!/usr/bin/env python3
"""
Analyze gateway placement strategies across 100 iterations of each type.
Track warning rates, minimum distances, code hack counts, and enemy counts.
"""

import sys
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
import random

# Set up logging to capture warnings
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

# Create a custom handler to capture warnings
class WarningCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.warnings = []

    def emit(self, record):
        if record.levelno == logging.WARNING:
            self.warnings.append(record.getMessage())

# Set up the game environment
from game_config import GameConfig
from game_map import GameMap
from game_level import LevelGenerator
from game_entities import Position

def analyze_gateway_strategy(strategy_name: str, iterations: int = 100) -> Dict:
    """Analyze a specific gateway strategy over multiple iterations."""

    results = {
        'strategy': strategy_name,
        'iterations': iterations,
        'warnings': 0,
        'distances': [],
        'code_hack_counts': [],
        'enemy_counts': [],
        'warning_messages': []
    }

    for i in range(iterations):
        # Create fresh map and generator for each iteration
        game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        level_generator = LevelGenerator(game_map)

        # Set up warning capture
        warning_capture = WarningCapture()
        logger = logging.getLogger()
        logger.addHandler(warning_capture)

        # Generate level with specific seed
        seed = random.randint(1, 1000000)
        level = 1  # Test on level 1

        try:
            level_generator.generate_level(level, seed)

            # Calculate distance from spawn to gateway
            spawn = Position(5, 5)
            if game_map.gateway:
                distance = spawn.distance_to(game_map.gateway)
                results['distances'].append(distance)

            # Count code hacks
            results['code_hack_counts'].append(len(game_map.code_hacks))

            # Check for warnings
            if warning_capture.warnings:
                results['warnings'] += 1
                # Store first warning message for this strategy
                if not results['warning_messages']:
                    results['warning_messages'] = warning_capture.warnings[:1]

        except Exception as e:
            print(f"Error in {strategy_name} iteration {i}: {e}")

        finally:
            logger.removeHandler(warning_capture)

    return results

def analyze_with_enemies(strategy_name: str, iterations: int = 100) -> Dict:
    """Analyze with full level generation including enemies."""
    from game_level_coordinator import GameLevelCoordinator
    from game_engine import GameEngine
    from game_state import GameStateManager
    from game_audio import SoundManager
    from game_enemies import EnemyManager

    results = {
        'strategy': strategy_name,
        'iterations': iterations,
        'warnings': 0,
        'distances': [],
        'code_hack_counts': [],
        'enemy_counts': [],
        'warning_messages': []
    }

    for i in range(iterations):
        # Force specific gateway strategy by temporarily modifying config
        original_weights = GameConfig._get_required('room_generation.gateway_strategy_weights')

        # Set weights to force our desired strategy
        forced_weights = {k: 0.0 for k in original_weights.keys()}
        forced_weights[strategy_name] = 1.0

        try:
            # Temporarily override the config
            import game_config
            config_data = game_config.GameConfig._config_data
            config_data['room_generation']['gateway_strategy_weights'] = forced_weights

            # Create a minimal game engine setup
            from game_message_log import MessageLog

            game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
            message_log = MessageLog()
            sound_manager = SoundManager()
            enemy_manager = EnemyManager(game_map, message_log)
            game_state = GameStateManager()

            # Create minimal engine (we'll only use parts of it)
            class MinimalEngine:
                def __init__(self):
                    self.game_map = game_map
                    self.message_log = message_log
                    self.sound_manager = sound_manager
                    self.enemy_manager = enemy_manager
                    self.game_state = game_state
                    self.level = 1
                    self.admin_spawned = False
                    self.level_generator = LevelGenerator(game_map)

                    # Create minimal player
                    class MinimalPlayer:
                        def __init__(self):
                            self.x = 5
                            self.y = 5
                            self.trace_level = 0

                    self.player = MinimalPlayer()

            engine = MinimalEngine()
            coordinator = GameLevelCoordinator(engine)

            # Set up warning capture
            warning_capture = WarningCapture()
            logger = logging.getLogger()
            logger.addHandler(warning_capture)

            # Generate level
            seed = random.randint(1, 1000000)
            engine.game_state.dungeon_seed = seed

            try:
                coordinator.generate_procedural_level()

                # Calculate distance
                spawn = Position(5, 5)
                if game_map.gateway:
                    distance = spawn.distance_to(game_map.gateway)
                    results['distances'].append(distance)

                # Count items and enemies
                results['code_hack_counts'].append(len(game_map.code_hacks))
                results['enemy_counts'].append(len(enemy_manager.enemies))

                # Check warnings
                if warning_capture.warnings:
                    results['warnings'] += 1
                    if not results['warning_messages']:
                        results['warning_messages'] = warning_capture.warnings[:1]

            except Exception as e:
                print(f"Error in {strategy_name} iteration {i}: {e}")

            finally:
                logger.removeHandler(warning_capture)
                # Restore original weights
                config_data['room_generation']['gateway_strategy_weights'] = original_weights

        except Exception as e:
            print(f"Setup error in {strategy_name} iteration {i}: {e}")
            # Restore weights even on error
            import game_config
            config_data = game_config.GameConfig._config_data
            config_data['room_generation']['gateway_strategy_weights'] = original_weights

    return results

def print_results(all_results: List[Dict]):
    """Print formatted results table."""

    print("\n" + "="*100)
    print("GATEWAY PLACEMENT ANALYSIS - 100 ITERATIONS PER STRATEGY")
    print("="*100)
    print()

    # Header
    print(f"{'Strategy':<18} | {'Warnings':<10} | {'Min Dist':<10} | {'Avg Dist':<10} | {'Code Hacks':<15} | {'Enemies':<15}")
    print(f"{'':18} | {'(count/%)':<10} | {'(tiles)':<10} | {'(tiles)':<10} | {'(min-max/avg)':<15} | {'(min-max/avg)':<15}")
    print("-" * 100)

    for result in all_results:
        strategy = result['strategy'].replace('_', ' ').title()

        # Warning stats
        warning_count = result['warnings']
        warning_pct = (warning_count / result['iterations']) * 100
        warning_str = f"{warning_count} ({warning_pct:.1f}%)"

        # Distance stats
        if result['distances']:
            min_dist = min(result['distances'])
            avg_dist = sum(result['distances']) / len(result['distances'])
            max_dist = max(result['distances'])
            min_dist_str = f"{min_dist:.1f}"
            avg_dist_str = f"{avg_dist:.1f}"
        else:
            min_dist_str = "N/A"
            avg_dist_str = "N/A"

        # Code hack stats
        if result['code_hack_counts']:
            min_hacks = min(result['code_hack_counts'])
            max_hacks = max(result['code_hack_counts'])
            avg_hacks = sum(result['code_hack_counts']) / len(result['code_hack_counts'])
            hacks_str = f"{min_hacks}-{max_hacks} ({avg_hacks:.1f})"
        else:
            hacks_str = "N/A"

        # Enemy stats
        if result['enemy_counts']:
            min_enemies = min(result['enemy_counts'])
            max_enemies = max(result['enemy_counts'])
            avg_enemies = sum(result['enemy_counts']) / len(result['enemy_counts'])
            enemies_str = f"{min_enemies}-{max_enemies} ({avg_enemies:.1f})"
        else:
            enemies_str = "N/A"

        print(f"{strategy:<18} | {warning_str:<10} | {min_dist_str:<10} | {avg_dist_str:<10} | {hacks_str:<15} | {enemies_str:<15}")

    print("-" * 100)

    # Print warning messages if any
    print("\nWARNING MESSAGES ENCOUNTERED:")
    print("-" * 100)
    for result in all_results:
        if result['warning_messages']:
            strategy = result['strategy'].replace('_', ' ').title()
            print(f"\n{strategy}:")
            for msg in result['warning_messages']:
                print(f"  - {msg}")

    if not any(r['warning_messages'] for r in all_results):
        print("  (None)")

    print("\n" + "="*100)
    print()

def main():
    """Run the analysis."""
    print("Starting gateway placement analysis...")
    print("Testing 100 iterations of each strategy type...")
    print()

    strategies = ['far_corner', 'central_hub', 'hidden_dead_end', 'gauntlet']
    all_results = []

    for strategy in strategies:
        print(f"Testing {strategy.replace('_', ' ').title()}... ", end='', flush=True)
        result = analyze_with_enemies(strategy, iterations=100)
        all_results.append(result)
        print("Done!")

    print_results(all_results)

if __name__ == '__main__':
    main()
