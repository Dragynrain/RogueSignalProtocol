#!/usr/bin/env python3
"""
Unit tests for FrameRecorder - in-engine gameplay frame capture for trailers.

The recorder grabs the fully-composited SDL backbuffer (read_pixels) as PNG
frames and tags the frame index of highlight-worthy events (enemy explosions,
player death, admin avatar spawn) into events.json for automated trailer
assembly.

These tests use a fake SDL renderer so they run headless with no window.
"""

import json

import numpy as np
import pytest
from PIL import Image

from rsp.systems.frame_recorder import FrameRecorder


class FakeSDLRenderer:
    """Minimal stand-in for tcod.sdl.render.Renderer.

    Returns a solid-color RGBA frame so tests can assert on pixel content
    without a real window/backbuffer.
    """

    def __init__(self, width=8, height=4, color=(10, 20, 30, 255)):
        self.width = width
        self.height = height
        self.color = color
        self.present_calls = 0

    def read_pixels(self):
        frame = np.empty((self.height, self.width, 4), dtype=np.uint8)
        frame[:, :] = self.color
        return frame

    def present(self):
        self.present_calls += 1


@pytest.fixture
def renderer():
    return FakeSDLRenderer()


def test_disabled_recorder_captures_nothing(tmp_path, renderer):
    rec = FrameRecorder(output_dir=tmp_path, enabled=False)
    for _ in range(3):
        rec.capture(renderer)
    rec.finalize()

    assert list(tmp_path.glob("*.png")) == []
    assert rec.frame_count == 0


def test_capture_writes_sequential_pngs(tmp_path, renderer):
    rec = FrameRecorder(output_dir=tmp_path, enabled=True)
    for _ in range(3):
        rec.capture(renderer)
    rec.finalize()

    frames = sorted(tmp_path.glob("frame_*.png"))
    assert len(frames) == 3
    # Zero-padded, sortable names
    assert frames[0].name == "frame_000001.png"
    assert frames[2].name == "frame_000003.png"

    # Pixels round-trip to the color the renderer produced
    img = Image.open(frames[0]).convert("RGBA")
    assert img.size == (renderer.width, renderer.height)
    assert img.getpixel((0, 0)) == renderer.color


def test_capture_returns_frame_index(tmp_path, renderer):
    rec = FrameRecorder(output_dir=tmp_path, enabled=True)
    assert rec.capture(renderer) == 1
    assert rec.capture(renderer) == 2
    assert rec.frame_count == 2


def test_tag_event_binds_to_next_frame(tmp_path, renderer):
    """An event tagged before a capture should point at that upcoming frame."""
    rec = FrameRecorder(output_dir=tmp_path, enabled=True)
    rec.capture(renderer)  # frame 1
    rec.tag_event("enemy_explosion", enemy_type="hunter")
    rec.capture(renderer)  # frame 2 - the explosion frame
    rec.finalize()

    data = json.loads((tmp_path / "events.json").read_text())
    events = data["events"]
    assert len(events) == 1
    assert events[0]["event_type"] == "enemy_explosion"
    assert events[0]["frame"] == 2
    assert events[0]["meta"]["enemy_type"] == "hunter"


def test_finalize_writes_manifest(tmp_path, renderer):
    rec = FrameRecorder(output_dir=tmp_path, enabled=True, fps=30)
    for _ in range(5):
        rec.capture(renderer)
    rec.finalize()

    data = json.loads((tmp_path / "events.json").read_text())
    assert data["fps"] == 30
    assert data["frame_count"] == 5
    assert data["width"] == renderer.width
    assert data["height"] == renderer.height


def test_tag_event_on_disabled_recorder_is_noop(tmp_path, renderer):
    rec = FrameRecorder(output_dir=tmp_path, enabled=False)
    rec.tag_event("player_death")
    rec.finalize()
    assert not (tmp_path / "events.json").exists()


class FakeRenderer:
    """Stands in for tcod.sdl.render.Renderer: a NEW wrapper per access, one
    shared class. Verifies the hook is installed on the class, not an instance."""

    _frames = [FakeSDLRenderer()]  # shared backing frame source

    def read_pixels(self):
        return FakeRenderer._frames[0].read_pixels()

    def present(self):  # original method, replaced by the hook
        FakeRenderer._frames[0].present_calls += 1


def test_install_hook_captures_on_present(tmp_path):
    rec = FrameRecorder(output_dir=tmp_path, enabled=True)
    rec.install(renderer_cls=FakeRenderer)
    try:
        # Each "access" is a fresh instance, mirroring context.sdl_renderer.
        FakeRenderer().present()
        FakeRenderer().present()
    finally:
        rec.uninstall()

    assert rec.frame_count == 2
    assert len(list(tmp_path.glob("frame_*.png"))) == 2
    # Original present still ran (hook chains through).
    assert FakeRenderer._frames[0].present_calls >= 2
    # After uninstall, the class method is restored (no further capture).
    FakeRenderer().present()
    assert rec.frame_count == 2


def test_finalize_serializes_numpy_scalar_meta(tmp_path, renderer):
    """Event meta from the engine carries numpy scalars (e.g. intc); finalize
    must still produce valid JSON with plain numbers."""
    rec = FrameRecorder(output_dir=tmp_path, enabled=True)
    rec.capture(renderer)
    rec.tag_event("enemy_explosion", x=np.intc(11), y=np.int64(7))
    rec.finalize()

    data = json.loads((tmp_path / "events.json").read_text())
    meta = data["events"][0]["meta"]
    assert meta["x"] == 11 and meta["y"] == 7
    assert isinstance(meta["x"], int)


def test_segments_capture_beat_ranges(tmp_path, renderer):
    """begin_segment marks narrative beats; finalize resolves their frame ranges."""
    rec = FrameRecorder(output_dir=tmp_path, enabled=True)

    rec.begin_segment("establishing", overlay="Detection means deletion.")
    rec.capture(renderer)  # frame 1
    rec.capture(renderer)  # frame 2
    rec.begin_segment("kill", card="NO COMBAT RNG.")
    rec.capture(renderer)  # frame 3
    rec.finalize()

    segs = json.loads((tmp_path / "events.json").read_text())["segments"]
    assert len(segs) == 2
    assert segs[0]["label"] == "establishing"
    assert segs[0]["card"] is None
    assert segs[0]["overlay"] == "Detection means deletion."
    assert segs[0]["start_frame"] == 1
    assert segs[0]["end_frame"] == 2
    assert segs[1]["label"] == "kill"
    assert segs[1]["card"] == "NO COMBAT RNG."
    assert segs[1]["overlay"] is None
    assert segs[1]["start_frame"] == 3
    assert segs[1]["end_frame"] == 3


def test_empty_segment_is_dropped(tmp_path, renderer):
    """A segment that captured no frames is not emitted."""
    rec = FrameRecorder(output_dir=tmp_path, enabled=True)
    rec.begin_segment("a")
    rec.capture(renderer)  # frame 1
    rec.begin_segment("b")  # no captures before finalize
    rec.finalize()

    segs = json.loads((tmp_path / "events.json").read_text())["segments"]
    assert [s["label"] for s in segs] == ["a"]
    assert segs[0]["end_frame"] == 1


class RecordingSpy:
    """Captures tag_event calls without touching the filesystem."""

    def __init__(self):
        self.tags: list[tuple[str, dict]] = []

    def tag_event(self, event_type, **meta):
        self.tags.append((event_type, meta))


def test_engine_tag_recording_event_noop_without_recorder():
    """tag_recording_event must be safe when no recorder is attached."""
    from tests.test_agent import GameTestAgent

    agent = GameTestAgent(seed=1)
    assert agent.engine.frame_recorder is None
    # Should not raise
    agent.engine.tag_recording_event("enemy_explosion", enemy_type="bot")


def test_trigger_death_particles_tags_explosion():
    from tests.test_agent import GameTestAgent

    agent = GameTestAgent(seed=1)
    spy = RecordingSpy()
    agent.engine.frame_recorder = spy

    agent.engine.trigger_death_particles("hunter", world_x=5, world_y=7)

    assert ("enemy_explosion", {"enemy_type": "hunter", "x": 5, "y": 7}) in spy.tags


def test_player_death_tags_event():
    from tests.test_agent import GameTestAgent

    agent = GameTestAgent(seed=1)
    spy = RecordingSpy()
    agent.engine.frame_recorder = spy

    agent.player.cpu = 0
    agent.engine.death_handler.check_death("combat", "hunter")

    assert any(t[0] == "player_death" for t in spy.tags)


pytestmark = pytest.mark.unit
