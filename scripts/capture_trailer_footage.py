#!/usr/bin/env python3
"""
Auto-play trailer capture driver.

Stands up the real rendered game (window, tileset, SDL renderer, tile manager,
engine) exactly as the normal launch path does, attaches a FrameRecorder, then
plays a curated run while every frame is captured through the real render
pipeline.

The run is genuine gameplay, not staged particle bursts: the player moves
through the level (vision cones + enemy movement-prediction arrows render),
slips into a blind spot while a patrol advances along its predicted path, then
earns its kills by bump-attacking enemies and firing a real exploit, before
trace rises, the Admin Avatar spawns and pursues, and the run ends.

Each narrative beat is marked as a segment (with its full-screen text card) so
scripts/build_trailer.py can cut per beat and interleave the cards instead of
merging everything into one blob.

Output (default marketing/capture, override with --out):
    frame_000001.png ...        one PNG per presented frame
    events.json                 fps/size manifest + segments + event tags

Run (graphics mode is required for sprites/particles):
    .venv/Scripts/python.exe scripts/capture_trailer_footage.py --frames 900

A game window opens, plays itself, and closes. No interaction required.
"""

import argparse
import logging
import os
import random
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import tcod  # noqa: E402

from rsp.core.config import GameConfig, GameSettings  # noqa: E402
from rsp.core.engine import GameEngine  # noqa: E402
from rsp.core.file_paths import use_sandbox_data_directory  # noqa: E402
from rsp.core.loop import initialize_tcod_context  # noqa: E402
from rsp.entities.base import Position  # noqa: E402
from rsp.rendering.core import GameRenderer  # noqa: E402
from rsp.rendering.tiles import TileManager  # noqa: E402
from rsp.systems.frame_recorder import FrameRecorder  # noqa: E402

FPS = 30
FRAME_DT = 1.0 / FPS
# Minimum beat length: long enough to read its caption (~3s).
BEAT_FRAMES = 90
# A seed whose map keeps the stealth beats clean (no enemy notices the player).
DEFAULT_SEED = 5


def _sign(n):
    n = int(n)  # coerce numpy scalars; numpy booleans can't be subtracted
    return (n > 0) - (n < 0)


class TrailerDriver:
    """Plays scripted-but-genuine gameplay beats, rendering every frame."""

    def __init__(self, game, renderer, console, context, recorder, frame_budget):
        self.game = game
        self.renderer = renderer
        self.console = console
        self.context = context
        self.recorder = recorder
        self.frame_budget = frame_budget
        self.frames_rendered = 0
        self._beat_start = 0

    # --- frame pump -------------------------------------------------------

    def render_frames(self, count):
        """Render `count` frames through the real pipeline (capture happens via
        the installed present() hook). Advances particle animation each frame."""
        for _ in range(count):
            if self.frames_rendered >= self.frame_budget:
                return
            # Never let a confirmation/story modal wedge the scripted run. The
            # death screen is the exception: it is the payoff of the end beat.
            try:
                if self.game.dialogue_state.is_active() and not self.game.game_over:
                    self.game.dialogue_state.close()
            except Exception:
                pass
            # Kill achievement popups before they render over the gameplay.
            try:
                mgr = getattr(self.game, "achievement_popup_manager", None)
                if mgr is not None:
                    mgr.active_popup = None
                    mgr.popup_queue.clear()
                from rsp.systems.achievements import AchievementManager

                AchievementManager.clear_pending_popups()
            except Exception:
                pass
            ps = getattr(self.game, "particle_system", None)
            if ps is not None:
                ps.update(FRAME_DT)
            self.renderer.render_game(self.console, self.game, self.context)
            self.frames_rendered += 1
            for _ in tcod.event.get():
                pass

    def budget_left(self):
        return self.frames_rendered < self.frame_budget

    # --- world helpers ----------------------------------------------------

    def _player_pos(self):
        return self.game.player.x, self.game.player.y

    def walkable(self, x, y):
        pos = Position(x, y)
        try:
            return self.game.game_map.is_valid_position(pos) and not self.game.game_map.is_wall(pos)
        except Exception:
            return False

    def _occupied(self, x, y):
        try:
            return self.game._get_enemy_at(Position(x, y)) is not None
        except Exception:
            return False

    def find_floor(self, min_r, max_r, blind=None, in_view=False):
        """Return a free walkable tile between radii of the player, optionally
        constrained to blind-spot (True) or non-blind (False) tiles, and to
        tiles the player can see. Skips tiles occupied by an enemy or the
        player."""
        px, py = self._player_pos()
        for r in range(min_r, max_r + 1):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    x, y = px + dx, py + dy
                    if (x, y) == (px, py) or not self.walkable(x, y) or self._occupied(x, y):
                        continue
                    if in_view and not self._player_sees(x, y):
                        continue
                    if blind is not None:
                        try:
                            if self.game.game_map.is_blind_spot(Position(x, y)) != blind:
                                continue
                        except Exception:
                            if blind:
                                continue
                    return x, y
        return None

    def _player_sees(self, x, y):
        try:
            player = self.game.player
            return self.game.game_map.can_see_position(
                player.position, Position(x, y), player.get_vision_range()
            )
        except Exception:
            return False

    def spawn(self, x, y, enemy_type):
        try:
            if not self.walkable(x, y):
                return None
            return self.game.enemy_manager.spawn_enemy(Position(x, y), enemy_type)
        except Exception as e:
            logging.warning("[DRIVER] spawn %s failed: %s", enemy_type, e)
            return None

    def step_player_toward(self, tx, ty, hold=8):
        """One real player move toward a target (a turn is processed)."""
        px, py = self._player_pos()
        dx, dy = _sign(tx - px), _sign(ty - py)
        if dx == 0 and dy == 0:
            return
        try:
            self.game.move_player(dx, dy)
        except Exception as e:
            logging.warning("[DRIVER] move failed: %s", e)
        self.render_frames(hold)

    def _seen_at(self, x, y):
        """Would any enemy see the player standing on (x, y)? Uses the real
        can_see_player() rules, checked from each enemy's current tile and
        its next planned move (the tile it will occupy after this turn)."""
        player = self.game.player
        game_map = self.game.game_map
        original = player.position
        player.position = Position(x, y)
        try:
            for e in self.game.enemies:
                if e.type == "admin":
                    continue
                if e.can_see_player(player, game_map):
                    return True
                if e.move_queue:
                    here = e.position
                    e.position = e.move_queue[0]
                    try:
                        if e.can_see_player(player, game_map):
                            return True
                    finally:
                        e.position = here
            return False
        except Exception:
            return False
        finally:
            player.position = original

    def sneak_toward(self, tx, ty, hold=8):
        """One real turn toward a target, only onto tiles no enemy can see.
        If no hidden tile is closer, waits in place when that is hidden too,
        otherwise backs off to any hidden neighbor."""
        px, py = self._player_pos()
        here_d = max(abs(tx - px), abs(ty - py))
        best, best_d = None, None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                x, y = px + dx, py + dy
                if (dx, dy) == (0, 0) or not self.walkable(x, y) or self._occupied(x, y):
                    continue
                if self._seen_at(x, y):
                    continue
                d = max(abs(tx - x), abs(ty - y))
                if best_d is None or d < best_d:
                    best, best_d = (dx, dy), d
        if best is not None and best_d >= here_d and not self._seen_at(px, py):
            best = None  # nothing gained by moving and staying put is safe
        if best is None:
            self.advance_turns(1, hold=hold)
            return
        try:
            self.game.move_player(*best)
        except Exception as e:
            logging.warning("[DRIVER] move failed: %s", e)
        self.render_frames(hold)

    def _detected(self):
        """Any non-admin enemy alerted or hunting the player."""
        from rsp.entities.enums import EnemyState

        return [e for e in self.game.enemies if e.type != "admin" and e.state != EnemyState.UNAWARE]

    def advance_turns(self, n, hold=10):
        """Process real game turns (enemy AI moves) with frames rendered."""
        for _ in range(n):
            if not self.budget_left():
                return
            try:
                self.game.process_turn()
            except Exception as e:
                logging.warning("[DRIVER] process_turn failed: %s", e)
            self.render_frames(hold)

    # --- beats ------------------------------------------------------------

    def _pin_trace_zero(self):
        """Hold trace at 0 during the stealth phases so the HUD stays calm and
        the Admin never spawns early. Released at the 'loud' phase."""
        try:
            self.game.player.trace_level = 0
        except Exception:
            pass

    def _visible_enemy(self):
        """A patrol/enemy the player can currently see (so its arrows render)."""
        try:
            for e in self.game.enemies:
                if self.game.player.can_see_enemy(e, self.game.game_map):
                    return e
        except Exception:
            pass
        return None

    def _adjacent_enemy(self):
        px, py = self._player_pos()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                try:
                    e = self.game._get_enemy_at(Position(px + dx, py + dy))
                except Exception:
                    e = None
                if e is not None:
                    return e
        return None

    def _force_aware(self, enemy):
        """Lock an enemy onto the player's current tile so it actively pursues
        (same mechanism the Admin Avatar uses). Makes its prediction arrows
        point at the player and keeps it following."""
        if enemy is None:
            return
        try:
            from rsp.entities.enums import EnemyState

            enemy.state = EnemyState.HOSTILE
            enemy.last_seen_player = Position(self.game.player.x, self.game.player.y)
        except Exception as e:
            logging.warning("[DRIVER] could not force awareness: %s", e)

    def _longest_open_dir(self, max_len=9):
        """Cardinal direction with the most consecutive walkable tiles ahead."""
        px, py = self._player_pos()
        best, best_len = (1, 0), -1
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            n = 0
            while n < max_len and self.walkable(px + dx * (n + 1), py + dy * (n + 1)):
                n += 1
            if n > best_len:
                best, best_len = (dx, dy), n
        return best, best_len

    def _report_stealth(self, phase):
        """Warn if a stealth beat ended with the player detected (red cones
        and 'detected you' log lines would contradict the caption)."""
        seen = self._detected()
        if seen:
            logging.warning(
                "[DRIVER] %s: %d enemy(s) aware of the player: %s",
                phase,
                len(seen),
                ", ".join(f"{e.type}@{e.x},{e.y}" for e in seen),
            )

    def _beat_frames(self):
        """Frames captured since the current beat began."""
        return self.recorder.frame_count - self._beat_start

    def _begin_beat(self, label, overlay):
        self._beat_start = self.recorder.frame_count
        self.recorder.begin_segment(label, overlay=overlay)

    def _sneak_ahead(self, until_frames, hold=9):
        """Advance along the most open direction without being seen, one real
        turn at a time, until the beat has run `until_frames` frames. Turns
        keep enemies moving, so the beat never sits on a still frame."""
        (dx, dy), run = self._longest_open_dir()
        px, py = self._player_pos()
        goal = (px + dx * max(run, 1), py + dy * max(run, 1))
        while self.budget_left() and self._beat_frames() < until_frames:
            self.sneak_toward(*goal, hold=hold)
            self._pin_trace_zero()

    def phase_infiltrate(self):
        """Phase 1: slip into the network. A patrol is in view but too far to
        spot the player; the HUD stays calm. Opens with the tagline."""
        self._begin_beat(
            "infiltrate", "A coffee break cyberspace stealth roguelike"
        )
        self._pin_trace_zero()
        # In view (so its arrows show from the first frame) but beyond its
        # 4-tile vision.
        spot = self.find_floor(6, 8, blind=False, in_view=True) or self.find_floor(
            5, 8, blind=False, in_view=True
        )
        if spot:
            self.spawn(spot[0], spot[1], "patrol")
        self.render_frames(12)
        self._sneak_ahead(BEAT_FRAMES)
        self._report_stealth("infiltrate")

    def phase_read(self):
        """Phase 2: a patrol shows its next-3-moves arrows; the player reads
        them and routes around, still undetected."""
        self._begin_beat("read", "See their next moves. Plan around them.")
        self._pin_trace_zero()
        if self._visible_enemy() is None:
            spot = self.find_floor(5, 7, blind=False, in_view=True)
            if spot:
                self.spawn(spot[0], spot[1], "patrol")
        # Let the patrol advance a turn so its arrows visibly move, then
        # route around it.
        self.advance_turns(1, hold=10)
        self._pin_trace_zero()
        self._sneak_ahead(BEAT_FRAMES + 15)
        self._report_stealth("read")

    def phase_strike(self):
        """Phase 3: slip into a blind spot unseen, then take an unaware enemy
        down from cover in one stealth hit."""
        self._begin_beat("strike", "Hit from the dark, not head-on.")
        self._pin_trace_zero()
        blind = self.find_floor(1, 4, blind=True)
        if blind:
            for _ in range(5):
                if self._player_pos() == blind:
                    break
                self.sneak_toward(blind[0], blind[1], hold=9)
                self._pin_trace_zero()
        self.render_frames(8)
        # A bot wanders into reach and is struck before its turn comes up.
        spot = self.find_floor(1, 1)
        target = self.spawn(spot[0], spot[1], "bot") if spot else None
        if target is not None:
            self.render_frames(8)
            self.step_player_toward(target.x, target.y, hold=8)
            self._pin_trace_zero()
        self._report_stealth("strike")
        self.render_frames(26)  # takedown explosion blooms
        self._sneak_ahead(BEAT_FRAMES)

    def phase_spend(self):
        """Phase 4: fire a real exploit - heat and RAM tick up."""
        self._begin_beat("spend", "Exploits cost heat and RAM.")
        self._pin_trace_zero()
        try:
            self.game.player.inventory_manager.equipped_exploits = [
                "code_injection",
                *self.game.player.inventory_manager.equipped_exploits,
            ]
        except Exception as e:
            logging.warning("[DRIVER] equip failed: %s", e)
        targets = []
        for off in [(3, 0), (3, 1), (4, -1)]:
            d0 = abs(off[0]) + abs(off[1])
            spot = self.find_floor(d0, d0 + 1, blind=False)
            if spot:
                e = self.spawn(spot[0], spot[1], "bot")
                if e:
                    targets.append(e)
        self.render_frames(16)  # captioned pause, then the detonation
        if targets:
            try:
                self.game.exploit_system.execute_exploit(
                    "code_injection", Position(targets[0].x, targets[0].y)
                )
            except Exception as e:
                logging.warning("[DRIVER] exploit failed: %s", e)
        self.render_frames(32)
        while self.budget_left() and self._beat_frames() < BEAT_FRAMES:
            self.advance_turns(1, hold=9)
            self._pin_trace_zero()

    def phase_loud(self):
        """Phase 5: it goes loud. Trace climbs, nearby enemies lock on, the
        Admin Avatar spawns and hunts."""
        self._begin_beat("loud", "Draw too much heat and the Admin hunts you.")
        chasers = [
            e for e in self.game.enemies if self.game.player.can_see_enemy(e, self.game.game_map)
        ][:3]
        if not chasers and self.game.enemies:
            chasers = self.game.enemies[:3]
        for e in chasers:
            self._force_aware(e)
        try:
            self.game.player.trace_level = GameConfig.MAX_TRACE_LEVEL
            self.game.game_session.turn_manager._check_admin_spawn()
        except Exception as e:
            logging.warning("[DRIVER] admin spawn failed: %s", e)
        # Hits land and CPU drains for real, but the run survives to the end
        # beat, where the death screen is the payoff.
        player = self.game.player
        real_take_damage = player.take_damage
        player.take_damage = lambda dmg: real_take_damage(min(dmg, max(0, player.cpu - 10)))
        try:
            self.render_frames(20)
            (dx, dy), _ = self._longest_open_dir()
            while self.budget_left() and self._beat_frames() < BEAT_FRAMES + 15:
                for e in chasers:
                    self._force_aware(e)
                px, py = self._player_pos()
                if self.walkable(px + dx, py + dy) and not self._occupied(px + dx, py + dy):
                    self.step_player_toward(px + dx, py + dy, hold=9)
                else:
                    self.advance_turns(1, hold=9)  # cornered; the hunters close in
        finally:
            del player.take_damage

    def phase_end(self):
        """Phase 6: the run ends - permadeath."""
        self._begin_beat("end", "Permadeath. Die once and the save is gone.")
        self.render_frames(10)
        # Let the hunters land the killing blow on a real turn; force it only
        # if nobody connects.
        if not self.game.game_over:
            self.game.player.cpu = min(self.game.player.cpu, 5)
            self.advance_turns(1, hold=6)
        if not self.game.game_over:
            try:
                self.game.player.cpu = 0
                self.game.death_handler.check_death("combat", "admin")
            except Exception as e:
                logging.warning("[DRIVER] death failed: %s", e)
        self.render_frames(75)  # hold on the CONSCIOUSNESS PURGED screen

    def run(self):
        for phase in (
            self.phase_infiltrate,
            self.phase_read,
            self.phase_strike,
            self.phase_spend,
            self.phase_loud,
            self.phase_end,
        ):
            try:
                phase()
            except Exception as e:
                logging.warning("[DRIVER] phase %s failed: %s", phase.__name__, e)


def main():
    parser = argparse.ArgumentParser(description="Capture trailer footage automatically.")
    parser.add_argument("--out", default=None, help="Output directory for frames + events.json")
    parser.add_argument("--frames", type=int, default=900, help="Max frames to capture")
    parser.add_argument(
        "--timeout",
        type=float,
        default=150.0,
        help="Wall-clock seconds before the watchdog force-finalizes",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="RNG seed; fixes the map and enemy behavior so a capture is repeatable",
    )
    args = parser.parse_args()
    random.seed(args.seed)

    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    # The scripted run dies at the end, which deletes the save and records
    # metrics/achievements. Point all user data at a throwaway directory so
    # the player's real save and progress are never touched.
    sandbox = Path(tempfile.mkdtemp(prefix="rsp_trailer_data_"))
    if not use_sandbox_data_directory(sandbox):
        sys.exit(f"Could not use sandbox data directory {sandbox}.")
    print(f"[DRIVER] User data sandboxed in {sandbox}", flush=True)
    GameConfig.load_from_json()

    out_dir = Path(args.out) if args.out else REPO_ROOT / "marketing" / "capture"
    out_dir.mkdir(parents=True, exist_ok=True)

    settings = GameSettings()
    settings.graphics_mode = "graphics"

    context = initialize_tcod_context(settings)
    win = getattr(context, "sdl_window", None)
    if win is not None:
        try:
            win.restore()
            win.size = (1920, 1080)
        except Exception as e:
            logging.warning("[DRIVER] could not force 1080p window: %s", e)

    console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

    tile_manager = TileManager(context, settings)
    tile_manager.preload_common_tiles()

    game = GameEngine(settings=settings, load_save=False)
    game.tile_manager = tile_manager
    if game.dialogue_state.is_active():
        game.dialogue_state.close()

    # Suppress confirmation modals that would block scripted actions.
    try:
        game.friendly_fire_confirmed = True
        settings.dialogue_preferences = {
            "show_system_crash_warning": False,
            "show_friendly_fire_warning": False,
        }
        if hasattr(game, "settings"):
            game.settings.show_achievement_popups = False
    except Exception as e:
        logging.warning("[DRIVER] could not suppress modals: %s", e)

    renderer = GameRenderer(settings, tile_manager=tile_manager, context=context)

    recorder = FrameRecorder(out_dir, enabled=True, fps=FPS)
    game.frame_recorder = recorder
    recorder.install()

    print(f"[DRIVER] Capturing up to {args.frames} frames -> {out_dir}", flush=True)
    start = time.time()

    # Safety net: if any beat wedges, always write whatever we captured and
    # force-exit (SDL/tcod can otherwise keep the process alive after close()).
    def watchdog():
        time.sleep(args.timeout)
        print(f"[DRIVER] Watchdog fired after {args.timeout}s; finalizing.", flush=True)
        try:
            recorder.finalize()
        except Exception:
            pass
        os._exit(0)

    threading.Thread(target=watchdog, daemon=True).start()

    try:
        TrailerDriver(game, renderer, console, context, recorder, args.frames).run()
    finally:
        recorder.finalize()
        try:
            context.close()
        except Exception:
            pass

    print(
        f"[DRIVER] Seed {args.seed}. Done: {recorder.frame_count} frames in {time.time() - start:.1f}s -> {out_dir}",
        flush=True,
    )
    shutil.rmtree(sandbox, ignore_errors=True)
    # Force-exit past any lingering SDL/audio threads that block a clean return.
    os._exit(0)


if __name__ == "__main__":
    main()
