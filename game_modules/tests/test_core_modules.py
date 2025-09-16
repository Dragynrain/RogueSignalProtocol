"""
Unit tests for core modules.
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os

from ..core import Position, Colors, GameConfig
from ..events import EventManager, Event
from ..services import ServiceLocator, ServiceLifetime
from ..configuration import ConfigManager, ConfigSection, ConfigOption


class TestEvent(Event):
    """Test event for unit testing."""
    
    def __init__(self, data: str = ""):
        super().__init__()
        self.data = data
    
    def get_event_type(self) -> str:
        return "test_event"


class TestCoreModules(unittest.TestCase):
    """Test core data structures and utilities."""
    
    def test_position_creation(self):
        """Test Position creation and methods."""
        pos = Position(5, 10)
        self.assertEqual(pos.x, 5)
        self.assertEqual(pos.y, 10)
        
        # Test distance calculation
        other_pos = Position(8, 14)
        distance = pos.distance_to(other_pos)
        self.assertAlmostEqual(distance, 5.0, places=1)
        
        # Test adjacency
        adjacent_pos = Position(6, 10)
        self.assertTrue(pos.is_adjacent_to(adjacent_pos))
        
        far_pos = Position(10, 20)
        self.assertFalse(pos.is_adjacent_to(far_pos))
    
    def test_position_validation(self):
        """Test Position boundary validation."""
        pos = Position(5, 5)
        
        # Valid position
        self.assertTrue(pos.is_valid(10, 10))
        
        # Invalid positions
        self.assertFalse(pos.is_valid(5, 5))  # On boundary
        self.assertFalse(pos.is_valid(3, 10))  # Out of bounds
    
    def test_colors(self):
        """Test color definitions."""
        self.assertEqual(Colors.WHITE, (255, 255, 255))
        self.assertEqual(Colors.BLACK, (0, 0, 0))
        
        # Test color interpolation
        result = Colors.interpolate_color(Colors.BLACK, Colors.WHITE, 0.5)
        self.assertEqual(result, (127, 127, 127))
    
    def test_game_config(self):
        """Test game configuration constants."""
        self.assertGreater(GameConfig.SCREEN_WIDTH, 0)
        self.assertGreater(GameConfig.SCREEN_HEIGHT, 0)
        self.assertGreater(GameConfig.MAP_WIDTH, 0)


class TestEventSystem(unittest.TestCase):
    """Test event management system."""
    
    def setUp(self):
        """Set up test event manager."""
        self.event_manager = EventManager(max_workers=2, enable_async=False)
        self.handler_called = False
        self.received_event = None
    
    def tearDown(self):
        """Clean up after tests."""
        self.event_manager.shutdown()
    
    def test_event_subscription_and_emission(self):
        """Test basic event subscription and emission."""
        def test_handler(event):
            self.handler_called = True
            self.received_event = event
        
        # Subscribe to event
        self.event_manager.subscribe("test_event", test_handler)
        
        # Emit event
        test_event = TestEvent("test_data")
        self.event_manager.emit(test_event, immediate=True)
        
        # Verify handler was called
        self.assertTrue(self.handler_called)
        self.assertIsNotNone(self.received_event)
        self.assertEqual(self.received_event.data, "test_data")
    
    def test_event_queue_processing(self):
        """Test queued event processing."""
        def test_handler(event):
            self.handler_called = True
        
        self.event_manager.subscribe("test_event", test_handler)
        
        # Emit event to queue
        test_event = TestEvent()
        self.event_manager.emit(test_event, immediate=False)
        
        # Handler should not be called yet
        self.assertFalse(self.handler_called)
        
        # Process events
        processed = self.event_manager.process_events()
        self.assertEqual(processed, 1)
        self.assertTrue(self.handler_called)
    
    def test_wildcard_subscription(self):
        """Test wildcard event subscription."""
        def wildcard_handler(event):
            self.handler_called = True
        
        self.event_manager.subscribe_all(wildcard_handler)
        
        # Emit any event
        test_event = TestEvent()
        self.event_manager.emit(test_event, immediate=True)
        
        self.assertTrue(self.handler_called)
    
    def test_handler_priority(self):
        """Test event handler priority ordering."""
        call_order = []
        
        def high_priority_handler(event):
            call_order.append("high")
        
        def low_priority_handler(event):
            call_order.append("low")
        
        # Subscribe with different priorities
        self.event_manager.subscribe("test_event", low_priority_handler, priority=1)
        self.event_manager.subscribe("test_event", high_priority_handler, priority=10)
        
        test_event = TestEvent()
        self.event_manager.emit(test_event, immediate=True)
        
        # High priority should be called first
        self.assertEqual(call_order, ["high", "low"])


class TestServiceLocator(unittest.TestCase):
    """Test service locator and dependency injection."""
    
    def setUp(self):
        """Set up test service locator."""
        # Reset singleton for testing
        ServiceLocator.reset()
        self.service_locator = ServiceLocator.get_instance()
    
    def tearDown(self):
        """Clean up after tests."""
        ServiceLocator.reset()
    
    def test_service_registration_and_resolution(self):
        """Test basic service registration and resolution."""
        # Register a simple service
        self.service_locator.register_instance(str, "test_string")
        
        # Resolve the service
        resolved = self.service_locator.resolve(str)
        self.assertEqual(resolved, "test_string")
    
    def test_singleton_lifetime(self):
        """Test singleton service lifetime."""
        class TestService:
            def __init__(self):
                self.value = id(self)
        
        self.service_locator.register(TestService, lifetime=ServiceLifetime.SINGLETON)
        
        # Resolve multiple times
        instance1 = self.service_locator.resolve(TestService)
        instance2 = self.service_locator.resolve(TestService)
        
        # Should be the same instance
        self.assertIs(instance1, instance2)
    
    def test_transient_lifetime(self):
        """Test transient service lifetime."""
        class TestService:
            def __init__(self):
                self.value = id(self)
        
        self.service_locator.register(TestService, lifetime=ServiceLifetime.TRANSIENT)
        
        # Resolve multiple times
        instance1 = self.service_locator.resolve(TestService)
        instance2 = self.service_locator.resolve(TestService)
        
        # Should be different instances
        self.assertIsNot(instance1, instance2)
    
    def test_service_not_registered(self):
        """Test resolving unregistered service."""
        from ..services.service_locator import ServiceError
        
        with self.assertRaises(ServiceError):
            self.service_locator.resolve(dict)


class TestConfigurationSystem(unittest.TestCase):
    """Test configuration management system."""
    
    def setUp(self):
        """Set up test configuration manager."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.config_manager = ConfigManager(self.temp_file.name, auto_save=False)
    
    def tearDown(self):
        """Clean up test files."""
        try:
            os.unlink(self.temp_file.name)
        except OSError:
            pass
    
    def test_config_section_creation(self):
        """Test configuration section creation and options."""
        section = ConfigSection("test_section", "Test section description")
        
        from ..configuration.config_manager import ConfigOption, TypeValidator
        option = ConfigOption("test_key", "default_value", "Test option", 
                            TypeValidator(str))
        section.add_option(option)
        
        # Test getting default value
        self.assertEqual(section.get("test_key"), "default_value")
        
        # Test setting value
        success = section.set("test_key", "new_value")
        self.assertTrue(success)
        self.assertEqual(section.get("test_key"), "new_value")
    
    def test_config_validation(self):
        """Test configuration value validation."""
        section = ConfigSection("test_section")
        
        from ..configuration.config_manager import ConfigOption, RangeValidator
        option = ConfigOption("numeric_key", 50, "Numeric option", 
                            RangeValidator(0, 100))
        section.add_option(option)
        
        # Valid value
        success = section.set("numeric_key", 75)
        self.assertTrue(success)
        
        # Invalid value
        success = section.set("numeric_key", 150)
        self.assertFalse(success)
        self.assertEqual(section.get("numeric_key"), 75)  # Should remain unchanged
    
    def test_config_save_and_load(self):
        """Test configuration persistence."""
        # Set some values
        self.config_manager.set("display", "width", 100)
        self.config_manager.set("audio", "master_volume", 0.5)
        
        # Save configuration
        success = self.config_manager.save()
        self.assertTrue(success)
        
        # Create new manager and load
        new_manager = ConfigManager(self.temp_file.name, auto_save=False)
        success = new_manager.load()
        self.assertTrue(success)
        
        # Verify values
        self.assertEqual(new_manager.get("display", "width"), 100)
        self.assertEqual(new_manager.get("audio", "master_volume"), 0.5)


def run_core_tests():
    """Run all core module tests."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestCoreModules))
    suite.addTest(unittest.makeSuite(TestEventSystem))
    suite.addTest(unittest.makeSuite(TestServiceLocator))
    suite.addTest(unittest.makeSuite(TestConfigurationSystem))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_core_tests()