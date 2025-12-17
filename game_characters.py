#!/usr/bin/env python3
"""
Enemy character classes with AI behavior and movement systems.

This module handles enemy AI logic including:
- Enemy AI states (UNAWARE -> ALERT -> HOSTILE) and vision
- Movement queue system (FIFO 3-move rolling queue for all enemies)
- Status effects, damage calculation, and attack logic
- Combat and special behaviors (virus mimicry, admin omniscience)

Pathfinding and Player logic have been extracted to separate modules:
- game_pathfinding.py: PathfindingHelper for A* and Dijkstra maps
- game_player.py: Player class for stats, abilities, and inventory
"""

import logging
import random

from game_config import GameConfig
from game_entities import Colors, EnemyMovement, EnemyState, Position, PositionValidator
from game_pathfinding import PathfindingHelper
from game_player import Player


class Enemy:
    """
    Enemy character with state-based AI, pathfinding, and movement queue system.

    The Enemy class manages several interconnected systems:
    - AI state machine (UNAWARE -> ALERT -> HOSTILE) with vision checks
    - Movement queue system (FIFO 3-move rolling queue) for smooth pathfinding
    - TCOD A* pathfinding with enemy collision avoidance
    - Combat (melee attacks, status effects like virus/slow)
    - Special behaviors (virus mimicry, admin omniscience, patrol routes)

    Movement queue ensures enemies plan 3 moves ahead, providing smooth
    pathfinding that adapts when blocked. All enemies use the same queue
    system regardless of movement type (PATROL, RANDOM, SEEK, STATIC).

    Key delegation:
    - Type data loaded from GameData.ENEMY_TYPES (stats, vision, damage)
    - Pathfinding uses PathfindingHelper for all pathfinding operations
    - Position validation uses PositionValidator
    """

    _next_id = 1  # Class variable for unique IDs

    @classmethod
    def get_next_id_counter(cls) -> int:
        """Get current enemy ID counter for serialization."""
        return cls._next_id

    @classmethod
    def set_next_id_counter(cls, value: int):
        """Set enemy ID counter when deserializing saved games."""
        cls._next_id = value

    def __init__(self, position: Position, enemy_type: str):
        """
        Initialize enemy with type-specific stats and AI state.

        Args:
            position: Starting Position on the game map
            enemy_type: Key into GameData.ENEMY_TYPES (e.g., 'admin', 'virus', 'drone')

        Note:
            - Admin enemies start HOSTILE (can always see player)
            - Virus enemies store original_movement_type for mimicry behavior
            - Movement queue starts empty and is filled on first move
        """
        self.id = Enemy._next_id
        Enemy._next_id += 1

        self.position = position
        self.type = enemy_type

        # Load type data - imported here to avoid circular imports
        from game_data import GameData

        self.type_data = GameData.ENEMY_TYPES[enemy_type]

        # Stats
        self.cpu = self.type_data.cpu
        self.max_cpu = self.type_data.cpu

        # AI state - admin starts hostile since it can always see player
        self.state = EnemyState.HOSTILE if enemy_type == "admin" else EnemyState.UNAWARE
        self.alert_timer = 0
        self.disabled_turns = 0
        self.move_cooldown = 0
        self.blinded_turns = 0  # Memory Leak blindness - can't see player

        # Movement data
        self.patrol_points: list[Position] = []
        self.patrol_index = 0
        self.last_seen_player: Position | None = None
        self.original_patrol_index = 0  # Store original patrol index when becoming hostile

        # Virus-specific: Store the original non-hostile movement type
        self.original_movement_type: EnemyMovement | None = None

        # Movement queue system - stores next 3 planned moves
        self.move_queue: list[Position] = []

    @property
    def x(self) -> int:
        return self.position.x

    @x.setter
    def x(self, value: int) -> None:
        self.position.x = value

    @property
    def y(self) -> int:
        return self.position.y

    @y.setter
    def y(self, value: int) -> None:
        self.position.y = value

    # Ascension modifier properties
    damage_multiplier: float = 1.0  # Set by apply_ascension_modifiers
    _vision_bonus: int = 0  # Set by apply_ascension_modifiers

    @property
    def vision_range(self) -> int:
        """Get vision range including ascension bonuses."""
        return self.type_data.vision + self._vision_bonus

    def apply_ascension_modifiers(self, modifiers) -> None:
        """
        Apply ascension modifiers to this enemy's stats.

        Args:
            modifiers: AscensionModifiers dataclass with modifier values
        """
        # A2: Enemy HP bonus
        if modifiers.enemy_hp_bonus > 0:
            self.cpu += modifiers.enemy_hp_bonus
            self.max_cpu += modifiers.enemy_hp_bonus

        # A4: Enemy damage multiplier
        self.damage_multiplier = modifiers.enemy_damage_multiplier

        # A1: Scanner vision bonus (only for scanners)
        vision_bonus = 0
        if self.type == "scanner" and modifiers.scanner_vision_bonus > 0:
            vision_bonus += modifiers.scanner_vision_bonus

        # A5: All enemy vision bonus
        if modifiers.enemy_vision_bonus > 0:
            vision_bonus += modifiers.enemy_vision_bonus

        self._vision_bonus = vision_bonus

    def get_color(self) -> tuple[int, int, int]:
        """
        Get the color for rendering this enemy (glyph mode).

        Color indicates both AI state and health:
        - Alert state: Yellow (unaware), Orange (alert), Red (hostile), Blue (disabled)
        - HP damage: Blends in red tint as HP decreases
        """
        # Get base color from state
        if self.disabled_turns > 0:
            base_color = Colors.BLUE
        elif self.state == EnemyState.UNAWARE:
            base_color = Colors.ENEMY_UNAWARE
        elif self.state == EnemyState.ALERT:
            base_color = Colors.ENEMY_ALERT
        else:
            base_color = Colors.ENEMY_HOSTILE

        # Safety check to prevent division by zero
        if self.max_cpu <= 0:
            return base_color  # Return base color if invalid max_cpu

        # Apply HP-based tinting (blend with red) from game_rules.json
        from game_color_manager import ColorManager

        hp_percent = self.cpu / self.max_cpu

        if hp_percent >= 1.0:
            # Full HP - no tint
            return base_color
        elif hp_percent >= 0.5:
            # 50-99% HP - slight red tint (75% base, 25% red)
            red_tint = ColorManager.get("damage_tints", "hp_50_to_99")
            return tuple(int(base_color[i] * 0.75 + red_tint[i] * 0.25) for i in range(3))
        else:
            # <50% HP - heavy red tint (50% base, 50% red)
            red_tint = ColorManager.get("damage_tints", "hp_below_50")
            return tuple(int(base_color[i] * 0.5 + red_tint[i] * 0.5) for i in range(3))

    def get_graphics_tint(self) -> tuple[int, int, int]:
        """
        Get subtle damage tint for graphics mode sprites from game_rules.json.

        Uses multiplicative blending (texture.color_mod), so tint values close to
        (255, 255, 255) preserve original sprite colors.

        Returns:
            RGB tint: (255, 255, 255) = no tint, (255, 200, 200) = slight red wash
        """
        from game_color_manager import ColorManager

        # Safety check to prevent division by zero
        if self.max_cpu <= 0:
            return ColorManager.get("damage_tints_graphics", "hp_50_to_99")  # From JSON

        hp_percent = self.cpu / self.max_cpu

        if hp_percent >= 1.0:
            # Full HP - no tint (pure white)
            return Colors.PURE_WHITE
        elif hp_percent >= 0.5:
            # 50-99% HP - very subtle red tint (preserves ~86% of green/blue)
            return ColorManager.get("damage_tints_graphics", "hp_50_to_99")
        else:
            # <50% HP - stronger red tint (preserves ~70% of green/blue)
            return ColorManager.get("damage_tints_graphics", "hp_below_50")

    def get_movement_type(self) -> EnemyMovement:
        """Get the effective movement type for this enemy.

        For virus enemies:
        - If STATIC: always STATIC (even when hostile - stationary viruses never move)
        - When HOSTILE: use SEEK movement (chase player)
        - When not HOSTILE (UNAWARE/ALERT): use their original mimicked movement type
        For all other enemies: returns type_data.movement
        """
        if self.type == "virus":
            # Stationary viruses NEVER move, even when hostile
            if self.original_movement_type == EnemyMovement.STATIC:
                return EnemyMovement.STATIC

            if self.state == EnemyState.HOSTILE:
                # Hostile viruses actively seek the player
                return EnemyMovement.SEEK
            elif self.original_movement_type is not None:
                # Non-hostile viruses use their mimicked movement type
                return self.original_movement_type
            # Fallback if original_movement_type wasn't set (shouldn't happen)
            return self.type_data.movement
        return self.type_data.movement

    def can_see_player(self, player: Player, game_map) -> bool:
        """
        Check if enemy can see player using layered vision rules.

        Vision checks are performed in order of efficiency:
        1. Disabled enemies cannot see anything
        2. Admin enemies always see player (omniscient)
        3. Range check using enemy's vision stat
        4. Invisibility check (data mimic blocks vision)
        5. Shadow check (players in shadows only visible when adjacent)
        6. TCOD FOV line-of-sight check

        Args:
            player: Player instance to check visibility for
            game_map: GameMap instance for shadow/FOV checking

        Returns:
            True if enemy can see player
        """
        if self.disabled_turns > 0:
            return False

        # Admin always sees player
        if self.type == "admin":
            return True

        # Check basic range (use Euclidean - TCOD FOV uses Euclidean internally)
        distance = self.position.distance_to(player.position)
        if distance > self.type_data.vision:
            return False

        # Invisible players can't be seen
        if player.is_invisible():
            return False

        # Players in shadows only visible when adjacent (use grid distance for gameplay)
        if (
            game_map.is_blind_spot(player.position)
            and self.position.grid_distance_to(player.position) > 1
        ):
            return False

        # Final LOS check using TCOD FOV
        return game_map.can_see_position(self.position, player.position, self.type_data.vision)

    def can_attack_player(self, player: Player) -> bool:
        """Check if enemy can attack player (adjacent including diagonally)."""
        # Can't attack if disabled
        if self.disabled_turns > 0:
            return False

        # Can't attack invisible players unless this is an admin
        if player.is_invisible() and self.type != "admin":
            return False

        # Can't attack if no damage, unless it's a virus or inhibitor (which apply status effects)
        if self.type_data.damage <= 0 and self.type not in ("virus", "inhibitor"):
            return False

        # Use Position helper for adjacency check (excluding same position)
        return self.position.is_adjacent_to(player.position) and self.position != player.position

    def attack_player(self, player: Player, game_engine=None) -> int:
        """Attack the player and return damage dealt."""
        if self.type == "virus":
            virus_increment = GameConfig._get_required("balance.virus_increment_turns")
            virus_max = GameConfig._get_required("gameplay.virus_max_duration")
            virus_turns = player.temporary_effects.get("virus_turns", 0) + virus_increment
            player.temporary_effects["virus_turns"] = min(virus_turns, virus_max)
            return 0

        if self.type == "inhibitor":
            player.speed_moves_remaining = 0
            current_speed = player.temporary_effects["speed_boost_turns"]
            net_effect = current_speed - 1

            if net_effect >= 0:
                # Still have speed boost remaining - just reduce it
                player.temporary_effects["speed_boost_turns"] = net_effect
            else:
                # No speed boost - apply slowdown by extending duration (stacking with cap)
                player.temporary_effects["speed_boost_turns"] = 0
                current_slow = player.temporary_effects.get("movement_slowed_turns", 0)
                # Add slowdown and cap at 5 turns to prevent infinite stacking
                player.temporary_effects["movement_slowed_turns"] = min(
                    current_slow + (-net_effect), 5
                )
            return 0

        # A4+: Apply enemy damage multiplier from ascension modifiers
        base_damage = self.type_data.damage
        final_damage = int(base_damage * self.damage_multiplier)
        damage = player.take_damage(final_damage)

        # CRITICAL: Check for death immediately after attack
        # Don't wait for process_turn() - death may have occurred mid-turn
        if player.cpu <= 0 and game_engine is not None:
            if (
                not hasattr(game_engine, "pending_death_dialogue")
                or not game_engine.pending_death_dialogue
            ):
                game_engine.game_over = True
                game_engine.pending_death_dialogue = True
                logging.warning(
                    f"Player killed by {self.type_data.name} attack - pending_death_dialogue set"
                )
                # Delete save immediately - don't wait for turn processing
                # This prevents "Continue" appearing after death
                from game_save import SaveGameManager

                if SaveGameManager.save_exists():
                    try:
                        SaveGameManager.delete_save()
                        logging.info("Save file deleted on combat death (permadeath)")
                    except OSError as e:
                        logging.error(f"Failed to delete save on combat death: {e}")

        return damage

    def take_damage(self, damage: int) -> bool:
        """Take damage and return True if destroyed."""
        # Admin avatar has damage resistance
        original_damage = damage
        if self.type == "admin":
            resist_percent = (
                self.type_data.damage_resistance_percent
                if hasattr(self.type_data, "damage_resistance_percent")
                else 50
            )
            resist_min = (
                self.type_data.damage_resistance_min
                if hasattr(self.type_data, "damage_resistance_min")
                else 5
            )
            damage = max(resist_min, damage * (100 - resist_percent) // 100)
            logging.debug(
                f"Enemy {self.type_data.name}@({self.x},{self.y}): damage reduced by resistance: {original_damage} -> {damage}"
            )

        self.cpu -= damage
        is_dead = self.cpu <= 0
        return is_dead

    def move(self, game_map, player, game_engine) -> bool:
        """
        Execute next queued move, maintaining fixed 3-length queue.

        Simplified flow:
        1. Check patrol waypoint advancement
        2. Check disabilities/cooldowns
        3. Ensure queue has moves (fill if needed)
        4. Pop and validate next move
        5. Execute move
        6. Ensure queue stays full (top up to 3)

        Returns:
            True if moved successfully, False otherwise
        """
        # 1. Patrol waypoint advancement
        if self._should_advance_patrol_waypoint():
            self._advance_patrol_waypoint()
            # Don't clear queue - it already has valid moves to next waypoint
            # from _extend_patrol_queue. Queue is only cleared when blocked.

        # 2. Disability check
        if self.disabled_turns > 0:
            self.disabled_turns -= 1
            return False

        if self.move_cooldown > 0 and self.type != "admin":
            self.move_cooldown -= 1
            return False

        # 3. Blindness decrement (blind enemies still move, just can't see)
        if self.blinded_turns > 0:
            self.blinded_turns -= 1

        # 3. Ensure queue has moves
        if not self.move_queue:
            self._ensure_queue_full(game_map, player, game_engine)

        # No moves available
        if not self.move_queue:
            return False

        # 4. Pop next move
        next_position = self.move_queue.pop(0)

        # 5. Validate move
        if not self._is_move_valid(next_position, game_map, player, game_engine):
            # Blocked - clear queue and replan next turn
            logging.debug(
                f"Enemy {self.type_data.name}@({self.x},{self.y}): move to ({next_position.x},{next_position.y}) BLOCKED, clearing queue"
            )
            self.move_queue.clear()
            return False

        # 6. Execute move
        self.position = next_position

        # 7. Top up queue to maintain 3 moves
        self._ensure_queue_full(game_map, player, game_engine)

        # 8. Update cooldown
        if self.get_movement_type() == EnemyMovement.STATIC:
            self.move_cooldown = GameConfig._get_required("balance.static_enemy_cooldown")
        else:
            self.move_cooldown = 0

        return True

    def _should_advance_patrol_waypoint(self) -> bool:
        """
        Check if enemy reached current patrol waypoint.

        Only advances for PATROL movement type enemies who are not hostile.
        Uses adjacency threshold to determine if waypoint reached.

        Returns:
            True if should advance to next waypoint, False otherwise
        """
        if self.get_movement_type() != EnemyMovement.PATROL:
            return False
        if not self.patrol_points:
            return False
        if self.state == EnemyState.HOSTILE:
            return False  # Hostile patrol enemies chase player

        # Check if arrived at current patrol waypoint (use grid distance for gameplay)
        current_target = self.patrol_points[self.patrol_index]
        return self.position.grid_distance_to(current_target) <= 1

    def _advance_patrol_waypoint(self) -> None:
        """Advance to next patrol waypoint (wraps around)."""
        self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)

    def _get_queue_end_position(self) -> Position:
        """
        Get the last queued position or current position if queue is empty.

        This helper encapsulates the common pattern of checking the movement
        queue's endpoint for pathfinding and validation purposes.

        Returns:
            Position at end of move queue, or current position if queue is empty
        """
        return self.move_queue[-1] if self.move_queue else self.position

    def _ensure_queue_full(self, game_map, player, game_engine) -> None:
        """
        Ensure move queue has 3 moves (or as many as possible).

        This is the ONLY method that fills the queue. Called after each move
        to maintain a fixed 3-length queue for player predictability.

        The 3-length queue is a core gameplay mechanic that allows players
        to predict enemy positions up to 3 turns ahead and plan tactically.

        Queue Invalidation: Queue is cleared (invalidated) in only 2 cases:
        1. Enemy state changes (UNAWARE <-> ALERT <-> HOSTILE)
        2. Next queued move is blocked (wall, enemy, etc.)

        Strategy:
        - If queue already has 3 moves, do nothing
        - Otherwise, calculate path from last queued position (or current position)
        - Add moves until queue has 3 (or path exhausted)

        Args:
            game_map: GameMap for pathfinding
            player: Player for targeting
            game_engine: GameEngine for enemy collision avoidance
        """
        # Already full
        if len(self.move_queue) >= 3:
            return

        movement_type = self.get_movement_type()

        # Static enemies don't move
        if movement_type == EnemyMovement.STATIC:
            return

        # If we're already adjacent to player (in attack range), don't queue more moves
        # Check from last queued position (or current position if queue empty)
        check_pos = self._get_queue_end_position()
        if check_pos.grid_distance_to(player.position) <= 1:
            # Exception: non-hostile enemies can pass by the player
            # Only stop if we're hostile and targeting the player
            if self.state == EnemyState.HOSTILE:
                return  # In attack range, stay put and attack

        # PRIORITY 1: Flee behavior for low-health enemies (unless Admin)
        if self._should_flee(player, game_map) and self.type != "admin":
            logging.debug(
                f"Enemy {self.type_data.name}@({self.x},{self.y}): FLEEING (cpu={self.cpu}/{self.type_data.max_cpu})"
            )
            self._fill_flee_moves(game_map, player, game_engine)
            return

        # Random movement - fill with random moves (but only if not hostile/admin)
        # Hostile and admin enemies always use pathfinding, regardless of base movement type
        if (
            movement_type == EnemyMovement.RANDOM
            and self.type != "admin"
            and self.state != EnemyState.HOSTILE
        ):
            self._fill_random_moves(game_map, player, game_engine)
            return

        # Pathfinding-based movement (PATROL, SEEK, or HOSTILE/ADMIN override)
        target = self._get_current_target(player, game_map)
        if not target:
            return

        # Start pathfinding from last queued position (or current if empty)
        start_pos = self._get_queue_end_position()

        # Calculate path
        path = PathfindingHelper.calculate_path(
            start=start_pos,
            goal=target,
            game_map=game_map,
            game_engine=game_engine,
            moving_enemy=self,
        )

        # Fill queue from path
        if path is not None and len(path) > 1:
            # Add moves until queue has 3
            for i in range(1, len(path)):
                if len(self.move_queue) >= 3:
                    break
                # TCOD returns (y, x), convert to Position(x, y)
                pos = Position(path[i][1], path[i][0])

                # NEVER queue the player's exact position
                if pos.x == player.position.x and pos.y == player.position.y:
                    break

                # Add the move
                self.move_queue.append(pos)

                # Stop queuing once we've added an adjacent position (in attack range)
                # Don't queue moves beyond the player - we want to attack, not path past
                if pos.grid_distance_to(player.position) <= 1:
                    break

        # Pathfinding failed - try greedy fallback (chain up to 3 moves)
        elif target and not self.move_queue:
            self._fill_greedy_moves(target, game_map, player, game_engine)

        # PATROL special case: If queue still not full, extend with next waypoint(s)
        # Only extend patrol queue for non-hostile enemies (hostile chase player, not patrol)
        if (
            movement_type == EnemyMovement.PATROL
            and self.state != EnemyState.HOSTILE
            and self.patrol_points
            and len(self.move_queue) < 3
        ):
            self._extend_patrol_queue(game_map, game_engine)

    def _fill_random_moves(self, game_map, player, game_engine) -> None:
        """
        Fill queue with random moves for RANDOM movement type enemies.

        Chains random moves from last queued position to maintain
        3-length queue predictability. Used only for enemies with
        RANDOM base movement type who are not hostile.

        Args:
            game_map: GameMap for move validation
            player: Player to avoid colliding with
            game_engine: GameEngine for enemy collision avoidance
        """
        # Start from last queued position (or current if empty)
        start_pos = self._get_queue_end_position()

        # Add random moves until queue has 3
        while len(self.move_queue) < 3:
            next_move = self._calculate_random_move_from(start_pos, game_map, player, game_engine)
            if next_move:
                self.move_queue.append(next_move)
                start_pos = next_move  # Chain for next random move
            else:
                break  # No valid random moves

    def _calculate_random_move_from(
        self, from_pos: Position, game_map, player, game_engine
    ) -> Position | None:
        """
        Calculate a random valid move from given position.

        Tries all 8 directions in random order until valid move found.

        Args:
            from_pos: Position to move from
            game_map: GameMap for boundary validation
            player: Player to avoid colliding with
            game_engine: GameEngine for enemy collision avoidance

        Returns:
            Valid random Position, or None if no valid moves
        """
        directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
        random.shuffle(directions)

        for dx, dy in directions:
            next_pos = Position(from_pos.x + dx, from_pos.y + dy)
            if self._is_move_valid_from(next_pos, from_pos, game_map, player, game_engine):
                return next_pos
        return None

    def _is_move_valid_from(
        self, position: Position, from_position: Position, game_map, player, game_engine
    ) -> bool:
        """
        Check if move from from_position to position is valid.

        Validates: boundaries, player collision, enemy collision.

        Args:
            position: Target position
            from_position: Current position (unused but kept for consistency)
            game_map: GameMap for boundary validation
            player: Player to avoid colliding with
            game_engine: GameEngine for enemy collision avoidance

        Returns:
            True if move is valid, False otherwise
        """
        # Use centralized PositionValidator for consistency
        return PositionValidator.is_valid_for_enemy_movement(
            position, game_map, game_engine.enemies, player.position, self
        )

    def _extend_patrol_queue(self, game_map, game_engine) -> None:
        """
        Extend patrol queue with next waypoint(s) to reach 3 moves.

        When close to current waypoint, this chains pathfinding to subsequent
        waypoints to maintain the 3-move prediction guarantee.

        Args:
            game_map: GameMap for pathfinding
            game_engine: GameEngine for enemy collision avoidance
        """
        attempts = 0
        max_attempts = len(self.patrol_points)  # Avoid infinite loops

        while len(self.move_queue) < 3 and attempts < max_attempts:
            attempts += 1

            # Calculate next waypoint index (wraps around)
            next_index = (self.patrol_index + attempts) % len(self.patrol_points)
            next_waypoint = self.patrol_points[next_index]

            # Start from last queued position
            start_pos = self._get_queue_end_position()

            # Skip only if already exactly at this waypoint
            # Don't skip if 1 tile away - we still need to queue that move for short patrols
            if start_pos.grid_distance_to(next_waypoint) == 0:
                continue

            # Calculate path to next waypoint
            path = PathfindingHelper.calculate_path(
                start=start_pos,
                goal=next_waypoint,
                game_map=game_map,
                game_engine=game_engine,
                moving_enemy=self,
            )

            # Add moves from path
            if path is not None and len(path) > 1:
                for i in range(1, len(path)):
                    if len(self.move_queue) >= 3:
                        return  # Queue full, done
                    self.move_queue.append(Position(path[i][1], path[i][0]))
            else:
                # Can't pathfind to next waypoint, stop trying
                break

    def _fill_greedy_moves(self, target: Position, game_map, player, game_engine) -> None:
        """
        Fill queue with greedy moves toward target (up to 3 moves).

        When pathfinding fails, this provides a fallback that maintains the
        3-move lookahead for player predictability. Chains greedy moves by
        simulating future positions and picking best direction each step.

        Args:
            target: Destination Position to move toward
            game_map: GameMap for wall checking
            player: Player to avoid
            game_engine: GameEngine for enemy collision checking
        """
        # Start from current position
        current_pos = self.position

        # Chain up to 3 greedy moves
        while len(self.move_queue) < 3:
            greedy_move = self._calculate_greedy_move_from(
                current_pos, target, game_map, player, game_engine
            )

            # No valid move found - stop chaining
            if not greedy_move:
                break

            # Add move to queue
            self.move_queue.append(greedy_move)

            # Stop if we've reached adjacent to player (attack range)
            if greedy_move.grid_distance_to(player.position) <= 1:
                break

            # Continue from this new position
            current_pos = greedy_move

    def _calculate_greedy_move_from(
        self, from_pos: Position, target: Position, game_map, player, game_engine
    ) -> Position | None:
        """
        Calculate single greedy move from a given position toward target.

        Helper for _fill_greedy_moves that allows chaining moves.

        Args:
            from_pos: Position to move from
            target: Destination Position to move toward
            game_map: GameMap for wall checking
            player: Player to avoid
            game_engine: GameEngine for enemy collision checking

        Returns:
            Position closest to target that is valid, or None if no valid moves
        """
        if not target:
            return None

        best_move = None
        best_distance = float("inf")

        # Try all 8 adjacent directions
        directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

        for dx, dy in directions:
            next_pos = Position(from_pos.x + dx, from_pos.y + dy)

            # Check if move is valid (not blocked by walls)
            if not next_pos.is_valid(game_map.width, game_map.height):
                continue
            if game_map.is_wall(next_pos):
                continue

            # NEVER queue player's exact position
            if next_pos.x == player.position.x and next_pos.y == player.position.y:
                continue

            # Skip positions blocked by other enemies
            enemy_blocking = any(
                e.position.x == next_pos.x and e.position.y == next_pos.y
                for e in game_engine.enemies
                if e.id != self.id
            )
            if enemy_blocking:
                continue

            # Skip positions already in queue (avoid loops)
            if any(q.x == next_pos.x and q.y == next_pos.y for q in self.move_queue):
                continue

            # Calculate distance to target from this position (grid distance for gameplay)
            distance = next_pos.grid_distance_to(target)

            # Keep track of best VALID move (closest to target)
            if distance < best_distance:
                best_distance = distance
                best_move = next_pos

        return best_move

    def _should_flee(self, player, game_map) -> bool:
        """
        Determine if enemy should flee from player.

        Enemies flee when:
        1. Health is below 30% of maximum
        2. Player is visible OR hostile state (knows player is nearby)
        3. Not a static enemy (can't flee if can't move)

        Args:
            player: Player instance
            game_map: GameMap for visibility checks

        Returns:
            True if enemy should flee, False otherwise
        """
        # Don't flee if static
        if self.get_movement_type() == EnemyMovement.STATIC:
            return False

        # Check health threshold
        # Safety check for tests where max_cpu might be a mock
        try:
            max_cpu = int(self.type_data.max_cpu)
            if max_cpu <= 0:
                return False
            health_percent = self.cpu / max_cpu
            flee_threshold = GameConfig._get_required("balance.enemy_flee_health_threshold")
            if health_percent > flee_threshold:
                return False
        except (TypeError, ValueError, AttributeError):
            # In tests or invalid state, don't flee
            return False

        # Only flee if we can see player or are hostile (know player is nearby)
        if self.can_see_player(player, game_map) or self.state == EnemyState.HOSTILE:
            return True

        return False

    def _fill_flee_moves(self, game_map, player, game_engine) -> None:
        """
        Fill move queue with flee moves using Dijkstra maps.

        Uses TCOD Dijkstra maps to find the best escape route away from player.
        Each move in the queue maximizes distance from player.

        Args:
            game_map: GameMap for pathfinding
            player: Player to flee from
            game_engine: GameEngine for enemy collision avoidance
        """
        # Create Dijkstra map with player as threat
        dijkstra_map = PathfindingHelper.create_dijkstra_map(
            goals=[player.position], game_map=game_map, game_engine=game_engine, moving_enemy=self
        )

        # Fill queue with up to 3 flee moves
        current_pos = self._get_queue_end_position()

        while len(self.move_queue) < 3:
            # Get best flee move from current position
            flee_direction = PathfindingHelper.get_flee_move(
                current_pos=current_pos, dijkstra_map=dijkstra_map, game_map=game_map
            )

            if flee_direction is None:
                # No valid flee move, stop filling
                logging.debug(
                    f"Enemy {self.type_data.name}@({self.x},{self.y}): No valid flee move from ({current_pos.x},{current_pos.y})"
                )
                break

            # Calculate next position
            dx, dy = flee_direction
            next_pos = Position(current_pos.x + dx, current_pos.y + dy)

            # Validate move
            if not self._is_move_valid_from(next_pos, current_pos, game_map, player, game_engine):
                logging.debug(
                    f"Enemy {self.type_data.name}@({self.x},{self.y}): Flee move to ({next_pos.x},{next_pos.y}) invalid"
                )
                break

            # Add to queue
            self.move_queue.append(next_pos)
            current_pos = next_pos

    def _get_current_target(self, player, game_map) -> Position | None:
        """Get the current target position based on enemy state and movement type."""
        # Admin always targets player (can always see them)
        if self.type == "admin":
            self.last_seen_player = player.position
            return player.position

        # HOSTILE enemies target player
        if self.state == EnemyState.HOSTILE:
            if self.can_see_player(player, game_map):
                self.last_seen_player = player.position
                return player.position
            # Target last known position
            return self.last_seen_player

        # PATROL enemies target current patrol point
        movement_type = self.get_movement_type()
        if movement_type == EnemyMovement.PATROL and self.patrol_points:
            return self.patrol_points[self.patrol_index]

        # RANDOM enemies have no fixed target
        return None

    def _is_move_valid(self, position, game_map, player, game_engine) -> bool:
        """Check if a position is valid for movement."""
        # Use centralized PositionValidator for consistency
        return PositionValidator.is_valid_for_enemy_movement(
            position, game_map, game_engine.enemies, player.position, self
        )


# Pathfinding helper functions
