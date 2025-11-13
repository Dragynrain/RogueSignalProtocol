#!/usr/bin/env python3
"""
Ninja Agent - Pacifist Stealth Testing

Tests stealth-to-victory gameplay:
- NinjaAgent: Gateway-seeking pacifist that avoids all combat
- Tests vision-aware pathfinding and evasion mechanics
- Validates stealth as a complete gameplay strategy

Real ninjas were spies, not assassins - this agent tests infiltration
mechanics and whether a pure stealth playthrough is viable.
"""


import pytest

from game_entities import EnemyState
from tests.test_agent import GameTestAgent


class StealthMixin:
    """
    Shared stealth mechanics for stealth-based agents.

    Provides common detection monitoring, enemy tracking, and
    awareness state inspection utilities.
    """

    def is_detected(self) -> bool:
        """
        Check if player has been detected by any enemy.

        Returns:
            True if any enemy is ALERT or HOSTILE
        """
        for enemy in self.enemies:
            if enemy.state in (EnemyState.ALERT, EnemyState.HOSTILE):
                return True
        return False

    def get_enemy_states(self) -> dict:
        """
        Get current states of all enemies.

        Returns:
            Dict mapping enemy state names to counts
        """
        states = {}
        for enemy in self.enemies:
            state_name = enemy.state.name
            states[state_name] = states.get(state_name, 0) + 1
        return states

    def find_nearest_enemy(self):
        """
        Find nearest enemy to player.

        Returns:
            Enemy object or None
        """
        if not self.enemies:
            return None

        player_pos = (self.player.x, self.player.y)
        min_dist = float("inf")
        nearest = None

        for enemy in self.enemies:
            dist = abs(enemy.x - player_pos[0]) + abs(enemy.y - player_pos[1])
            if dist < min_dist:
                min_dist = dist
                nearest = enemy

        return nearest


class NinjaAgent(GameTestAgent, StealthMixin):
    """
    Pacifist stealth agent that seeks gateways while avoiding combat.

    Strategy:
    - Find gateway and path toward it
    - Avoid enemy vision cones
    - If detected, run away and hide
    - Never engage in combat
    - Test stealth-to-victory viability

    Validates:
    - Vision-aware pathfinding
    - Evasion and escape mechanics
    - Gateway reachability under stealth
    - Pacifist playthrough balance
    - Enemy coordination and blind spots
    """

    def __init__(self, seed=None, max_turns=2000):
        """
        Initialize ninja agent.

        Args:
            seed: Random seed for deterministic testing
            max_turns: Maximum turns to attempt (default 1000)
        """
        super().__init__(seed=seed, level=1)
        self.max_turns = max_turns
        self.turns_taken = 0
        self.detection_events = 0
        self.evasion_attempts = 0
        self.successful_evasions = 0
        self.gateway_reached = False
        self.damage_taken = 0
        self.initial_hp = self.player.cpu
        self.blind_spot_moves = 0
        self.visible_moves = 0
        self.wait_turns = 0
        self.explored_tiles = set()  # Track where we've been
        self.gateway_found = False  # Track if we've seen the gateway
        self.gateway_found_turn = 0

    def get_gateway_position(self) -> tuple[int, int] | None:
        """
        Find gateway/uplink position on map.

        Returns:
            (x, y) tuple of gateway position, or None if not found
        """
        if self.game_map.gateway:
            return (self.game_map.gateway.x, self.game_map.gateway.y)
        return None

    def is_position_safe(self, x: int, y: int) -> bool:
        """
        Check if a position is safe (no enemies very close).

        Args:
            x: X coordinate to check
            y: Y coordinate to check

        Returns:
            True if no enemies within danger radius
        """
        danger_radius = 3  # Consider "safe" if enemies are 3+ tiles away

        for enemy in self.enemies:
            dist = max(abs(enemy.x - x), abs(enemy.y - y))
            if dist < danger_radius:
                return False

        return True

    def get_collective_enemy_vision(self) -> set:
        """
        Get all tiles visible to any enemy (collective FOV).

        Returns:
            Set of (x, y) tuples that are in at least one enemy's vision
        """
        enemy_vision = set()

        # Use visibility manager for efficient FOV computation
        visibility_manager = self.engine.visibility_manager
        current_turn = self.engine.turn

        for enemy in self.enemies:
            # Use the enemy FOV cache mechanism
            enemy_key = (enemy.x, enemy.y, enemy.type_data.vision)

            # Check if already cached
            if visibility_manager._enemy_cache_turn != current_turn:
                visibility_manager._enemy_fov_cache.clear()
                visibility_manager._enemy_cache_turn = current_turn

            if enemy_key not in visibility_manager._enemy_fov_cache:
                visibility_manager._enemy_fov_cache[enemy_key] = (
                    visibility_manager._compute_fov_set(enemy.x, enemy.y, enemy.type_data.vision)
                )

            # Add this enemy's vision to collective vision
            enemy_vision.update(visibility_manager._enemy_fov_cache[enemy_key])

        return enemy_vision

    def is_tile_in_blind_spot(self, x: int, y: int) -> bool:
        """
        Check if a tile is in a blind spot (not visible to any enemy).

        Args:
            x: X coordinate to check
            y: Y coordinate to check

        Returns:
            True if tile is not visible to any enemy
        """
        enemy_vision = self.get_collective_enemy_vision()
        return (x, y) not in enemy_vision

    def find_evasion_direction(self) -> tuple[int, int] | None:
        """
        Find best direction to run away from enemies.

        Returns:
            (dx, dy) direction tuple, or None if no clear escape
        """
        if not self.enemies:
            return None

        # Find average enemy position to run opposite direction
        avg_enemy_x = sum(e.x for e in self.enemies) / len(self.enemies)
        avg_enemy_y = sum(e.y for e in self.enemies) / len(self.enemies)

        # Run away from average enemy position
        dx = -1 if avg_enemy_x > self.player.x else (1 if avg_enemy_x < self.player.x else 0)
        dy = -1 if avg_enemy_y > self.player.y else (1 if avg_enemy_y < self.player.y else 0)

        return (dx, dy)

    def evade_and_hide(self, max_moves=20) -> bool:
        """
        Attempt to evade detection by retreating through known safe areas.

        Strategy:
        - Run back through explored tiles (known terrain)
        - Prefer blind spots (no enemy vision)
        - Move away from enemies
        - Use methodical retreat, not random panic

        Args:
            max_moves: Maximum moves to attempt evasion

        Returns:
            True if successfully evaded (no longer detected)
        """
        self.evasion_attempts += 1

        for _ in range(max_moves):
            if not self.is_detected():
                # Successfully evaded!
                self.successful_evasions += 1
                return True

            # Find best evasion move (explored + blind spots + away from enemies)
            direction = self.find_evasion_direction()
            if not direction:
                # No clear direction - wait
                self.wait(1)
                self.turns_taken += 1
                continue

            dx, dy = direction

            # Score all possible moves for evasion
            candidates = []
            for try_dx, try_dy in [
                (dx, dy),
                (dx, 0),
                (0, dy),
                (-dx, -dy),
                (1, 0),
                (0, 1),
                (-1, 0),
                (0, -1),
            ]:
                if try_dx == 0 and try_dy == 0:
                    continue

                target_x = self.player.x + try_dx
                target_y = self.player.y + try_dy

                # Check bounds
                if not (
                    0 <= target_x < self.game_map.width and 0 <= target_y < self.game_map.height
                ):
                    continue

                # Check walkable
                if (target_x, target_y) in self.game_map.walls:
                    continue

                # Check not on enemy
                if any(e.x == target_x and e.y == target_y for e in self.enemies):
                    continue

                # Score factors:
                # 1. Is it explored? (known safe) +10
                # 2. Is it a blind spot? (no vision) +5
                # 3. Distance from nearest enemy +distance
                score = 0

                if (target_x, target_y) in self.explored_tiles:
                    score += 10

                if self.is_tile_in_blind_spot(target_x, target_y):
                    score += 5

                # Distance to nearest enemy
                min_enemy_dist = min(
                    (abs(e.x - target_x) + abs(e.y - target_y) for e in self.enemies), default=0
                )
                score += min_enemy_dist

                candidates.append((try_dx, try_dy, score))

            # Try best moves first
            candidates.sort(key=lambda c: c[2], reverse=True)

            moved = False
            for move_dx, move_dy, score in candidates:
                if self.move_player(move_dx, move_dy):
                    moved = True
                    break

            if not moved:
                # Completely stuck
                self.wait(1)

            self.turns_taken += 1

            if self.player.cpu <= 0:
                # Died during evasion
                return False

        # Still detected after max_moves
        return False

    def update_exploration(self):
        """Update explored tiles based on current player vision."""
        # Get all tiles player can currently see
        visible_tiles = self.engine.visibility_manager.get_player_visible_tiles(
            self.player, self.engine.turn
        )
        self.explored_tiles.update(visible_tiles)

        # Check if gateway is now visible
        gateway_pos = self.get_gateway_position()
        if gateway_pos and not self.gateway_found:
            if gateway_pos in visible_tiles:
                self.gateway_found = True
                self.gateway_found_turn = self.turns_taken

    def count_nearby_blind_spots(self, x: int, y: int, radius: int = 5) -> int:
        """
        Count blind spot tiles near a position (cluster quality).

        Args:
            x, y: Position to check around
            radius: How far to look

        Returns:
            Number of blind spot tiles in radius
        """
        count = 0
        enemy_vision = self.get_collective_enemy_vision()

        for check_x in range(max(0, x - radius), min(self.game_map.width, x + radius + 1)):
            for check_y in range(max(0, y - radius), min(self.game_map.height, y + radius + 1)):
                if (check_x, check_y) not in enemy_vision:
                    count += 1

        return count

    def evaluate_path_risk(self, target_x: int, target_y: int) -> dict:
        """
        Evaluate risk of path to target.

        Returns dict with:
        - path_length: Number of steps
        - consecutive_visible: Max consecutive tiles in enemy vision
        - total_visible: Total visible tiles in path
        - risk_score: Overall risk (lower = safer)
        """
        # Simple greedy path for now (could use A* for better accuracy)
        path = []
        cx, cy = self.player.x, self.player.y

        while (cx, cy) != (target_x, target_y) and len(path) < 100:
            # Move toward target
            dx = 1 if target_x > cx else (-1 if target_x < cx else 0)
            dy = 1 if target_y > cy else (-1 if target_y < cy else 0)

            cx += dx
            cy += dy
            path.append((cx, cy))

        # Analyze path
        enemy_vision = self.get_collective_enemy_vision()

        consecutive_visible = 0
        max_consecutive = 0
        total_visible = 0

        for px, py in path:
            if (px, py) in enemy_vision:
                consecutive_visible += 1
                total_visible += 1
                max_consecutive = max(max_consecutive, consecutive_visible)
            else:
                consecutive_visible = 0

        # Risk scoring:
        # - 1 tile in vision = 1 point (safe, alert grace)
        # - 2-5 tiles no vision = 2 points (safe, no one watching)
        # - 2+ consecutive tiles in vision = 20+ points (DANGEROUS)
        if max_consecutive <= 1:
            risk_score = 1  # Safe
        elif total_visible == 0:
            risk_score = 2  # Very safe, pure blind spots
        else:
            # Penalize consecutive visible tiles heavily
            risk_score = 10 + (max_consecutive * 10)

        return {
            "path_length": len(path),
            "consecutive_visible": max_consecutive,
            "total_visible": total_visible,
            "risk_score": risk_score,
        }

    def find_nearest_unexplored(self) -> tuple[int, int] | None:
        """
        Find best unexplored target using risk-aware search.

        Considers:
        - Distance to unexplored area
        - Path risk (consecutive tiles in enemy vision)
        - Blind spot cluster quality (worth the risk?)

        Returns:
            (x, y) tuple of best unexplored target, or None
        """
        from collections import deque

        # BFS to find all nearby unexplored tiles
        visited = set()
        queue = deque([(self.player.x, self.player.y)])
        visited.add((self.player.x, self.player.y))

        unexplored_candidates = []

        while queue and len(unexplored_candidates) < 10:  # Find up to 10 candidates
            x, y = queue.popleft()

            # Check all neighbors
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                nx, ny = x + dx, y + dy

                if (nx, ny) in visited:
                    continue

                if not (0 <= nx < self.game_map.width and 0 <= ny < self.game_map.height):
                    continue

                if (nx, ny) in self.game_map.walls:
                    continue

                # Found unexplored tile!
                if (nx, ny) not in self.explored_tiles:
                    unexplored_candidates.append((nx, ny))
                    if len(unexplored_candidates) >= 10:
                        break

                visited.add((nx, ny))
                queue.append((nx, ny))

        if not unexplored_candidates:
            return None

        # Evaluate each candidate
        best_target = None
        best_score = float("inf")

        for ux, uy in unexplored_candidates:
            # Evaluate path risk
            risk = self.evaluate_path_risk(ux, uy)

            # Count blind spots near target (is it worth reaching?)
            cluster_quality = self.count_nearby_blind_spots(ux, uy, radius=5)

            # Score: balance risk vs reward
            # Lower risk + higher cluster quality = better score
            score = risk["risk_score"] - (cluster_quality * 0.1)

            if score < best_score:
                best_score = score
                best_target = (ux, uy)

        return best_target

    def find_frontier_tiles(self) -> list[tuple[int, int]]:
        """
        Find frontier tiles - explored tiles next to unexplored areas.
        These are good places to continue methodical exploration.

        Returns:
            List of (x, y) frontier tiles
        """
        frontier = []

        for ex, ey in self.explored_tiles:
            # Check if this explored tile is next to unexplored area
            has_unexplored_neighbor = False

            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                nx, ny = ex + dx, ey + dy

                if not (0 <= nx < self.game_map.width and 0 <= ny < self.game_map.height):
                    continue

                if (nx, ny) not in self.explored_tiles and (nx, ny) not in self.game_map.walls:
                    has_unexplored_neighbor = True
                    break

            if has_unexplored_neighbor:
                frontier.append((ex, ey))

        return frontier

    def find_unexplored_move(self) -> tuple[int, int] | None:
        """
        Find a move toward unexplored areas using methodical exploration.

        Strategy:
        - Find frontier tiles (explored tiles next to unexplored)
        - Pick closest frontier tile
        - Move toward it to continue systematic exploration

        Returns:
            (dx, dy) tuple for best move, or None
        """
        # Find frontier tiles for methodical exploration
        frontier = self.find_frontier_tiles()

        if not frontier:
            # No frontier - try finding any unexplored tile
            unexplored_target = self.find_nearest_unexplored()
            if not unexplored_target:
                return None
            target_x, target_y = unexplored_target
        else:
            # Pick closest frontier tile
            closest_frontier = min(
                frontier, key=lambda pos: abs(pos[0] - self.player.x) + abs(pos[1] - self.player.y)
            )
            target_x, target_y = closest_frontier

        # Move toward target (greedy)
        dx = 1 if target_x > self.player.x else (-1 if target_x < self.player.x else 0)
        dy = 1 if target_y > self.player.y else (-1 if target_y < self.player.y else 0)

        return (dx, dy)

    def move_toward_gateway_sprint(self, max_moves=50) -> str:
        """
        Explore map to find gateway, then approach it.

        Strategy:
        - Phase 1: Explore in blind spots, find gateway
        - Phase 2: Once found, move toward it
        - Take 1-3 tile risks through visible areas to reach new zones
        - Evade if detected

        Args:
            max_moves: Maximum turns to attempt

        Returns:
            Status string: 'reached', 'detected', 'died', 'no_gateway', or 'timeout'
        """
        gateway_pos = self.get_gateway_position()
        if not gateway_pos:
            return "no_gateway"

        gw_x, gw_y = gateway_pos

        while self.turns_taken < max_moves:
            # Update what we've explored
            self.update_exploration()

            # Check if reached gateway
            if self.player.x == gw_x and self.player.y == gw_y:
                self.gateway_reached = True
                return "reached"

            # Check if detected (ALERT or HOSTILE)
            if self.is_detected():
                self.detection_events += 1

                # Decision: evade or sprint to gateway?
                # If gateway found, skip evasion and just GO FOR IT
                if not self.gateway_found:
                    # Gateway not found yet - try to evade
                    if not self.evade_and_hide():
                        # Evasion failed - check if we should give up
                        map_size = self.game_map.width * self.game_map.height
                        explored_pct = len(self.explored_tiles) / map_size

                        if self.player.cpu <= 0:
                            return "died"

                        # Give up if <40% explored and gateway not found
                        if explored_pct < 0.4:
                            return "detected"
                        # else: keep going even while detected!

                # Update exploration after evasion attempt (or skipping it)
                self.update_exploration()

            # Calculate exploration progress for adaptive strategy
            map_size = self.game_map.width * self.game_map.height
            explored_pct = len(self.explored_tiles) / map_size

            # Choose movement strategy based on whether we've found gateway
            moved = False

            if self.gateway_found:
                # Phase 2: Move toward known gateway
                dx = 1 if gw_x > self.player.x else (-1 if gw_x < self.player.x else 0)
                dy = 1 if gw_y > self.player.y else (-1 if gw_y < self.player.y else 0)

                # Try moves toward gateway
                for try_dx, try_dy in [(dx, dy), (dx, 0), (0, dy)]:
                    if try_dx == 0 and try_dy == 0:
                        continue
                    if self.move_player(try_dx, try_dy):
                        moved = True
                        is_blind = self.is_tile_in_blind_spot(self.player.x, self.player.y)
                        if is_blind:
                            self.blind_spot_moves += 1
                        else:
                            self.visible_moves += 1
                        break
            else:
                # Phase 1: Explore to find gateway

                # Desperate sprint mode: >80% explored, haven't found gateway
                if explored_pct > 0.8:
                    # Pick direction with most unexplored tiles and SPRINT
                    # Count unexplored tiles in each quadrant
                    quadrants = {"N": 0, "S": 0, "E": 0, "W": 0}

                    for x in range(self.game_map.width):
                        for y in range(self.game_map.height):
                            if (x, y) not in self.explored_tiles and (
                                x,
                                y,
                            ) not in self.game_map.walls:
                                # Relative to player
                                if y < self.player.y:
                                    quadrants["N"] += 1
                                else:
                                    quadrants["S"] += 1
                                if x < self.player.x:
                                    quadrants["W"] += 1
                                else:
                                    quadrants["E"] += 1

                    # Sprint toward largest unexplored quadrant
                    best_direction = (
                        max(quadrants, key=quadrants.get) if any(quadrants.values()) else None
                    )

                    if best_direction:
                        # DESPERATE SPRINT - ignore safety, just GO
                        sprint_dx = {"W": -1, "E": 1}.get(best_direction, 0)
                        sprint_dy = {"N": -1, "S": 1}.get(best_direction, 0)

                        if sprint_dx != 0 or sprint_dy != 0:
                            for try_dx, try_dy in [
                                (sprint_dx, sprint_dy),
                                (sprint_dx, 0),
                                (0, sprint_dy),
                            ]:
                                if try_dx == 0 and try_dy == 0:
                                    continue
                                if self.move_player(try_dx, try_dy):
                                    moved = True
                                    self.visible_moves += 1  # Don't care about blind spots now!
                                    break

                # Normal exploration if not desperate or sprint failed
                if not moved:
                    explore_move = self.find_unexplored_move()
                    if explore_move:
                        dx, dy = explore_move
                        if self.move_player(dx, dy):
                            moved = True
                            is_blind = self.is_tile_in_blind_spot(self.player.x, self.player.y)
                            if is_blind:
                                self.blind_spot_moves += 1
                            else:
                                self.visible_moves += 1

            # If still stuck, try any valid move
            if not moved:
                for try_dx, try_dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                    if self.move_player(try_dx, try_dy):
                        moved = True
                        self.visible_moves += 1
                        break

            if not moved:
                self.wait_turns += 1
                self.wait(1)

            self.turns_taken += 1

            # Track damage
            current_hp = self.player.cpu
            if current_hp < self.initial_hp:
                self.damage_taken = self.initial_hp - current_hp

            if self.player.cpu <= 0:
                return "died"

        return "timeout"

    def run_pacifist_attempt(self) -> dict:
        """
        Attempt pacifist stealth run to gateway.

        Returns:
            Dict with results of pacifist attempt
        """
        initial_state = self.get_state()

        # Attempt to reach gateway
        status = self.move_toward_gateway_sprint(max_moves=self.max_turns)

        final_state = self.get_state()

        # Calculate stats
        total_moves = self.blind_spot_moves + self.visible_moves
        blind_spot_percent = (self.blind_spot_moves / total_moves * 100) if total_moves > 0 else 0

        result = {
            "status": status,
            "gateway_reached": self.gateway_reached,
            "turns_taken": self.turns_taken,
            "detection_events": self.detection_events,
            "evasion_attempts": self.evasion_attempts,
            "successful_evasions": self.successful_evasions,
            "damage_taken": self.damage_taken,
            "initial_hp": self.initial_hp,
            "final_hp": self.player.cpu,
            "survived": self.player.cpu > 0,
            "pacifist": self.damage_taken == 0,  # True pacifist = no damage
            "initial_enemy_count": len(initial_state["enemies"]),
            "final_enemy_count": len(final_state["enemies"]),
            "enemy_states": self.get_enemy_states(),
            "blind_spot_moves": self.blind_spot_moves,
            "visible_moves": self.visible_moves,
            "blind_spot_percent": blind_spot_percent,
            "wait_turns": self.wait_turns,
            "explored_tiles": len(self.explored_tiles),
            "gateway_found": self.gateway_found,
            "gateway_found_turn": self.gateway_found_turn if self.gateway_found else None,
        }

        return result


# ===== Tests =====


class TestNinjaAgent:
    """Test NinjaAgent behavior and pacifist stealth mechanics."""

    def test_ninja_agent_initialization(self):
        """Test ninja agent initializes correctly."""
        agent = NinjaAgent(seed=42)
        assert agent.max_turns == 2000
        assert agent.turns_taken == 0
        assert agent.detection_events == 0
        assert agent.evasion_attempts == 0
        assert not agent.gateway_reached

    def test_ninja_agent_finds_gateway(self):
        """Test ninja agent can locate gateway."""
        agent = NinjaAgent(seed=42)
        gateway_pos = agent.get_gateway_position()

        # Should find gateway on map
        assert gateway_pos is not None
        assert isinstance(gateway_pos, tuple)
        assert len(gateway_pos) == 2

    def test_ninja_agent_detection_mixin(self):
        """Test ninja agent has stealth mixin capabilities."""
        agent = NinjaAgent(seed=42)

        # Should have detection checking
        detected = agent.is_detected()
        assert isinstance(detected, bool)

        # Should get enemy states
        states = agent.get_enemy_states()
        assert isinstance(states, dict)

        # Should find nearest enemy
        enemy = agent.find_nearest_enemy()
        # May or may not be enemies, just check it doesn't crash
        assert enemy is None or hasattr(enemy, "x")

    def test_ninja_agent_safety_checking(self):
        """Test ninja agent can evaluate position safety."""
        agent = NinjaAgent(seed=42)

        # Player's current position safety
        is_safe = agent.is_position_safe(agent.player.x, agent.player.y)
        assert isinstance(is_safe, bool)

        # Gateway position safety
        gateway_pos = agent.get_gateway_position()
        if gateway_pos:
            gw_x, gw_y = gateway_pos
            is_safe = agent.is_position_safe(gw_x, gw_y)
            assert isinstance(is_safe, bool)

    def test_ninja_agent_evasion_direction(self):
        """Test ninja agent can calculate evasion direction."""
        agent = NinjaAgent(seed=42)

        direction = agent.find_evasion_direction()

        if agent.enemies:
            # Should have evasion direction if enemies exist
            assert direction is not None
            assert isinstance(direction, tuple)
            assert len(direction) == 2
        else:
            # No enemies = no direction needed
            assert direction is None

    def test_ninja_agent_gateway_movement(self):
        """Test ninja agent attempts to reach gateway."""
        agent = NinjaAgent(seed=42)

        # Short attempt toward gateway
        status = agent.move_toward_gateway_sprint(max_moves=20)

        # Should return valid status
        valid_statuses = ["reached", "detected", "died", "stuck", "moving", "timeout", "no_gateway"]
        assert status in valid_statuses

        # Should have taken some turns
        assert agent.turns_taken >= 0

    def test_ninja_agent_pacifist_attempt_short(self):
        """Test ninja agent short pacifist run."""
        agent = NinjaAgent(seed=42, max_turns=100)

        result = agent.run_pacifist_attempt()

        # Should return comprehensive results
        assert "status" in result
        assert "gateway_reached" in result
        assert "detection_events" in result
        assert "evasion_attempts" in result
        assert "damage_taken" in result
        assert "pacifist" in result

        # Pacifist = no damage taken
        if result["damage_taken"] == 0:
            assert result["pacifist"]

        print("\n=== Ninja Agent Short Run ===")
        print(f"Status: {result['status']}")
        print(f"Gateway reached: {result['gateway_reached']}")
        print(f"Turns: {result['turns_taken']}")
        print(f"Explored tiles: {result['explored_tiles']}")
        print(
            f"Gateway found: {result['gateway_found']} (turn {result['gateway_found_turn']})"
            if result["gateway_found"]
            else "Gateway found: False"
        )
        print(f"Detections: {result['detection_events']}")
        print(f"Evasions: {result['successful_evasions']}/{result['evasion_attempts']}")
        print(f"Damage: {result['damage_taken']} (Pacifist: {result['pacifist']})")
        print(
            f"Blind spot moves: {result['blind_spot_moves']}/{result['blind_spot_moves'] + result['visible_moves']} ({result['blind_spot_percent']:.1f}%)"
        )

    def test_ninja_agent_multiple_seeds(self):
        """Test ninja agent across multiple map seeds."""
        results = []

        for seed in [1, 42, 123, 456, 789]:
            agent = NinjaAgent(seed=seed, max_turns=200)
            result = agent.run_pacifist_attempt()
            results.append(
                {
                    "seed": seed,
                    "status": result["status"],
                    "gateway_reached": result["gateway_reached"],
                    "pacifist": result["pacifist"],
                }
            )

        print("\n=== Ninja Agent Multi-Seed Results ===")
        for r in results:
            print(
                f"Seed {r['seed']}: {r['status']} | Gateway: {r['gateway_reached']} | Pacifist: {r['pacifist']}"
            )

        # At least one should make some progress (not all die immediately)
        statuses = [r["status"] for r in results]
        assert "reached" in statuses or "moving" in statuses or "timeout" in statuses

    @pytest.mark.slow
    def test_ninja_agent_long_pacifist_run(self):
        """Test ninja agent extended pacifist attempt."""
        agent = NinjaAgent(seed=999, max_turns=1000)

        result = agent.run_pacifist_attempt()

        print("\n=== Ninja Agent Long Run ===")
        print(f"Status: {result['status']}")
        print(f"Gateway reached: {result['gateway_reached']}")
        print(f"Turns taken: {result['turns_taken']}/{agent.max_turns}")
        print(f"Explored tiles: {result['explored_tiles']}")
        print(
            f"Gateway found: {result['gateway_found']} (turn {result['gateway_found_turn']})"
            if result["gateway_found"]
            else "Gateway found: False"
        )
        print(f"Detection events: {result['detection_events']}")
        print(f"Evasion success: {result['successful_evasions']}/{result['evasion_attempts']}")
        print(f"Final HP: {result['final_hp']}/{result['initial_hp']}")
        print(f"Damage taken: {result['damage_taken']}")
        print(f"Pure pacifist: {result['pacifist']}")
        print(
            f"Blind spot moves: {result['blind_spot_moves']}/{result['blind_spot_moves'] + result['visible_moves']} ({result['blind_spot_percent']:.1f}%)"
        )
        print(f"Enemy states: {result['enemy_states']}")

        # Should survive the attempt (even if doesn't reach gateway)
        assert result["survived"], "Ninja agent should survive long run"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
