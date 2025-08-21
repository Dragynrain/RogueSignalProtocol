#!/usr/bin/env python3
"""
Integration module to connect the JSON data loader with the main game
This replaces hardcoded constants with data-driven configurations
"""

from typing import Dict, Any, Optional, List
from data_loader import DataManager, GameDataLoader
import logging

class GameDataIntegration:
    """
    Integration layer between JSON data and game systems
    Provides backwards compatibility while enabling data-driven configuration
    """
    
    def __init__(self, data_directory: str = "data"):
        self.data_manager = DataManager(data_directory)
        self.logger = logging.getLogger("GameDataIntegration")
        
        # Cache converted data for performance
        self._enemy_types_cache = None
        self._exploits_cache = None
        self._network_configs_cache = None
        
    def get_enemy_types(self) -> Dict[str, Any]:
        """Get enemy types in the format expected by the game"""
        if self._enemy_types_cache is None:
            self._enemy_types_cache = self._convert_enemy_types()
        return self._enemy_types_cache
    
    def get_exploits(self) -> Dict[str, Any]:
        """Get exploits in the format expected by the game"""
        if self._exploits_cache is None:
            self._exploits_cache = self._convert_exploits()
        return self._exploits_cache
    
    def get_network_configs(self) -> Dict[int, Any]:
        """Get network configurations in the format expected by the game"""
        if self._network_configs_cache is None:
            self._network_configs_cache = self._convert_network_configs()
        return self._network_configs_cache
    
    def _convert_enemy_types(self) -> Dict[str, Any]:
        """Convert JSON enemy data to game format"""
        json_enemies = self.data_manager.get_data("enemies", "enemy_types") or {}
        
        converted = {}
        for enemy_id, enemy_data in json_enemies.items():
            # Convert JSON format to dataclass-like format expected by game
            from rogue_signal import EnemyMovement
            
            movement_map = {
                "static": EnemyMovement.STATIC,
                "linear": EnemyMovement.LINEAR,
                "random": EnemyMovement.RANDOM,
                "seek": EnemyMovement.SEEK,
                "track": EnemyMovement.TRACK
            }
            
            converted[enemy_id] = type('EnemyType', (), {
                'symbol': enemy_data.get('symbol', '?'),
                'cpu': enemy_data.get('cpu', 20),
                'vision': enemy_data.get('vision', 2),
                'movement': movement_map.get(enemy_data.get('movement', 'static'), EnemyMovement.STATIC),
                'name': enemy_data.get('name', enemy_id.title()),
                'armor': enemy_data.get('armor', 0),
                'damage_reduction': enemy_data.get('damage_reduction', 0)
            })()
        
        return converted
    
    def _convert_exploits(self) -> Dict[str, Any]:
        """Convert JSON exploit data to game format"""
        json_exploits = self.data_manager.get_data("exploits", "exploits") or {}
        
        converted = {}
        for exploit_id, exploit_data in json_exploits.items():
            # Convert JSON format to dataclass-like format expected by game
            from rogue_signal import TargetingMode
            
            targeting_map = {
                "none": TargetingMode.NONE,
                "single": TargetingMode.SINGLE,
                "area": TargetingMode.AREA,
                "direction": TargetingMode.DIRECTION
            }
            
            converted[exploit_id] = type('ExploitDef', (), {
                'name': exploit_data.get('name', exploit_id.title()),
                'ram': exploit_data.get('ram', 1),
                'heat': exploit_data.get('heat', 10),
                'range': exploit_data.get('range', 0),
                'exploit_type': exploit_data.get('category', 'utility'),
                'targeting': targeting_map.get(exploit_data.get('targeting', 'none'), TargetingMode.NONE),
                'description': exploit_data.get('description', '')
            })()
        
        return converted
    
    def _convert_network_configs(self) -> Dict[int, Any]:
        """Convert JSON network data to game format"""
        json_networks = self.data_manager.get_data("networks", "network_configs") or {}
        
        converted = {}
        for level_str, network_data in json_networks.items():
            try:
                level = int(level_str)
                enemy_config = network_data.get('enemy_config', {})
                terrain = network_data.get('terrain', {})
                
                converted[level] = {
                    'name': network_data.get('name', f'Level {level}'),
                    'enemies': enemy_config.get('total_enemies', 1),
                    'shadow_coverage': terrain.get('shadow_coverage', 0.3),
                    'spawn_threshold': network_data.get('admin_avatar', {}).get('spawn_threshold', 100)
                }
            except ValueError:
                self.logger.warning(f"Invalid level key: {level_str}")
        
        return converted
    
    def get_balance_config(self) -> Dict[str, Any]:
        """Get balance configuration"""
        return self.data_manager.get_data("balance") or {}
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return self.data_manager.get_data("ui") or {}
    
    def get_items_config(self) -> Dict[str, Any]:
        """Get items configuration"""
        return self.data_manager.get_data("items") or {}
    
    def reload_all_data(self) -> bool:
        """Reload all data and clear caches"""
        success = self.data_manager.reload_data()
        if success:
            # Clear caches to force regeneration
            self._enemy_types_cache = None
            self._exploits_cache = None
            self._network_configs_cache = None
            self.logger.info("Game data reloaded successfully")
        return success
    
    def get_starting_exploits(self) -> List[str]:
        """Get list of starting exploits for new game"""
        balance = self.get_balance_config()
        starting = balance.get('player_stats', {}).get('starting_exploits', [])
        
        # Fallback to default if not specified
        if not starting:
            starting = ['shadow_step', 'network_scan', 'code_injection']
        
        return starting
    
    def get_admin_spawn_threshold(self, level: int) -> int:
        """Get admin spawn threshold for specific level"""
        balance = self.get_balance_config()
        thresholds = balance.get('detection_system', {}).get('admin_spawn_thresholds', {})
        
        level_names = {0: 'tutorial', 1: 'corporate', 2: 'government', 3: 'military'}
        level_name = level_names.get(level, 'tutorial')
        
        return thresholds.get(level_name, 100)
    
    def get_player_starting_stats(self) -> Dict[str, Any]:
        """Get player starting statistics"""
        balance = self.get_balance_config()
        return balance.get('player_stats', {}).get('starting_stats', {
            'cpu': 100,
            'max_cpu': 100,
            'heat': 0,
            'detection': 0,
            'ram_total': 8,
            'ram_used': 0
        })
    
    def get_combat_config(self) -> Dict[str, Any]:
        """Get combat configuration"""
        balance = self.get_balance_config()
        return balance.get('combat_balance', {})
    
    def validate_data_integrity(self) -> bool:
        """Validate that all required data is present and valid"""
        try:
            # Check essential data
            enemy_types = self.get_enemy_types()
            exploits = self.get_exploits()
            networks = self.get_network_configs()
            
            if not enemy_types:
                self.logger.error("No enemy types loaded")
                return False
            
            if not exploits:
                self.logger.error("No exploits loaded")
                return False
            
            if not networks:
                self.logger.error("No network configurations loaded")
                return False
            
            # Check that tutorial level exists
            if 0 not in networks:
                self.logger.error("Tutorial network (level 0) not found")
                return False
            
            self.logger.info("Data integrity validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Data integrity validation failed: {e}")
            return False


# Global integration instance for easy access
_game_data_integration = None

def get_game_data() -> GameDataIntegration:
    """Get global game data integration instance"""
    global _game_data_integration
    if _game_data_integration is None:
        _game_data_integration = GameDataIntegration()
    return _game_data_integration

def initialize_game_data(data_directory: str = "data") -> bool:
    """Initialize game data integration"""
    global _game_data_integration
    try:
        _game_data_integration = GameDataIntegration(data_directory)
        return _game_data_integration.validate_data_integrity()
    except Exception as e:
        print(f"Failed to initialize game data: {e}")
        return False

# Backward compatibility functions for existing game code
def get_enemy_types():
    """Backward compatibility: Get enemy types"""
    return get_game_data().get_enemy_types()

def get_exploits():
    """Backward compatibility: Get exploits"""
    return get_game_data().get_exploits()

def get_network_configs():
    """Backward compatibility: Get network configs"""
    return get_game_data().get_network_configs()

def get_admin_spawn_thresholds():
    """Backward compatibility: Get admin spawn thresholds"""
    data = get_game_data()
    return {
        level: data.get_admin_spawn_threshold(level)
        for level in range(4)
    }


if __name__ == "__main__":
    # Test the integration
    print("Testing Game Data Integration...")
    
    try:
        integration = GameDataIntegration()
        
        print("✅ Integration initialized")
        
        # Test data loading
        enemy_types = integration.get_enemy_types()
        print(f"✅ Loaded {len(enemy_types)} enemy types")
        
        exploits = integration.get_exploits()
        print(f"✅ Loaded {len(exploits)} exploits")
        
        networks = integration.get_network_configs()
        print(f"✅ Loaded {len(networks)} network configs")
        
        # Test validation
        if integration.validate_data_integrity():
            print("✅ Data integrity validation passed")
        else:
            print("❌ Data integrity validation failed")
        
        print("\n🎮 Sample Data:")
        
        # Show some enemy data
        for i, (enemy_id, enemy_data) in enumerate(list(enemy_types.items())[:3]):
            print(f"  Enemy: {enemy_id} - {enemy_data.name} (CPU: {enemy_data.cpu})")
        
        # Show some exploit data
        for i, (exploit_id, exploit_data) in enumerate(list(exploits.items())[:3]):
            print(f"  Exploit: {exploit_id} - {exploit_data.name} (Heat: {exploit_data.heat})")
        
        # Show network data
        for level, network_data in networks.items():
            print(f"  Network {level}: {network_data['name']} ({network_data['enemies']} enemies)")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
