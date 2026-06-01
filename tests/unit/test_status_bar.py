#!/usr/bin/env python3
"""
Status bar rendering tests.

Focus: the prologue-mode "TOO CLOSE!" audio cue, which is the only place
the status bar triggers a sound. Regression coverage for the play_sound()
keyword-argument signature (volume_modifier, not volume).
"""

import types
import unittest
from unittest.mock import create_autospec

import tcod.console

from rsp.systems.audio import SoundManager
from rsp.ui.status_bar import StatusBarRenderer
from tests.fixtures.simple_fixtures import player


def _prologue_game(sound_manager, spotted=True):
    """Minimal game object exercising the prologue visibility-status path."""
    return types.SimpleNamespace(
        player=player(10, 10, 100),
        prologue_mode=True,
        prologue_spotted_in_blind_spot=spotted,
        game_map=types.SimpleNamespace(blind_spots=set()),
        sound_manager=sound_manager,
    )


class TestPrologueBlindSpotAlert(unittest.TestCase):
    """The 'spotted in blind spot' cue must call play_sound with a valid signature."""

    def test_alert_cue_uses_valid_play_sound_signature(self):
        # autospec enforces the real play_sound signature, so a wrong keyword
        # (e.g. volume= instead of volume_modifier=) raises TypeError just like
        # production - a plain Mock would silently accept anything and hide the bug.
        sound_manager = create_autospec(SoundManager, instance=True)
        renderer = StatusBarRenderer(settings=None)
        console = tcod.console.Console(80, 50)
        game = _prologue_game(sound_manager, spotted=True)

        # Must not raise (the bug raised TypeError, which the surrounding
        # except clause does not catch).
        renderer.render_top_status_bar(console, game)

        sound_manager.play_sound.assert_called_once()
        args, kwargs = sound_manager.play_sound.call_args
        self.assertEqual(args[0], "alert")
        self.assertNotIn("volume", kwargs)
        self.assertEqual(kwargs.get("volume_modifier"), 0.5)

    def test_no_cue_when_not_spotted(self):
        sound_manager = create_autospec(SoundManager, instance=True)
        renderer = StatusBarRenderer(settings=None)
        console = tcod.console.Console(80, 50)
        game = _prologue_game(sound_manager, spotted=False)

        renderer.render_top_status_bar(console, game)

        sound_manager.play_sound.assert_not_called()


if __name__ == "__main__":
    unittest.main()
