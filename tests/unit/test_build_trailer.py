#!/usr/bin/env python3
"""
Unit tests for the trailer assembler's edit-decision logic.

These cover the pure functions only (no ffmpeg, no real frames): given a capture
manifest (events.json contents), what clips get selected, in what order, and how
overlapping highlight windows merge. ffmpeg invocation is exercised only by the
real assembly run, not here.
"""

import pytest

from scripts.build_trailer import (
    EditConfig,
    cta_layout,
    build_edit_decisions,
    build_timeline,
    ffmpeg_clip_args,
    music_filtergraph,
    time_before_label,
    timeline_durations,
)


def manifest(events, frame_count=900, fps=30):
    return {"fps": fps, "frame_count": frame_count, "width": 1920, "height": 1080, "events": events}


def test_clip_window_centered_on_event():
    m = manifest([{"event_type": "enemy_explosion", "frame": 300, "meta": {}}])
    cfg = EditConfig(windows={"enemy_explosion": (1.0, 1.0)}, fps=30)
    clips = build_edit_decisions(m, cfg)

    assert len(clips) == 1
    # 1s before/after at 30fps = 30 frames each side.
    assert clips[0]["start_frame"] == 270
    assert clips[0]["end_frame"] == 330
    assert clips[0]["event_types"] == ["enemy_explosion"]


def test_clip_windows_clamp_to_footage_bounds():
    m = manifest([{"event_type": "player_death", "frame": 5, "meta": {}}], frame_count=20)
    cfg = EditConfig(windows={"player_death": (2.0, 2.0)}, fps=30)
    clips = build_edit_decisions(m, cfg)

    assert clips[0]["start_frame"] == 1
    assert clips[0]["end_frame"] == 20


def test_clips_ordered_chronologically():
    m = manifest(
        [
            {"event_type": "player_death", "frame": 800, "meta": {}},
            {"event_type": "enemy_explosion", "frame": 200, "meta": {}},
        ]
    )
    cfg = EditConfig(windows={"enemy_explosion": (0.5, 0.5), "player_death": (0.5, 0.5)}, fps=30)
    clips = build_edit_decisions(m, cfg)

    assert [c["event_types"][0] for c in clips] == ["enemy_explosion", "player_death"]


def test_overlapping_windows_merge():
    m = manifest(
        [
            {"event_type": "enemy_explosion", "frame": 300, "meta": {}},
            {"event_type": "enemy_explosion", "frame": 320, "meta": {}},
        ]
    )
    cfg = EditConfig(windows={"enemy_explosion": (1.0, 1.0)}, fps=30)
    clips = build_edit_decisions(m, cfg)

    # 270..330 and 290..350 overlap -> one clip 270..350 tagged with both.
    assert len(clips) == 1
    assert clips[0]["start_frame"] == 270
    assert clips[0]["end_frame"] == 350
    assert clips[0]["event_types"].count("enemy_explosion") == 2


def test_unknown_event_uses_default_window():
    m = manifest([{"event_type": "mystery", "frame": 100, "meta": {}}])
    cfg = EditConfig(windows={}, default_window=(0.5, 0.5), fps=30)
    clips = build_edit_decisions(m, cfg)

    assert clips[0]["start_frame"] == 85
    assert clips[0]["end_frame"] == 115


def test_no_events_yields_no_clips():
    assert build_edit_decisions(manifest([]), EditConfig(fps=30)) == []


def test_ffmpeg_clip_args_include_range_and_fps():
    args = ffmpeg_clip_args(
        frames_dir="cap",
        start_frame=270,
        end_frame=330,
        fps=30,
        out_path="clip_000.mp4",
    )
    joined = " ".join(args)
    assert "ffmpeg" in args[0]
    assert "-start_number" in args and "270" in args
    # 270..330 inclusive = 61 frames
    assert "61" in args
    assert "frame_%06d.png" in joined
    assert joined.endswith("clip_000.mp4")


def test_timeline_interleaves_cards_and_clips():
    m = manifest(
        [],
        frame_count=300,
    )
    m["segments"] = [
        {
            "label": "establishing",
            "card": None,
            "overlay": "Detection means deletion.",
            "start_frame": 1,
            "end_frame": 100,
        },
        {
            "label": "kill",
            "card": "NO COMBAT RNG.",
            "overlay": None,
            "start_frame": 101,
            "end_frame": 200,
        },
        {"label": "read", "card": None, "overlay": None, "start_frame": 201, "end_frame": 300},
    ]
    items = build_timeline(m, EditConfig(fps=30))

    kinds = [it["type"] for it in items]
    # clip(overlay), card, clip, (no card/overlay) clip
    assert kinds == ["clip", "card", "clip", "clip"]
    assert items[0]["overlay"] == "Detection means deletion."
    assert items[0]["start_frame"] == 1 and items[0]["end_frame"] == 100
    assert items[1]["text"] == "NO COMBAT RNG."
    assert items[3]["start_frame"] == 201 and items[3]["overlay"] is None


def test_timeline_without_segments_falls_back_to_event_clips():
    m = manifest([{"event_type": "enemy_explosion", "frame": 150, "meta": {}}])
    items = build_timeline(m, EditConfig(fps=30))
    assert [it["type"] for it in items] == ["clip"]


def test_timeline_durations_card_and_clip():
    cfg = EditConfig(fps=30, card_seconds=2.0)
    timeline = [
        {"type": "card", "text": "x"},
        {"type": "clip", "start_frame": 1, "end_frame": 60, "label": "a"},  # 60 frames = 2.0s
        {"type": "clip", "start_frame": 61, "end_frame": 120, "label": "b"},  # 2.0s
    ]
    durs = timeline_durations(timeline, cfg)
    assert durs[0] == pytest.approx(2.0)  # card
    assert durs[1] == pytest.approx(2.0)  # 60 frames at 30fps
    assert durs[2] == pytest.approx(2.0)


def test_time_before_label_sums_preceding_items():
    cfg = EditConfig(fps=30, card_seconds=2.0)
    timeline = [
        {"type": "clip", "start_frame": 1, "end_frame": 30, "label": "establishing"},  # 1.0s
        {"type": "card", "text": "card"},  # 2.0s
        {"type": "clip", "start_frame": 31, "end_frame": 60, "label": "escalation"},
    ]
    # escalation clip starts after 1.0 (clip) + 2.0 (card) = 3.0s
    assert time_before_label(timeline, "escalation", cfg) == pytest.approx(3.0)


def test_time_before_missing_label_is_none():
    cfg = EditConfig(fps=30)
    timeline = [{"type": "clip", "start_frame": 1, "end_frame": 30, "label": "a"}]
    assert time_before_label(timeline, "nope", cfg) is None


pytestmark = pytest.mark.unit


def test_music_filtergraph_single_track_fades_and_normalizes():
    fg = music_filtergraph(total_dur=20.0)
    assert "afade=t=out:st=19.00:d=1" in fg
    assert "loudnorm=I=-14" in fg
    assert fg.endswith("[aout]")


def test_music_filtergraph_ramp_crossfades_then_normalizes():
    fg = music_filtergraph(total_dur=20.0, ramp_at=10.0, crossfade=2.0)
    assert "[1:a]atrim=0:12.00[a1]" in fg
    assert "[2:a]atrim=0:12.00[a2]" in fg
    assert "acrossfade=d=2.0" in fg
    # Normalize after the mix so both tracks land at the same target.
    assert fg.index("acrossfade") < fg.index("loudnorm")
    assert fg.endswith("[aout]")


def test_cta_layout_shows_whole_portrait_on_the_right():
    layout = cta_layout(size=(1920, 1080), art_size=(1440, 1440))
    x, y, w, h = layout["art"]
    assert (y, h) == (0, 1080)  # full height, nothing cropped
    assert w == 1080  # aspect preserved
    assert x + w == 1920  # right-aligned


def test_cta_text_column_stays_clear_of_the_face():
    # The portrait's subject is centered, so its middle third is the face.
    layout = cta_layout(size=(1920, 1080), art_size=(1440, 1440))
    ax, _, aw, _ = layout["art"]
    face_left = ax + aw / 3
    left, right = layout["text"]
    assert 0 < left < right <= face_left - 40


def test_cta_layout_without_art_centers_the_text():
    layout = cta_layout(size=(1920, 1080), art_size=None)
    assert layout["art"] is None
    left, right = layout["text"]
    assert left == pytest.approx(1920 - right)
