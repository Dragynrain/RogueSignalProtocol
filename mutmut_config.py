#!/usr/bin/env python3
"""
Mutation testing configuration for RogueSignalProtocol.
Defines which files to mutate and test quality thresholds.
"""

# Configuration for mutmut mutation testing
MUTMUT_CONFIG = {
    # Files to include in mutation testing
    "paths_to_mutate": [
        "game_entities.py",
        "game_characters.py", 
        "game_combat.py",
        "game_core.py",
        "game_config.py",
        "game_data.py",
        "game_state.py",
        "data_loading.py"
    ],
    
    # Files to exclude from mutation testing
    "paths_to_exclude": [
        "tests/",
        "*_test.py",
        "test_*.py",
        "*_backup.py",
        "simple_tests.py",
        "RogueSignalProtocol_backup.py",
        ".venv/",
        "__pycache__/"
    ],
    
    # Test command to run for each mutation
    "test_command": ".venv/Scripts/python.exe -m pytest tests/unit/ -x --tb=no -q",
    
    # Mutation testing thresholds
    "thresholds": {
        "minimum_mutation_score": 80,  # Target 80% mutation score
        "timeout_per_test": 60,        # 60 seconds per mutation test
        "max_mutations": 1000          # Limit total mutations
    }
}


def get_mutation_config():
    """Get mutation testing configuration."""
    return MUTMUT_CONFIG


# Mutation test runner script
def run_mutation_tests():
    """Run mutation tests with proper configuration."""
    import subprocess
    import sys
    
    config = get_mutation_config()
    
    print("🧬 Starting mutation testing...")
    print(f"Target files: {', '.join(config['paths_to_mutate'])}")
    
    # Build mutmut command
    cmd = [
        "mutmut", "run",
        "--paths-to-mutate", ",".join(config['paths_to_mutate']),
        "--test-command", config['test_command'],
        "--timeout", str(config['thresholds']['timeout_per_test']),
        "--max-mutations", str(config['thresholds']['max_mutations'])
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("✅ Mutation testing completed successfully")
            show_mutation_results()
        else:
            print("❌ Mutation testing failed")
            return False
            
    except Exception as e:
        print(f"❌ Error running mutation tests: {e}")
        return False
    
    return True


def show_mutation_results():
    """Show mutation testing results."""
    import subprocess
    
    try:
        # Show results
        result = subprocess.run(
            ["mutmut", "results"], 
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("\n📊 Mutation Testing Results:")
            print(result.stdout)
        
        # Show summary
        result = subprocess.run(
            ["mutmut", "show"], 
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("\n📈 Mutation Summary:")
            print(result.stdout)
            
    except Exception as e:
        print(f"❌ Error showing results: {e}")


def check_mutation_score():
    """Check if mutation score meets threshold."""
    import subprocess
    import re
    
    try:
        result = subprocess.run(
            ["mutmut", "show"], 
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return False
        
        # Parse mutation score from output
        output = result.stdout
        score_match = re.search(r"(\d+)% mutation score", output)
        
        if score_match:
            score = int(score_match.group(1))
            threshold = get_mutation_config()['thresholds']['minimum_mutation_score']
            
            print(f"📊 Mutation score: {score}% (threshold: {threshold}%)")
            
            if score >= threshold:
                print("✅ Mutation score meets threshold")
                return True
            else:
                print("❌ Mutation score below threshold")
                return False
        else:
            print("❌ Could not parse mutation score")
            return False
            
    except Exception as e:
        print(f"❌ Error checking mutation score: {e}")
        return False


if __name__ == "__main__":
    """Run mutation tests from command line."""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "run":
            success = run_mutation_tests()
            sys.exit(0 if success else 1)
        elif command == "results":
            show_mutation_results()
        elif command == "check":
            success = check_mutation_score()
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        print("""
🧬 Mutation Testing for RogueSignalProtocol

Usage: python mutmut_config.py <command>

Commands:
  run     - Run mutation tests
  results - Show mutation test results  
  check   - Check if mutation score meets threshold

Examples:
  python mutmut_config.py run
  python mutmut_config.py results
  python mutmut_config.py check
        """)