#!/usr/bin/env python3
"""
Rogue Signal Protocol - Combat System

Handles exploit usage, targeting, and combat effects.
Manages all exploit execution including:
- Heat cost calculation and overclocking
- Targeting validation and confirmation
- Individual exploit effects (damage, stun, buffs, debuffs)
- Sound effects and message log updates
"""

import logging
from typing import TYPE_CHECKING

# Import required modules
from game_config import GameConfig, GameBalance
from game_entities import Position, TargetingMode, ExploitDefinition, EnemyMovement, EnemyState
from game_data import GameData

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    pass


class ExploitSystem:
    """
    Handles exploit usage and effects.

    Coordinates exploit execution by validating requirements, calculating costs,
    executing effects, and processing turns. Each exploit type has its own
    _execute_* method with specific logic.
    """

    def __init__(self, game):
        """
        Initialize exploit system with reference to game engine.

        Args:
            game: GameEngine instance for accessing player, enemies, map, etc.
        """
        self.game = game

        # Exploit handler dispatch table
        # Lambdas normalize different handler signatures (no params, target only, target + range)
        self.exploit_handlers = {
            'shadow_step': lambda exploit, target: self._execute_shadow_step(target),
            'data_mimic': lambda exploit, target: self._execute_data_mimic(),
            'noise_maker': lambda exploit, target: self._execute_noise_maker(target),
            'code_injection': lambda exploit, target: self._execute_code_injection(target),
            'buffer_overflow': lambda exploit, target: self._execute_buffer_overflow(target),
            'system_crash': lambda exploit, target: self._execute_system_crash(target, exploit.range),
            'threat_scan': lambda exploit, target: self._execute_threat_scan(),
            'log_wiper': lambda exploit, target: self._execute_log_wiper(),
            'antivirus': lambda exploit, target: self._execute_antivirus(),
            'denial_of_service': lambda exploit, target: self._execute_denial_of_service(target, exploit.range),
            'memory_leak': lambda exploit, target: self._execute_memory_leak(target),
            'network_scan': lambda exploit, target: self._execute_network_scan(),
        }
    
    def use_exploit(self, exploit_key: str) -> bool:
        """
        Attempt to use an equipped exploit.

        Validates exploit is equipped, checks heat limits, and shows overclock
        warning if needed. Enters targeting mode for ranged exploits or executes
        immediately for self-targeted effects.

        Args:
            exploit_key: Unique identifier for the exploit (e.g., 'shadow_step')

        Returns:
            True if exploit was used/entered targeting, False if failed validation
        """
        if exploit_key not in self.game.player.inventory_manager.equipped_exploits:
            self.game.message_log.add_message("Exploit not equipped")
            return False

        exploit = GameData.EXPLOITS[exploit_key]

        # Check heat limit - show overclock warning dialogue
        heat_cost = self._calculate_heat_cost(exploit)
        logging.debug(f"Combat: Player attempting exploit '{exploit.name}', heat={self.game.player.heat}/{self.game.player.max_heat}, cost={heat_cost}")
        if self.game.player.heat + heat_cost > self.game.player.max_heat:
            # Calculate overclock damage
            overheat_amount = (self.game.player.heat + heat_cost) - self.game.player.max_heat
            cpu_damage = overheat_amount  # 1:1 ratio

            # Calculate remaining CPU after damage
            remaining_cpu = self.game.player.cpu - cpu_damage

            # Show overclock warning dialogue with exact calculations
            from game_dialogue_system import create_overclock_warning_dialogue
            dialogue = create_overclock_warning_dialogue(
                exploit_name=exploit.name,
                overheat_amount=overheat_amount,
                damage=cpu_damage,
                remaining_cpu=remaining_cpu,
                max_cpu=self.game.player.max_cpu
            )
            self.game.dialogue_state.show(dialogue)

            # Play warning sound
            self.game.sound_manager.play_sound("exploit_failed")
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
        """
        Execute an exploit at target location.

        Validates target position and range, executes the exploit-specific effect,
        applies heat cost (with potential overclocking damage), and processes turn.

        Args:
            exploit_key: Unique identifier for the exploit
            target: Target position for the exploit

        Returns:
            True if exploit executed successfully, False otherwise
        """
        if exploit_key not in GameData.EXPLOITS:
            self.game.message_log.add_message("Unknown exploit")
            return False

        exploit = GameData.EXPLOITS[exploit_key]

        # Validate target
        if not self._validate_target(exploit, target):
            logging.debug(f"Combat: Exploit '{exploit.name}' failed validation for target ({target.x},{target.y})")
            return False

        logging.debug(f"Combat: Executing exploit '{exploit.name}' on target ({target.x},{target.y})")

        # Execute specific exploit
        success = self._execute_specific_exploit(exploit_key, exploit, target)

        # Only apply heat cost if the exploit was successful
        if success:
            heat_cost = self._calculate_heat_cost(exploit)
            new_heat = self.game.player.heat + heat_cost

            # Track metrics
            from game_metrics import track
            track("exploits_used", category=exploit_key)
            track("heat_generated", amount=heat_cost)

            # Check if this will cause overheating
            if new_heat > self.game.player.max_heat:
                # Apply overclock damage (confirmed via dialogue)
                overheat_amount = new_heat - self.game.player.max_heat
                actual_damage = self.game.player.take_damage(overheat_amount)
                logging.debug(f"Combat: OVERCLOCKING! overheat={overheat_amount}, damage={actual_damage}, heat capped at {self.game.player.max_heat}")
                self.game.message_log.add_message(f"OVERCLOCKING: {actual_damage} CPU damage!")
                self.game.sound_manager.play_sound("overclocking")
                # Set heat to max (not over)
                self.game.player.heat = self.game.player.max_heat
            else:
                # Normal heat application
                old_heat = self.game.player.heat
                self.game.player.heat = new_heat
                logging.debug(f"Combat: Heat applied for '{exploit.name}': {old_heat} -> {new_heat} (+{heat_cost})")

        if success:
            self.game.targeting_mode = False
            self.game.targeting_exploit = None
            self.game.maybe_process_turn()

        return success
    
    def _calculate_heat_cost(self, exploit: ExploitDefinition) -> int:
        """
        Calculate heat cost with exploit efficiency bonus.

        Exploit efficiency reduces heat cost by 40% (60% of original cost).

        Args:
            exploit: Exploit definition with base heat cost

        Returns:
            Final heat cost after efficiency bonus
        """
        multiplier = 0.6 if self.game.player.temporary_effects['exploit_efficiency_turns'] > 0 else 1.0
        return int(exploit.heat * multiplier)

    def _validate_target(self, exploit: ExploitDefinition, target: Position) -> bool:
        """
        Validate targeting for exploit.

        Checks that target is within map bounds and within exploit's range.

        IMPORTANT: Uses grid distance (Chebyshev), NOT Euclidean distance!
        This means diagonals count as range 1, allowing range-1 exploits
        like Buffer Overflow to target all 8 adjacent tiles.

        Args:
            exploit: Exploit definition with range limit
            target: Target position

        Returns:
            True if target is valid, False otherwise
        """
        if not target.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
            self.game.message_log.add_message("Invalid target location")
            return False

        # Use grid distance so diagonals count as 1 for gameplay purposes
        distance = self.game.player.position.grid_distance_to(target)
        if distance > exploit.range:
            self.game.message_log.add_message(f"Out of range (Max: {exploit.range})")
            return False

        return True

    def _execute_specific_exploit(self, exploit_key: str, exploit: ExploitDefinition, target: Position) -> bool:
        """
        Execute the specific exploit effect by dispatching to appropriate handler.

        Uses dictionary dispatch to route to the correct _execute_* method based on exploit_key.
        Each exploit has unique mechanics defined in its handler method.

        Args:
            exploit_key: Unique identifier for the exploit
            exploit: Exploit definition with stats
            target: Target position

        Returns:
            True if exploit executed successfully, False otherwise
        """
        handler = self.exploit_handlers.get(exploit_key)
        if handler:
            return handler(exploit, target)
        return False
    
    def _execute_shadow_step(self, target: Position) -> bool:
        """
        Execute Shadow Step exploit - teleport to shadow zone.

        Instantly moves player to target position if it's in a shadow zone,
        not occupied by an enemy, and is a valid walkable tile.

        Args:
            target: Target shadow position

        Returns:
            True if teleport succeeded, False if target invalid
        """
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
        """
        Execute Data Mimic exploit - grant temporary invisibility.

        Makes player invisible to enemies for the duration specified in JSON config.
        Enemies cannot see or pursue an invisible player.

        Returns:
            True (always succeeds)
        """
        self.game.sound_manager.play_sound("exploit_data_mimic")
        exploit = GameData.EXPLOITS['data_mimic']
        self.game.player.temporary_effects['data_mimic_turns'] = exploit.effect_duration
        self.game.message_log.add_message("Data Mimic active")
        return True
    
    def _execute_noise_maker(self, target: Position) -> bool:
        """
        Execute Noise Maker exploit - create distraction to lure enemies.

        Attracts nearby enemies (within effect_radius) to the target location.
        PATROL enemies become ALERT for 3 turns, others get last_seen_player set
        to target and become ALERT for 2 turns. Does not affect STATIC enemies.

        Uses grid distance so diagonals count as 1 for consistent gameplay.

        Args:
            target: Location of the noise

        Returns:
            True (always succeeds), displays count of attracted enemies
        """
        self.game.sound_manager.play_sound("exploit_noise_maker")
        exploit = GameData.EXPLOITS['noise_maker']
        attracted = 0
        for enemy in self.game.enemies:
            movement_type = enemy.get_movement_type()
            # Use grid distance for AoE radius (diagonals = 1)
            if (movement_type in [EnemyMovement.SEEK, EnemyMovement.RANDOM, EnemyMovement.PATROL] and
                enemy.position.grid_distance_to(target) <= exploit.effect_radius):
                if movement_type == EnemyMovement.PATROL:
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
        """
        Apply damage to enemy and handle elimination/hostility.

        If enemy is eliminated, removes it and grants CPU reward.
        If enemy survives, makes it HOSTILE and aware of player position.
        Preserves patrol state for PATROL enemies before they become hostile.

        Args:
            enemy: Enemy to damage
            damage: Amount of damage to apply

        Returns:
            True (always succeeds)
        """
        if enemy.take_damage(damage):
            self.game.enemies.remove(enemy)
            self.game.player.cpu = min(self.game.player.max_cpu, self.game.player.cpu + GameBalance.ENEMY_ELIMINATION_CPU_REWARD)
            logging.debug(f"Combat: Enemy {enemy.type_data.name}@({enemy.x},{enemy.y}) ELIMINATED, CPU reward={GameBalance.ENEMY_ELIMINATION_CPU_REWARD}")
            self.game.message_log.add_message(f"Eliminated {enemy.type_data.name}")
        else:
            self.game.message_log.add_message(f"{enemy.type_data.name} damaged")
            movement_type = enemy.get_movement_type()
            old_state = enemy.state
            if movement_type == EnemyMovement.PATROL and enemy.patrol_points:
                enemy.original_patrol_index = enemy.patrol_index
            enemy.state = EnemyState.HOSTILE
            enemy.last_seen_player = Position(self.game.player.x, self.game.player.y)
            logging.debug(f"Combat: Enemy {enemy.type_data.name}@({enemy.x},{enemy.y}) damaged, state {old_state.name} -> HOSTILE")
        return True

    def _execute_code_injection(self, target: Position) -> bool:
        """
        Execute Code Injection exploit - single target ranged damage.

        Deals 30 damage (35 to firewalls) to enemy at target position.
        Fails if no enemy at target.

        Args:
            target: Target enemy position

        Returns:
            True if enemy hit, False if no target
        """
        self.game.sound_manager.play_sound("exploit_code_injection")
        enemy = self.game._get_enemy_at(target)
        if not enemy:
            self.game.message_log.add_message("No target at location")
            return False

        damage = 35 if enemy.type == 'firewall' else 30
        return self._damage_enemy(enemy, damage)

    def _execute_buffer_overflow(self, target: Position) -> bool:
        """
        Execute Buffer Overflow exploit - high damage melee attack.

        Deals 50 damage to adjacent enemy (all 8 surrounding tiles including diagonals).
        Requires enemy to be adjacent to player.

        IMPORTANT: Uses grid distance (Chebyshev), NOT Euclidean distance!
        Diagonals count as range 1, so all 8 adjacent tiles are valid targets.

        Args:
            target: Target adjacent enemy position

        Returns:
            True if enemy hit, False if target not adjacent or no enemy
        """
        self.game.sound_manager.play_sound("exploit_buffer_overflow")
        # Check if target is within range-1 (all 8 adjacent tiles including diagonals)
        # Use grid distance so diagonals = 1, not ~1.414
        distance = self.game.player.position.grid_distance_to(target)
        if distance > 1:
            self.game.message_log.add_message("Must target adjacent enemy")
            return False

        enemy = self.game._get_enemy_at(target)
        if not enemy:
            self.game.message_log.add_message("No enemy at target")
            return False

        return self._damage_enemy(enemy, 50)
    
    def _disable_area_enemies(self, target: Position, radius: int, duration: int) -> int:
        """
        Disable enemies in area for the specified duration.

        Stun effect is additive - multiple stuns stack duration.
        Disabled enemies cannot move or attack. Resets their state to UNAWARE.

        Uses grid distance so diagonals count as 1 for consistent gameplay.

        Args:
            target: Center of AoE
            radius: Effect radius (grid distance)
            duration: Number of turns enemies are disabled

        Returns:
            Count of enemies disabled
        """
        count = 0
        for enemy in self.game.enemies:
            # Use grid distance for AoE radius (diagonals = 1)
            if enemy.position.grid_distance_to(target) <= radius:
                enemy.disabled_turns += duration  # Additive stun effect
                enemy.state = EnemyState.UNAWARE
                enemy.alert_timer = 0
                logging.debug(f"Combat: Enemy {enemy.type_data.name}@({enemy.x},{enemy.y}) STUNNED for {duration} turns, total={enemy.disabled_turns}")
                count += 1
        return count

    def _execute_system_crash(self, target: Position, exploit_range: int) -> bool:
        """
        Execute System Crash exploit - emergency AoE stun around player.

        Untargeted AoE centered on player position (not target).
        Disables all enemies within effect_radius for effect_duration turns.
        Emergency defensive tool with high heat cost.

        Uses grid distance so diagonals count as 1 for consistent gameplay.

        Args:
            target: Ignored (exploit is centered on player)
            exploit_range: Ignored (uses effect_radius from JSON)

        Returns:
            True (always succeeds)
        """
        self.game.sound_manager.play_sound("exploit_system_crash")
        # System Crash is an emergency untargeted AoE centered on player
        exploit = GameData.EXPLOITS['system_crash']
        player_pos = self.game.player.position
        count = 0
        for enemy in self.game.enemies:
            # Use grid distance for AoE radius (diagonals = 1)
            if enemy.position.grid_distance_to(player_pos) <= exploit.effect_radius:
                enemy.disabled_turns += exploit.effect_duration  # Additive stun effect
                enemy.state = EnemyState.UNAWARE
                enemy.alert_timer = 0
                count += 1
        self.game.message_log.add_message(f"System crash: {count} disabled")
        return True
    
    def _execute_threat_scan(self) -> bool:
        """
        Execute Threat Scan exploit - reveal enemy positions.

        Reveals all enemies on the map and their immediate surroundings (3x3 area).
        Does NOT reveal the entire map - only enemy locations and local context.
        Updates last_known_enemy_positions for all enemies.
        Effect lasts for effect_duration turns (from JSON config).

        Returns:
            True (always succeeds)
        """
        self.game.sound_manager.play_sound("exploit_threat_scan")
        exploit = GameData.EXPLOITS['threat_scan']
        self.game.game_state.threat_scan_turns = exploit.effect_duration  # Duration from JSON config
        
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
        """
        Execute Log Wiper exploit - reduce trace level.

        Reduces trace level by 30%, minimum 0. Useful for lowering detection risk.

        Returns:
            True (always succeeds)
        """
        self.game.sound_manager.play_sound("exploit_log_wiper")
        old_trace = self.game.player.trace_level
        self.game.player.trace_level = max(0, self.game.player.trace_level - 30)
        actual_reduction = old_trace - self.game.player.trace_level
        self.game.message_log.add_message(f"Trace Level: -{actual_reduction:.1f}%")
        return True
    
    def _execute_antivirus(self) -> bool:
        """
        Execute Antivirus exploit - purge negative status effects.

        Removes all negative temporary effects (virus, movement inhibition).
        Essential for countering virus enemy attacks.

        Returns:
            True (always succeeds)
        """
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
        """
        Execute Denial of Service exploit - targeted AoE stun.

        Disables all enemies within effect_radius of target for effect_duration turns.
        More targeted than System Crash, allowing tactical positioning.

        Args:
            target: Center of AoE
            exploit_range: Maximum range to place AoE center

        Returns:
            True (always succeeds)
        """
        self.game.sound_manager.play_sound("exploit_denial_of_service")
        # Denial of Service uses configured effect_radius at the target location
        exploit = GameData.EXPLOITS['denial_of_service']
        count = self._disable_area_enemies(target, exploit.effect_radius, exploit.effect_duration)
        self.game.message_log.add_message(f"DoS: {count} disabled")
        return True
    
    def _execute_memory_leak(self, target: Position) -> bool:
        """
        Execute Memory Leak exploit - make enemies forget player.

        Resets all enemies within effect_radius to UNAWARE state and clears
        their last_seen_player position. They forget they ever saw the player.
        Useful for escaping pursuit.

        Uses grid distance so diagonals count as 1 for consistent gameplay.

        Args:
            target: Center of AoE

        Returns:
            True (always succeeds)
        """
        self.game.sound_manager.play_sound("exploit_memory_leak")
        exploit = GameData.EXPLOITS['memory_leak']
        count = 0
        for enemy in self.game.enemies:
            # Use grid distance for AoE radius (diagonals = 1)
            if enemy.position.grid_distance_to(target) <= exploit.effect_radius:
                enemy.state = EnemyState.UNAWARE
                enemy.last_seen_player = None
                enemy.alert_timer = 0
                count += 1

        msg = f"Memory Leak: {count} enemies confused" if count > 0 else "No enemies in range"
        self.game.message_log.add_message(msg)
        return True
    
    def _execute_network_scan(self) -> bool:
        """
        Execute Network Scan exploit - reveal all special nodes on the level.

        Reveals and adds to explored tiles all cooling nodes, CPU recovery nodes,
        and ghost nodes (3x3 area around each). Provides strategic visibility
        for resource planning without revealing the entire map.

        Returns:
            True (always succeeds)
        """
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