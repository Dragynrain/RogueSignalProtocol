"""
Entity factory using Factory pattern for creating game entities.
"""

import logging
import random
from typing import Dict, Type, Any, Optional, List, Callable
from abc import ABC, abstractmethod

from ..core.data_structures import Position
from ..core.definitions import GameData
from ..core.exceptions import GameLogicError
from ..game.entities import Player, Enemy
from ..inventory import DataPatch, ExploitItem, StoryFragment


class EntityCreationError(GameLogicError):
    """Exception raised when entity creation fails."""
    pass


class EntityTemplate:
    """
    Template for creating entities with specific configurations.
    """
    
    def __init__(self, entity_type: str, base_config: Dict[str, Any] = None,
                 modifiers: List[Callable] = None):
        """
        Initialize entity template.
        
        Args:
            entity_type: Type of entity to create
            base_config: Base configuration parameters
            modifiers: List of modifier functions to apply
        """
        self.entity_type = entity_type
        self.base_config = base_config or {}
        self.modifiers = modifiers or []
        self.creation_count = 0
    
    def apply_modifiers(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all modifiers to the configuration."""
        for modifier in self.modifiers:
            config = modifier(config) or config
        return config
    
    def create_config(self) -> Dict[str, Any]:
        """Create final configuration for entity."""
        config = self.base_config.copy()
        config = self.apply_modifiers(config)
        self.creation_count += 1
        return config


class EntityFactory:
    """
    Factory for creating game entities with proper configuration.
    
    Uses Factory pattern to centralize entity creation logic
    and provide consistent initialization.
    """
    
    def __init__(self):
        """Initialize entity factory."""
        self._templates: Dict[str, EntityTemplate] = {}
        self._creation_stats: Dict[str, int] = {}
        self._custom_creators: Dict[str, Callable] = {}
        
        # Register default templates
        self._register_default_templates()
        
        logging.info("Entity factory initialized")
    
    def _register_default_templates(self) -> None:
        """Register default entity templates."""
        # Player template
        self.register_template("player", EntityTemplate(
            "player",
            {"x": 0, "y": 0}
        ))
        
        # Enemy templates for each type
        for enemy_type in GameData.ENEMY_TYPES.keys():
            self.register_template(f"enemy_{enemy_type}", EntityTemplate(
                "enemy",
                {"enemy_type": enemy_type}
            ))
    
    def register_template(self, name: str, template: EntityTemplate) -> None:
        """
        Register an entity template.
        
        Args:
            name: Unique name for the template
            template: Entity template to register
        """
        self._templates[name] = template
        logging.debug(f"Registered entity template: {name}")
    
    def register_custom_creator(self, entity_type: str, creator_func: Callable) -> None:
        """
        Register a custom entity creator function.
        
        Args:
            entity_type: Type of entity
            creator_func: Function to create entity
        """
        self._custom_creators[entity_type] = creator_func
        logging.debug(f"Registered custom creator for: {entity_type}")
    
    def create_player(self, x: int, y: int, **kwargs) -> Player:
        """
        Create a player entity.
        
        Args:
            x: Starting x position
            y: Starting y position
            **kwargs: Additional configuration
            
        Returns:
            Player instance
        """
        try:
            config = {"x": x, "y": y, **kwargs}
            
            # Apply template modifiers if available
            if "player" in self._templates:
                template_config = self._templates["player"].create_config()
                config.update(template_config)
            
            player = Player(config["x"], config["y"])
            
            # Apply additional configuration
            for key, value in config.items():
                if key not in ["x", "y"] and hasattr(player, key):
                    setattr(player, key, value)
            
            self._update_stats("player")
            logging.debug(f"Created player at ({x}, {y})")
            
            return player
            
        except Exception as e:
            raise EntityCreationError(f"Failed to create player: {e}")
    
    def create_enemy(self, position: Position, enemy_type: str, **kwargs) -> Enemy:
        """
        Create an enemy entity.
        
        Args:
            position: Enemy position
            enemy_type: Type of enemy to create
            **kwargs: Additional configuration
            
        Returns:
            Enemy instance
        """
        try:
            # Validate enemy type
            if enemy_type not in GameData.ENEMY_TYPES:
                raise EntityCreationError(f"Unknown enemy type: {enemy_type}")
            
            config = {"position": position, "enemy_type": enemy_type, **kwargs}
            
            # Apply template modifiers if available
            template_name = f"enemy_{enemy_type}"
            if template_name in self._templates:
                template_config = self._templates[template_name].create_config()
                config.update(template_config)
            
            # Check for custom creator
            if "enemy" in self._custom_creators:
                enemy = self._custom_creators["enemy"](config)
            else:
                enemy = Enemy(position, enemy_type)
            
            # Apply additional configuration
            for key, value in config.items():
                if key not in ["position", "enemy_type"] and hasattr(enemy, key):
                    setattr(enemy, key, value)
            
            self._update_stats(f"enemy_{enemy_type}")
            logging.debug(f"Created {enemy_type} enemy at {position}")
            
            return enemy
            
        except Exception as e:
            raise EntityCreationError(f"Failed to create enemy {enemy_type}: {e}")
    
    def create_enemy_group(self, positions: List[Position], enemy_type: str,
                          **kwargs) -> List[Enemy]:
        """
        Create a group of enemies of the same type.
        
        Args:
            positions: List of positions for enemies
            enemy_type: Type of enemies to create
            **kwargs: Additional configuration
            
        Returns:
            List of Enemy instances
        """
        enemies = []
        
        for position in positions:
            try:
                enemy = self.create_enemy(position, enemy_type, **kwargs)
                enemies.append(enemy)
            except EntityCreationError as e:
                logging.error(f"Failed to create enemy in group: {e}")
                continue
        
        logging.info(f"Created enemy group: {len(enemies)} {enemy_type} enemies")
        return enemies
    
    def create_random_enemy(self, position: Position, 
                           allowed_types: List[str] = None,
                           level_factor: float = 1.0, **kwargs) -> Enemy:
        """
        Create a random enemy appropriate for the current level.
        
        Args:
            position: Enemy position
            allowed_types: List of allowed enemy types (None for all)
            level_factor: Factor for scaling enemy difficulty
            **kwargs: Additional configuration
            
        Returns:
            Random Enemy instance
        """
        available_types = allowed_types or list(GameData.ENEMY_TYPES.keys())
        
        if not available_types:
            raise EntityCreationError("No enemy types available for random creation")
        
        # Weight enemy types by appropriateness for level
        weights = []
        for enemy_type in available_types:
            enemy_data = GameData.ENEMY_TYPES[enemy_type]
            # Simple weighting based on enemy strength and level factor
            base_weight = 100
            if enemy_data.cpu > 100:  # Strong enemies
                base_weight = max(10, base_weight - int((2.0 - level_factor) * 50))
            weights.append(base_weight)
        
        # Select random enemy type
        selected_type = random.choices(available_types, weights=weights)[0]
        
        # Create enemy with level scaling
        enemy = self.create_enemy(position, selected_type, **kwargs)
        
        # Apply level scaling
        if level_factor != 1.0:
            enemy.cpu = int(enemy.cpu * level_factor)
            enemy.max_cpu = enemy.cpu
        
        logging.debug(f"Created random enemy: {selected_type} (level factor: {level_factor})")
        return enemy
    
    def create_data_patch(self, name: str, cpu_boost: int = 0, 
                         heat_reduction: int = 0, ram_cost: int = 1,
                         **kwargs) -> DataPatch:
        """
        Create a data patch item.
        
        Args:
            name: Patch name
            cpu_boost: CPU restoration amount
            heat_reduction: Heat reduction amount
            ram_cost: RAM cost to carry
            **kwargs: Additional configuration
            
        Returns:
            DataPatch instance
        """
        try:
            patch = DataPatch(name, cpu_boost, heat_reduction, ram_cost, **kwargs)
            self._update_stats("data_patch")
            logging.debug(f"Created data patch: {name}")
            return patch
            
        except Exception as e:
            raise EntityCreationError(f"Failed to create data patch {name}: {e}")
    
    def create_exploit_item(self, exploit_key: str, **kwargs) -> ExploitItem:
        """
        Create an exploit item.
        
        Args:
            exploit_key: Key identifying the exploit
            **kwargs: Additional configuration
            
        Returns:
            ExploitItem instance
        """
        try:
            # Validate exploit key
            if exploit_key not in GameData.EXPLOITS:
                raise EntityCreationError(f"Unknown exploit: {exploit_key}")
            
            exploit_data = GameData.EXPLOITS[exploit_key]
            item = ExploitItem(exploit_key, exploit_data.name, **kwargs)
            
            self._update_stats("exploit_item")
            logging.debug(f"Created exploit item: {exploit_key}")
            return item
            
        except Exception as e:
            raise EntityCreationError(f"Failed to create exploit item {exploit_key}: {e}")
    
    def create_story_fragment(self, title: str, content: str, **kwargs) -> StoryFragment:
        """
        Create a story fragment item.
        
        Args:
            title: Fragment title
            content: Story content
            **kwargs: Additional configuration
            
        Returns:
            StoryFragment instance
        """
        try:
            fragment = StoryFragment(title, content, **kwargs)
            self._update_stats("story_fragment")
            logging.debug(f"Created story fragment: {title}")
            return fragment
            
        except Exception as e:
            raise EntityCreationError(f"Failed to create story fragment {title}: {e}")
    
    def create_balanced_loot(self, level: int, loot_type: str = "random") -> List[Any]:
        """
        Create balanced loot appropriate for the given level.
        
        Args:
            level: Game level for balancing
            loot_type: Type of loot to create ("random", "data_patches", "exploits")
            
        Returns:
            List of created items
        """
        loot = []
        
        try:
            if loot_type in ["random", "data_patches"]:
                # Create data patches scaled to level
                patch_count = random.randint(1, 3)
                for _ in range(patch_count):
                    cpu_boost = random.randint(10, 30) + (level * 5)
                    heat_reduction = random.randint(5, 20) + (level * 2)
                    
                    patch = self.create_data_patch(
                        f"Data Patch L{level}",
                        cpu_boost=cpu_boost,
                        heat_reduction=heat_reduction
                    )
                    loot.append(patch)
            
            if loot_type in ["random", "exploits"]:
                # Create exploits appropriate for level
                available_exploits = list(GameData.EXPLOITS.keys())
                if level < 3:  # Early levels - basic exploits only
                    available_exploits = [k for k in available_exploits 
                                        if GameData.EXPLOITS[k].heat <= 30]
                
                if available_exploits and random.random() < 0.3:  # 30% chance
                    exploit_key = random.choice(available_exploits)
                    exploit = self.create_exploit_item(exploit_key)
                    loot.append(exploit)
            
            logging.debug(f"Created balanced loot for level {level}: {len(loot)} items")
            
        except Exception as e:
            logging.error(f"Error creating balanced loot: {e}")
        
        return loot
    
    def _update_stats(self, entity_type: str) -> None:
        """Update creation statistics."""
        self._creation_stats[entity_type] = self._creation_stats.get(entity_type, 0) + 1
    
    def get_creation_stats(self) -> Dict[str, int]:
        """Get entity creation statistics."""
        return self._creation_stats.copy()
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a registered template."""
        if template_name not in self._templates:
            return None
        
        template = self._templates[template_name]
        return {
            "name": template_name,
            "entity_type": template.entity_type,
            "base_config": template.base_config,
            "modifier_count": len(template.modifiers),
            "creation_count": template.creation_count
        }
    
    def clear_stats(self) -> None:
        """Clear creation statistics."""
        self._creation_stats.clear()
        logging.debug("Cleared entity factory statistics")
    
    def reset(self) -> None:
        """Reset factory to initial state."""
        self._templates.clear()
        self._creation_stats.clear()
        self._custom_creators.clear()
        self._register_default_templates()
        logging.info("Entity factory reset to initial state")