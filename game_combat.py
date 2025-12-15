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

# Import required modules
from game_config import GameBalance, GameConfig
from game_data import GameData
from game_entities import (
    Colors,
    EnemyMovement,
    EnemyState,
    ExploitDefinition,
    Position,
    TargetingMode,
)
from game_errors import GameErrorHandler


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
            "system_hop": lambda exploit, target: self._execute_system_hop(target),
            "traffic_masquerade": lambda exploit, target: self._execute_traffic_masquerade(),
            "decoy_swarm": lambda exploit, target: self._execute_decoy_swarm(target),
            "code_injection": lambda exploit, target: self._execute_code_injection(exploit, target),
            "buffer_overflow": lambda exploit, target: self._execute_buffer_overflow(
                exploit, target
            ),
            "system_crash": lambda exploit, target: self._execute_system_crash(exploit, target),
            "logic_bomb": lambda exploit, target: self._execute_logic_bomb(exploit, target),
            "threat_scan": lambda exploit, target: self._execute_threat_scan(),
            "log_wiper": lambda exploit, target: self._execute_log_wiper(),
            "antivirus": lambda exploit, target: self._execute_antivirus(),
            "denial_of_service": lambda exploit, target: self._execute_denial_of_service(
                exploit, target
            ),
            "memory_leak": lambda exploit, target: self._execute_memory_leak(target),
            "network_scan": lambda exploit, target: self._execute_network_scan(),
        }

    def use_exploit(self, exploit_key: str) -> bool:
        """
        Attempt to use an equipped exploit.

        Validates exploit is equipped, checks heat limits, and shows overclock
        warning if needed. Enters targeting mode for ranged exploits or executes
        immediately for self-targeted effects.

        Args:
            exploit_key: Unique identifier for the exploit (e.g., 'system_hop')

        Returns:
            True if exploit was used/entered targeting, False if failed validation
        """
        if exploit_key not in self.game.player.inventory_manager.equipped_exploits:
            self.game.message_log.add_message("Exploit not equipped")
            return False

        exploit = GameData.EXPLOITS[exploit_key]

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
            logging.debug(
                f"Combat: Exploit '{exploit.name}' failed validation for target ({target.x},{target.y})"
            )
            return False

        # Check heat limit - show overclock warning dialogue if needed
        heat_cost = self._calculate_heat_cost(exploit)
        will_overheat = self.game.player.heat + heat_cost > self.game.player.max_heat

        if will_overheat and not self.game.overclock_confirmation:
            # Calculate overclock damage
            overheat_amount = (self.game.player.heat + heat_cost) - self.game.player.max_heat
            cpu_damage = overheat_amount  # 1:1 ratio
            remaining_cpu = self.game.player.cpu - cpu_damage

            # Store pending exploit info for confirmation
            self.game.overclock_exploit = exploit_key
            self.game.overclock_confirmation = False
            # Store target position if not in targeting mode (for direct execute_exploit calls)
            if not self.game.targeting_mode:
                self.game.cursor_position = target

            # Get input mapper for dynamic button hints
            input_mapper = getattr(self.game, "input_mapper", None)
            if not input_mapper and hasattr(self.game, "input_handler"):
                input_mapper = getattr(self.game.input_handler, "input_mapper", None)

            # Check if this is System Crash - show combined dialogue for both damages
            if exploit_key == "system_crash" and exploit.self_damage > 0:
                from game_dialogue_system import create_system_crash_overheat_dialogue

                dialogue = create_system_crash_overheat_dialogue(
                    overheat_damage=cpu_damage,
                    self_damage=exploit.self_damage,
                    current_cpu=self.game.player.cpu,
                    max_cpu=self.game.player.max_cpu,
                    input_mapper=input_mapper,
                )
                was_shown = self.game.dialogue_state.show(dialogue)

                if not was_shown:
                    # Combined dialogue can't be disabled - this shouldn't happen
                    logging.debug("Combat: Combined System Crash+overheat warning auto-confirming")
                    self.game.overclock_confirmation = True
                    self.game.system_crash_confirmed = True
                else:
                    self.game.sound_manager.play_sound("exploit_failed")
                    logging.debug(
                        "Combat: Combined System Crash+overheat warning shown, awaiting confirmation"
                    )
                    return False
            else:
                # Regular overclock warning dialogue
                from game_dialogue_system import create_overclock_warning_dialogue

                dialogue = create_overclock_warning_dialogue(
                    exploit_name=exploit.name,
                    overheat_amount=overheat_amount,
                    damage=cpu_damage,
                    remaining_cpu=remaining_cpu,
                    max_cpu=self.game.player.max_cpu,
                    input_mapper=input_mapper,
                )
                was_shown = self.game.dialogue_state.show(dialogue)

                if not was_shown:
                    # User disabled overclock warnings - auto-confirm and proceed
                    logging.debug(
                        f"Combat: Overclock warning suppressed by user preference, auto-confirming for '{exploit.name}'"
                    )
                    # Set confirmation flag and fall through to execution (no recursion needed)
                    self.game.overclock_confirmation = True
                    # Don't return - continue to execute below
                else:
                    # Dialogue was shown - block and wait for user confirmation
                    self.game.sound_manager.play_sound("exploit_failed")
                    logging.debug(
                        f"Combat: Overheat warning shown for '{exploit.name}', awaiting confirmation"
                    )
                    return False

        # Clear overclock confirmation if it was set
        if self.game.overclock_confirmation:
            logging.debug(f"Combat: Overclock confirmed for '{exploit.name}'")
            self.game.overclock_confirmation = False
            self.game.overclock_exploit = None

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
                logging.debug(
                    f"Combat: OVERCLOCKING! overheat={overheat_amount}, damage={actual_damage}, heat capped at {self.game.player.max_heat}"
                )
                self.game.message_log.add_message(f"OVERCLOCKING: {actual_damage} CPU damage!")
                self.game.sound_manager.play_sound("overclocking")
                # Set heat to max (not over)
                self.game.player.heat = self.game.player.max_heat
            else:
                # Normal heat application
                self.game.player.heat = new_heat

        if success:
            self.game.targeting_mode = False
            self.game.targeting_exploit = None
            self.game.maybe_process_turn()

        return success

    def _calculate_heat_cost(self, exploit: ExploitDefinition) -> int:
        """
        Calculate heat cost with exploit efficiency bonus and A17+ melee bonus.

        Exploit efficiency reduces heat cost by 40% (60% of original cost).
        A17+ adds melee_heat_bonus to melee attacks (range 1 exploits).

        Args:
            exploit: Exploit definition with base heat cost

        Returns:
            Final heat cost after efficiency bonus and melee bonus
        """
        base_heat = exploit.heat

        # A17+: Add melee heat bonus for range-1 (melee) exploits
        if exploit.range == 1:
            base_heat += self.game.ascension_modifiers.melee_heat_bonus

        multiplier = (
            0.6 if self.game.player.temporary_effects["exploit_efficiency_turns"] > 0 else 1.0
        )
        return int(base_heat * multiplier)

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

    def _execute_specific_exploit(
        self, exploit_key: str, exploit: ExploitDefinition, target: Position
    ) -> bool:
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
        # Unknown exploit - log for debugging (should not happen in normal gameplay)
        logging.warning(f"Combat: No handler for exploit '{exploit_key}'")
        return False

    def _execute_system_hop(self, target: Position) -> bool:
        """
        Execute System Hop exploit - pivot to blind spot.

        Instantly moves player to target position if it's in a blind spot zone,
        visible from player position (line of sight), not occupied by an enemy,
        and is a valid walkable tile.

        Args:
            target: Target blind spot position

        Returns:
            True if hop succeeded, False if target invalid
        """
        # Must be a blind spot and valid walkable position
        if not (
            self.game.game_map.is_blind_spot(target)
            and self.game.game_map.is_valid_position(target)
        ):
            self.game.message_log.add_message("Must target blind spot")
            return False

        # Must have line of sight (can't teleport through walls)
        if not self.game.game_map.has_line_of_sight(self.game.player.position, target):
            self.game.message_log.add_message("No line of sight")
            return False

        # Target must be unoccupied
        if self.game._get_enemy_at(target):
            self.game.message_log.add_message("Target occupied")
            return False

        # All checks passed - execute hop
        self.game.sound_manager.play_sound("exploit_system_hop")
        self.game.player.position = target
        self.game.message_log.add_message("System Hop executed")
        return True

    def _execute_traffic_masquerade(self) -> bool:
        """
        Execute Traffic Masquerade exploit - masquerade as legitimate traffic.

        Makes player invisible to enemies for the duration specified in JSON config.
        Enemies cannot see or pursue a masquerading player.

        Returns:
            True (always succeeds)
        """
        self.game.sound_manager.play_sound("exploit_traffic_masquerade")
        exploit = GameData.EXPLOITS["traffic_masquerade"]
        self.game.player.temporary_effects["traffic_masquerade_turns"] = exploit.effect_duration
        self.game.message_log.add_message("Traffic Masquerade active")
        return True

    def _execute_decoy_swarm(self, target: Position) -> bool:
        """
        Execute Decoy Swarm exploit - spawn decoys to lure enemies.

        Attracts nearby enemies (within effect_radius) to the target location.
        PATROL enemies become ALERT for 3 turns, others get last_seen_player set
        to target and become ALERT for 2 turns. Does not affect STATIC enemies.

        Uses grid distance so diagonals count as 1 for consistent gameplay.

        Args:
            target: Location of the decoy swarm

        Returns:
            True (always succeeds), displays count of attracted enemies
        """
        self.game.sound_manager.play_sound("exploit_decoy_swarm")
        exploit = GameData.EXPLOITS["decoy_swarm"]
        attracted = 0
        for enemy in self.game.enemies:
            movement_type = enemy.get_movement_type()
            # Use grid distance for AoE radius (diagonals = 1)
            if (
                movement_type in [EnemyMovement.SEEK, EnemyMovement.RANDOM, EnemyMovement.PATROL]
                and enemy.position.grid_distance_to(target) <= exploit.effect_radius
            ):
                if movement_type == EnemyMovement.PATROL:
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = exploit.alert_duration_patrol
                else:
                    enemy.last_seen_player = target
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = exploit.alert_duration_normal
                attracted += 1
        enemy_word = "enemy" if attracted == 1 else "enemies"
        self.game.message_log.add_message(f"Decoy Swarm: {attracted} {enemy_word} attracted")
        return True

    def _calculate_exploit_damage(self, base_damage: int) -> int:
        """
        Calculate final exploit damage with shadow bonus.

        Adds +10 damage if player is in a blind spot or invisible.

        Args:
            base_damage: Base damage from exploit definition

        Returns:
            Final damage amount
        """
        if base_damage == 0:
            return 0  # No bonus for non-damaging exploits

        # Shadow bonus: extra damage if attacking from blind spots or while invisible
        if (
            self.game.game_map.is_blind_spot(self.game.player.position)
            or self.game.player.is_invisible()
        ):
            shadow_bonus = GameConfig._get_required("balance.shadow_damage_bonus")
            return base_damage + shadow_bonus
        return base_damage

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
            # Enemy destroyed
            is_admin = enemy.type == "admin"
            self.game.sound_manager.play_sound("enemy_death")
            # Trigger particle explosion effect (graphics mode only, if enabled)
            if (
                hasattr(self.game, "particle_system")
                and self.game.particle_system is not None
                and hasattr(self.game, "tile_manager")
                and self.game.tile_manager is not None
                and self.game.settings.graphics_mode == "graphics"
                and self.game.settings.show_particle_effects
            ):
                try:
                    # Extract colors from enemy sprite for particles
                    colors = self.game.tile_manager.extract_sprite_colors(
                        enemy.type, num_colors=GameConfig.PARTICLE_SPRITE_COLOR_COUNT()
                    )

                    # Create explosion at enemy position (uses particle_count from config)
                    self.game.particle_system.create_death_explosion(
                        world_x=enemy.x, world_y=enemy.y, colors=colors
                    )
                except Exception as e:
                    # Don't crash game if particle effect fails
                    GameErrorHandler.handle_error(
                        e, "particle_effect", "Particle effect failed", fatal=False
                    )

            self.game.enemies.remove(enemy)
            self.game.player.cpu = min(
                self.game.player.max_cpu,
                self.game.player.cpu + GameBalance.ENEMY_ELIMINATION_CPU_REWARD,
            )
            self.game.message_log.add_message(
                f"Eliminated {enemy.type_data.name} (+{GameBalance.ENEMY_ELIMINATION_CPU_REWARD} CPU)"
            )

            # Track metrics
            from game_metrics import get_current_session, track

            track("enemies_killed", category=enemy.type)
            track("damage_dealt", amount=damage)
            if enemy.state == EnemyState.UNAWARE:
                track("stealth_kills")

            # Update max single hit damage for Overkill achievement
            current_session = get_current_session()
            if current_session and damage > current_session.max_single_hit_damage:
                current_session.max_single_hit_damage = damage

            # Check for immediate achievement unlocks (First Blood, Massacre, Overkill, etc.)
            from game_achievements import AchievementManager

            if current_session:
                AchievementManager.check_immediate_achievements_and_notify(
                    current_session, self.game
                )

            # Add environmental narrative for first combat or admin defeat
            if is_admin:
                env_msg = self.game.narrative_manager.trigger_admin_defeated()
            else:
                env_msg = self.game.narrative_manager.trigger_first_combat()
            if env_msg:
                self.game.message_log.add_message(env_msg)
        else:
            self.game.message_log.add_message(f"{enemy.type_data.name} damaged")
            movement_type = enemy.get_movement_type()
            if movement_type == EnemyMovement.PATROL and enemy.patrol_points:
                enemy.original_patrol_index = enemy.patrol_index
            enemy.state = EnemyState.HOSTILE
            enemy.last_seen_player = Position(self.game.player.x, self.game.player.y)
        return True

    def _execute_code_injection(self, exploit: ExploitDefinition, target: Position) -> bool:
        """
        Execute Code Injection exploit - single target ranged damage.

        Deals damage to enemy at target position.
        Fails if no enemy at target.
        Applies +10 shadow bonus if attacking from blind spots.

        Args:
            exploit: Exploit definition with damage value
            target: Target enemy position

        Returns:
            True if enemy hit, False if no target
        """
        self.game.sound_manager.play_sound("exploit_code_injection")
        enemy = self.game._get_enemy_at(target)
        if not enemy:
            self.game.message_log.add_message("No target at location")
            return False

        damage = self._calculate_exploit_damage(exploit.damage)
        return self._damage_enemy(enemy, damage)

    def _execute_buffer_overflow(self, exploit: ExploitDefinition, target: Position) -> bool:
        """
        Execute Buffer Overflow exploit - high damage melee attack.

        Deals damage to adjacent enemy (all 8 surrounding tiles including diagonals).
        Requires enemy to be adjacent to player.
        Applies +10 shadow bonus if attacking from blind spots.

        IMPORTANT: Uses grid distance (Chebyshev), NOT Euclidean distance!
        Diagonals count as range 1, so all 8 adjacent tiles are valid targets.

        Args:
            exploit: Exploit definition with damage value
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

        damage = self._calculate_exploit_damage(exploit.damage)
        return self._damage_enemy(enemy, damage)

    def _execute_system_crash(self, exploit: ExploitDefinition, target: Position) -> bool:
        """
        Execute System Crash exploit - emergency AoE damage + stun around player.

        Untargeted AoE centered on player position (not target).
        SELF-DAMAGE: Also damages the player for 30 CPU (crashes the system you're on!).
        Shows warning dialogue if this would kill the player or if warning not disabled.
        Applies +10 shadow bonus if attacking from blind spots.

        Uses grid distance so diagonals count as 1 for consistent gameplay.

        Args:
            exploit: Exploit definition with damage, self_damage, radius, and duration
            target: Ignored (exploit is centered on player)

        Returns:
            True if executed, False if cancelled by warning dialogue
        """
        # Check for self-damage warning
        if exploit.self_damage > 0 and not self.game.system_crash_confirmed:
            remaining_cpu = self.game.player.cpu - exploit.self_damage
            would_die = remaining_cpu <= 0

            # Show warning dialogue
            from game_dialogue_system import create_system_crash_warning_dialogue

            # Get input mapper for dynamic button hints
            input_mapper = getattr(self.game, "input_mapper", None)
            if not input_mapper and hasattr(self.game, "input_handler"):
                input_mapper = getattr(self.game.input_handler, "input_mapper", None)

            dialogue = create_system_crash_warning_dialogue(
                damage=exploit.self_damage,
                remaining_cpu=remaining_cpu,
                max_cpu=self.game.player.max_cpu,
                would_die=would_die,
                input_mapper=input_mapper,
            )
            was_shown = self.game.dialogue_state.show(dialogue)

            if not was_shown:
                # User disabled System Crash warnings - auto-confirm
                logging.debug(
                    "Combat: System Crash warning suppressed by user preference, auto-confirming"
                )
                # Set confirmation flag and fall through to execution (no recursion needed)
                self.game.system_crash_confirmed = True
                # Don't return - continue to execute below
            else:
                # Dialogue was shown - block and wait for confirmation
                self.game.sound_manager.play_sound("exploit_failed")
                logging.debug("Combat: System Crash warning shown, awaiting confirmation")
                return False

        # Clear confirmation flag
        self.game.system_crash_confirmed = False

        # Apply self-damage FIRST (before enemies, for dramatic effect)
        if exploit.self_damage > 0:
            actual_self_damage = self.game.player.take_damage(exploit.self_damage)
            self.game.message_log.add_message(
                f"CRITICAL SYSTEM FAILURE! Taking {actual_self_damage} collateral damage!",
                Colors.RED,
            )
            logging.debug(f"Combat: System Crash self-damage: {actual_self_damage} CPU")

        self.game.sound_manager.play_sound("exploit_system_crash")
        # System Crash is an emergency untargeted AoE centered on player
        player_pos = self.game.player.position

        # Calculate damage with shadow bonus once (not per enemy)
        damage = self._calculate_exploit_damage(exploit.damage)

        count = 0
        for enemy in self.game.enemies[:]:  # Iterate over copy to avoid skipping when enemies die
            # Use grid distance for AoE radius (diagonals = 1)
            if enemy.position.grid_distance_to(player_pos) <= exploit.effect_radius:
                # Deal damage first
                if damage > 0:
                    self._damage_enemy(enemy, damage)
                # Then apply stun (enemy might be dead, but that's OK - damage_enemy handles removal)
                if enemy in self.game.enemies:  # Check if enemy still exists after damage
                    enemy.disabled_turns += exploit.effect_duration  # Additive stun effect
                    enemy.state = EnemyState.UNAWARE
                    enemy.alert_timer = 0
                count += 1
        self.game.message_log.add_message(f"System crash: {count} affected")
        return True

    def _execute_logic_bomb(self, exploit: ExploitDefinition, target: Position) -> bool:
        """
        Execute Logic Bomb exploit - ranged AoE damage with friendly fire.

        Targeted AoE centered on target position. Deals damage to all enemies
        within effect_radius. WARNING: Also damages player if caught in blast!
        Shows friendly fire confirmation if player is in danger zone.
        Applies +10 shadow bonus if attacking from blind spots.

        Uses grid distance so diagonals count as 1 for consistent gameplay.

        Args:
            exploit: Exploit definition with damage and radius
            target: Center of explosion

        Returns:
            True if executed, False if cancelled due to friendly fire warning
        """
        player_pos = self.game.player.position
        player_distance = player_pos.grid_distance_to(target)

        # Calculate damage with shadow bonus (applies to both enemies and player)
        damage = self._calculate_exploit_damage(exploit.damage)

        # Check if player is in blast radius
        player_in_blast = player_distance <= exploit.effect_radius

        # If player is in blast and not confirmed, show warning
        if player_in_blast and not self.game.friendly_fire_confirmed:
            # Calculate potential damage to player (includes shadow bonus)
            remaining_cpu = self.game.player.cpu - damage

            # Store pending exploit info
            self.game.friendly_fire_exploit = "logic_bomb"
            self.game.friendly_fire_target = target

            # Show friendly fire warning
            from game_dialogue_system import create_friendly_fire_warning_dialogue

            # Get input mapper for dynamic button hints
            input_mapper = getattr(self.game, "input_mapper", None)
            if not input_mapper and hasattr(self.game, "input_handler"):
                input_mapper = getattr(self.game.input_handler, "input_mapper", None)

            dialogue = create_friendly_fire_warning_dialogue(
                exploit_name=exploit.name,
                damage=damage,
                remaining_cpu=remaining_cpu,
                max_cpu=self.game.player.max_cpu,
                input_mapper=input_mapper,
            )
            self.game.dialogue_state.show(dialogue)
            self.game.sound_manager.play_sound("exploit_failed")
            return False

        # Clear friendly fire confirmation (whether it was set or not)
        self.game.friendly_fire_confirmed = False
        self.game.friendly_fire_exploit = None
        self.game.friendly_fire_target = None

        # Execute the explosion
        self.game.sound_manager.play_sound("exploit_logic_bomb")

        # Damage all enemies in radius
        enemy_count = 0
        for enemy in list(self.game.enemies):  # Use list() to avoid modification during iteration
            if enemy.position.grid_distance_to(target) <= exploit.effect_radius:
                self._damage_enemy(enemy, damage)
                enemy_count += 1

        # Damage player if in radius (friendly fire!)
        if player_in_blast:
            actual_damage = self.game.player.take_damage(damage)
            self.game.message_log.add_message(f"FRIENDLY FIRE: {actual_damage} damage!", Colors.RED)
            logging.debug(f"Combat: Logic Bomb friendly fire! Player took {actual_damage} damage")

        # Show result message
        if enemy_count > 0:
            self.game.message_log.add_message(f"Logic Bomb: {enemy_count} targets eliminated!")
        else:
            self.game.message_log.add_message("Logic Bomb detonated (no targets)")

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
        exploit = GameData.EXPLOITS["threat_scan"]
        self.game.game_state.threat_scan_turns = (
            exploit.effect_duration
        )  # Duration from JSON config

        # Threat scan reveals only enemy positions and immediate surroundings, not entire map
        enemy_count = 0
        for enemy in self.game.enemies:
            # Update enemy position in memory
            self.game.game_map.last_known_enemy_positions[enemy.id] = (
                enemy.position,
                self.game.turn,
            )

            # Reveal a small area around each enemy (3x3) to show their local context
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    reveal_pos = Position(enemy.position.x + dx, enemy.position.y + dy)
                    if reveal_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                        self.game.game_map.explored_tiles.add((reveal_pos.x, reveal_pos.y))
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
        exploit = GameData.EXPLOITS["log_wiper"]
        trace_reduction = exploit.trace_reduction_percent
        self.game.player.trace_level = max(0, self.game.player.trace_level - trace_reduction)
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
        negative_effects = ["virus_turns", "movement_slowed_turns"]
        effects_cured = []

        for effect in negative_effects:
            if self.game.player.temporary_effects.get(effect, 0) > 0:
                effects_cured.append(effect)
                self.game.player.temporary_effects[effect] = 0

        if effects_cured:
            if "virus_turns" in effects_cured:
                self.game.message_log.add_message("Virus purged from system")
            if "movement_slowed_turns" in effects_cured:
                self.game.message_log.add_message("Movement inhibition removed")
            self.game.message_log.add_message("System cleansed of negative effects")
        else:
            self.game.message_log.add_message("No negative effects detected")

        return True

    def _execute_denial_of_service(self, exploit: ExploitDefinition, target: Position) -> bool:
        """
        Execute Denial of Service exploit - targeted AoE disable.

        Disables all enemies within effect_radius of target for effect_duration turns.
        Denial of service attacks overwhelm availability, not damage systems.
        More targeted than System Crash, allowing tactical positioning.

        Args:
            exploit: Exploit definition with radius and duration
            target: Center of AoE

        Returns:
            True (always succeeds)
        """
        self.game.sound_manager.play_sound("exploit_denial_of_service")
        # Denial of Service: disable in area (no damage)
        count = 0
        for enemy in self.game.enemies:
            if enemy.position.grid_distance_to(target) <= exploit.effect_radius:
                enemy.disabled_turns += exploit.effect_duration
                enemy.state = EnemyState.UNAWARE
                enemy.alert_timer = 0
                count += 1

        self.game.message_log.add_message(f"DoS: {count} disabled")
        return True

    def _execute_memory_leak(self, target: Position) -> bool:
        """
        Execute Memory Leak exploit - blind enemies temporarily.

        Corrupts enemy vision systems, making them unable to see the player for 3 turns
        while they reboot. Resets all enemies within effect_radius to UNAWARE state and
        blinds them. They keep moving but can't detect the player until blindness expires.
        Useful for escaping pursuit and getting into shadows.

        Uses grid distance so diagonals count as 1 for consistent gameplay.

        Args:
            target: Center of AoE

        Returns:
            True (always succeeds)
        """
        self.game.sound_manager.play_sound("exploit_memory_leak")
        exploit = GameData.EXPLOITS["memory_leak"]
        count = 0
        for enemy in self.game.enemies:
            # Use grid distance for AoE radius (diagonals = 1)
            if enemy.position.grid_distance_to(target) <= exploit.effect_radius:
                enemy.state = EnemyState.UNAWARE
                enemy.last_seen_player = None
                enemy.alert_timer = 0
                enemy.blinded_turns = exploit.effect_duration
                count += 1

        msg = f"Memory Leak: {count} enemies blinded" if count > 0 else "No enemies in range"
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
        if not hasattr(self.game.game_state, "revealed_special_nodes"):
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
                    explore_pos = Position(node_pos[0] + dx, node_pos[1] + dy)
                    if explore_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                        self.game.game_map.explored_tiles.add((explore_pos.x, explore_pos.y))

        # Reveal all CPU recovery nodes and add to explored tiles
        for node_pos in self.game.game_map.cpu_recovery_nodes:
            self.game.game_state.revealed_special_nodes[node_pos] = "cpu"
            # Add surrounding 3x3 area to explored tiles
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    explore_pos = Position(node_pos[0] + dx, node_pos[1] + dy)
                    if explore_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                        self.game.game_map.explored_tiles.add((explore_pos.x, explore_pos.y))

        # Reveal all ghost nodes and add to explored tiles
        for node_pos in self.game.game_map.ghost_nodes:
            self.game.game_state.revealed_special_nodes[node_pos] = "ghost"
            # Add surrounding 3x3 area to explored tiles
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    explore_pos = Position(node_pos[0] + dx, node_pos[1] + dy)
                    if explore_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                        self.game.game_map.explored_tiles.add((explore_pos.x, explore_pos.y))

        total_revealed = len(self.game.game_state.revealed_special_nodes)
        self.game.message_log.add_message(
            f"Network Scan: {cooling_count} cooling, {cpu_count} CPU, {ghost_count} ghost nodes found"
        )
        self.game.message_log.add_message(f"Total {total_revealed} special nodes revealed")
        return True
