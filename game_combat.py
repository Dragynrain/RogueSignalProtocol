#!/usr/bin/env python3
"""
Rogue Signal Protocol - Combat System
Handles exploit usage, targeting, and combat effects.
"""

from typing import TYPE_CHECKING

# Import required modules
from game_config import GameConfig, GameBalance
from game_entities import Position, TargetingMode, ExploitDefinition, EnemyMovement, EnemyState
from game_data import GameData

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    pass


class ExploitSystem:
    """Handles exploit usage and effects."""
    
    def __init__(self, game):
        self.game = game
    
    def use_exploit(self, exploit_key: str) -> bool:
        """Attempt to use an exploit."""
        if exploit_key not in self.game.player.inventory_manager.equipped_exploits:
            self.game.message_log.add_message("Exploit not equipped")
            return False
        
        exploit = GameData.EXPLOITS[exploit_key]
        
        # Check heat limit - allow overclocking with confirmation
        heat_cost = self._calculate_heat_cost(exploit)
        if self.game.player.heat + heat_cost > 100:
            # Calculate overclock damage
            overclock_damage = (self.game.player.heat + heat_cost) - 100
            if (hasattr(self.game, 'overclock_confirmation') and self.game.overclock_confirmation and 
                hasattr(self.game, 'overclock_exploit') and self.game.overclock_exploit == exploit_key):
                # Confirmed, apply overclock damage
                self.game.overclock_confirmation = False
                actual_damage = self.game.player.take_damage(overclock_damage)
                self.game.message_log.add_message(f"OVERCLOCKING: {actual_damage} CPU damage!")
                self.game.sound_manager.play_sound("overclocking")
                # Set heat to 100 (not over)
                self.game.player.heat = 100
            else:
                # Need confirmation
                self.game.sound_manager.play_sound("exploit_failed")
                self.game.message_log.add_message(f"Overclocking required: {overclock_damage} CPU damage. Press exploit key again to confirm.")
                self.game.overclock_confirmation = True
                self.game.overclock_exploit = exploit_key
                return False
        
        # Check if exploit requires targeting

        if exploit.targeting != TargetingMode.NONE and exploit.range > 0:
            self.game.sound_manager.play_sound("exploit_targeting")
            self.game.targeting_mode = True
            self.game.targeting_exploit = exploit_key
            self.game.cursor_position = Position(self.game.player.x, self.game.player.y)
            self.game.message_log.add_message(f"Targeting {exploit.name}")
            return True
        
        # Execute non-targeting exploits immediately

        return self.execute_exploit(exploit_key, self.game.player.position)
    
    def execute_exploit(self, exploit_key: str, target: Position) -> bool:
        """Execute an exploit at target location."""
        if exploit_key not in GameData.EXPLOITS:
            self.game.message_log.add_message("Unknown exploit")
            return False
        
        exploit = GameData.EXPLOITS[exploit_key]

        # Validate target
        if not self._validate_target(exploit, target):
            return False
        
        # Execute specific exploit
        success = self._execute_specific_exploit(exploit_key, exploit, target)
        
        # Only apply heat cost if the exploit was successful
        if success:
            heat_cost = self._calculate_heat_cost(exploit)
            self.game.player.heat = min(100, self.game.player.heat + heat_cost)
        
        if success:
            self.game.targeting_mode = False
            self.game.targeting_exploit = None
            self.game.maybe_process_turn()
        
        return success
    
    def _calculate_heat_cost(self, exploit: ExploitDefinition) -> int:
        """Calculate heat cost with efficiency bonus."""
        multiplier = 0.6 if self.game.player.temporary_effects['exploit_efficiency_turns'] > 0 else 1.0
        return int(exploit.heat * multiplier)
    
    def _validate_target(self, exploit: ExploitDefinition, target: Position) -> bool:
        """Validate targeting for exploit."""
        if not target.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
            self.game.message_log.add_message("Invalid target location")
            return False
        
        distance = self.game.player.position.distance_to(target)
        if distance > exploit.range:
            self.game.message_log.add_message(f"Out of range (Max: {exploit.range})")
            return False
        
        return True

    
    def _execute_specific_exploit(self, exploit_key: str, exploit: ExploitDefinition, target: Position) -> bool:
        """Execute the specific exploit effect."""
        if exploit_key == 'shadow_step':
            return self._execute_shadow_step(target)
        elif exploit_key == 'data_mimic':
            return self._execute_data_mimic()
        elif exploit_key == 'noise_maker':
            return self._execute_noise_maker(target)
        elif exploit_key == 'code_injection':
            return self._execute_code_injection(target)
        elif exploit_key == 'buffer_overflow':
            return self._execute_buffer_overflow(target)
        elif exploit_key == 'system_crash':
            return self._execute_system_crash(target, exploit.range)
        elif exploit_key == 'threat_scan':
            return self._execute_threat_scan()
        elif exploit_key == 'log_wiper':
            return self._execute_log_wiper()
        elif exploit_key == 'antivirus':
            return self._execute_antivirus()
        elif exploit_key == 'denial_of_service':
            return self._execute_denial_of_service(target, exploit.range)
        elif exploit_key == 'memory_leak':
            return self._execute_memory_leak(target)
        elif exploit_key == 'network_scan':
            return self._execute_network_scan()
        
        return False
    
    def _execute_shadow_step(self, target: Position) -> bool:
        """Execute shadow step exploit."""
        if self.game.game_map.is_shadow(target) and self.game.game_map.is_valid_position(target):
            if not self.game._get_enemy_at(target):
                self.game.sound_manager.play_sound("exploit_shadow_step")
                self.game.player.position = target
                self.game.message_log.add_message("Shadow Step executed")
                return True
            else:
                self.game.message_log.add_message("Target occupied")
        else:
            self.game.message_log.add_message("Must target shadow zone")
        return False
    
    def _execute_data_mimic(self) -> bool:
        """Execute data mimic exploit."""
        self.game.sound_manager.play_sound("exploit_data_mimic")
        self.game.player.temporary_effects['data_mimic_turns'] = 5
        self.game.message_log.add_message("Data Mimic active")
        return True
    
    def _execute_noise_maker(self, target: Position) -> bool:
        """Execute noise maker exploit."""
        self.game.sound_manager.play_sound("exploit_noise_maker")
        exploit = GameData.EXPLOITS['noise_maker']
        attracted = 0
        for enemy in self.game.enemies:
            if (enemy.type_data.movement in [EnemyMovement.SEEK, EnemyMovement.RANDOM, EnemyMovement.PATROL] and
                enemy.position.distance_to(target) <= exploit.effect_radius):
                if enemy.type_data.movement == EnemyMovement.PATROL:
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 3
                else:
                    enemy.last_seen_player = target
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 2
                attracted += 1
        self.game.message_log.add_message(f"Noise: {attracted} enemies attracted")
        return True
    
    def _damage_enemy(self, enemy, damage: int) -> bool:
        """Apply damage to enemy and handle elimination/hostility."""
        if enemy.take_damage(damage):
            self.game.enemies.remove(enemy)
            self.game.player.cpu = min(self.game.player.max_cpu, self.game.player.cpu + GameBalance.ENEMY_ELIMINATION_CPU_REWARD)
            self.game.message_log.add_message(f"Eliminated {enemy.type_data.name}")
        else:
            self.game.message_log.add_message(f"{enemy.type_data.name} damaged")
            if enemy.type_data.movement == EnemyMovement.PATROL and enemy.patrol_points:
                enemy.original_patrol_index = enemy.patrol_index
            enemy.state = EnemyState.HOSTILE
            enemy.last_seen_player = Position(self.game.player.x, self.game.player.y)
        return True

    def _execute_code_injection(self, target: Position) -> bool:
        """Execute code injection exploit."""
        self.game.sound_manager.play_sound("exploit_code_injection")
        enemy = self.game._get_enemy_at(target)
        if not enemy:
            self.game.message_log.add_message("No target at location")
            return False

        damage = 35 if enemy.type == 'firewall' else 30
        return self._damage_enemy(enemy, damage)

    def _execute_buffer_overflow(self, target: Position) -> bool:
        """Execute buffer overflow exploit."""
        self.game.sound_manager.play_sound("exploit_buffer_overflow")
        # Check if target is within range-1 (including diagonals, distance <= 1.5)
        distance = self.game.player.position.distance_to(target)
        if distance > GameBalance.ADJACENT_DISTANCE_THRESHOLD:
            self.game.message_log.add_message("Must target adjacent enemy")
            return False

        enemy = self.game._get_enemy_at(target)
        if not enemy:
            self.game.message_log.add_message("No enemy at target")
            return False

        return self._damage_enemy(enemy, 50)
    
    def _disable_area_enemies(self, target: Position, radius: int, duration: int) -> int:
        """Disable enemies in area for the specified duration and return count."""
        count = 0
        for enemy in self.game.enemies:
            if enemy.position.distance_to(target) <= radius:
                enemy.disabled_turns = duration
                enemy.state = EnemyState.UNAWARE
                enemy.alert_timer = 0
                count += 1
        return count

    def _execute_system_crash(self, target: Position, exploit_range: int) -> bool:
        """Execute system crash exploit - untargeted AoE around player."""
        self.game.sound_manager.play_sound("exploit_system_crash")
        # System Crash is an emergency untargeted AoE centered on player
        exploit = GameData.EXPLOITS['system_crash']
        player_pos = self.game.player.position
        count = 0
        for enemy in self.game.enemies:
            if enemy.position.distance_to(player_pos) <= exploit.effect_radius:
                enemy.disabled_turns = exploit.stun_duration
                enemy.state = EnemyState.UNAWARE
                enemy.alert_timer = 0
                count += 1
        self.game.message_log.add_message(f"System crash: {count} disabled")
        return True
    
    def _execute_threat_scan(self) -> bool:
        """Execute threat scan exploit."""
        self.game.sound_manager.play_sound("exploit_threat_scan")
        self.game.game_state.threat_scan_turns = 5  # Extended duration for tactical advantage
        
        # Threat scan reveals only enemy positions and immediate surroundings, not entire map
        enemy_count = 0
        for enemy in self.game.enemies:
            # Update enemy position in memory
            self.game.game_map.last_known_enemy_positions[enemy.id] = (enemy.position, self.game.turn)
            
            # Reveal a small area around each enemy (3x3) to show their local context
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    reveal_x = enemy.position.x + dx
                    reveal_y = enemy.position.y + dy
                    if (0 <= reveal_x < GameConfig.MAP_WIDTH and 
                        0 <= reveal_y < GameConfig.MAP_HEIGHT):
                        self.game.game_map.explored_tiles.add((reveal_x, reveal_y))
            enemy_count += 1
        
        self.game.message_log.add_message(f"THREAT SCAN ACTIVE - {enemy_count} hostiles detected!")
        return True

    def _execute_log_wiper(self) -> bool:
        """Execute log wiper exploit."""
        self.game.sound_manager.play_sound("exploit_log_wiper")
        old_trace = self.game.player.trace_level
        self.game.player.trace_level = max(0, self.game.player.trace_level - 30)
        actual_reduction = old_trace - self.game.player.trace_level
        self.game.message_log.add_message(f"Trace Level: -{actual_reduction:.1f}%")
        return True
    
    def _execute_antivirus(self) -> bool:
        """Execute antivirus exploit - purges negative status effects."""
        self.game.sound_manager.play_sound("exploit_antivirus")
        
        # Check if player has any negative effects to cure
        negative_effects = ['virus_turns', 'movement_slowed_turns']
        effects_cured = []
        
        for effect in negative_effects:
            if self.game.player.temporary_effects.get(effect, 0) > 0:
                effects_cured.append(effect)
                self.game.player.temporary_effects[effect] = 0
        
        if effects_cured:
            if 'virus_turns' in effects_cured:
                self.game.message_log.add_message("Virus purged from system")
            if 'movement_slowed_turns' in effects_cured:
                self.game.message_log.add_message("Movement inhibition removed")
            self.game.message_log.add_message("System cleansed of negative effects")
        else:
            self.game.message_log.add_message("No negative effects detected")
        
        return True
    
    def _execute_denial_of_service(self, target: Position, exploit_range: int) -> bool:
        """Execute Denial of Service exploit."""
        self.game.sound_manager.play_sound("exploit_denial_of_service")
        # Denial of Service uses configured effect_radius at the target location
        exploit = GameData.EXPLOITS['denial_of_service']
        count = self._disable_area_enemies(target, exploit.effect_radius, exploit.stun_duration)
        self.game.message_log.add_message(f"DoS: {count} disabled")
        return True
    
    def _execute_memory_leak(self, target: Position) -> bool:
        """Execute memory leak exploit - makes enemies forget they saw the player."""
        self.game.sound_manager.play_sound("exploit_memory_leak")
        exploit = GameData.EXPLOITS['memory_leak']
        count = 0
        for enemy in self.game.enemies:
            if enemy.position.distance_to(target) <= exploit.effect_radius:
                enemy.state = EnemyState.UNAWARE
                enemy.last_seen_player = None
                enemy.alert_timer = 0
                count += 1

        msg = f"Memory Leak: {count} enemies confused" if count > 0 else "No enemies in range"
        self.game.message_log.add_message(msg)
        return True
    
    def _execute_network_scan(self) -> bool:
        """Execute network scan exploit - reveals all special nodes on the level."""
        self.game.sound_manager.play_sound("exploit_network_scan")

        # Add all special nodes to revealed dict
        if not hasattr(self.game.game_state, 'revealed_special_nodes'):
            self.game.game_state.revealed_special_nodes = {}

        # Count nodes on the map for debugging
        cooling_count = len(self.game.game_map.cooling_nodes)
        cpu_count = len(self.game.game_map.cpu_recovery_nodes)
        ghost_count = len(self.game.game_map.ghost_nodes)

        # Reveal all cooling nodes and add to explored tiles
        for node_pos in self.game.game_map.cooling_nodes:
            self.game.game_state.revealed_special_nodes[node_pos] = "cooling"
            # Add surrounding 3x3 area to explored tiles so node is visible in fog of war
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    explore_x = node_pos[0] + dx
                    explore_y = node_pos[1] + dy
                    if (0 <= explore_x < GameConfig.MAP_WIDTH and
                        0 <= explore_y < GameConfig.MAP_HEIGHT):
                        self.game.game_map.explored_tiles.add((explore_x, explore_y))

        # Reveal all CPU recovery nodes and add to explored tiles
        for node_pos in self.game.game_map.cpu_recovery_nodes:
            self.game.game_state.revealed_special_nodes[node_pos] = "cpu"
            # Add surrounding 3x3 area to explored tiles
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    explore_x = node_pos[0] + dx
                    explore_y = node_pos[1] + dy
                    if (0 <= explore_x < GameConfig.MAP_WIDTH and
                        0 <= explore_y < GameConfig.MAP_HEIGHT):
                        self.game.game_map.explored_tiles.add((explore_x, explore_y))

        # Reveal all ghost nodes and add to explored tiles
        for node_pos in self.game.game_map.ghost_nodes:
            self.game.game_state.revealed_special_nodes[node_pos] = "ghost"
            # Add surrounding 3x3 area to explored tiles
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    explore_x = node_pos[0] + dx
                    explore_y = node_pos[1] + dy
                    if (0 <= explore_x < GameConfig.MAP_WIDTH and
                        0 <= explore_y < GameConfig.MAP_HEIGHT):
                        self.game.game_map.explored_tiles.add((explore_x, explore_y))

        total_revealed = len(self.game.game_state.revealed_special_nodes)
        self.game.message_log.add_message(f"Network Scan: {cooling_count} cooling, {cpu_count} CPU, {ghost_count} ghost nodes found")
        self.game.message_log.add_message(f"Total {total_revealed} special nodes revealed")
        return True