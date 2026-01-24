#!/usr/bin/env python3
"""
Prologue Diagnostic Tool - Simulates walking through the tutorial.

Traces player movement through each section using SMART agent behavior:
- Waits for patrols to move away before crossing doors
- Uses blindspots for stealth
- Times movements to avoid detection
- Demonstrates proper tutorial lesson learning

The agent is "constrained" to follow the intended stealth paths,
validating that the tutorial teaches the right lessons.

Run with: python scripts/diagnose_prologue.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Initialize directories first
from rsp.core.file_paths import initialize_data_directories
initialize_data_directories()

from rsp.core.config import GameSettings
from rsp.core.engine import GameEngine
from rsp.entities.base import Position
from rsp.systems.prologue_thoughts import reset_prologue_thoughts


def silent_settings():
    """Create GameSettings with all audio disabled."""
    settings = GameSettings()
    settings.master_volume = 0.0
    settings.sfx_volume = 0.0
    settings.music_volume = 0.0
    settings.graphics_mode = "glyph"
    return settings


class PrologueDiagnostic:
    """Diagnostic tool for prologue walkthrough."""

    def __init__(self):
        reset_prologue_thoughts()
        self.engine = GameEngine(
            settings=silent_settings(),
            prologue_mode=True,
            load_save=False,
        )
        # Dismiss intro dialogue
        if self.engine.dialogue_state.is_active():
            self.engine.dialogue_state.close()

        self.move_count = 0
        self.spotted_by = []
        self.kills = []

    def print_map_state(self):
        """Print current map state with player and enemy positions."""
        game_map = self.engine.game_map
        player = self.engine.player

        print("\n=== MAP STATE ===")
        print(f"Player at ({player.x}, {player.y}), CPU: {player.cpu}")
        print(f"Enemies: {len(self.engine.enemies)}")

        for enemy in self.engine.enemies:
            state = enemy.alert_state.name if hasattr(enemy, 'alert_state') else 'UNKNOWN'
            print(f"  {enemy.type} at ({enemy.position.x}, {enemy.position.y}) "
                  f"- State: {state}, Vision: {enemy.vision_range}, CPU: {enemy.cpu}")

        # Print relevant wall tiles for sections
        print("\n=== WALL CHECK (rows 4-15, cols 0-12) ===")
        for y in range(4, 16):
            row = ""
            for x in range(13):
                if (x, y) in game_map.walls:
                    row += "#"
                elif (x, y) in game_map.blind_spots:
                    row += "s"
                else:
                    row += "."
            print(f"  y={y:2d}: {row}")

        # Test LOS from section 2 to section 3
        print("\n=== LOS TEST: section isolation ===")
        from rsp.entities.base import Position
        p1 = Position(4, 5)   # Patrol in section 2
        p2 = Position(4, 9)   # Scanner in section 3
        los = game_map.has_line_of_sight(p1, p2)
        print(f"  LOS from patrol (4,5) to scanner (4,9): {los}")
        print(f"  Wall row 8 at x=0-9: {all((x,8) in game_map.walls for x in range(10))}")

    def check_visibility(self):
        """Check which enemies can see the player.

        IMPORTANT: Blind spots block enemy vision! If player is in a blind spot,
        enemies cannot see them regardless of distance or LOS.
        """
        player_pos = self.engine.player.position
        visible_enemies = []

        # Blind spots block ALL enemy vision
        if (player_pos.x, player_pos.y) in self.engine.game_map.blind_spots:
            return []

        for enemy in self.engine.enemies:
            # Check distance
            dist = player_pos.distance_to(enemy.position)
            if dist <= enemy.vision_range:
                # Check line of sight
                los = self.engine.game_map.has_line_of_sight(enemy.position, player_pos)
                if los:
                    visible_enemies.append((enemy, dist))

        return visible_enemies

    def is_in_blind_spot(self) -> bool:
        """Check if player is in a blind spot."""
        player_pos = (self.engine.player.x, self.engine.player.y)
        return player_pos in self.engine.game_map.blind_spots

    def is_position_visible_to_enemy(self, x: int, y: int, enemy) -> bool:
        """Check if a position would be visible to a specific enemy.

        Blind spots block all enemy vision.
        """
        # Blind spots block vision
        if (x, y) in self.engine.game_map.blind_spots:
            return False
        pos = Position(x, y)
        dist = pos.distance_to(enemy.position)
        if dist > enemy.vision_range:
            return False
        # Check line of sight
        return self.engine.game_map.has_line_of_sight(enemy.position, pos)

    def is_position_safe(self, x: int, y: int) -> bool:
        """Check if a position is safe from ALL enemy vision."""
        # Blind spots are always safe
        if (x, y) in self.engine.game_map.blind_spots:
            return True
        for enemy in self.engine.enemies:
            if self.is_position_visible_to_enemy(x, y, enemy):
                return False
        return True

    def get_nearby_enemies(self, y_min: int, y_max: int) -> list:
        """Get enemies within a Y-range (section)."""
        return [e for e in self.engine.enemies if y_min <= e.y <= y_max]

    def wait_until_safe(self, target_x: int, target_y: int, max_waits: int = 10) -> bool:
        """Wait until target position is safe to move to."""
        for _ in range(max_waits):
            if self.is_position_safe(target_x, target_y):
                return True
            self.wait()
            # Print enemy positions for debugging
            nearby = [e for e in self.engine.enemies if abs(e.y - target_y) <= 4]
            for e in nearby:
                print(f"    (waiting) {e.type} at ({e.x}, {e.y})")
        return False

    def move_via_blindspots(self, target_x: int, target_y: int, description: str = ""):
        """Move to target, preferring blindspot tiles when available."""
        while (self.engine.player.x, self.engine.player.y) != (target_x, target_y):
            px, py = self.engine.player.x, self.engine.player.y

            # Calculate direction to target
            dx = 1 if px < target_x else (-1 if px > target_x else 0)
            dy = 1 if py < target_y else (-1 if py > target_y else 0)

            # Try to find a blindspot step if we're near blindspots
            best_move = None
            for try_dx, try_dy in [(dx, dy), (dx, 0), (0, dy), (0, 0)]:
                if try_dx == 0 and try_dy == 0:
                    continue
                nx, ny = px + try_dx, py + try_dy
                if (nx, ny) in self.engine.game_map.blind_spots:
                    best_move = (try_dx, try_dy)
                    break

            # Use blindspot move if found, otherwise direct move
            if best_move:
                if not self.move(best_move[0], best_move[1], description):
                    # Blocked, try alternate
                    self.move(dx, 0, description) or self.move(0, dy, description)
            else:
                if not self.move(dx, dy, description):
                    if not self.move(dx, 0, description):
                        if not self.move(0, dy, description):
                            print(f"  [BLOCKED] at ({px}, {py})")
                            break

            if self.move_count > 200:
                print("  [ERROR] Too many moves!")
                break

    def move(self, dx: int, dy: int, description: str = "") -> bool:
        """Move player and report what happens."""
        old_pos = self.engine.player.position
        old_enemies = len(self.engine.enemies)

        # Check visibility BEFORE move
        pre_visible = self.check_visibility()

        # Make the move
        if self.engine.dialogue_state.is_active():
            self.engine.dialogue_state.close()

        self.engine.move_player(dx, dy)
        self.move_count += 1

        new_pos = self.engine.player.position
        moved = new_pos != old_pos

        # Check for combat
        if len(self.engine.enemies) < old_enemies:
            killed = old_enemies - len(self.engine.enemies)
            self.kills.append(f"Move {self.move_count}: Killed {killed} enemy")
            print(f"  [COMBAT] Killed {killed} enemy!")

        # Check visibility AFTER move
        post_visible = self.check_visibility()
        in_blind_spot = self.is_in_blind_spot()

        # Report
        action = f"({old_pos.x},{old_pos.y})->({new_pos.x},{new_pos.y})"
        if description:
            action = f"{description}: {action}"

        status = []
        if in_blind_spot:
            status.append("BLINDSPOT")
        if post_visible:
            for enemy, dist in post_visible:
                status.append(f"VISIBLE to {enemy.type}@{dist:.1f}")
                if enemy not in [e for e, _ in pre_visible]:
                    self.spotted_by.append(f"Move {self.move_count}: Spotted by {enemy.type}")
                    print(f"  [SPOTTED] by {enemy.type} at distance {dist:.1f}!")

        status_str = ", ".join(status) if status else "clear"
        print(f"Move {self.move_count}: {action} - {status_str}")

        return moved

    def wait(self):
        """Wait one turn."""
        if self.engine.dialogue_state.is_active():
            self.engine.dialogue_state.close()
        self.engine.game_session.process_turn()
        self.move_count += 1
        print(f"Move {self.move_count}: WAIT")

    def move_to(self, x: int, y: int, description: str = ""):
        """Move to target position using simple pathfinding with wall avoidance."""
        attempts = 0
        while (self.engine.player.x, self.engine.player.y) != (x, y):
            dx = 0
            dy = 0
            if self.engine.player.x < x:
                dx = 1
            elif self.engine.player.x > x:
                dx = -1
            if self.engine.player.y < y:
                dy = 1
            elif self.engine.player.y > y:
                dy = -1

            # Try diagonal first
            if dx != 0 and dy != 0:
                if self.move(dx, dy, description):
                    attempts = 0
                    continue
                # Diagonal blocked - try horizontal first, then vertical
                if self.move(dx, 0, description):
                    attempts = 0
                    continue
                if self.move(0, dy, description):
                    attempts = 0
                    continue
            elif dx != 0:
                if self.move(dx, 0, description):
                    attempts = 0
                    continue
            elif dy != 0:
                if self.move(0, dy, description):
                    attempts = 0
                    continue

            # Completely blocked
            attempts += 1
            if attempts > 3:
                print(f"  [BLOCKED] at ({self.engine.player.x}, {self.engine.player.y})")
                break

            if self.move_count > 200:
                print("  [ERROR] Too many moves!")
                break

    def walk_section_1(self):
        """Section 1: Melee - kill X to exit.

        LESSON: Melee combat basics - bump into enemies to attack.
        CONSTRAINT: Must kill X before door is accessible.
        SMART BEHAVIOR: After killing X, wait until patrol in section 2 is far
        from the door before crossing.
        """
        print("\n" + "="*50)
        print("SECTION 1: MELEE (kill X at door)")
        print("="*50)

        # X at (2, 3) blocks door at (3, 4)
        # Player starts at (1, 1)
        x_enemy = None
        for enemy in self.engine.enemies:
            if enemy.cpu == 5:  # Damaged scanner has 5 HP
                x_enemy = enemy
                print(f"  X (damaged scanner) at ({x_enemy.x}, {x_enemy.y})")
                break

        if x_enemy:
            # Move toward and attack X
            while x_enemy in self.engine.enemies and self.move_count < 20:
                dx = x_enemy.x - self.engine.player.x
                dy = x_enemy.y - self.engine.player.y
                # Normalize to single step
                if dx > 0: dx = 1
                elif dx < 0: dx = -1
                if dy > 0: dy = 1
                elif dy < 0: dy = -1
                self.move(dx, dy, "approach/attack X")

        # SMART: Wait at safe position (2,3) until the door tile (3,4) is safe
        # The patrol in section 2 can see through the door
        print("  [SMART] Waiting for section 2 patrol to move away from door...")
        self.move_to(2, 3, "position near door")
        if not self.wait_until_safe(3, 4, max_waits=8):
            print("  [WARNING] Door never became safe - proceeding anyway")

        # Move through door
        self.move_to(3, 4, "exit section 1")

    def walk_section_2(self):
        """Section 2: Turn-based - time the patrol.

        LESSON: Turn-based timing - enemies move on your turn, plan accordingly.
        CONSTRAINT: Patrol patrols right side (x=7-10), left wall is safe path.
        SMART BEHAVIOR: Stay against left wall (x=1), move down to door at (2, 8).
        Door is a blind spot - safe entry into Section 3.
        """
        print("\n" + "="*50)
        print("SECTION 2: TURN-BASED (observe patrol, use safe path)")
        print("="*50)

        # Patrol at (7, 6) patrols right side of corridor
        patrol = None
        for enemy in self.engine.enemies:
            if enemy.position.y == 6:
                patrol = enemy
                print(f"  Patrol at ({patrol.x}, {patrol.y}), vision: {patrol.vision_range}")
                break

        # SMART: Move to left wall - patrol is always far right, left is safe
        print("  [SMART] Moving to left wall (safe path)...")
        self.move_to(1, 5, "left wall")

        # No need to wait - patrol is always at x=7+ which is outside vision range
        print("  [SMART] Left path is safe, patrol at x=7+ (vision 4, distance 6+)")

        # Move down the left side to blind spot door at (2, 8)
        self.move_to(1, 7, "down left wall")
        self.move_to(2, 8, "enter section 3 via blind spot door")

    def walk_section_3(self):
        """Section 3: FOV + Blindspots - use blindspots to pass scanner.

        LESSON: Blind spots block enemy vision, use them for stealth.
        CONSTRAINT: Scanner at (4,9) has vision 5. Blind spots at (2,8) and (1-3, 9-11).
        SMART BEHAVIOR: Enter at blind spot door (2,8), move through blind spot
        corridor to exit at row 12.
        """
        print("\n" + "="*50)
        print("SECTION 3: FOV + BLINDSPOTS (scanner area)")
        print("="*50)

        # Scanner at (4, 9), blindspots at (2,8) and (1-3, 9-11)
        scanner = None
        for enemy in self.engine.enemies:
            if enemy.type == "scanner" and enemy.cpu > 5:  # Not damaged scanner
                scanner = enemy
                print(f"  Scanner at ({scanner.x}, {scanner.y}), vision: {scanner.vision_range}")
                break

        # Already in blind spot at (2,8) - continue through blind spot corridor
        print("  [SMART] Already in blind spot zone at entry...")

        # Move through blind spots (1-3, 9-11)
        self.move_via_blindspots(1, 9, "continue in blindspots")
        self.move_via_blindspots(1, 10, "traverse blindspots")
        self.move_via_blindspots(3, 10, "through blindspot row")

        # Show blindspot status
        if self.is_in_blind_spot():
            print("    Confirmed: in blind spot!")

        # Exit through door area at (3, 11) - still blind spot
        self.move_via_blindspots(3, 11, "exit through blind spot")
        self.move_to(3, 12, "enter section 4")

    def walk_section_4(self):
        """Section 4: Recovery node area - optional safety net.

        LESSON: Recovery nodes restore CPU if you take damage.
        CONSTRAINT: Patrol at x=8-10, left path is safe. Recovery at (6,12) optional.
        SMART BEHAVIOR: Stealth down left side, optionally grab recovery node.
        """
        print("\n" + "="*50)
        print("SECTION 4: RECOVERY NODE (optional safety net)")
        print("="*50)

        # Patrol at (8, 12), recovery at (6, 12)
        patrol = None
        for enemy in self.engine.enemies:
            if enemy.position.y == 12:
                patrol = enemy
                print(f"  Patrol at ({patrol.x}, {patrol.y}), vision: {patrol.vision_range}")
                break

        recovery_pos = (6, 12)
        print(f"  Recovery node at {recovery_pos}")
        print("  [SMART] Left path is safe (patrol at x=8+, vision 4)")

        # Move down left side - patrol is always far right
        self.move_to(1, 12, "sneak down left wall")

        # Optionally get recovery if needed
        print("  [SMART] Recovery node available if needed...")
        # Skip recovery for clean run, just exit
        self.move_to(3, 13, "approach section 5 door")
        self.move_to(3, 14, "enter section 5")

    def walk_section_5(self):
        """Section 5: Exploits + Ranged combat.

        LESSON: Exploits provide ranged attacks - patrol is at range, use exploit.
        CONSTRAINT: Patrol at (6, 15) is at range 3+ from exploit pickup.
        Walls at (4-5, 15) block direct melee approach from left.
        Exploit pickup at (3, 14), cooling node at (1, 14).
        SMART BEHAVIOR: Get cooling node, get exploit, patrol at range suggests ranged.
        """
        print("\n" + "="*50)
        print("SECTION 5: EXPLOITS + RANGED")
        print("="*50)

        # Cooling at (1, 14), exploit at (3, 14)
        # Walls at (4-5, 15), patrol at (6, 15) at range
        patrol = None
        for enemy in self.engine.enemies:
            if enemy.position.y == 15:
                patrol = enemy
                print(f"  Patrol at ({patrol.x}, {patrol.y})")
                break

        print("  Cooling node at (1, 14)")
        print("  Exploit pickup at (3, 14)")
        print("  Walls at (4-5, 15) + patrol at x=6 suggests ranged attack")

        # SMART: Get cooling node first for heat management
        print("  [SMART] Getting cooling node for heat management...")
        self.move_to(1, 14, "get cooling node")

        # Get exploit
        print("  [SMART] Getting exploit for ranged combat...")
        self.move_to(3, 14, "get exploit pickup")

        # Move toward section 6 - the wall forces us around
        # Note: In the real game, player would use exploit here
        print("  [SMART] Moving around wall toward section 6...")
        self.move_to(3, 15, "approach wall")

        # Check if patrol is still there
        if patrol and patrol in self.engine.enemies:
            print(f"  [NOTE] Patrol still at ({patrol.x}, {patrol.y}) - would use exploit here")
            # Move toward door at row 16
            self.move_to(3, 16, "approach door")
        else:
            print("  Patrol eliminated")

        self.move_to(3, 17, "enter section 6")

    def walk_section_6(self):
        """Section 6: Synthesis - path to gateway.

        LESSON: Combine all skills - blindspots, timing, and sprinting to escape.
        CONSTRAINT: Large open area with patrol at (5, 21), blindspots at (1-3, 17-21),
        ghost node at (5, 18), gateway at (26, 21).
        SMART BEHAVIOR: Use blindspots all the way down the left side, then wait
        for patrol to be away from the corridor opening, then sprint to gateway.
        """
        print("\n" + "="*50)
        print("SECTION 6: SYNTHESIS (to gateway)")
        print("="*50)

        # Blindspots at (1-3, 17-21), ghost at (5, 18)
        # Patrol at (5, 21), gateway at (26, 21)
        patrol = None
        for enemy in self.engine.enemies:
            if enemy.position.y == 21:
                patrol = enemy
                print(f"  Patrol at ({patrol.x}, {patrol.y})")
                break

        gateway = self.engine.game_map.gateway
        print(f"  Gateway at ({gateway.x}, {gateway.y})")
        print("  Ghost node at (5, 18)")
        print("  Blindspots: (1-3, 17-21)")

        # SMART: Use blindspots to traverse down the left side
        print("  [SMART] Using blindspots to move down left corridor...")
        self.move_via_blindspots(1, 17, "enter blindspot zone")
        self.move_via_blindspots(1, 18, "through blindspots")

        # Get ghost node if we pass by it
        print("  [SMART] Getting ghost node for extra stealth...")
        self.move_to(5, 18, "get ghost node")

        # Return to blindspot corridor
        self.move_via_blindspots(1, 19, "return to blindspots")
        self.move_via_blindspots(1, 20, "continue in blindspots")
        self.move_via_blindspots(1, 21, "bottom of blindspot corridor")

        # SMART: Wait for patrol to be far right before sprinting to gateway
        print("  [SMART] Waiting for patrol to move away from corridor opening...")
        waits = 0
        while patrol and patrol in self.engine.enemies and patrol.x < 10 and waits < 10:
            self.wait()
            waits += 1
            print(f"    Patrol at ({patrol.x}, {patrol.y})")

        if patrol and patrol in self.engine.enemies:
            if patrol.x >= 10:
                print("  Patrol moved right - sprinting to gateway!")
            else:
                print("  [WARNING] Patrol still blocking - attempting run anyway")
        else:
            print("  Path is clear!")

        # Sprint through the corridor opening to gateway
        print("  [SMART] Sprinting to gateway...")
        self.move_to(3, 21, "exit blindspots")
        self.move_to(16, 21, "through corridor door")
        self.move_to(26, 21, "reach gateway!")

    def run_full_walkthrough(self):
        """Run complete diagnostic walkthrough."""
        print("\n" + "#"*60)
        print("# PROLOGUE DIAGNOSTIC WALKTHROUGH")
        print("#"*60)

        self.print_map_state()

        self.walk_section_1()
        self.walk_section_2()
        self.walk_section_3()
        self.walk_section_4()
        self.walk_section_5()
        self.walk_section_6()

        print("\n" + "#"*60)
        print("# WALKTHROUGH SUMMARY")
        print("#"*60)
        print(f"Total moves: {self.move_count}")
        print(f"Times spotted: {len(self.spotted_by)}")
        for spotted in self.spotted_by:
            print(f"  - {spotted}")
        print(f"Kills: {len(self.kills)}")
        for kill in self.kills:
            print(f"  - {kill}")

        final_pos = self.engine.player.position
        gateway = self.engine.game_map.gateway
        print(f"\nFinal position: ({final_pos.x}, {final_pos.y})")
        if gateway:
            print(f"Gateway at: ({gateway.x}, {gateway.y})")
            if final_pos.x == gateway.x and final_pos.y == gateway.y:
                print("[SUCCESS] Reached gateway!")
            else:
                dist = final_pos.distance_to(gateway)
                print(f"[INCOMPLETE] {dist:.1f} tiles from gateway")


if __name__ == "__main__":
    diag = PrologueDiagnostic()
    diag.run_full_walkthrough()
