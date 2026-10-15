#!/usr/bin/env python3
"""
FrameRecorder - in-engine gameplay capture for automated trailers.

Grabs the fully-composited SDL backbuffer (backgrounds + sprites + particles +
console UI) via the renderer's read_pixels() and writes it as a PNG frame. It
also tags the frame index of highlight-worthy events (enemy explosions, player
death, admin avatar spawn) so a downstream assembler can auto-select clips.

Design notes:
- Zero cost when disabled: capture() and tag_event() return immediately.
- No window required to unit test: anything with read_pixels()/present() works.
- ASCII-only logging (Windows console), per project logging rules.
"""

import json
import logging
from pathlib import Path

import numpy as np
from PIL import Image


def _json_default(obj):
    """Coerce numpy scalars (engine positions are numpy ints) to plain numbers."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class FrameRecorder:
    """Captures composited frames and tags gameplay events for trailer editing.

    Typical use (driven from the render loop):
        recorder = FrameRecorder(output_dir, enabled=True, fps=30)
        recorder.install(context)          # wrap sdl_renderer.present (optional)
        ...
        recorder.tag_event("enemy_explosion", enemy_type="hunter")
        recorder.capture(sdl_renderer)     # one call per presented frame
        ...
        recorder.finalize()                # writes events.json manifest
    """

    def __init__(self, output_dir, enabled: bool = False, fps: int = 30):
        """
        Args:
            output_dir: Directory to write frame_*.png and events.json into.
            enabled: When False, capture/tag are no-ops and nothing is written.
            fps: Nominal capture rate, recorded in the manifest for the editor.
        """
        self.output_dir = Path(output_dir)
        self.enabled = enabled
        self.fps = fps
        self.frame_count = 0
        self._events: list[dict] = []
        self._segments: list[dict] = []
        self._width = 0
        self._height = 0
        self._original_present = None
        self._patched_cls = None

        if self.enabled:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logging.info("[RECORDER] Frame capture enabled -> %s", self.output_dir)

    def capture(self, sdl_renderer) -> int:
        """Grab the current backbuffer and write it as the next PNG frame.

        Must be called BEFORE present() swaps the buffer. Returns the 1-based
        index of the captured frame, or 0 when recording is disabled.
        """
        if not self.enabled:
            return 0

        try:
            pixels = sdl_renderer.read_pixels()
        except Exception as e:  # pragma: no cover - hardware/driver dependent
            logging.error("[RECORDER] read_pixels failed: %s", e)
            return self.frame_count

        frame = np.asarray(pixels, dtype=np.uint8)
        height, width = frame.shape[0], frame.shape[1]
        self._width, self._height = width, height

        mode = "RGBA" if frame.ndim == 3 and frame.shape[2] == 4 else "RGB"
        image = Image.fromarray(frame, mode)

        self.frame_count += 1
        frame_path = self.output_dir / f"frame_{self.frame_count:06d}.png"
        image.save(frame_path)
        return self.frame_count

    def tag_event(self, event_type: str, **meta) -> None:
        """Record that an event occurred at the next frame to be captured.

        Tagging before capture() points the event at the frame that will show
        it (e.g. the explosion that is about to render). No-op when disabled.
        """
        if not self.enabled:
            return
        self._events.append(
            {
                "event_type": event_type,
                "frame": self.frame_count + 1,
                "meta": meta,
            }
        )

    def begin_segment(
        self, label: str, card: str | None = None, overlay: str | None = None
    ) -> None:
        """Mark the start of a narrative beat for the editor.

        The beat runs from the next captured frame until the following
        begin_segment (or the final frame).

        Args:
            label: Beat name.
            card: Optional full-screen text shown just BEFORE this beat (a hard
                cut). Reserve for the few moments that earn a hold.
            overlay: Optional lower-third text burned OVER this beat's footage
                while it keeps playing.

        No-op when disabled.
        """
        if not self.enabled:
            return
        self._segments.append(
            {
                "label": label,
                "card": card,
                "overlay": overlay,
                "start_frame": self.frame_count + 1,
            }
        )

    def _resolve_segments(self) -> list[dict]:
        """Fill in each segment's end_frame and drop beats that caught no frames."""
        resolved = []
        for i, seg in enumerate(self._segments):
            start = seg["start_frame"]
            end = (
                self._segments[i + 1]["start_frame"] - 1
                if i + 1 < len(self._segments)
                else self.frame_count
            )
            if end < start:
                continue  # beat captured no frames
            resolved.append({**seg, "end_frame": end})
        return resolved

    def finalize(self) -> None:
        """Write events.json with the event tags and capture manifest.

        No-op when disabled so a recorder that never ran leaves nothing behind.
        """
        self.uninstall()
        if not self.enabled:
            return

        manifest = {
            "fps": self.fps,
            "frame_count": self.frame_count,
            "width": self._width,
            "height": self._height,
            "events": self._events,
            "segments": self._resolve_segments(),
        }
        (self.output_dir / "events.json").write_text(
            json.dumps(manifest, indent=2, default=_json_default)
        )
        logging.info(
            "[RECORDER] Finalized: %d frames, %d events -> %s",
            self.frame_count,
            len(self._events),
            self.output_dir / "events.json",
        )

    def install(self, renderer_cls=None) -> None:
        """Patch Renderer.present at the CLASS level so every presented frame is
        captured.

        tcod's Context.sdl_renderer builds a NEW Renderer wrapper on every
        access, so patching a single instance never sticks. Patching the class
        method means every fresh wrapper's present() runs through the capture
        hook. The backbuffer is read just before it is swapped. No-op when
        disabled.

        Args:
            renderer_cls: Class whose present() to wrap. Defaults to
                tcod.sdl.render.Renderer; injectable for tests.
        """
        if not self.enabled:
            return
        if renderer_cls is None:
            import tcod.sdl.render

            renderer_cls = tcod.sdl.render.Renderer

        original_present = renderer_cls.present
        recorder = self

        def capturing_present(renderer_self, *args, **kwargs):
            recorder.capture(renderer_self)
            return original_present(renderer_self, *args, **kwargs)

        self._patched_cls = renderer_cls
        self._original_present = original_present
        renderer_cls.present = capturing_present
        logging.info("[RECORDER] Installed present() capture hook on %s", renderer_cls.__name__)

    def uninstall(self) -> None:
        """Restore the original present() if install() patched it."""
        if self._patched_cls is not None and self._original_present is not None:
            self._patched_cls.present = self._original_present
            self._patched_cls = None
            self._original_present = None
