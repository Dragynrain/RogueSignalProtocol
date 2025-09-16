#!/usr/bin/env python3
"""
Phase 3 Unit Test Runner - Simple Version
"""

import sys
import time

# Add current directory to path
sys.path.insert(0, '.')

def test_core_modules():
    """Test core module functionality."""
    print("Testing Core Modules...")
    
    try:
        from game_modules.core import Position, Colors, GameConfig
        
        # Test Position
        pos = Position(5, 10)
        assert pos.x == 5 and pos.y == 10
        
        other_pos = Position(8, 14)
        distance = pos.distance_to(other_pos)
        assert abs(distance - 5.0) < 0.1
        
        # Test Colors
        assert Colors.WHITE == (255, 255, 255)
        result = Colors.interpolate_color(Colors.BLACK, Colors.WHITE, 0.5)
        assert result == (127, 127, 127)
        
        print("  ✓ Core modules PASSED")
        return True
    except Exception as e:
        print(f"  ✗ Core modules FAILED: {e}")
        return False

def test_event_system():
    """Test event system."""
    print("Testing Event System...")
    
    try:
        from game_modules.events import EventManager, Event
        
        event_manager = EventManager(enable_async=False)
        
        class TestEvent(Event):
            def __init__(self, data="test"):
                super().__init__()
                self.data = data
            def get_event_type(self):
                return "test_event"
        
        handler_called = False
        def test_handler(event):
            nonlocal handler_called
            handler_called = True
        
        event_manager.subscribe("test_event", test_handler)
        event_manager.emit(TestEvent("test"), immediate=True)
        
        assert handler_called
        event_manager.shutdown()
        
        print("  ✓ Event system PASSED")
        return True
    except Exception as e:
        print(f"  ✗ Event system FAILED: {e}")
        return False

def test_service_locator():
    """Test service locator."""
    print("Testing Service Locator...")
    
    try:
        from game_modules.services import ServiceLocator, ServiceLifetime
        
        ServiceLocator.reset()
        service_locator = ServiceLocator.get_instance()
        
        service_locator.register_instance(str, "test_string")
        resolved = service_locator.resolve(str)
        assert resolved == "test_string"
        
        ServiceLocator.reset()
        
        print("  ✓ Service locator PASSED")
        return True
    except Exception as e:
        print(f"  ✗ Service locator FAILED: {e}")
        return False

def test_entity_factory():
    """Test entity factory."""
    print("Testing Entity Factory...")
    
    try:
        from game_modules.factories import EntityFactory
        from game_modules.core import Position
        
        factory = EntityFactory()
        
        # Test player creation
        player = factory.create_player(10, 20)
        assert player.x == 10 and player.y == 20
        
        # Test enemy creation
        position = Position(5, 5)
        enemy = factory.create_enemy(position, "scanner")
        assert enemy.position.x == 5 and enemy.position.y == 5
        
        print("  ✓ Entity factory PASSED")
        return True
    except Exception as e:
        print(f"  ✗ Entity factory FAILED: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    print("PHASE 3 UNIT TEST RESULTS")
    print("=" * 40)
    
    tests = [
        test_core_modules,
        test_event_system,
        test_service_locator,
        test_entity_factory,
    ]
    
    passed = 0
    total = len(tests)
    
    start_time = time.time()
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    end_time = time.time()
    
    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"  Total Tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Success Rate: {(passed/total*100):.1f}%")
    print(f"  Execution Time: {(end_time-start_time):.2f}s")
    
    if passed == total:
        print("\nALL TESTS PASSED! Phase 3 architecture is working!")
        return True
    else:
        print(f"\n{total - passed} test(s) failed.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)