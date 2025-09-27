#!/usr/bin/env python3
"""
Test runner scripts for RogueSignalProtocol TDD workflow.
Provides various test commands for different development scenarios.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and handle output."""
    print(f"\n[SEARCH] {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"[FAIL] Command failed with exit code {result.returncode}")
        return False
    else:
        print(f"[OK] {description} completed successfully")
        return True

def quick_tests():
    """Run quick unit tests only."""
    cmd = [
        ".venv/Scripts/python.exe", "-m", "pytest",
        "tests/unit/", 
        "-x", "--tb=short", "-q"
    ]
    return run_command(cmd, "Quick unit tests")

def full_tests():
    """Run all tests with coverage."""
    cmd = [
        ".venv/Scripts/python.exe", "-m", "pytest",
        "--cov=.", "--cov-report=term-missing",
        "--durations=10"
    ]
    return run_command(cmd, "Full test suite with coverage")

def integration_tests():
    """Run integration tests only."""
    cmd = [
        ".venv/Scripts/python.exe", "-m", "pytest",
        "tests/integration/", "-v"
    ]
    return run_command(cmd, "Integration tests")

def run_specific_file(file_path):
    """Run tests for a specific file."""
    cmd = [
        ".venv/Scripts/python.exe", "-m", "pytest",
        file_path, "-v", "--tb=short"
    ]
    return run_command(cmd, f"Tests for {file_path}")

def run_changed_files():
    """Run tests for recently changed files (requires git)."""
    try:
        # Get changed Python files
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print("[FAIL] Could not get changed files from git")
            return False
            
        changed_files = [f for f in result.stdout.strip().split('\n') 
                        if f.endswith('.py') and not f.startswith('tests/')]
        
        if not changed_files:
            print("[INFO] No Python files changed")
            return True
            
        # Find corresponding test files
        test_files = []
        for file in changed_files:
            test_file = f"tests/unit/test_{Path(file).stem}.py"
            if os.path.exists(test_file):
                test_files.append(test_file)
        
        if not test_files:
            print("[INFO] No corresponding test files found")
            return True
            
        cmd = [
            ".venv/Scripts/python.exe", "-m", "pytest"
        ] + test_files + ["-v"]
        
        return run_command(cmd, f"Tests for changed files: {', '.join(changed_files)}")
        
    except Exception as e:
        print(f"[FAIL] Error running tests for changed files: {e}")
        return False

def run_coverage_report():
    """Generate detailed coverage report."""
    cmd = [
        ".venv/Scripts/python.exe", "-m", "pytest",
        "--cov=.", "--cov-report=html", "--cov-report=term",
        "--cov-fail-under=70"
    ]
    success = run_command(cmd, "Generate coverage report")
    
    if success:
        print("\n[INFO] Coverage report generated in htmlcov/index.html")
    
    return success

def run_performance():
    """Run performance benchmarks."""
    cmd = [
        ".venv/Scripts/python.exe", "-m", "pytest",
        "-m", "performance", "--benchmark-only"
    ]
    return run_command(cmd, "Performance benchmarks")

def run_watch():
    """Watch for file changes and run tests automatically."""
    try:
        import watchdog
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class TestHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.src_path.endswith('.py'):
                    print(f"\n[CHANGE] File changed: {event.src_path}")
                    if event.src_path.startswith('tests/'):
                        run_specific_file(event.src_path)
                    else:
                        quick_tests()
        
        observer = Observer()
        observer.schedule(TestHandler(), '.', recursive=True)
        observer.start()
        
        print("[WATCH] Watching for file changes... Press Ctrl+C to stop")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            observer.stop()
            print("\n[STOP] Stopped watching")
        
        observer.join()
        
    except ImportError:
        print("[FAIL] watchdog not installed. Install with: pip install watchdog")
        return False

def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("""
[TEST] RogueSignalProtocol Test Runner

Usage: python test_commands.py <command>

Commands:
  quick       - Run quick unit tests only
  full        - Run all tests with coverage  
  integration - Run integration tests only
  coverage    - Generate detailed coverage report
  changed     - Run tests for recently changed files
  performance - Run performance benchmarks
  watch       - Watch files and run tests on changes
  
Examples:
  python test_commands.py quick
  python test_commands.py coverage
  python test_commands.py watch
        """)
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        'quick': quick_tests,
        'full': full_tests, 
        'integration': integration_tests,
        'coverage': run_coverage_report,
        'changed': run_changed_files,
        'performance': run_performance,
        'watch': run_watch
    }
    
    if command in commands:
        success = commands[command]()
        sys.exit(0 if success else 1)
    else:
        print(f"[FAIL] Unknown command: {command}")
        print("Available commands:", ', '.join(commands.keys()))
        sys.exit(1)

if __name__ == "__main__":
    main()