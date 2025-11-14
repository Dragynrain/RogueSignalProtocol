#!/usr/bin/env python3
"""
Parallel Chaos Testing - Mass Fuzzing to Find Bugs

Runs multiple chaos agents in parallel to stress test the game.
Great for finding:
- Race conditions
- Memory leaks
- Rare edge cases that only appear after many actions
- Seed-specific bugs

Usage:
    python tests/integration/run_parallel_chaos.py
    python tests/integration/run_parallel_chaos.py --agents 100 --actions 10000
    python tests/integration/run_parallel_chaos.py --quick  # 10 agents, 1000 actions
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def convert_numpy_types(obj):
    """
    Recursively convert numpy types to native Python types for JSON serialization.

    Args:
        obj: Any object that might contain numpy types

    Returns:
        Object with all numpy types converted to Python native types
    """
    import numpy as np

    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    else:
        return obj


def run_single_chaos_agent(agent_id: int, max_actions: int, seed: int = None) -> dict:
    """
    Run a single chaos agent in a separate process.

    Args:
        agent_id: Unique ID for this agent
        max_actions: Maximum number of actions to perform
        seed: Optional random seed (uses agent_id if not provided)

    Returns:
        Dictionary with agent results and crash info
    """
    from tests.integration.test_chaos_agent import ChaosAgent
    from tests.test_agent import GameTestAgent

    # Use agent_id as seed if not provided (ensures different behavior per agent)
    if seed is None:
        seed = agent_id

    result = {
        "agent_id": agent_id,
        "seed": seed,
        "max_actions": max_actions,
        "crashed": False,
        "crash_reason": None,
        "crash_type": None,
        "stats": None,
        "duration_seconds": 0,
    }

    start_time = time.time()

    try:
        # Create game agent and chaos agent
        game_agent = GameTestAgent(seed=seed)
        chaos = ChaosAgent(game_agent)

        # Run chaos!
        stats = chaos.run_chaos(max_actions=max_actions)

        result["stats"] = stats
        result["crashed"] = stats.get("crashed", False)
        result["crash_reason"] = stats.get("crash_reason")
        result["crash_type"] = stats.get("crash_type")

    except Exception as e:
        # Agent crashed during execution
        result["crashed"] = True
        result["crash_reason"] = str(e)
        result["crash_type"] = type(e).__name__

    finally:
        result["duration_seconds"] = time.time() - start_time

    return result


def run_parallel_chaos(num_agents: int, actions_per_agent: int, output_file: str = None):
    """
    Run multiple chaos agents in parallel.

    Args:
        num_agents: Number of parallel agents to run
        actions_per_agent: Maximum actions per agent
        output_file: Optional file to save detailed results
    """
    print("=" * 80)
    print("PARALLEL CHAOS TESTING")
    print("=" * 80)
    print(f"Agents: {num_agents}")
    print(f"Actions per agent: {actions_per_agent}")
    print(f"Total actions: {num_agents * actions_per_agent:,}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    start_time = time.time()
    results = []
    crashes = []

    # Run agents in parallel using process pool
    with ProcessPoolExecutor(max_workers=min(num_agents, os.cpu_count() or 4)) as executor:
        # Submit all chaos agents
        futures = {
            executor.submit(run_single_chaos_agent, agent_id, actions_per_agent): agent_id
            for agent_id in range(num_agents)
        }

        # Collect results as they complete
        completed = 0
        for future in as_completed(futures):
            agent_id = futures[future]
            completed += 1

            try:
                result = future.result()
                results.append(result)

                # Track crashes
                if result["crashed"]:
                    crashes.append(result)
                    print(
                        f"[{completed}/{num_agents}] Agent {agent_id:3d} CRASHED: {result['crash_type']} - {result['crash_reason']}"
                    )
                else:
                    actions = result["stats"]["actions_taken"] if result["stats"] else 0
                    print(
                        f"[{completed}/{num_agents}] Agent {agent_id:3d} completed {actions:4d} actions in {result['duration_seconds']:.2f}s"
                    )

            except Exception as e:
                print(f"[{completed}/{num_agents}] Agent {agent_id:3d} FAILED TO RUN: {e}")

    total_time = time.time() - start_time

    # Analyze results
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)

    total_actions = sum(r["stats"]["actions_taken"] for r in results if r["stats"])
    total_key_presses = sum(r["stats"]["key_presses"] for r in results if r["stats"])

    print(f"Agents completed: {num_agents}")
    print(f"Total runtime: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
    print(f"Actions/second: {total_actions/total_time:.1f}")
    print(f"Total actions: {total_actions:,}")
    print(f"Total key presses: {total_key_presses:,}")
    print()

    # Crash summary
    print(f"Crashes: {len(crashes)}/{num_agents} ({len(crashes)/num_agents*100:.1f}%)")

    if crashes:
        print()
        print("CRASH DETAILS:")
        print("-" * 80)

        # Group crashes by type
        crash_types = {}
        for crash in crashes:
            crash_type = crash["crash_type"] or "Unknown"
            if crash_type not in crash_types:
                crash_types[crash_type] = []
            crash_types[crash_type].append(crash)

        for crash_type, crash_list in crash_types.items():
            print(f"\n{crash_type}: {len(crash_list)} occurrences")
            for crash in crash_list[:3]:  # Show first 3 of each type
                print(
                    f"  Agent {crash['agent_id']} (seed {crash['seed']}): {crash['crash_reason'][:100]}"
                )
            if len(crash_list) > 3:
                print(f"  ... and {len(crash_list)-3} more")

    # Save detailed results if requested
    if output_file:
        output_data = {
            "test_info": {
                "num_agents": num_agents,
                "actions_per_agent": actions_per_agent,
                "total_runtime_seconds": total_time,
                "timestamp": datetime.now().isoformat(),
            },
            "summary": {
                "total_actions": total_actions,
                "total_key_presses": total_key_presses,
                "crashes": len(crashes),
                "crash_rate": len(crashes) / num_agents if num_agents > 0 else 0,
            },
            "results": results,
        }

        # Convert numpy types to native Python types for JSON serialization
        output_data = convert_numpy_types(output_data)

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print()
        print(f"Detailed results saved to: {output_file}")

    print()
    print("=" * 80)

    # Return exit code based on crashes
    return 0 if len(crashes) == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description="Run parallel chaos agents to stress test the game",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 10 quick agents
  python run_parallel_chaos.py --quick

  # Run 100 agents for 10,000 actions each
  python run_parallel_chaos.py --agents 100 --actions 10000

  # Save detailed results to file
  python run_parallel_chaos.py --agents 50 --actions 5000 --output results.json
        """,
    )

    parser.add_argument(
        "--agents", type=int, default=20, help="Number of parallel agents (default: 20)"
    )
    parser.add_argument(
        "--actions", type=int, default=2000, help="Actions per agent (default: 2000)"
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output file for detailed results (JSON)"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Quick test: 10 agents, 1000 actions each"
    )

    args = parser.parse_args()

    # Handle quick mode
    if args.quick:
        num_agents = 10
        actions_per_agent = 1000
        print("[QUICK MODE] Running 10 agents with 1000 actions each")
    else:
        num_agents = args.agents
        actions_per_agent = args.actions

    # Run the chaos!
    exit_code = run_parallel_chaos(
        num_agents=num_agents, actions_per_agent=actions_per_agent, output_file=args.output
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
