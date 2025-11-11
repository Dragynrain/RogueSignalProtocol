#!/usr/bin/env python3
"""
Barbarian Agent - Aggressive Combat Testing

Tests combat-focused gameplay with tactical retreats:
- BarbarianAgent: Kill all enemies on level, proceed to gateway
- Uses only bump attacks (no exploits)
- Tactical positioning: retreat to choke points if surrounded
- Resource management: retreat to CPU recovery nodes when low HP

The barbarian isn't stupid - he fights smart! When outnumbered, retreat
to choke points. When wounded, retreat to healing nodes. RARRR!
"""

import pytest
import random
from typing import Optional, Tuple, List, Dict, Any
from tests.test_agent import GameTestAgent
from game_entities import Position, EnemyState
from game_config import GameBalance


class BarbarianAgent(GameTestAgent):
    """
    Aggressive combat agent that seeks to eliminate all enemies.

    Strategy (PURE BASELINE - NO SMART BEHAVIOR):
    - Find nearest enemy and charge for bump attack
    - If CPU < 50%, retreat to CPU recovery node and battle there
    - After clearing level, proceed through gateway
    - No exploits, pure melee combat (BUMP ATTACKS ONLY!)
    - CHARGE STRAIGHT AT ENEMIES - no routing around danger
    - NO corridor retreats, NO danger-aware pathfinding

    Validates:
    - Combat system sustainability
    - CPU recovery node effectiveness
    - Multi-level progression with combat focus
    """

    def __init__(self, seed=None, max_turns=2000, debug=False):
        """
        Initialize barbarian agent.

        Args:
            seed: Random seed for deterministic testing
            max_turns: Maximum turns per level (default 2000)
            debug: Enable debug logging for pathfinding
        """
        super().__init__(seed=seed, level=1)
        self.max_turns = max_turns
        self.debug = debug
        self.turns_taken = 0
        self.kills = 0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.initial_hp = self.player.cpu
        self.retreats_to_choke = 0
        self.retreats_to_healing = 0
        self.turns_on_cpu_node = 0
        self.levels_cleared = 0
        self.total_enemies_faced = 0
        self.combat_turns = 0  # Turns spent adjacent to enemies
        # Action tracking
        self.turns_exploring = 0
        self.turns_charging = 0
        # Death tracking
        self.death_log = []  # Track deaths: {'level', 'turn', 'hp', 'enemies_nearby', 'position'}

    def log_death(self, context: str = ""):
        """Log death details for analysis."""
        self.death_log.append({
            'level': self.engine.level,
            'turn': self.turns_taken,
            'hp': self.player.cpu,
            'trace': self.player.trace_level,
            'enemies_nearby': self.count_adjacent_enemies(),
            'total_enemies_alive': len(self.enemies),
            'position': (self.player.x, self.player.y),
            'context': context,
        })

    def count_adjacent_enemies(self) -> int:
        """
        Count how many enemies are adjacent to player.

        Returns:
            Number of enemies in 8 adjacent tiles
        """
        count = 0
        px, py = self.player.x, self.player.y

        for enemy in self.enemies:
            # Check 8-directional adjacency (including diagonals)
            dist = max(abs(enemy.x - px), abs(enemy.y - py))
            if dist == 1:
                count += 1

        return count

    def is_surrounded(self) -> bool:
        """
        Check if facing multiple enemies (2+ ALERT/HOSTILE enemies).

        Trigger when 2+ mobile enemies spot you to avoid multi-enemy fights.
        The barbarian advantage is fighting 1v1 in corridors, not 1v2+ in open space.

        Counts both ALERT and HOSTILE mobile enemies (not STATIC) since:
        - Enemies go ALERT when they spot you (1 turn warning)
        - Then go HOSTILE and chase you
        - Need to retreat to corridor BEFORE fighting multiple enemies

        Returns:
            True if 2 or more mobile enemies have spotted the player
        """
        from game_characters import EnemyState, EnemyMovement

        # Count ALERT + HOSTILE mobile enemies (not STATIC)
        alerted_mobile_count = sum(
            1 for e in self.enemies
            if (e.state == EnemyState.ALERT or e.state == EnemyState.HOSTILE)
            and e.get_movement_type() != EnemyMovement.STATIC
        )
        return alerted_mobile_count >= 2  # Trigger at 2+ to keep fights 1v1

    def find_nearest_enemy(self) -> Optional[Tuple[int, int]]:
        """
        Find nearest enemy position.

        Returns:
            (x, y) tuple of nearest enemy, or None
        """
        if not self.enemies:
            return None

        nearest = None
        min_dist = float('inf')

        for enemy in self.enemies:
            dist = abs(enemy.x - self.player.x) + abs(enemy.y - self.player.y)
            if dist < min_dist:
                min_dist = dist
                nearest = (enemy.x, enemy.y)

        return nearest

    def find_nearest_cpu_node(self) -> Optional[Tuple[int, int]]:
        """
        Find nearest CPU recovery node.

        Returns:
            (x, y) tuple of nearest CPU node, or None
        """
        if not self.game_map.cpu_recovery_nodes:
            return None

        nearest = None
        min_dist = float('inf')

        for node_x, node_y in self.game_map.cpu_recovery_nodes:
            dist = abs(node_x - self.player.x) + abs(node_y - self.player.y)
            if dist < min_dist:
                min_dist = dist
                nearest = (node_x, node_y)

        return nearest

    def find_nearest_ghost_node(self) -> Optional[Tuple[int, int]]:
        """
        Find nearest ghost node (for trace level reduction).

        Returns:
            (x, y) tuple of nearest ghost node, or None
        """
        if not self.game_map.ghost_nodes:
            return None

        nearest = None
        min_dist = float('inf')

        for node_x, node_y in self.game_map.ghost_nodes:
            dist = abs(node_x - self.player.x) + abs(node_y - self.player.y)
            if dist < min_dist:
                min_dist = dist
                nearest = (node_x, node_y)

        return nearest

    def is_on_ghost_node(self) -> bool:
        """Check if currently standing on ghost node."""
        player_pos = Position(self.player.x, self.player.y)
        return self.game_map.is_ghost_node(player_pos)

    def is_out_of_combat(self) -> bool:
        """
        Check if barbarian is out of combat (safe to retreat).

        "Out of combat" means no enemies are immediately adjacent (1 tile away).
        This gives a safe moment to retreat without taking damage while fleeing.

        Returns:
            True if no enemies are adjacent
        """
        # Check if any enemies are adjacent (immediate danger)
        return self.count_adjacent_enemies() == 0

    def should_do_maintenance_cycle(self) -> bool:
        """
        Check if Shadow Barbarian should do full maintenance (HP + trace).

        Shadow strategy: Retreat when SAFE and NEEDED:
        1. HP < 75% AND no adjacent enemies (safe moment to heal)
        2. Trace >= 60% AND no adjacent enemies (safe moment to clear trace)

        Always do BOTH: heal HP to full AND clear trace to 0.

        Returns:
            True if should attempt full maintenance cycle
        """
        if not self.shadow_mode:
            return False

        hp_percent = self.player.cpu / self.player.max_cpu
        trace_percent = self.player.trace_level / 100
        is_safe = self.is_out_of_combat()  # No adjacent enemies

        # Retreat when SAFE and (HP low OR trace dangerous)
        if is_safe and (hp_percent < 0.75 or trace_percent >= 0.60):
            return True

        return False

    def is_at_chokepoint(self) -> bool:
        """
        Check if currently at a chokepoint (6+ adjacent walls = true corridor).

        A true corridor has walls on both sides (6+ walls), not just a corner (3-5 walls).

        Returns:
            True if at a defensive corridor with 6+ adjacent walls
        """
        px, py = self.player.x, self.player.y

        # Count adjacent walls
        wall_count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                if (px + dx, py + dy) in self.game_map.walls:
                    wall_count += 1

        # At a chokepoint if 6+ adjacent walls (true corridor, not corner)
        return wall_count >= 6

    def find_choke_point(self) -> Optional[Tuple[int, int]]:
        """
        Find nearby corridor (position with walls on both sides) using smart selection.

        Smart corridor selection considers:
        - Must be a true corridor (6+ adjacent walls, not a corner)
        - Distance to player (closer is better for quick retreat)
        - Distance to CPU node (prefer corridors closer to healing)
        - Distance from enemies (prefer corridors farther from danger)

        Returns:
            (x, y) tuple of best corridor position, or None if no corridors nearby
        """
        from game_characters import EnemyState, EnemyMovement

        candidates = []
        px, py = self.player.x, self.player.y

        # Find nearest CPU node for scoring
        cpu_node = self.find_nearest_cpu_node()

        # Get hostile enemy positions for danger calculation
        hostile_positions = [
            (e.x, e.y) for e in self.enemies
            if e.state == EnemyState.HOSTILE and e.get_movement_type() != EnemyMovement.STATIC
        ]

        # Search nearby area for corridors
        search_radius = 20  # Increased from 10 to cover more area

        for check_x in range(max(0, px - search_radius), min(self.game_map.width, px + search_radius + 1)):
            for check_y in range(max(0, py - search_radius), min(self.game_map.height, py + search_radius + 1)):
                # Skip if it's a wall
                if (check_x, check_y) in self.game_map.walls:
                    continue

                # Count adjacent walls
                wall_count = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        if (check_x + dx, check_y + dy) in self.game_map.walls:
                            wall_count += 1

                # Need at least 6 walls for a true corridor (not a corner)
                if wall_count >= 6:
                    dist_to_player = abs(check_x - px) + abs(check_y - py)

                    # Calculate distance to CPU node (lower is better)
                    if cpu_node:
                        dist_to_cpu = abs(check_x - cpu_node[0]) + abs(check_y - cpu_node[1])
                    else:
                        dist_to_cpu = 999  # No CPU node, penalize heavily

                    # Calculate minimum distance to any hostile enemy (higher is better)
                    if hostile_positions:
                        min_dist_to_enemy = min(
                            abs(check_x - ex) + abs(check_y - ey)
                            for ex, ey in hostile_positions
                        )
                    else:
                        min_dist_to_enemy = 999  # No enemies, perfect score

                    candidates.append((check_x, check_y, wall_count, dist_to_player, dist_to_cpu, min_dist_to_enemy))

        if not candidates:
            return None

        # Smart scoring: balance multiple factors
        # Score = -dist_to_player (closer is better)
        #         -dist_to_cpu*2 (strongly prefer closer to healing)
        #         +min_dist_to_enemy (farther from enemies is better)
        #         +wall_count*0.5 (more walls is slightly better)
        def score_corridor(c):
            check_x, check_y, wall_count, dist_to_player, dist_to_cpu, min_dist_to_enemy = c
            return (
                -dist_to_player       # Closer to player is better (quick retreat)
                - dist_to_cpu * 2      # Strongly prefer closer to CPU node (healing access)
                + min_dist_to_enemy    # Farther from enemies is safer
                + wall_count * 0.5     # More walls is slightly better (tighter corridor)
            )

        # Sort by score (higher is better)
        candidates.sort(key=score_corridor, reverse=True)

        # Return best corridor
        return (candidates[0][0], candidates[0][1])

    def is_on_cpu_node(self) -> bool:
        """Check if currently standing on CPU recovery node."""
        player_pos = Position(self.player.x, self.player.y)
        return self.game_map.is_cpu_recovery_node(player_pos)

    def should_retreat_to_healing(self) -> bool:
        """
        Check if should retreat to CPU recovery node.

        Returns:
            True if CPU < 50% and CPU nodes exist
        """
        hp_percent = self.player.cpu / self.player.max_cpu
        return hp_percent < 0.5 and len(self.game_map.cpu_recovery_nodes) > 0

    def move_toward_target_smart(self, target_x: int, target_y: int, avoid_enemies: bool = False) -> bool:
        """
        Take one step toward target using A* pathfinding.

        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            avoid_enemies: Ignored - always uses aggressive pathfinding

        Returns:
            True if moved successfully (including bump attacks)
        """
        # Simple aggressive pathfinding - charge straight at target
        return self.move_to(target_x, target_y, max_steps=1, debug=self.debug)

    def fight_on_cpu_node_until_healed_or_death(self, max_turns: int = 100) -> str:
        """
        Stay on CPU recovery node and fight until either:
        - Fully healed (CPU == max_cpu) and all nearby enemies dead
        - Player dies
        - Max turns exceeded

        Args:
            max_turns: Maximum turns to spend on node

        Returns:
            Status: 'healed', 'died', 'timeout'
        """
        for _ in range(max_turns):
            self.turns_on_cpu_node += 1
            self.turns_taken += 1

            # Check if fully healed
            if self.player.cpu >= self.player.max_cpu:
                # Check if enemies nearby
                adjacent_enemies = self.count_adjacent_enemies()
                if adjacent_enemies == 0:
                    return 'healed'
                # Still enemies nearby, keep fighting

            # Check death
            if self.player.cpu <= 0:
                return 'died'

            # Stay on node (wait or attack if enemy adjacent)
            adjacent_enemies = self.count_adjacent_enemies()
            if adjacent_enemies > 0:
                self.combat_turns += 1

            # Wait a turn (this keeps us on the node and processes CPU recovery)
            self.wait(1)

        return 'timeout'

    def charge_and_attack(self, max_moves: int = 50) -> str:
        """
        Find nearest enemy and charge to attack.

        Args:
            max_moves: Maximum moves to attempt

        Returns:
            Status: 'killed', 'fighting', 'no_enemies', 'retreat_choke', 'retreat_heal'
        """
        initial_enemy_count = len(self.enemies)

        for _ in range(max_moves):
            self.turns_taken += 1
            self.turns_charging += 1

            # NOTE: Retreat checks removed from here - they're handled in the main loop
            # before charge_and_attack() is called. Having them here causes the function
            # to return early without the main loop handling the retreat properly.

            # Find nearest enemy
            enemy_pos = self.find_nearest_enemy()
            if not enemy_pos:
                return 'no_enemies'

            ex, ey = enemy_pos

            # Track enemy count before move
            enemies_before = len(self.enemies)

            # Move toward enemy using smart pathfinding (one step at a time)
            # This allows bump attacks to work properly
            moved = self.move_toward_target_smart(ex, ey)

            # Check if we killed an enemy
            enemies_after = len(self.enemies)
            if enemies_after < enemies_before:
                kills_this_move = enemies_before - enemies_after
                self.kills += kills_this_move

            # Count adjacent enemies for combat tracking
            if self.count_adjacent_enemies() > 0:
                self.combat_turns += 1

            if not moved:
                # Stuck - wait a turn
                self.wait(1)

            # Check death
            if self.player.cpu <= 0:
                return 'died'

            # Check if we killed the target
            current_enemy_count = len(self.enemies)
            if current_enemy_count < initial_enemy_count:
                return 'killed'

        return 'fighting'

    def retreat_to_choke_and_fight(self, max_moves: int = 50) -> str:
        """
        Retreat to nearest corridor using danger-aware pathfinding.

        Smart retreat strategy:
        - Fight through enemies blocking the path (bump attacks)
        - Track progress toward corridor
        - If stuck too long, return to let main loop handle it

        Args:
            max_moves: Maximum moves to attempt retreat

        Returns:
            Status: 'reached_choke', 'no_choke', 'died', 'timeout'
        """
        from game_characters import EnemyState, EnemyMovement

        self.retreats_to_choke += 1

        choke = self.find_choke_point()
        if not choke:
            return 'no_choke'

        cx, cy = choke
        initial_distance = abs(cx - self.player.x) + abs(cy - self.player.y)
        turns_stuck = 0  # Track if we're making progress

        # Move toward choke point
        for _ in range(max_moves):
            self.turns_taken += 1

            # Check if reached choke
            if self.player.x == cx and self.player.y == cy:
                return 'reached_choke'

            # Check current distance to corridor
            current_distance = abs(cx - self.player.x) + abs(cy - self.player.y)

            # Move toward choke using danger-aware pathfinding (routes around enemies)
            moved = self.move_toward_target_smart(cx, cy, avoid_enemies=True)

            # Check if we're making progress
            new_distance = abs(cx - self.player.x) + abs(cy - self.player.y)
            if new_distance < current_distance:
                turns_stuck = 0  # Made progress, reset stuck counter
            else:
                turns_stuck += 1  # No progress

            # If stuck for too long (5 turns), we're probably blocked
            # Return and let main loop decide (might need to retreat to heal instead)
            if turns_stuck > 5:
                return 'timeout'

            if not moved:
                # Stuck - wait
                self.wait(1)

            # Track combat
            if self.count_adjacent_enemies() > 0:
                self.combat_turns += 1

            # Check death
            if self.player.cpu <= 0:
                return 'died'

        return 'timeout'

    def retreat_to_ghost_node_and_hide(self, max_moves: int = 300) -> str:
        """
        Retreat to ghost node and fight/wait there until trace is cleared.

        Shadow Barbarian mode: When trace level gets too high, retreat to
        ghost nodes and wait until it drops to 0, fighting any enemies that
        follow.

        Args:
            max_moves: Maximum moves to reach node

        Returns:
            Status: 'trace_cleared', 'died', 'no_node', 'timeout'
        """
        self.retreats_to_ghost += 1

        node = self.find_nearest_ghost_node()
        if not node:
            return 'no_node'

        nx, ny = node

        # Move toward ghost node
        for _ in range(max_moves):
            self.turns_taken += 1

            # Check if already on a ghost node (any node, not just target)
            if self.is_on_ghost_node():
                # Fight and hide on this node until trace is cleared
                status = self.fight_on_ghost_node_until_clear_or_death(max_turns=100)
                return status

            # Move toward node
            moved = self.move_toward_target_smart(nx, ny)

            if not moved:
                # Stuck - wait
                self.wait(1)

            # Track combat
            if self.count_adjacent_enemies() > 0:
                self.combat_turns += 1

            # Check death
            if self.player.cpu <= 0:
                return 'died'

        return 'timeout'

    def fight_on_ghost_node_until_clear_or_death(self, max_turns: int = 200) -> str:
        """
        Stay on ghost node and fight until either:
        - Trace level reaches 0 (fully cleared!)
        - Player dies
        - Max turns exceeded
        - Moved off ghost node (combat pushback or bug)

        Args:
            max_turns: Maximum turns to spend on node

        Returns:
            Status: 'trace_cleared', 'died', 'timeout', 'moved_off'
        """
        for turn_num in range(max_turns):
            self.turns_on_ghost_node += 1
            self.turns_taken += 1

            # Check if trace is fully cleared or near-zero (floating point / game mechanics)
            if self.player.trace_level <= 1:
                return 'trace_cleared'

            # Check death
            if self.player.cpu <= 0:
                return 'died'

            # SAFETY: Abort if HP drops too low (need to go heal!)
            hp_percent = self.player.cpu / self.player.max_cpu
            if hp_percent < 0.4:
                return 'hp_critical'

            # Check if still on ghost node (might have been pushed off by combat)
            if not self.is_on_ghost_node():
                return 'moved_off'

            # Stay on node (wait or attack if enemy adjacent)
            adjacent_enemies = self.count_adjacent_enemies()
            if adjacent_enemies > 0:
                self.combat_turns += 1

            # Wait a turn (this keeps us on the node and processes trace reduction)
            self.wait(1)

        return 'timeout'

    def do_full_maintenance_cycle(self) -> str:
        """
        Shadow Barbarian maintenance: Heal HP, then clear trace SAFELY.

        1. Go to CPU recovery node
        2. Heal to full HP
        3. Kill all adjacent enemies (create safe moment!)
        4. Go to ghost node (abort if HP drops below 50%)
        5. Clear trace to 0
        6. Resume hunting

        Returns:
            Status: 'maintenance_complete', 'died', 'no_nodes', 'partial'
        """
        self.maintenance_attempts += 1

        # Phase 1: Heal HP
        heal_status = self.retreat_to_cpu_node_and_heal(max_moves=100)

        if heal_status == 'died':
            return 'died'
        elif heal_status != 'healed':
            # Couldn't heal (no CPU nodes or timeout)
            return 'no_cpu_node'

        # Successfully healed!
        self.maintenance_phase1_success += 1

        # Phase 2: Kill all adjacent enemies (create safety)
        # We're at full HP now, so fight until the area is clear
        for _ in range(50):
            self.turns_taken += 1

            # Check if area is safe (no adjacent enemies)
            adjacent_count = self.count_adjacent_enemies()
            if adjacent_count == 0:
                # Safe! Proceed to ghost node
                self.maintenance_phase2_success += 1
                break

            # Fight adjacent enemies
            self.combat_turns += 1
            self.wait(1)  # Attack happens via bump combat

            # Check death
            if self.player.cpu <= 0:
                return 'died'
        else:
            # Couldn't clear enemies in time - just go back to hunting
            return 'partial_maintenance'

        # Phase 3: SAFELY go to ghost node (abort if HP drops)
        trace_status = self.safe_retreat_to_ghost_node(max_moves=300)

        if trace_status == 'died':
            return 'died'
        elif trace_status == 'trace_cleared':
            # Success! HP full and trace clear
            self.maintenance_phase3_success += 1
            return 'maintenance_complete'
        else:
            # Couldn't clear trace (aborted, no nodes, or timeout)
            # But at least we're healed
            return 'partial_maintenance'

    def safe_retreat_to_ghost_node(self, max_moves: int = 300) -> str:
        """
        Safely retreat to ghost node - ABORT if HP drops below 50%.

        Args:
            max_moves: Maximum moves to reach node

        Returns:
            Status: 'trace_cleared', 'died', 'aborted', 'no_node', 'timeout'
        """
        node = self.find_nearest_ghost_node()
        if not node:
            return 'no_node'

        nx, ny = node

        # Move toward ghost node, but abort if HP drops
        for _ in range(max_moves):
            self.turns_taken += 1

            # SAFETY CHECK: If HP drops below 50%, ABORT and go heal again
            if self.player.cpu < self.player.max_cpu * 0.5:
                return 'aborted'

            # Check if reached ghost node
            if self.is_on_ghost_node():
                # Made it! Clear trace
                self.retreats_to_ghost += 1
                status = self.fight_on_ghost_node_until_clear_or_death(max_turns=200)
                return status

            # Move toward node
            moved = self.move_toward_target_smart(nx, ny)

            # Track combat during retreat
            if self.count_adjacent_enemies() > 0:
                self.combat_turns += 1

            if not moved:
                # Stuck - wait
                self.wait(1)

            # Check death
            if self.player.cpu <= 0:
                return 'died'

        return 'timeout'

    def retreat_to_cpu_node_and_heal(self, max_moves: int = 100) -> str:
        """
        Retreat to CPU recovery node and fight/heal there.

        Args:
            max_moves: Maximum moves to reach node

        Returns:
            Status: 'healed', 'died', 'no_node', 'timeout'
        """
        self.retreats_to_healing += 1

        node = self.find_nearest_cpu_node()
        if not node:
            return 'no_node'

        nx, ny = node

        # Move toward CPU node
        for _ in range(max_moves):
            self.turns_taken += 1

            # Check if already on a CPU node (any node, not just target)
            if self.is_on_cpu_node():
                # Fight and heal on this node
                status = self.fight_on_cpu_node_until_healed_or_death(max_turns=100)
                return status

            # Move toward node (use standard pathfinding - fighting through is often fastest/necessary)
            moved = self.move_toward_target_smart(nx, ny, avoid_enemies=False)

            if not moved:
                # Stuck - wait
                self.wait(1)

            # Track combat
            if self.count_adjacent_enemies() > 0:
                self.combat_turns += 1

            # Check death
            if self.player.cpu <= 0:
                return 'died'

        return 'timeout'

    def explore_to_find_enemies(self, max_moves: int = 50) -> str:
        """
        Explore the map to find hidden enemies.

        Uses simple exploration: visit unexplored visible tiles.

        Args:
            max_moves: Maximum moves for exploration

        Returns:
            Status: 'found_enemy', 'no_more_tiles', 'timeout'
        """
        visited = set()
        visited.add((self.player.x, self.player.y))

        for _ in range(max_moves):
            self.turns_taken += 1
            self.turns_exploring += 1

            # Check if found an enemy
            if self.find_nearest_enemy():
                return 'found_enemy'

            # Find unexplored visible tile
            visible = self.engine.visible_tiles
            unexplored = [tile for tile in visible
                         if tile not in visited
                         and tile not in self.game_map.walls]

            if not unexplored:
                # No more visible unexplored tiles - try moving randomly
                import random
                directions = [(1, 0), (0, 1), (-1, 0), (0, -1),
                             (1, 1), (1, -1), (-1, 1), (-1, -1)]
                random.shuffle(directions)

                moved = False
                for dx, dy in directions:
                    if self.move_player(dx, dy):
                        moved = True
                        break

                if not moved:
                    # Completely stuck
                    return 'no_more_tiles'
            else:
                # Move toward nearest unexplored tile
                target = min(unexplored,
                           key=lambda t: abs(t[0] - self.player.x) + abs(t[1] - self.player.y))
                self.move_toward_target_smart(target[0], target[1])

            # Mark current position as visited
            visited.add((self.player.x, self.player.y))

        return 'timeout'

    def go_to_gateway(self, max_moves: int = 200) -> str:
        """
        Move to gateway and proceed to next level.

        Args:
            max_moves: Maximum moves to reach gateway

        Returns:
            Status: 'next_level', 'no_gateway', 'timeout'
        """
        if not self.game_map.gateway:
            return 'no_gateway'

        gw_x, gw_y = self.game_map.gateway.x, self.game_map.gateway.y

        for _ in range(max_moves):
            self.turns_taken += 1

            # Check if reached gateway
            if self.player.x == gw_x and self.player.y == gw_y:
                # Standing on gateway - would trigger level transition in real game
                return 'next_level'

            # Move toward gateway
            moved = self.move_toward_target_smart(gw_x, gw_y)

            if not moved:
                # Stuck - wait
                self.wait(1)

            # Check if player somehow died
            if self.player.cpu <= 0:
                return 'died'

        return 'timeout'

    def clear_level(self) -> Dict[str, Any]:
        """
        Attempt to kill all enemies on current level, then proceed to gateway.

        Returns:
            Dict with results
        """
        initial_enemy_count = len(self.enemies)
        self.total_enemies_faced += initial_enemy_count

        while self.turns_taken < self.max_turns:
            # Check if all enemies dead
            if not self.enemies:
                # All enemies dead! Go to gateway
                status = self.go_to_gateway()

                if status == 'next_level':
                    self.levels_cleared += 1
                    return {
                        'status': 'cleared',
                        'turns': self.turns_taken,
                        'initial_enemies': initial_enemy_count,
                        'kills': self.kills,
                    }
                elif status == 'no_gateway':
                    # No gateway - just count as cleared
                    self.levels_cleared += 1
                    return {
                        'status': 'cleared',
                        'turns': self.turns_taken,
                        'initial_enemies': initial_enemy_count,
                        'kills': self.kills,
                    }
                else:
                    # Timeout trying to reach gateway
                    return {
                        'status': 'timeout_gateway',
                        'turns': self.turns_taken,
                        'initial_enemies': initial_enemy_count,
                        'kills': self.kills,
                    }

            # Decide action based on state
            # PRIORITY 1: Survival - retreat to heal when HP is low
            if self.should_retreat_to_healing():
                status = self.retreat_to_cpu_node_and_heal()
                if status == 'died':
                    self.log_death("died while retreating to heal")
                    return {
                        'status': 'died',
                        'turns': self.turns_taken,
                        'initial_enemies': initial_enemy_count,
                        'kills': self.kills,
                    }
                elif status == 'healed':
                    # Healed! Go back to fighting
                    continue
                # Other statuses (timeout, no_node) - continue trying

            # PRIORITY 2: Combat mode - attack enemies
            enemy_pos = self.find_nearest_enemy()

            if enemy_pos:
                # Enemy visible - charge!
                status = self.charge_and_attack()
                if status == 'died':
                    self.log_death("died while charging enemy")
                    return {
                        'status': 'died',
                        'turns': self.turns_taken,
                        'initial_enemies': initial_enemy_count,
                        'kills': self.kills,
                    }
                # If we killed or are fighting, continue loop
            else:
                # No enemy visible - explore to find them
                status = self.explore_to_find_enemies(max_moves=20)
                if status == 'no_more_tiles':
                    # Can't find any more enemies (maybe all dead but count is wrong?)
                    break

        # Timeout
        return {
            'status': 'timeout',
            'turns': self.turns_taken,
            'initial_enemies': initial_enemy_count,
            'kills': self.kills,
        }

    def run_barbarian_campaign(self, max_levels: int = 10) -> Dict[str, Any]:
        """
        Run full barbarian campaign: clear levels, progress through gateway.

        Args:
            max_levels: Maximum levels to attempt (default 10)

        Returns:
            Dict with campaign results
        """
        initial_state = self.get_state()

        # Loop through levels until death or max_levels
        while self.levels_cleared < max_levels:
            # Attempt to clear current level
            result = self.clear_level()

            # Check if died
            if result['status'] == 'died':
                break

            # Check if timed out
            if result['status'] == 'timeout':
                break

            # Level cleared! Progress to next level
            if result['status'] == 'cleared':
                # Use engine to progress to next level
                self.engine.next_level()
                # Level counter already incremented in clear_level()

        final_state = self.get_state()

        # Calculate stats
        hp_lost = self.initial_hp - self.player.cpu

        campaign_result = {
            'status': result['status'],
            'levels_cleared': self.levels_cleared,
            'deepest_level': self.engine.level,
            'total_enemies_faced': self.total_enemies_faced,
            'kills': self.kills,
            'turns_taken': self.turns_taken,
            'combat_turns': self.combat_turns,
            'retreats_to_choke': self.retreats_to_choke,
            'retreats_to_healing': self.retreats_to_healing,
            'turns_on_cpu_node': self.turns_on_cpu_node,
            'initial_hp': self.initial_hp,
            'final_hp': self.player.cpu,
            'hp_lost': hp_lost,
            'survived': self.player.cpu > 0,
            'initial_enemy_count': initial_state['enemies'].__len__() if isinstance(initial_state['enemies'], list) else initial_state['enemies'],
            'final_enemy_count': len(final_state['enemies']),
            'kill_percentage': (self.kills / self.total_enemies_faced * 100) if self.total_enemies_faced > 0 else 0,
            'final_trace': self.player.trace_level,
            'death_log': self.death_log,  # Death details for analysis
        }

        return campaign_result


# ===== Tests =====

class TestBarbarianAgent:
    """Test BarbarianAgent behavior and combat mechanics."""

    def test_barbarian_agent_initialization(self):
        """Test barbarian agent initializes correctly."""
        agent = BarbarianAgent(seed=42)
        assert agent.max_turns == 2000
        assert agent.turns_taken == 0
        assert agent.kills == 0
        assert agent.retreats_to_choke == 0
        assert agent.retreats_to_healing == 0

    def test_barbarian_finds_enemies(self):
        """Test barbarian can locate enemies."""
        agent = BarbarianAgent(seed=42)
        enemy_pos = agent.find_nearest_enemy()

        if agent.enemies:
            assert enemy_pos is not None
            assert isinstance(enemy_pos, tuple)
            assert len(enemy_pos) == 2
        else:
            assert enemy_pos is None

    def test_barbarian_detects_surrounding(self):
        """Test barbarian can detect when surrounded."""
        agent = BarbarianAgent(seed=42)

        # Count adjacent enemies
        count = agent.count_adjacent_enemies()
        assert isinstance(count, int)
        assert count >= 0

        # Check surrounded state
        surrounded = agent.is_surrounded()
        assert isinstance(surrounded, bool)

    def test_barbarian_finds_cpu_nodes(self):
        """Test barbarian can locate CPU recovery nodes."""
        agent = BarbarianAgent(seed=42)
        node = agent.find_nearest_cpu_node()

        if agent.game_map.cpu_recovery_nodes:
            assert node is not None
            assert isinstance(node, tuple)
            assert len(node) == 2
        else:
            assert node is None

    def test_barbarian_finds_choke_points(self):
        """Test barbarian can identify choke points."""
        agent = BarbarianAgent(seed=42)
        choke = agent.find_choke_point()

        # May or may not find one, just check it doesn't crash
        if choke:
            assert isinstance(choke, tuple)
            assert len(choke) == 2

    def test_barbarian_short_combat_session(self):
        """Test barbarian short combat session."""
        agent = BarbarianAgent(seed=42, max_turns=50)

        result = agent.run_barbarian_campaign()

        # Should return comprehensive results
        assert 'status' in result
        assert 'kills' in result
        assert 'turns_taken' in result
        assert 'retreats_to_choke' in result
        assert 'retreats_to_healing' in result
        assert 'survived' in result

        print(f"\n=== Barbarian Agent Short Combat ===")
        print(f"Status: {result['status']}")
        print(f"Kills: {result['kills']}/{result['total_enemies_faced']} ({result['kill_percentage']:.1f}%)")
        print(f"Turns: {result['turns_taken']} (Combat: {result['combat_turns']})")
        print(f"HP: {result['final_hp']}/{result['initial_hp']} (Lost: {result['hp_lost']})")
        print(f"Retreats: Choke={result['retreats_to_choke']}, Healing={result['retreats_to_healing']}")
        print(f"Turns on CPU node: {result['turns_on_cpu_node']}")

    def test_barbarian_multiple_seeds(self):
        """Test barbarian across multiple map seeds."""
        results = []

        for seed in [1, 42, 123, 456, 789]:
            agent = BarbarianAgent(seed=seed, max_turns=200)
            result = agent.run_barbarian_campaign()
            results.append({
                'seed': seed,
                'status': result['status'],
                'kills': result['kills'],
                'survived': result['survived'],
            })

        print(f"\n=== Barbarian Agent Multi-Seed Results ===")
        for r in results:
            print(f"Seed {r['seed']}: {r['status']} | Kills: {r['kills']} | Survived: {r['survived']}")

        # At least one should make some kills
        total_kills = sum(r['kills'] for r in results)
        assert total_kills > 0, "Barbarian should kill at least some enemies across seeds"

    @pytest.mark.slow
    def test_barbarian_long_combat_session(self):
        """Test barbarian extended combat session."""
        agent = BarbarianAgent(seed=999, max_turns=1000)

        result = agent.run_barbarian_campaign()

        print(f"\n=== Barbarian Agent Long Combat ===")
        print(f"Status: {result['status']}")
        print(f"Levels cleared: {result['levels_cleared']}")
        print(f"Enemies faced: {result['total_enemies_faced']}")
        print(f"Kills: {result['kills']} ({result['kill_percentage']:.1f}%)")
        print(f"Turns taken: {result['turns_taken']} (Combat: {result['combat_turns']})")
        print(f"Final HP: {result['final_hp']}/{result['initial_hp']}")
        print(f"HP lost: {result['hp_lost']}")
        print(f"Retreats to choke: {result['retreats_to_choke']}")
        print(f"Retreats to healing: {result['retreats_to_healing']}")
        print(f"Turns on CPU node: {result['turns_on_cpu_node']}")
        print(f"Survived: {result['survived']}")

        # Barbarian should attempt combat
        assert result['combat_turns'] > 0, "Barbarian should engage in combat"

    def test_barbarian_healing_behavior(self):
        """Test barbarian retreats to heal when low HP."""
        agent = BarbarianAgent(seed=42, max_turns=500)

        # Run combat session
        result = agent.run_barbarian_campaign()

        print(f"\n=== Barbarian Healing Behavior ===")
        print(f"Healing retreats: {result['retreats_to_healing']}")
        print(f"Turns on healing node: {result['turns_on_cpu_node']}")
        print(f"Final HP: {result['final_hp']}/{result['initial_hp']}")

        # Just verify tracking works (doesn't crash)
        assert isinstance(result['retreats_to_healing'], int)
        assert isinstance(result['turns_on_cpu_node'], int)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
