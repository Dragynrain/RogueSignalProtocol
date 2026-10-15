#!/usr/bin/env python3
"""
Unit tests for the press kit builder's pure functions: YouTube URL parsing,
trailer markup for the web page vs the emailed zip, and template rendering.
File copying and zipping are exercised only by a real build.
"""

import pytest

from scripts.build_presskit import (
    WEB_PATHS,
    ZIP_PATHS,
    plain_text,
    render_page,
    trailer_html,
    youtube_id,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=abcDEF12345",
        "https://youtube.com/watch?v=abcDEF12345&t=3s",
        "https://youtu.be/abcDEF12345",
        "https://www.youtube.com/shorts/abcDEF12345",
        "https://www.youtube.com/embed/abcDEF12345",
    ],
)
def test_youtube_id_from_common_url_forms(url):
    assert youtube_id(url) == "abcDEF12345"


def test_youtube_id_rejects_non_youtube_url():
    with pytest.raises(ValueError):
        youtube_id("https://vimeo.com/12345")


def test_web_trailer_without_youtube_is_empty():
    assert trailer_html("web", None) == ""


def test_web_trailer_embeds_youtube():
    html = trailer_html("web", "https://youtu.be/abcDEF12345")
    assert "https://www.youtube-nocookie.com/embed/abcDEF12345" in html
    assert "<iframe" in html


def test_zip_trailer_plays_local_file_offline():
    html = trailer_html("zip", None)
    assert "<video" in html
    assert 'src="RogueSignalProtocol_trailer_1080p.mp4"' in html
    assert "youtu" not in html


def test_zip_trailer_also_links_youtube_when_known():
    html = trailer_html("zip", "https://youtu.be/abcDEF12345")
    assert "<video" in html
    assert "https://www.youtube.com/watch?v=abcDEF12345" in html


def test_render_page_fills_asset_paths():
    template = '<img src="{{SHOTS}}/a.png"><img src="{{LOGOS}}/b.png">{{TRAILER}}'
    out = render_page(template, WEB_PATHS, "<p>t</p>")
    assert out == '<img src="../images/screenshots/a.png"><img src="../images/b.png"><p>t</p>'


def test_render_page_zip_paths_are_local_folders():
    out = render_page("{{SHOTS}}/a.png {{LOGOS}}/b.png", ZIP_PATHS, "")
    assert out == "screenshots/a.png logos/b.png"


def test_render_page_fails_on_unknown_placeholder():
    with pytest.raises(ValueError, match="UNKNOWN"):
        render_page("{{UNKNOWN}}", WEB_PATHS, "")


def test_plain_text_drops_image_markup():
    md = "\n".join(
        [
            "# Title",
            "",
            "![Banner](images/banner.png)",
            "",
            "Some text.",
            "| ![A](images/a.png) | ![B](images/b.png) |",
            "| Caption A | Caption B |",
            "- [Logo, 256x256](images/logo-256.png)",
        ]
    )
    out = plain_text(md)
    assert "![" not in out
    assert "Some text." in out
    assert "Caption A" in out
    assert "Logo, 256x256" in out
    assert "\n\n\n" not in out
