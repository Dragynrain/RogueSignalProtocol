#!/usr/bin/env python3
"""
Build the press kit from one HTML template, in two forms:

    1. docs/presskit/index.html - served by GitHub Pages. Images come from
       docs/images, the trailer is a YouTube embed (once there is a URL).
    2. marketing/RogueSignalProtocol_presskit.zip - for email. A standalone
       copy of the page that works offline from the unzipped folder, with the
       screenshots, logos, font, trailer mp4, and a plain-text version.

Template: marketing/presskit/presskit.html. Placeholders are {{NAME}}.

Usage:
    python scripts/build_presskit.py [--youtube URL]
"""

import argparse
import re
import shutil
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "marketing" / "presskit" / "presskit.html"
FONT = REPO_ROOT / "KreativeSquare.ttf"
IMAGES = REPO_ROOT / "docs" / "images"
TEXT_VERSION = REPO_ROOT / "docs" / "PRESSKIT.md"
TRAILER = REPO_ROOT / "marketing" / "trailer_final.mp4"
WEB_OUT = REPO_ROOT / "docs" / "presskit" / "index.html"
ZIP_OUT = REPO_ROOT / "marketing" / "RogueSignalProtocol_presskit.zip"
ZIP_DIR_NAME = "RogueSignalProtocol_presskit"
TRAILER_FILE = "RogueSignalProtocol_trailer_1080p.mp4"
ZIP_URL = "https://github.com/Dragynrain/RogueSignalProtocol/releases/latest/download/RogueSignalProtocol_presskit.zip"

LOGO_FILES = ["logo.png", "logo-256.png", "banner.png", "key-art-1280x720.jpg"]

THUMB_WIDTH = 960

WEB_PATHS = {
    "SHOTS": "../images/screenshots",
    "THUMBS": "thumbs",
    "LOGOS": "../images",
    "DOWNLOAD": (
        f'<a class="button" href="{ZIP_URL}">Download everything (.zip)</a>'
        '<span class="hint">Screenshots, logos, key art, and the trailer in 1080p.</span>'
    ),
}

ZIP_PATHS = {
    "SHOTS": "screenshots",
    "THUMBS": "thumbs",
    "LOGOS": "logos",
    "DOWNLOAD": (
        '<span class="hint">Every file on this page is in this folder: '
        "screenshots/, logos/, and the trailer mp4.</span>"
    ),
}

_ID = r"([A-Za-z0-9_-]{11})"


def youtube_id(url: str) -> str:
    """Pull the 11-character video id out of the usual YouTube URL forms."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.").removeprefix("m.")
    if host == "youtu.be":
        m = re.match(r"/" + _ID, parsed.path)
    elif host == "youtube.com":
        v = parse_qs(parsed.query).get("v")
        if v:
            m = re.fullmatch(_ID, v[0])
        else:
            m = re.match(r"/(?:shorts|embed)/" + _ID, parsed.path)
    else:
        m = None
    if not m:
        raise ValueError(f"Not a YouTube video URL: {url}")
    return m.group(1)


def trailer_html(mode: str, youtube_url: str | None) -> str:
    """Trailer markup: YouTube embed on the web, local video in the zip."""
    vid = youtube_id(youtube_url) if youtube_url else None
    if mode == "web":
        if not vid:
            return ""
        return (
            '<div class="video"><iframe '
            f'src="https://www.youtube-nocookie.com/embed/{vid}" '
            'title="Rogue Signal Protocol trailer" loading="lazy" '
            'allow="encrypted-media; picture-in-picture; fullscreen" allowfullscreen>'
            "</iframe></div>"
        )
    html = f'<div class="video"><video controls preload="metadata" src="{TRAILER_FILE}"></video></div>'
    if vid:
        html += (
            '<p class="hint">Also on YouTube: '
            f'<a href="https://www.youtube.com/watch?v={vid}">youtube.com/watch?v={vid}</a></p>'
        )
    return html


def render_page(template: str, paths: dict, trailer: str) -> str:
    """Fill {{NAME}} placeholders. Fails on any placeholder it can't fill."""
    fills = {**paths, "TRAILER": trailer}

    def sub(m):
        key = m.group(1)
        if key not in fills:
            raise ValueError(f"No value for placeholder {{{{{key}}}}}")
        return fills[key]

    return re.sub(r"\{\{([A-Z_]+)\}\}", sub, template)


def plain_text(md: str) -> str:
    """PRESSKIT.md as email-friendly text: no image markup, local links unwrapped."""
    lines = [ln for ln in md.splitlines() if "![" not in ln]
    text = "\n".join(lines)
    text = re.sub(r"\[([^\]]+)\]\((?:images/)[^)]*\)", r"\1", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def make_thumbs(out_dir: Path) -> None:
    """Small JPGs for the screenshot grid; the 4K PNGs stay behind the click."""
    from PIL import Image

    out_dir.mkdir(parents=True, exist_ok=True)
    for png in sorted((IMAGES / "screenshots").glob("*.png")):
        with Image.open(png) as im:
            h = round(im.height * THUMB_WIDTH / im.width)
            im.convert("RGB").resize((THUMB_WIDTH, h), Image.LANCZOS).save(
                out_dir / f"{png.stem}.jpg", quality=85, optimize=True
            )


def build_web(template: str, youtube_url: str | None) -> None:
    WEB_OUT.parent.mkdir(parents=True, exist_ok=True)
    WEB_OUT.write_text(render_page(template, WEB_PATHS, trailer_html("web", youtube_url)), encoding="utf-8")
    shutil.copy2(FONT, WEB_OUT.parent / FONT.name)
    make_thumbs(WEB_OUT.parent / "thumbs")
    print(f"Wrote {WEB_OUT.relative_to(REPO_ROOT)}")


def build_zip(template: str, youtube_url: str | None) -> None:
    if not TRAILER.exists():
        raise FileNotFoundError(f"Trailer not found: {TRAILER}")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / ZIP_DIR_NAME
        (root / "screenshots").mkdir(parents=True)
        (root / "logos").mkdir()
        for png in sorted((IMAGES / "screenshots").glob("*.png")):
            shutil.copy2(png, root / "screenshots" / png.name)
        for name in LOGO_FILES:
            shutil.copy2(IMAGES / name, root / "logos" / name)
        shutil.copy2(FONT, root / FONT.name)
        make_thumbs(root / "thumbs")
        shutil.copy2(TRAILER, root / TRAILER_FILE)
        (root / "presskit.txt").write_text(plain_text(TEXT_VERSION.read_text(encoding="utf-8")), encoding="utf-8")
        page = render_page(template, ZIP_PATHS, trailer_html("zip", youtube_url))
        (root / "presskit.html").write_text(page, encoding="utf-8")
        ZIP_OUT.unlink(missing_ok=True)
        shutil.make_archive(str(ZIP_OUT.with_suffix("")), "zip", tmp, ZIP_DIR_NAME)
    print(f"Wrote {ZIP_OUT.relative_to(REPO_ROOT)} ({ZIP_OUT.stat().st_size // (1024 * 1024)} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--youtube", default=None, help="Trailer URL on YouTube")
    args = parser.parse_args()
    template = TEMPLATE.read_text(encoding="utf-8")
    build_web(template, args.youtube)
    build_zip(template, args.youtube)


if __name__ == "__main__":
    main()
