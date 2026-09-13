#!/usr/bin/env python3
"""Regression tests for the static video catalog helpers."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "import_videos.py"
SPEC = importlib.util.spec_from_file_location("import_videos", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
import_videos = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(import_videos)


class ShortClassificationTests(unittest.TestCase):
    def test_tagged_video_is_a_short_without_metadata(self) -> None:
        self.assertTrue(import_videos.is_short_video("Skate Clip #shorts", None))

    def test_portrait_short_video_is_a_short(self) -> None:
        metadata = {"width": 1080, "height": 1920, "duration": 179.9}
        self.assertTrue(import_videos.is_short_video("Portrait clip", metadata))

    def test_landscape_video_is_not_a_short(self) -> None:
        metadata = {"width": 1920, "height": 1080, "duration": 30.0}
        self.assertFalse(import_videos.is_short_video("Landscape clip", metadata))

    def test_long_square_video_is_not_a_short(self) -> None:
        metadata = {"width": 1080, "height": 1080, "duration": 180.1}
        self.assertFalse(import_videos.is_short_video("Long square clip", metadata))


class CatalogUpdateTests(unittest.TestCase):
    def test_new_cards_are_prepended_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            page = Path(temp_dir) / "catalog.html"
            page.write_text(
                '<div>\n  <!-- AUTO-START -->\n    <p>Existing card</p>\n  <!-- AUTO-END -->\n</div>',
                encoding="utf-8",
            )
            card = import_videos.video_card("fresh-upload", "Fresh Upload")
            import_videos.prepend_new_cards(page, "<!-- AUTO-START -->", "<!-- AUTO-END -->", [card])
            import_videos.prepend_new_cards(page, "<!-- AUTO-START -->", "<!-- AUTO-END -->", [card])
            rendered = page.read_text(encoding="utf-8")
            self.assertEqual(rendered.count('data-video-slug="fresh-upload"'), 1)
            self.assertLess(rendered.index("Fresh Upload"), rendered.index("Existing card"))


if __name__ == "__main__":
    unittest.main()
