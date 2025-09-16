"""
Service Locator pattern for dependency management.
"""

import logging
from typing import Dict, Type, TypeVar, Optional, Any, Set, List, Union
from abc import ABC, abstractmethod
from enum import Enum
import threading
import inspect

from ..core.exceptions import GameError


class ServiceError(GameError):
    """Exception raised when service locator encounters an error."""
    pass


class ServiceLifetime(Enum):
    """Service lifetime management options."""
    SINGLETON = "singleton"  # One instance for entire application
    TRANSIENT = "transient"  # New instance every time
    SCOPED = "scoped"       # One instance per scope (e.g., per level)


T = TypeVar('T')


class ServiceConfig:
    """Configuration for service registration."""
    
    def __init__(self, service_type: Type[T], implementation: Type[T] = None,
                 lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
                 factory: callable = None, init_params: Dict[str, Any] = None):
        """
        Initialize service configuration.
        
        Args:
            service_type: Interface or abstract class type
            implementation: Concrete implementation class
            lifetime: Service lifetime management
            factory: Custom factory function for creating instances
            init_params: Parameters to pass to constructor
        """
        self.service_type = service_type
        self.implementation = implementation or service_type
        self.lifetime = lifetime
        self.factory = factory
        self.init_params = init_params or {}
        self.dependencies: Set[Type] = set()
        
        # Analyze dependencies from constructor
        self._analyze_dependencies()
    
    def _analyze_dependencies(self) -> None:
        """Analyze constructor dependencies using type hints."""
        try:
            if self.factory:
                sig = inspect.signature(self.factory)
            else:
                sig = inspect.signature(self.implementation.__init__)
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                    
                if param.annotation != inspect.Parameter.empty:
                    self.dependencies.add(param.annotation)
                    
        except Exception as e:
            logging.warning(f"Could not analyze dependencies for {self.service_type}: {e}")


class ServiceScope:
    """Represents a service scope for scoped lifetime management."""
    
    def __init__(self, name: str):
        self.name = name
        self._scoped_instances: Dict[Type, Any] = {}
        self._active = True
    
    def get_instance(self, service_type: Type[T]) -> Optional[T]:
        """Get scoped instance if exists."""
        return self._scoped_instances.get(service_type)
    
    def set_instance(self, service_type: Type[T], instance: T) -> None:
        """Store scoped instance."""
        if self._active:
            self._scoped_instances[service_type] = instance
    
    def dispose(self) -> None:
        """Dispose of all scoped instances."""
        for instance in self._scoped_instances.values():
            try:
                if hasattr(instance, 'dispose'):
                    instance.dispose()
                elif hasattr(instance, 'cleanup'):
                    instance.cleanup()
            except Exception as e:
                logging.error(f"Error disposing service instance: {e}")
        
        self._scoped_instances.clear()
        self._active = False


class ServiceLocator:
    """
    Service Locator pattern implementation with dependency injection.
    
    Provides centralized service registration and resolution with
    lifetime management and automatic dependency injection.
    """
    
    _instance: Optional['ServiceLocator'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        """Initialize service locator."""
        self._services: Dict[Type, ServiceConfig] = {}
        self._singleton_instances: Dict[Type, Any] = {}
        self._scopes: Dict[str, ServiceScope] = {}
        self._current_scope: Optional[ServiceScope] = None
        self._resolving: Set[Type] = set()  # Circular dependency detection
        
        # Register self as a service
        self.register_instance(ServiceLocator, self)
        
        logging.info("Service locator initialized")
    
    @classmethod
    def get_instance(cls) -> 'ServiceLocator':
        """Get singleton instance of service locator."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ServiceLocator()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (mainly for testing)."""
        with cls._lock:
            if cls._instance:
                cls._instance.dispose_all()
            cls._instance = None
    
    def register(self, service_type: Type[T], implementation: Type[T] = None,
                lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
                **init_params) -> 'ServiceLocator':
        """
        Register a service with the locator.
        
        Args:
            service_type: Interface or abstract class
            implementation: Concrete implementation
            lifetime: Service lifetime management
            **init_params: Parameters for constructor
            
        Returns:
            Self for method chaining
        """
        config = ServiceConfig(
            service_type=service_type,
            implementation=implementation,
            lifetime=lifetime,
            init_params=init_params
        )
        
        self._services[service_type] = config
        logging.debug(f"Registered service: {service_type.__name__} -> {config.implementation.__name__}")
        
        return self
    
    def register_factory(self, service_type: Type[T], factory: callable,
                        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON) -> 'ServiceLocator':
        """
        Register a service with a custom factory function.
        
        Args:
            service_type: Service interface
            factory: Factory function to create instances
            lifetime: Service lifetime management
            
        Returns:
            Self for method chaining
        """
        config = ServiceConfig(
            service_type=service_type,
            factory=factory,
            lifetime=lifetime
        )
        
        self._services[service_type] = config
        logging.debug(f"Registered factory service: {service_type.__name__}")
        
        return self
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'ServiceLocator':
        """
        Register an existing instance as a singleton service.
        
        Args:
            service_type: Service interface
            instance: Pre-created instance
            
        Returns:
            Self for method chaining
        """
        config = ServiceConfig(service_type, type(instance), ServiceLifetime.SINGLETON)
        self._services[service_type] = config
        self._singleton_instances[service_type] = instance
        
        logging.debug(f"Registered instance service: {service_type.__name__}")
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance.
        
        Args:
            service_type: Type of service to resolve
            
        Returns:
            Service instance
            
        Raises:
            ServiceError: If service cannot be resolved
        """
        # Check for circular dependencies
        if service_type in self._resolving:
            raise ServiceError(f"Circular dependency detected for {service_type.__name__}")
        
        # Check if service is registered
        if service_type not in self._services:
            raise ServiceError(f"Service {service_type.__name__} is not registered")
        
        config = self._services[service_type]
        
        try:
            self._resolving.add(service_type)
            
            # Handle different lifetimes
            if config.lifetime == ServiceLifetime.SINGLETON:
                return self._resolve_singleton(service_type, config)
            elif config.lifetime == ServiceLifetime.SCOPED:
                return self._resolve_scoped(service_type, config)
            else:  # TRANSIENT
                return self._create_instance(config)
                
        finally:
            self._resolving.discard(service_type)
    
    def _resolve_singleton(self, service_type: Type[T], config: ServiceConfig) -> T:
        """Resolve singleton service."""
        if service_type not in self._singleton_instances:
            instance = self._create_instance(config)
            self._singleton_instances[service_type] = instance
        
        return self._singleton_instances[service_type]
    
    def _resolve_scoped(self, service_type: Type[T], config: ServiceConfig) -> T:
        """Resolve scoped service."""
        if not self._current_scope:
            # No scope active, treat as singleton
            return self._resolve_singleton(service_type, config)
        
        instance = self._current_scope.get_instance(service_type)
        if not instance:
            instance = self._create_instance(config)
            self._current_scope.set_instance(service_type, instance)
        
        return instance
    
    def _create_instance(self, config: ServiceConfig) -> Any:
        """Create new service instance with dependency injection."""
        try:
            if config.factory:
                # Use custom factory
                dependencies = self._resolve_dependencies(config.factory)
                return config.factory(**dependencies)
            else:
                # Use constructor
                dependencies = self._resolve_dependencies(config.implementation.__init__)
                combined_params = {**config.init_params, **dependencies}
                return config.implementation(**combined_params)
                
        except Exception as e:
            raise ServiceError(f"Failed to create instance of {config.service_type.__name__}: {e}")
    
    def _resolve_dependencies(self, func: callable) -> Dict[str, Any]:
        """Resolve dependencies for a function using type hints."""
        dependencies = {}
        
        try:
            sig = inspect.signature(func)
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # Skip if default value is provided
                if param.default != inspect.Parameter.empty:
                    continue
                
                # Resolve dependency if type annotation exists
                if param.annotation != inspect.Parameter.empty:
                    dependency_type = param.annotation
                    
                    # Handle Optional[Type] annotations
                    if hasattr(dependency_type, '__origin__'):
                        if dependency_type.__origin__ is Union:
                            # Extract non-None type from Optional
                            args = dependency_type.__args__
                            non_none_args = [arg for arg in args if arg != type(None)]
                            if len(non_none_args) == 1:
                                dependency_type = non_none_args[0]
                    
                    if dependency_type in self._services:
                        dependencies[param_name] = self.resolve(dependency_type)
                    
        except Exception as e:
            logging.warning(f"Could not resolve dependencies for {func}: {e}")
        
        return dependencies
    
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service, returning None if not available.
        
        Args:
            service_type: Type of service to resolve
            
        Returns:
            Service instance or None if not available
        """
        try:
            return self.resolve(service_type)
        except ServiceError:
            return None
    
    def is_registered(self, service_type: Type[T]) -> bool:
        """Check if a service type is registered."""
        return service_type in self._services
    
    def unregister(self, service_type: Type[T]) -> bool:
        """
        Unregister a service.
        
        Args:
            service_type: Type of service to unregister
            
        Returns:
            True if service was unregistered, False if not found
        """
        if service_type in self._services:
            del self._services[service_type]
            
            # Remove singleton instance if exists
            if service_type in self._singleton_instances:
                instance = self._singleton_instances[service_type]
                try:
                    if hasattr(instance, 'dispose'):
                        instance.dispose()
                    elif hasattr(instance, 'cleanup'):
                        instance.cleanup()
                except Exception as e:
                    logging.error(f"Error disposing service {service_type.__name__}: {e}")
                
                del self._singleton_instances[service_type]
            
            logging.debug(f"Unregistered service: {service_type.__name__}")
            return True
        
        return False
    
    def create_scope(self, name: str) -> ServiceScope:
        """
        Create a new service scope.
        
        Args:
            name: Unique name for the scope
            
        Returns:
            New service scope
        """
        if name in self._scopes:
            raise ServiceError(f"Scope {name} already exists")
        
        scope = ServiceScope(name)
        self._scopes[name] = scope
        logging.debug(f"Created service scope: {name}")
        
        return scope
    
    def enter_scope(self, scope_name: str) -> ServiceScope:
        """
        Enter a service scope.
        
        Args:
            scope_name: Name of scope to enter
            
        Returns:
            The entered scope
        """
        if scope_name not in self._scopes:
            raise ServiceError(f"Scope {scope_name} does not exist")
        
        self._current_scope = self._scopes[scope_name]
        logging.debug(f"Entered service scope: {scope_name}")
        
        return self._current_scope
    
    def exit_scope(self) -> None:
        """Exit current service scope."""
        if self._current_scope:
            logging.debug(f"Exited service scope: {self._current_scope.name}")
            self._current_scope = None
    
    def dispose_scope(self, scope_name: str) -> None:
        """
        Dispose of a service scope and cleanup its instances.
        
        Args:
            scope_name: Name of scope to dispose
        """
        if scope_name in self._scopes:
            scope = self._scopes[scope_name]
            scope.dispose()
            del self._scopes[scope_name]
            
            if self._current_scope == scope:
                self._current_scope = None
            
            logging.debug(f"Disposed service scope: {scope_name}")
    
    def get_registered_services(self) -> List[Type]:
        """Get list of all registered service types."""
        return list(self._services.keys())
    
    def get_service_info(self, service_type: Type[T]) -> Optional[Dict[str, Any]]:
        """Get information about a registered service."""
        if service_type not in self._services:
            return None
        
        config = self._services[service_type]
        return {
            'service_type': service_type.__name__,
            'implementation': config.implementation.__name__,
            'lifetime': config.lifetime.value,
            'has_factory': config.factory is not None,
            'dependencies': [dep.__name__ for dep in config.dependencies],
            'is_singleton_created': service_type in self._singleton_instances
        }
    
    def dispose_all(self) -> None:
        """Dispose of all services and clean up resources."""
        logging.info("Disposing all services")
        
        # Dispose all scopes
        for scope_name in list(self._scopes.keys()):
            self.dispose_scope(scope_name)
        
        # Dispose singleton instances
        for service_type, instance in self._singleton_instances.items():
            try:
                if hasattr(instance, 'dispose'):
                    instance.dispose()
                elif hasattr(instance, 'cleanup'):
                    instance.cleanup()
            except Exception as e:
                logging.error(f"Error disposing service {service_type.__name__}: {e}")
        
        # Clear all collections
        self._services.clear()
        self._singleton_instances.clear()
        self._scopes.clear()
        self._current_scope = None
        
        logging.info("All services disposed")


# Convenience functions for global service locator
def register_service(service_type: Type[T], implementation: Type[T] = None,
                    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
                    **init_params) -> ServiceLocator:
    """Register service with global service locator."""
    return ServiceLocator.get_instance().register(
        service_type, implementation, lifetime, **init_params
    )


def register_factory(service_type: Type[T], factory: callable,
                    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON) -> ServiceLocator:
    """Register factory with global service locator."""
    return ServiceLocator.get_instance().register_factory(service_type, factory, lifetime)


def register_instance(service_type: Type[T], instance: T) -> ServiceLocator:
    """Register instance with global service locator."""
    return ServiceLocator.get_instance().register_instance(service_type, instance)


def resolve_service(service_type: Type[T]) -> T:
    """Resolve service from global service locator."""
    return ServiceLocator.get_instance().resolve(service_type)


def try_resolve_service(service_type: Type[T]) -> Optional[T]:
    """Try to resolve service from global service locator."""
    return ServiceLocator.get_instance().try_resolve(service_type)