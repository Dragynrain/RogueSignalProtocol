#!/usr/bin/env python3
"""
Test data management system for consistent test data across all tests.
Provides fixtures, sample data, and data generators for testing.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import tempfile


@dataclass
class GameTestData:
    """Container for test game data."""
    maps: Dict[str, Any]
    enemies: Dict[str, Any]
    exploits: Dict[str, Any]
    upgrades: Dict[str, Any]
    levels: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create from dictionary."""
        return cls(**data)


class GameTestDataManager:
    """Manages test data loading, generation, and persistence."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize with optional custom data directory."""
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self._cache = {}
    
    def get_sample_map_data(self) -> Dict[str, Any]:
        """Get sample map data for testing."""
        return {
            "small_room": {
                "width": 10,
                "height": 8,
                "tiles": [
                    "##########",
                    "#........#",
                    "#........#",
                    "#...G....#",
                    "#........#",
                    "#....P...#",
                    "#........#",
                    "##########"
                ],
                "legend": {
                    "#": "wall",
                    ".": "floor",
                    "G": "gateway",
                    "P": "player_start"
                }
            },
            "corridor": {
                "width": 20,
                "height": 5,
                "tiles": [
                    "####################",
                    "#..................#",
                    "#....P.....E.......#",
                    "#..................#",
                    "####################"
                ],
                "legend": {
                    "#": "wall",
                    ".": "floor",
                    "P": "player_start",
                    "E": "enemy_spawn"
                }
            },
            "complex_level": {
                "width": 25,
                "height": 15,
                "tiles": [
                    "#########################",
                    "#.......#...............#",
                    "#.......#...............#",
                    "#.......####............#",
                    "#...........#...........#",
                    "#####.......#...........#",
                    "#...........#...........#",
                    "#...........#...E.......#",
                    "#####.......#...........#",
                    "#...........#...........#",
                    "#...........#...........#",
                    "#...........#...........#",
                    "#.......####............#",
                    "#......P................#",
                    "#########################"
                ]
            }
        }
    
    def get_sample_enemy_data(self) -> Dict[str, Any]:
        """Get sample enemy data for testing."""
        return {
            "scanner": {
                "type": "scanner",
                "cpu": 50,
                "movement": "random",
                "vision_range": 5,
                "detection_chance": 0.7,
                "symbol": "S"
            },
            "guard": {
                "type": "guard", 
                "cpu": 75,
                "movement": "patrol",
                "vision_range": 4,
                "detection_chance": 0.8,
                "symbol": "G"
            },
            "admin": {
                "type": "admin",
                "cpu": 150,
                "movement": "seek",
                "vision_range": 8,
                "detection_chance": 0.95,
                "symbol": "A"
            }
        }
    
    def get_sample_exploit_data(self) -> Dict[str, Any]:
        """Get sample exploit data for testing."""
        return {
            "buffer_overflow": {
                "name": "Buffer Overflow",
                "base_damage": 25,
                "heat_cost": 15,
                "success_rate": 0.8,
                "description": "Exploits buffer overflow vulnerability"
            },
            "sql_injection": {
                "name": "SQL Injection",
                "base_damage": 30,
                "heat_cost": 20,
                "success_rate": 0.75,
                "description": "Injects malicious SQL commands"
            },
            "privilege_escalation": {
                "name": "Privilege Escalation",
                "base_damage": 40,
                "heat_cost": 30,
                "success_rate": 0.6,
                "description": "Escalates system privileges"
            }
        }
    
    def get_sample_upgrade_data(self) -> Dict[str, Any]:
        """Get sample upgrade data for testing."""
        return {
            "enhanced_vision": {
                "name": "Enhanced Vision",
                "effect": "vision_range_boost",
                "value": 2,
                "duration": 10,
                "description": "Increases vision range"
            },
            "heat_sink": {
                "name": "Heat Sink",
                "effect": "heat_reduction",
                "value": 20,
                "duration": 0,
                "description": "Reduces heat instantly"
            },
            "stealth_mode": {
                "name": "Stealth Mode",
                "effect": "detection_reduction",
                "value": 0.5,
                "duration": 8,
                "description": "Reduces detection chance"
            }
        }
    
    def get_test_level_data(self) -> Dict[str, Any]:
        """Get test level configurations."""
        return {
            "level_1": {
                "enemy_count": 3,
                "enemy_types": ["scanner", "guard"],
                "special_nodes": 2,
                "difficulty": "easy"
            },
            "level_3": {
                "enemy_count": 6,
                "enemy_types": ["scanner", "guard", "guard"],
                "special_nodes": 3,
                "difficulty": "medium"
            },
            "level_5": {
                "enemy_count": 8,
                "enemy_types": ["scanner", "guard", "guard", "admin"],
                "special_nodes": 4,
                "difficulty": "hard"
            }
        }
    
    def get_all_test_data(self) -> GameTestData:
        """Get all test data as a structured object."""
        return GameTestData(
            maps=self.get_sample_map_data(),
            enemies=self.get_sample_enemy_data(),
            exploits=self.get_sample_exploit_data(),
            upgrades=self.get_sample_upgrade_data(),
            levels=self.get_test_level_data()
        )
    
    def save_test_data(self, filename: str, data: Any) -> None:
        """Save test data to file."""
        file_path = self.data_dir / filename
        
        if isinstance(data, GameTestData):
            data = data.to_dict()
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_test_data(self, filename: str) -> Any:
        """Load test data from file."""
        file_path = self.data_dir / filename
        
        if filename in self._cache:
            return self._cache[filename]
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self._cache[filename] = data
        return data
    
    def create_temporary_save_file(self, save_data: Dict[str, Any]) -> str:
        """Create a temporary save file for testing."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        )
        
        json.dump(save_data, temp_file, indent=2)
        temp_file.close()
        
        return temp_file.name
    
    def cleanup_temporary_file(self, file_path: str) -> None:
        """Clean up temporary file."""
        try:
            os.unlink(file_path)
        except OSError:
            pass


class GameTestScenarioGenerator:
    """Generates test scenarios with varying complexity."""
    
    def __init__(self, data_manager: GameTestDataManager):
        self.data_manager = data_manager
    
    def generate_empty_level(self, width: int = 10, height: int = 8) -> Dict[str, Any]:
        """Generate an empty level for testing."""
        tiles = []
        
        for y in range(height):
            row = ""
            for x in range(width):
                if x == 0 or x == width-1 or y == 0 or y == height-1:
                    row += "#"  # Wall
                else:
                    row += "."  # Floor
            tiles.append(row)
        
        return {
            "width": width,
            "height": height,
            "tiles": tiles
        }
    
    def generate_level_with_enemies(self, enemy_count: int = 3) -> Dict[str, Any]:
        """Generate a level with specified number of enemies."""
        level = self.generate_empty_level(20, 12)
        
        # Add enemy spawn points
        enemy_positions = [
            (5, 5), (15, 5), (10, 8), (3, 9), (17, 9)
        ]
        
        tiles = list(level["tiles"])
        for i, (x, y) in enumerate(enemy_positions[:enemy_count]):
            row = list(tiles[y])
            row[x] = "E"
            tiles[y] = "".join(row)
        
        level["tiles"] = tiles
        return level
    
    def generate_save_game_data(self, level: int = 1, **kwargs) -> Dict[str, Any]:
        """Generate save game data for testing."""
        default_save = {
            "player": {
                "cpu": kwargs.get("cpu", 100),
                "heat": kwargs.get("heat", 0),
                "detection": kwargs.get("detection", 0),
                "position": {"x": 5, "y": 5},
                "inventory": [],
                "temporary_effects": {}
            },
            "game_state": {
                "level": level,
                "turn": kwargs.get("turn", 0),
                "game_over": False,
                "admin_spawned": False
            },
            "enemies": kwargs.get("enemies", []),
            "discovered_codes": kwargs.get("discovered_codes", []),
            "map_data": self.generate_empty_level()
        }
        
        return default_save
    
    def generate_corrupted_save_data(self) -> Dict[str, Any]:
        """Generate intentionally corrupted save data for testing."""
        return {
            "player": {
                "cpu": "invalid",  # Should be int
                "position": {"x": "not_a_number"},  # Invalid position
                "inventory": "not_a_list"  # Should be list
            },
            "game_state": {
                "level": -1,  # Invalid level
                "turn": None  # Invalid turn
            }
        }


# Global test data manager instance
_test_data_manager = GameTestDataManager()

# Convenience functions for easy access
def get_test_data() -> GameTestData:
    """Get all test data."""
    return _test_data_manager.get_all_test_data()

def get_sample_maps() -> Dict[str, Any]:
    """Get sample map data."""
    return _test_data_manager.get_sample_map_data()

def get_sample_enemies() -> Dict[str, Any]:
    """Get sample enemy data."""
    return _test_data_manager.get_sample_enemy_data()

def create_temp_save(save_data: Dict[str, Any]) -> str:
    """Create temporary save file."""
    return _test_data_manager.create_temporary_save_file(save_data)

def cleanup_temp_file(file_path: str) -> None:
    """Clean up temporary file."""
    _test_data_manager.cleanup_temporary_file(file_path)

# Test data generators
scenario_generator = GameTestScenarioGenerator(_test_data_manager)

def generate_test_level(**kwargs) -> Dict[str, Any]:
    """Generate test level."""
    return scenario_generator.generate_empty_level(**kwargs)

def generate_save_data(**kwargs) -> Dict[str, Any]:
    """Generate save data."""
    return scenario_generator.generate_save_game_data(**kwargs)