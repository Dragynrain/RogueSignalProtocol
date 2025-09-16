#!/usr/bin/env python3
"""
Phase 3 Unit Test Runner - Comprehensive Test Suite
"""

import unittest
import sys
import time
from typing import List, Dict, Any

# Add current directory to path
sys.path.insert(0, '.')

def test_core_position():
    """Test Position class functionality."""
    try:
        from game_modules.core import Position
        
        # Test creation
        pos = Position(5, 10)
        assert pos.x == 5 and pos.y == 10, "Position creation failed"
        
        # Test distance calculation
        other_pos = Position(8, 14)
        distance = pos.distance_to(other_pos)
        assert abs(distance - 5.0) < 0.1, f"Distance calculation failed: {distance}"
        
        # Test adjacency
        adjacent_pos = Position(6, 10)
        assert pos.is_adjacent_to(adjacent_pos), "Adjacency test failed"
        
        far_pos = Position(10, 20)
        assert not pos.is_adjacent_to(far_pos), "Non-adjacency test failed"
        
        print("✅ Position class tests PASSED")
        return True
    except Exception as e:
        print(f"❌ Position class tests FAILED: {e}")
        return False

def test_colors():
    """Test Colors functionality."""
    try:
        from game_modules.core import Colors
        
        # Test basic colors
        assert Colors.WHITE == (255, 255, 255), "White color definition failed"
        assert Colors.BLACK == (0, 0, 0), "Black color definition failed"
        
        # Test color interpolation
        result = Colors.interpolate_color(Colors.BLACK, Colors.WHITE, 0.5)
        assert result == (127, 127, 127), f"Color interpolation failed: {result}"
        
        print("✅ Colors tests PASSED")
        return True
    except Exception as e:
        print(f"❌ Colors tests FAILED: {e}")
        return False

def test_event_system():
    """Test Event Management System."""
    try:
        from game_modules.events import EventManager, Event
        
        # Test event manager creation
        event_manager = EventManager(max_workers=2, enable_async=False)
        
        # Test simple event class
        class TestEvent(Event):
            def __init__(self, data="test"):
                super().__init__()
                self.data = data
            
            def get_event_type(self):
                return "test_event"
        
        # Test event subscription and emission
        handler_called = False
        received_event = None
        
        def test_handler(event):
            nonlocal handler_called, received_event
            handler_called = True
            received_event = event
        
        event_manager.subscribe("test_event", test_handler)
        
        # Emit event
        test_event = TestEvent("test_data")
        event_manager.emit(test_event, immediate=True)
        
        assert handler_called, "Event handler was not called"
        assert received_event.data == "test_data", "Event data not received correctly"
        
        # Test queue processing
        handler_called = False
        event_manager.emit(TestEvent("queued"), immediate=False)
        assert not handler_called, "Handler called too early"
        
        processed = event_manager.process_events()
        assert processed == 1, f"Wrong number of events processed: {processed}"
        assert handler_called, "Queued event handler not called"
        
        event_manager.shutdown()
        print("✅ Event System tests PASSED")
        return True
    except Exception as e:
        print(f"❌ Event System tests FAILED: {e}")
        return False

def test_service_locator():
    """Test Service Locator and Dependency Injection."""
    try:
        from game_modules.services import ServiceLocator, ServiceLifetime
        
        # Reset for testing
        ServiceLocator.reset()
        service_locator = ServiceLocator.get_instance()
        
        # Test instance registration
        service_locator.register_instance(str, "test_string")
        resolved = service_locator.resolve(str)
        assert resolved == "test_string", "Instance registration/resolution failed"
        
        # Test singleton lifetime
        class TestService:
            def __init__(self):
                self.value = id(self)
        
        service_locator.register(TestService, lifetime=ServiceLifetime.SINGLETON)
        instance1 = service_locator.resolve(TestService)
        instance2 = service_locator.resolve(TestService)
        assert instance1 is instance2, "Singleton lifetime failed"
        
        # Test transient lifetime
        service_locator.register(TestService, TestService, ServiceLifetime.TRANSIENT)
        instance3 = service_locator.resolve(TestService)
        instance4 = service_locator.resolve(TestService)
        assert instance3 is not instance4, "Transient lifetime failed"
        
        ServiceLocator.reset()
        print("✅ Service Locator tests PASSED")
        return True
    except Exception as e:
        print(f"❌ Service Locator tests FAILED: {e}")
        return False

def test_entity_factory():
    """Test Entity Factory functionality."""
    try:
        from game_modules.factories import EntityFactory
        from game_modules.core import Position
        
        factory = EntityFactory()
        
        # Test player creation
        player = factory.create_player(10, 20)
        assert player.x == 10 and player.y == 20, "Player creation failed"
        
        # Test enemy creation
        position = Position(5, 5)
        enemy = factory.create_enemy(position, "scanner")
        assert enemy.position.x == 5 and enemy.position.y == 5, "Enemy creation failed"
        assert enemy.type == "scanner", "Enemy type incorrect"
        
        # Test data patch creation
        patch = factory.create_data_patch("Test Patch", cpu_boost=25, heat_reduction=10)
        assert patch.name == "Test Patch", "Data patch name incorrect"
        assert patch.cpu_boost == 25, "Data patch CPU boost incorrect"
        
        print("✅ Entity Factory tests PASSED")
        return True
    except Exception as e:
        print(f"❌ Entity Factory tests FAILED: {e}")
        return False

def test_import_structure():
    """Test all module imports work correctly."""
    try:
        # Test core imports
        from game_modules.core import Position, Colors, GameConfig
        from game_modules.events import EventManager
        from game_modules.services import ServiceLocator
        from game_modules.factories import EntityFactory
        
        print("✅ Module Import tests PASSED")
        return True
    except Exception as e:
        print(f"❌ Module Import tests FAILED: {e}")
        return False

def run_comprehensive_tests():
    """Run all Phase 3 unit tests."""
    print("🧪 PHASE 3 COMPREHENSIVE TEST SUITE")
    print("=" * 50)
    
    start_time = time.time()
    
    tests = [
        ("Module Imports", test_import_structure),
        ("Core Position Class", test_core_position),
        ("Colors System", test_colors),
        ("Event Management", test_event_system),
        ("Service Locator", test_service_locator),
        ("Entity Factory", test_entity_factory),
    ]
    
    passed = 0
    failed = 0
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                results.append((test_name, "PASSED", ""))
            else:
                failed += 1
                results.append((test_name, "FAILED", "Test returned False"))
        except Exception as e:
            failed += 1
            results.append((test_name, "FAILED", str(e)))
    
    end_time = time.time()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for test_name, status, error in results:
        status_icon = "✅" if status == "PASSED" else "❌"
        print(f"{status_icon} {test_name}: {status}")
        if error:
            print(f"   Error: {error}")
    
    print(f"\n📈 STATISTICS:")
    print(f"   Total Tests: {len(tests)}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Success Rate: {(passed/len(tests)*100):.1f}%")
    print(f"   Execution Time: {(end_time-start_time):.2f}s")
    
    if failed == 0:
        print(f"\n🎉 ALL TESTS PASSED! Phase 3 architecture is working perfectly!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)