#!/usr/bin/env python3
"""
Prologue Diagnostic Tool - Simulates walking through the tutorial.

Traces player movement through each section, reporting:
- When/if player gets spotted
- By which enemy
- Whether stealth is possible
- Vision ranges and blind spot effectiveness

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
        """Check which enemies can see the player."""
        player_pos = self.engine.player.position
        visible_enemies = []

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
        """Section 1: Melee - kill X to exit."""
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

        # Move through door at (3,3) into section 2 corridor
        self.move_to(3, 4, "exit section 1")

    def walk_section_2(self):
        """Section 2: Turn-based - time the patrol."""
        print("\n" + "="*50)
        print("SECTION 2: TURN-BASED (time patrol crossing)")
        print("="*50)

        # Patrol at (4, 6) patrols horizontally in corridor
        patrol = None
        for enemy in self.engine.enemies:
            if enemy.position.y == 6:
                patrol = enemy
                print(f"  Patrol at ({patrol.x}, {patrol.y}), vision: {patrol.vision_range}")
                break

        # Wait for patrol to move away, then cross
        for _ in range(5):
            if patrol and patrol.x >= 6:
                print("  Patrol moved right - moving!")
                break
            self.wait()
            if patrol:
                print(f"  Patrol now at ({patrol.x}, {patrol.y})")

        # Move down corridor through door at (3, 8)
        self.move_to(1, 6, "sneak left side")
        self.move_to(3, 9, "exit section 2")

    def walk_section_3(self):
        """Section 3: FOV + Blindspots - use blindspots to pass scanner."""
        print("\n" + "="*50)
        print("SECTION 3: FOV + BLINDSPOTS (scanner area)")
        print("="*50)

        # Scanner at (4, 9), blindspots at (1-3, 10)
        scanner = None
        for enemy in self.engine.enemies:
            if enemy.type == "scanner" and enemy.cpu > 5:  # Not damaged scanner
                scanner = enemy
                print(f"  Scanner at ({scanner.x}, {scanner.y}), vision: {scanner.vision_range}")
                break

        # Move through blindspots on row 10 to avoid scanner
        print("  Attempting to move through blindspots...")
        self.move_to(2, 10, "enter blindspot")
        self.move_to(3, 11, "exit via door")
        self.move_to(3, 12, "exit section 3")

    def walk_section_4(self):
        """Section 4: Alert + Escape."""
        print("\n" + "="*50)
        print("SECTION 4: ALERT + ESCAPE")
        print("="*50)

        # Patrol at (4, 12), recovery at (6, 12)
        patrol = None
        for enemy in self.engine.enemies:
            if enemy.position.y == 12:
                patrol = enemy
                print(f"  Patrol at ({patrol.x}, {patrol.y})")
                break

        # Cross section - likely get spotted, use recovery node
        self.move_to(6, 12, "get recovery node")
        self.move_to(3, 14, "exit section 4")

    def walk_section_5(self):
        """Section 5: Exploits + Ranged combat."""
        print("\n" + "="*50)
        print("SECTION 5: EXPLOITS + RANGED")
        print("="*50)

        # Cooling at (1, 14), exploit at (3, 14)
        # Wall at (4, 15), patrol at (6, 15) behind wall
        patrol = None
        for enemy in self.engine.enemies:
            if enemy.position.y == 15:
                patrol = enemy
                print(f"  Patrol at ({patrol.x}, {patrol.y})")
                break

        # Get exploit, use ranged to defeat patrol behind wall
        self.move_to(3, 14, "get exploit")
        self.move_to(3, 17, "exit section 5")

    def walk_section_6(self):
        """Section 6: Synthesis - path to gateway."""
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

        # Use blindspots on left side, then run to gateway
        print("  Attempting stealth path through blindspots...")
        self.move_to(2, 21, "in blindspot row")
        self.move_to(16, 21, "approach gateway via door")
        self.move_to(26, 21, "reach gateway")

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
