#!/usr/bin/env python3
"""
Test Configuration and Runner for Rogue Signal Protocol
Includes pytest configuration, coverage setup, and performance benchmarks
"""

import pytest
import sys
import os
import time
import subprocess
from pathlib import Path

# pytest.ini configuration (create this file in your project root)
PYTEST_INI_CONTENT = """
[tool:pytest]
minversion = 6.0
addopts = -ra -q --strict-markers --strict-config
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    unit: marks tests as unit tests
    smoke: marks tests as smoke tests (quick validation)

# Coverage configuration
addopts = --cov=rogue_signal --cov-report=html --cov-report=term-missing --cov-fail-under=85

# Warnings configuration
filterwarnings =
    error
    ignore::UserWarning
    ignore::DeprecationWarning
"""

# Requirements for testing
REQUIREMENTS_TEST = """
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-benchmark>=4.0.0
pytest-xdist>=3.0.0
coverage>=7.0.0
"""

# Makefile for test automation
MAKEFILE_CONTENT = """
.PHONY: test test-unit test-integration test-performance test-coverage clean install-deps

# Install test dependencies
install-deps:
	pip install -r requirements-test.txt

# Run all tests
test:
	pytest tests/ -v

# Run only unit tests (fast)
test-unit:
	pytest tests/ -v -m "unit or not slow"

# Run integration tests
test-integration:
	pytest tests/ -v -m "integration"

# Run performance tests
test-performance:
	pytest tests/ -v -m "performance"

# Run tests with coverage
test-coverage:
	pytest tests/ --cov=rogue_signal --cov-report=html --cov-report=term-missing

# Run smoke tests (quick validation)
test-smoke:
	pytest tests/ -v -m "smoke" --maxfail=1

# Run tests in parallel
test-parallel:
	pytest tests/ -v -n auto

# Clean test artifacts
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Continuous testing (watch for changes)
test-watch:
	ptw tests/ --runner "pytest -v"

# Generate test report
test-report:
	pytest tests/ --html=test_report.html --self-contained-html
"""

class TestRunner:
    """Advanced test runner with reporting and benchmarking"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.test_results = {}
        
    def setup_test_environment(self):
        """Set up the testing environment"""
        print("🔧 Setting up test environment...")
        
        # Create requirements-test.txt
        with open("requirements-test.txt", "w") as f:
            f.write(REQUIREMENTS_TEST)
        
        # Create pytest.ini
        with open("pytest.ini", "w") as f:
            f.write(PYTEST_INI_CONTENT)
        
        # Create Makefile
        with open("Makefile", "w") as f:
            f.write(MAKEFILE_CONTENT)
        
        print("✅ Test environment setup complete!")
        
    def install_dependencies(self):
        """Install test dependencies"""
        print("📦 Installing test dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"], 
                         check=True, capture_output=True)
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
        return True
    
    def run_smoke_tests(self):
        """Run quick smoke tests for basic validation"""
        print("🚀 Running smoke tests...")
        start_time = time.time()
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "test_rogue_signal.py::TestPlayer::test_player_initialization",
                "test_rogue_signal.py::TestEnemy::test_enemy_initialization", 
                "test_rogue_signal.py::TestGameMap::test_map_initialization",
                "test_rogue_signal.py::TestGame::test_game_initialization",
                "-v"
            ], capture_output=True, text=True)
            
            duration = time.time() - start_time
            self.test_results['smoke'] = {
                'duration': duration,
                'passed': result.returncode == 0,
                'output': result.stdout
            }
            
            if result.returncode == 0:
                print(f"✅ Smoke tests passed in {duration:.2f}s")
            else:
                print(f"❌ Smoke tests failed in {duration:.2f}s")
                print(result.stdout)
                print(result.stderr)
                
        except Exception as e:
            print(f"❌ Error running smoke tests: {e}")
            return False
            
        return result.returncode == 0
    
    def run_unit_tests(self):
        """Run comprehensive unit tests"""
        print("🧪 Running unit tests...")
        start_time = time.time()
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "test_rogue_signal.py",
                "-v", "--tb=short",
                "--cov=rogue_signal",
                "--cov-report=term-missing"
            ], capture_output=True, text=True)
            
            duration = time.time() - start_time
            self.test_results['unit'] = {
                'duration': duration,
                'passed': result.returncode == 0,
                'output': result.stdout,
                'coverage': self._extract_coverage(result.stdout)
            }
            
            if result.returncode == 0:
                print(f"✅ Unit tests passed in {duration:.2f}s")
            else:
                print(f"❌ Unit tests failed in {duration:.2f}s")
                print(result.stdout[-1000:])  # Show last 1000 chars
                
        except Exception as e:
            print(f"❌ Error running unit tests: {e}")
            return False
            
        return result.returncode == 0
    
    def run_performance_tests(self):
        """Run performance benchmarks"""
        print("⚡ Running performance tests...")
        
        # Simple performance test inline
        try:
            import rogue_signal
            
            # Mock tcod to avoid import issues
            import sys
            from unittest.mock import Mock
            sys.modules['tcod'] = Mock()
            sys.modules['tcod.Color'] = Mock()
            sys.modules['tcod.event'] = Mock()
            
            # Test line of sight performance
            game_map = rogue_signal.GameMap(50, 50)
            
            start_time = time.time()
            for _ in range(1000):
                game_map.has_line_of_sight(0, 0, 49, 49)
            los_time = time.time() - start_time
            
            print(f"  Line of sight: 1000 calculations in {los_time:.3f}s")
            
            # Test enemy update performance
            with rogue_signal.patch('rogue_signal.Game.generate_tutorial_network'):
                game = rogue_signal.Game()
            
            # Add many enemies
            for i in range(100):
                enemy = rogue_signal.Enemy(i % 50, (i // 50) % 50, 'scanner')
                game.enemies.append(enemy)
            
            start_time = time.time()
            game.update_enemy_states()
            enemy_update_time = time.time() - start_time
            
            print(f"  Enemy updates: 100 enemies in {enemy_update_time:.3f}s")
            
            self.test_results['performance'] = {
                'line_of_sight_time': los_time,
                'enemy_update_time': enemy_update_time,
                'passed': los_time < 0.5 and enemy_update_time < 0.1
            }
            
            if los_time < 0.5 and enemy_update_time < 0.1:
                print("✅ Performance tests passed")
                return True
            else:
                print("❌ Performance tests failed - too slow")
                return False
                
        except Exception as e:
            print(f"❌ Error running performance tests: {e}")
            return False
    
    def _extract_coverage(self, output):
        """Extract coverage percentage from pytest output"""
        lines = output.split('\n')
        for line in lines:
            if 'TOTAL' in line and '%' in line:
                try:
                    # Extract percentage from line like "TOTAL    1234    567    89%"
                    parts = line.split()
                    for part in parts:
                        if '%' in part:
                            return int(part.replace('%', ''))
                except:
                    pass
        return 0
    
    def generate_report(self):
        """Generate a comprehensive test report"""
        print("\n" + "="*60)
        print("📊 TEST REPORT SUMMARY")
        print("="*60)
        
        total_duration = 0
        all_passed = True
        
        for test_type, results in self.test_results.items():
            if 'duration' in results:
                total_duration += results['duration']
            
            if test_type == 'smoke':
                status = "✅ PASS" if results['passed'] else "❌ FAIL"
                print(f"Smoke Tests:      {status}  ({results['duration']:.2f}s)")
                
            elif test_type == 'unit':
                status = "✅ PASS" if results['passed'] else "❌ FAIL"
                coverage = results.get('coverage', 0)
                print(f"Unit Tests:       {status}  ({results['duration']:.2f}s, {coverage}% coverage)")
                
            elif test_type == 'performance':
                status = "✅ PASS" if results['passed'] else "❌ FAIL"
                print(f"Performance:      {status}  (LOS: {results['line_of_sight_time']:.3f}s, EU: {results['enemy_update_time']:.3f}s)")
            
            if test_type != 'performance':
                all_passed = all_passed and results.get('passed', False)
        
        print("-" * 60)
        print(f"Total Duration:   {total_duration:.2f}s")
        print(f"Overall Status:   {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        print("="*60)
        
        return all_passed
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting comprehensive test suite for Rogue Signal Protocol")
        print("="*60)
        
        # Setup
        self.setup_test_environment()
        
        # Install dependencies
        if not self.install_dependencies():
            print("❌ Cannot proceed without test dependencies")
            return False
        
        # Run test suites
        smoke_passed = self.run_smoke_tests()
        if not smoke_passed:
            print("❌ Smoke tests failed - stopping execution")
            return False
        
        unit_passed = self.run_unit_tests()
        perf_passed = self.run_performance_tests()
        
        # Generate report
        all_passed = self.generate_report()
        
        if all_passed:
            print("\n🎉 All tests completed successfully!")
            print("The Rogue Signal Protocol is ready for deployment!")
        else:
            print("\n⚠️  Some tests failed. Please review the results above.")
        
        return all_passed

# Test data generators for complex scenarios
class TestDataGenerator:
    """Generate test data for complex scenarios"""
    
    @staticmethod
    def create_complex_network():
        """Create a complex test network with all features"""
        from rogue_signal import GameMap, Position, DataPatch
        
        game_map = GameMap(50, 50)
        
        # Add border walls
        for x in range(50):
            game_map.walls.add((x, 0))
            game_map.walls.add((x, 49))
        for y in range(50):
            game_map.walls.add((0, y))
            game_map.walls.add((49, y))
        
        # Add internal structures
        for x in range(10, 20):
            for y in range(10, 20):
                if x == 10 or x == 19 or y == 10 or y == 19:
                    game_map.walls.add((x, y))
        
        # Add shadows
        for x in range(5, 15):
            for y in range(5, 15):
                if not game_map.is_wall(x, y):
                    game_map.shadows.add((x, y))
        
        # Add special nodes
        game_map.cooling_nodes.add((25, 25))
        game_map.cpu_recovery_nodes.add((30, 30))
        
        # Add data patches
        patch = DataPatch('crimson', 'restore_cpu', 'Test Patch')
        game_map.data_patches[(20, 20)] = patch
        
        # Add gateway
        game_map.gateway = Position(45, 45)
        
        return game_map
    
    @staticmethod
    def create_test_enemies():
        """Create a variety of test enemies"""
        from rogue_signal import Enemy, Position
        
        enemies = []
        
        # Scanner
        scanner = Enemy(15, 15, 'scanner')
        enemies.append(scanner)
        
        # Patrol with route
        patrol = Enemy(20, 20, 'patrol')
        patrol.patrol_points = [
            Position(20, 20),
            Position(25, 20),
            Position(25, 25),
            Position(20, 25)
        ]
        enemies.append(patrol)
        
        # Random bot
        bot = Enemy(30, 30, 'bot')
        enemies.append(bot)
        
        # Firewall
        firewall = Enemy(35, 35, 'firewall')
        enemies.append(firewall)
        
        return enemies

# Command line interface
def main():
    """Main entry point for test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rogue Signal Protocol Test Runner")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests only")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--setup", action="store_true", help="Setup test environment only")
    parser.add_argument("--all", action="store_true", default=True, help="Run all tests (default)")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.setup:
        runner.setup_test_environment()
        return
    
    if args.smoke:
        success = runner.run_smoke_tests()
        runner.generate_report()
        sys.exit(0 if success else 1)
    
    if args.unit:
        success = runner.run_unit_tests()
        runner.generate_report()
        sys.exit(0 if success else 1)
    
    if args.performance:
        success = runner.run_performance_tests()
        runner.generate_report()
        sys.exit(0 if success else 1)
    
    # Run all tests by default
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
