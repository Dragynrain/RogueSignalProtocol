#!/usr/bin/env python3
"""
Trailer assembler.

Reads a capture directory (frame_*.png + events.json from
scripts/capture_trailer_footage.py) and stitches a trailer with ffmpeg.

Preferred path: the manifest's `segments` (narrative beats, each with an
optional full-screen text card). The assembler cuts one clip per beat and
drops the card in front of it, so beats stay distinct instead of merging. If
there are no segments, it falls back to selecting clips around tagged events.

Pipeline:
    1. build_timeline() -> ordered [card|clip] items (pure, unit-tested)
    2. cards      -> a PIL PNG rendered in the game font, encoded to a clip
       clips      -> ffmpeg encodes that PNG frame range
    3. concat all items (concat demuxer)
    4. optional: lay a music track under the whole cut

ffmpeg/PIL are only touched by the real run; the timeline logic is pure so the
tests stay headless.

Run:
    .venv/Scripts/python.exe scripts/build_trailer.py marketing/capture \
        --out marketing/trailer.mp4 --music music/level1_stealth.ogg
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CARD_FONT = REPO_ROOT / "KreativeSquare.ttf"

# Highlight windows (seconds before, after) per event type, for the no-segments
# fallback only. Shaped by marketing/trailer_plan_v1_gameplay.md.
DEFAULT_WINDOWS = {
    "enemy_explosion": (0.8, 1.2),
    "admin_spawn": (1.0, 1.5),
    "player_death": (0.5, 2.0),
}


@dataclass
class EditConfig:
    windows: dict = field(default_factory=lambda: dict(DEFAULT_WINDOWS))
    default_window: tuple = (0.5, 0.5)
    fps: int = 30
    card_seconds: float = 2.2
    ramp_label: str = "loud"  # beat where music crosses into the tension track
    crossfade: float = 2.0
    cta_seconds: float = 3.6


def _window_for(cfg: EditConfig, event_type: str) -> tuple:
    return cfg.windows.get(event_type, cfg.default_window)


def build_edit_decisions(manifest: dict, cfg: EditConfig) -> list[dict]:
    """Fallback: turn tagged events into ordered, merged clip ranges."""
    fps = manifest.get("fps", cfg.fps) or cfg.fps
    frame_count = manifest.get("frame_count", 0)
    events = sorted(manifest.get("events", []), key=lambda e: e["frame"])

    raw = []
    for ev in events:
        pre, post = _window_for(cfg, ev["event_type"])
        start = max(1, ev["frame"] - round(pre * fps))
        end = ev["frame"] + round(post * fps)
        if frame_count:
            end = min(frame_count, end)
        raw.append({"start_frame": start, "end_frame": end, "event_types": [ev["event_type"]]})

    merged: list[dict] = []
    for clip in raw:
        if merged and clip["start_frame"] <= merged[-1]["end_frame"]:
            prev = merged[-1]
            prev["end_frame"] = max(prev["end_frame"], clip["end_frame"])
            prev["event_types"].extend(clip["event_types"])
        else:
            merged.append(clip)
    return merged


def build_timeline(manifest: dict, cfg: EditConfig) -> list[dict]:
    """Build the ordered list of timeline items (cards and clips).

    With segments: each beat becomes an optional card item followed by a clip
    item. Without segments: fall back to event-window clips (no cards).
    """
    segments = manifest.get("segments") or []
    if not segments:
        return [
            {
                "type": "clip",
                "start_frame": c["start_frame"],
                "end_frame": c["end_frame"],
                "label": "+".join(c["event_types"]),
            }
            for c in build_edit_decisions(manifest, cfg)
        ]

    items: list[dict] = []
    for seg in segments:
        if seg.get("card"):
            items.append({"type": "card", "text": seg["card"]})
        items.append(
            {
                "type": "clip",
                "start_frame": seg["start_frame"],
                "end_frame": seg["end_frame"],
                "label": seg.get("label", ""),
                "overlay": seg.get("overlay"),
            }
        )
    return items


def timeline_durations(timeline: list[dict], cfg: EditConfig) -> list[float]:
    """Duration in seconds of each timeline item (cards fixed, clips by frames)."""
    out = []
    for it in timeline:
        if it["type"] == "clip":
            out.append((it["end_frame"] - it["start_frame"] + 1) / cfg.fps)
        else:  # card / cta: a fixed hold
            out.append(it.get("seconds", cfg.card_seconds))
    return out


def time_before_label(timeline: list[dict], label: str, cfg: EditConfig):
    """Cumulative seconds before the first clip with `label`, or None if absent."""
    durs = timeline_durations(timeline, cfg)
    acc = 0.0
    for it, d in zip(timeline, durs):
        if it["type"] == "clip" and it.get("label") == label:
            return acc
        acc += d
    return None


def ffmpeg_clip_args(
    frames_dir, start_frame: int, end_frame: int, fps: int, out_path, ffmpeg: str = "ffmpeg"
) -> list[str]:
    """ffmpeg args that encode an inclusive PNG frame range to mp4."""
    num_frames = end_frame - start_frame + 1
    pattern = str(Path(frames_dir) / "frame_%06d.png")
    return [
        ffmpeg,
        "-y",
        "-framerate",
        str(fps),
        "-start_number",
        str(start_frame),
        "-i",
        pattern,
        "-frames:v",
        str(num_frames),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-vf",
        "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1",
        str(out_path),
    ]


def _render_card_png(text: str, out_path: Path, size=(1920, 1080)) -> None:
    """Render a full-screen text card in the game font (PIL)."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", size, (6, 8, 10))
    draw = ImageDraw.Draw(img)
    font_size = 84
    try:
        font = ImageFont.truetype(str(CARD_FONT), font_size)
    except Exception:
        font = ImageFont.load_default()

    # Wrap to a sensible line width.
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) > size[0] * 0.8 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)

    line_h = int(font_size * 1.3)
    total_h = line_h * len(lines)
    y = (size[1] - total_h) // 2
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((size[0] - w) // 2, y), line, fill=(0, 230, 170), font=font)
        y += line_h
    img.save(out_path)


def _cover_fit(img, size):
    """Scale an image to cover `size` and center-crop (no distortion)."""
    from PIL import Image

    tw, th = size
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def _render_cta_png(cta: dict, out_path: Path, size=(1920, 1080)) -> None:
    """Render the closing card over title-screen art, darkened for legibility,
    with a clear title hierarchy."""
    from PIL import Image, ImageDraw, ImageFont

    bg_path = cta.get("bg")
    if bg_path and Path(bg_path).exists():
        base = _cover_fit(Image.open(bg_path).convert("RGB"), size).convert("RGBA")
    else:
        base = Image.new("RGBA", size, (6, 8, 10, 255))

    # Darken so text reads, a touch heavier at the bottom.
    shade = Image.new("RGBA", size, (4, 6, 10, 140))
    base = Image.alpha_composite(base, shade)
    draw = ImageDraw.Draw(base)

    def font(px):
        try:
            return ImageFont.truetype(str(CARD_FONT), px)
        except Exception:
            return ImageFont.load_default()

    # (text, size, color, stroke) rows, drawn as a centered vertical block.
    cyan = (64, 224, 255, 255)
    amber = (255, 196, 0, 255)
    white = (240, 244, 248, 255)
    gray = (168, 176, 184, 255)
    spec = [
        (cta.get("title", ""), 92, cyan, 4),
        (cta.get("tagline", ""), 44, white, 2),
        (cta.get("note", ""), 44, amber, 2),
        (cta.get("platforms", ""), 38, gray, 2),
        (cta.get("url", ""), 44, cyan, 2),
    ]
    spec = [r for r in spec if r[0]]

    # Keep each line well within a safe width so the slow push-in (which crops
    # the edges as it zooms) never clips the text.
    max_w = int(size[0] * 0.78)
    rows = []
    for text, px, color, stroke in spec:
        while px > 20 and draw.textlength(text, font=font(px)) > max_w:
            px -= 2
        rows.append((text, px, color, stroke))

    gap = 26
    heights = []
    for text, px, _c, _s in rows:
        f = font(px)
        bbox = draw.textbbox((0, 0), text, font=f, stroke_width=_s)
        heights.append(bbox[3] - bbox[1])
    # Extra breathing room under the title.
    total = sum(heights) + gap * (len(rows) - 1) + (28 if len(rows) > 1 else 0)
    # Sit the block low so it clears the artwork's face, with a safe bottom
    # margin (the push-in crops the very edges).
    bottom_margin = 96
    y = size[1] - total - bottom_margin
    for i, (text, px, color, stroke) in enumerate(rows):
        f = font(px)
        w = draw.textlength(text, font=f)
        draw.text(
            ((size[0] - w) / 2, y),
            text,
            font=f,
            fill=color,
            stroke_width=stroke,
            stroke_fill=(0, 0, 0, 255),
        )
        y += heights[i] + gap + (28 if i == 0 else 0)
    base.convert("RGB").save(out_path)


def _wrap_to_width(draw, text, font, max_w):
    """Greedy word-wrap so no line exceeds max_w pixels."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) > max_w and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# Overlay look: a full-width dark strip, white text with a dark outline so it
# reads over any background, and a bright accent line so it pops against the
# game's teal UI.
OVERLAY_TEXT = (255, 255, 255, 255)
OVERLAY_STROKE = (0, 0, 0, 255)
OVERLAY_ACCENT = (255, 196, 0, 255)  # amber
OVERLAY_BAND = (4, 6, 10, 225)


def _render_overlay_png(text: str, out_path: Path, size=(1920, 1080)) -> None:
    """Render a transparent full-width lower strip with wrapped, high-contrast
    text. Text wraps and the font shrinks until it fits with side margins, so
    nothing is clipped at the edges."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    side_margin = 120
    max_w = size[0] - side_margin * 2

    font_size = 54
    while font_size >= 30:
        try:
            font = ImageFont.truetype(str(CARD_FONT), font_size)
        except Exception:
            font = ImageFont.load_default()
            break
        lines = _wrap_to_width(draw, text, font, max_w)
        if all(draw.textlength(ln, font=font) <= max_w for ln in lines):
            break
        font_size -= 4
    else:
        lines = _wrap_to_width(draw, text, font, max_w)

    pad = 30
    line_h = int(font_size * 1.28)
    text_h = line_h * len(lines)
    band_h = text_h + pad * 2
    band_top = size[1] - band_h - 56  # sit the strip a little off the bottom

    # Full-width dark strip + a bright accent line along its top edge.
    draw.rectangle([0, band_top, size[0], band_top + band_h], fill=OVERLAY_BAND)
    draw.rectangle([0, band_top, size[0], band_top + 5], fill=OVERLAY_ACCENT)

    y = band_top + pad
    stroke = max(3, font_size // 16)
    for ln in lines:
        w = draw.textlength(ln, font=font)
        draw.text(
            ((size[0] - w) / 2, y),
            ln,
            font=font,
            fill=OVERLAY_TEXT,
            stroke_width=stroke,
            stroke_fill=OVERLAY_STROKE,
        )
        y += line_h
    img.save(out_path)


def _run(args: list[str]) -> None:
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Streaming platforms (YouTube, itch embeds) play around -14 LUFS. Raw game
# tracks sit far lower, so the trailer would sound quiet next to anything else.
LOUDNORM = "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000"


def music_filtergraph(total_dur: float, ramp_at: float | None = None, crossfade: float = 2.0) -> str:
    """Audio filtergraph for the music bed, ending in [aout].

    Input 1 is the opening track. With `ramp_at`, input 2 (the tension track)
    crossfades in at that time. Either way the bed fades out over the last
    second and is loudness-normalized after mixing.
    """
    fade_out_st = max(0.0, total_dur - 1.0)
    tail = f"afade=t=out:st={fade_out_st:.2f}:d=1,{LOUDNORM}[aout]"
    if ramp_at is None:
        return f"[1:a]{tail}"
    l1 = ramp_at + crossfade  # music1 plays until the crossfade completes
    l2 = (total_dur - ramp_at) + crossfade  # music2 covers the remainder (+overlap)
    return (
        f"[1:a]atrim=0:{l1:.2f}[a1];"
        f"[2:a]atrim=0:{l2:.2f}[a2];"
        f"[a1][a2]acrossfade=d={crossfade}:c1=tri:c2=tri[ax];"
        f"[ax]{tail}"
    )


def _mux_music(ffmpeg, video, out_path, tracks, filtergraph):
    """Lay looped music tracks under the silent cut using `filtergraph`."""
    args = [ffmpeg, "-y", "-i", str(video)]
    for track in tracks:
        args += ["-stream_loop", "-1", "-i", str(track)]
    args += [
        "-filter_complex",
        filtergraph,
        "-map",
        "0:v:0",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        str(out_path),
    ]
    _run(args)


def assemble(
    capture_dir: Path,
    out_path: Path,
    music: Path | None,
    cfg: EditConfig,
    ramp_music: Path | None = None,
    cta: dict | None = None,
) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        sys.exit("ffmpeg not found on PATH. Install it or add it to PATH, then re-run.")

    manifest = json.loads((capture_dir / "events.json").read_text())
    timeline = build_timeline(manifest, cfg)
    if not timeline:
        sys.exit(f"Nothing to assemble from {capture_dir / 'events.json'}.")
    if cta:
        timeline = timeline + [{"type": "cta", "seconds": cfg.cta_seconds, **cta}]

    fps = manifest.get("fps", cfg.fps) or cfg.fps
    clips = sum(1 for it in timeline if it["type"] == "clip")
    cards = sum(1 for it in timeline if it["type"] == "card")
    print(f"Assembling {clips} clip(s) + {cards} card(s) from {capture_dir} ...")

    work = Path(tempfile.mkdtemp(prefix="trailer_"))
    parts = []
    try:
        for i, item in enumerate(timeline):
            part = work / f"part_{i:03d}.mp4"
            if item["type"] == "cta":
                secs = item.get("seconds", cfg.cta_seconds)
                cta_png = work / f"cta_{i:03d}.png"
                _render_cta_png(item, cta_png)
                nframes = int(secs * fps)
                # Fade in from black + a slow push-in so it is not a dead still.
                vf = (
                    f"zoompan=z='min(zoom+0.00022,1.035)':d={nframes}:"
                    f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps},"
                    f"fade=t=in:st=0:d=0.5"
                )
                _run(
                    [
                        ffmpeg,
                        "-y",
                        "-loop",
                        "1",
                        "-framerate",
                        str(fps),
                        "-i",
                        str(cta_png),
                        "-t",
                        str(secs),
                        "-vf",
                        vf,
                        "-c:v",
                        "libx264",
                        "-pix_fmt",
                        "yuv420p",
                        str(part),
                    ]
                )
                print(f"  cta card over art: {item.get('bg')}")
            elif item["type"] == "card":
                card_png = work / f"card_{i:03d}.png"
                _render_card_png(item["text"], card_png)
                _run(
                    [
                        ffmpeg,
                        "-y",
                        "-loop",
                        "1",
                        "-framerate",
                        str(fps),
                        "-i",
                        str(card_png),
                        "-t",
                        str(item.get("seconds", cfg.card_seconds)),
                        "-c:v",
                        "libx264",
                        "-pix_fmt",
                        "yuv420p",
                        str(part),
                    ]
                )
                print(f"  card: {item['text'][:48]!r}")
            else:
                raw_clip = work / f"raw_{i:03d}.mp4"
                _run(
                    ffmpeg_clip_args(
                        capture_dir,
                        item["start_frame"],
                        item["end_frame"],
                        fps,
                        raw_clip,
                        ffmpeg=ffmpeg,
                    )
                )
                if item.get("overlay"):
                    overlay_png = work / f"overlay_{i:03d}.png"
                    _render_overlay_png(item["overlay"], overlay_png)
                    clip_dur = (item["end_frame"] - item["start_frame"] + 1) / fps
                    fade = 0.4
                    fo_st = max(0.0, clip_dur - fade)
                    slide = 70  # px the strip rises into place as it appears
                    # Slide up + fade in, hold, then fade out: the caption
                    # animates on instead of just blinking into existence.
                    fg = (
                        f"[1:v]format=rgba,"
                        f"fade=t=in:st=0:d={fade}:alpha=1,"
                        f"fade=t=out:st={fo_st:.2f}:d={fade}:alpha=1[ov];"
                        f"[0:v][ov]overlay=x=0:"
                        f"y='{slide}*(1-min(1,t/{fade}))':shortest=1"
                    )
                    _run(
                        [
                            ffmpeg,
                            "-y",
                            "-i",
                            str(raw_clip),
                            "-loop",
                            "1",
                            "-i",
                            str(overlay_png),
                            "-filter_complex",
                            fg,
                            "-c:v",
                            "libx264",
                            "-pix_fmt",
                            "yuv420p",
                            str(part),
                        ]
                    )
                    print(
                        f"  clip [{item['label']}] + overlay {item['overlay'][:40]!r}: "
                        f"frames {item['start_frame']}-{item['end_frame']}"
                    )
                else:
                    part = raw_clip
                    print(
                        f"  clip [{item['label']}]: frames "
                        f"{item['start_frame']}-{item['end_frame']}"
                    )
            parts.append(part)

        concat_list = work / "concat.txt"
        concat_list.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts))

        silent_cut = work / "video.mp4" if music else out_path
        _run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(silent_cut),
            ]
        )

        if music:
            if not music.exists():
                sys.exit(f"Music file not found: {music}")
            total_dur = sum(timeline_durations(timeline, cfg))
            ramp_at = (
                time_before_label(timeline, cfg.ramp_label, cfg)
                if ramp_music and ramp_music.exists()
                else None
            )
            if ramp_at is not None:
                _mux_music(
                    ffmpeg,
                    silent_cut,
                    out_path,
                    [music, ramp_music],
                    music_filtergraph(total_dur, ramp_at, cfg.crossfade),
                )
                print(
                    f"  music: {music.name} -> {ramp_music.name} ramp at {ramp_at:.1f}s "
                    f"('{cfg.ramp_label}')"
                )
            else:
                _mux_music(ffmpeg, silent_cut, out_path, [music], music_filtergraph(total_dur))
                print(f"  music: {music.name} (single track)")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print(f"\nTrailer written: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Assemble a trailer from captured frames.")
    parser.add_argument("capture_dir", help="Directory with frame_*.png and events.json")
    parser.add_argument("--out", default="marketing/trailer.mp4", help="Output video path")
    parser.add_argument("--music", default=None, help="Audio track under the opening beats")
    parser.add_argument(
        "--ramp-music", default=None, help="Tension track to crossfade into at the escalation beat"
    )
    parser.add_argument(
        "--cta-bg",
        default="graphics/main_menu/main_menu_01.png",
        help="Background art for the closing card",
    )
    parser.add_argument("--no-cta", action="store_true", help="Skip the closing card")
    args = parser.parse_args()

    cta = None
    if not args.no_cta:
        cta = {
            "title": "ROGUE SIGNAL PROTOCOL",
            "tagline": "A coffee break cyberspace stealth roguelike",
            "note": "Free and open source",
            "platforms": "Windows / Linux / Steam Deck",
            "url": "dragynrain.itch.io/rogue-signal-protocol",
            "bg": args.cta_bg,
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    assemble(
        Path(args.capture_dir),
        out_path,
        Path(args.music) if args.music else None,
        EditConfig(),
        Path(args.ramp_music) if args.ramp_music else None,
        cta,
    )


if __name__ == "__main__":
    main()
