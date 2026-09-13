#!/usr/bin/env python3
"""Import MP4 files into the static ArphixTube site and refresh video catalogs."""
from __future__ import annotations

from pathlib import Path
import html
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "incoming"
VIDEOS = ROOT / "videos"
THUMBNAILS = ROOT / "thumbnails"
INDEX = ROOT / "index.html"
SHORTS = ROOT / "shorts.html"
TEMPLATE = VIDEOS / "example.html"
MAX_PER_RUN = 20

HOT_START = "<!-- AUTO-HOT-START -->"
HOT_END = "<!-- AUTO-HOT-END -->"
FEATURED_START = "<!-- AUTO-FEATURED-START -->"
FEATURED_END = "<!-- AUTO-FEATURED-END -->"
SHORTS_START = "<!-- AUTO-SHORTS-START -->"
SHORTS_END = "<!-- AUTO-SHORTS-END -->"

INCOMING.mkdir(exist_ok=True)
VIDEOS.mkdir(exist_ok=True)
THUMBNAILS.mkdir(exist_ok=True)


def slugify(filename: str) -> str:
    stem = Path(filename).stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return stem or "video"


def unique_destination(directory: Path, filename: str) -> Path:
    destination = directory / filename
    counter = 2
    while destination.exists():
        destination = directory / f"{destination.stem}-{counter}{destination.suffix}"
        counter += 1
    return destination


def page_for(video_name: str, title: str, page_slug: str) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    page = template.replace("My Video - ArphixTube", f"{title} - ArphixTube")
    page = page.replace("My Video Title", title)
    page = page.replace("YourUsername", "ArphixTube")
    page = page.replace("Write a short description of your video here.", "Automatically imported from the incoming folder.")
    page = re.sub(r'poster="[^"]+"', f'poster="../thumbnails/{page_slug}.jpg"', page, count=1)
    page = re.sub(r'<source src="[^"]+" type="video/mp4">', f'<source src="{html.escape(video_name)}" type="video/mp4">', page, count=1)
    page = page.replace('href="example.html">Upload', 'href="../index.html">Upload')
    return page


def extract_thumbnail(video_path: Path, thumbnail_path: Path, duration: float | None = None) -> None:
    timestamp = min(1.0, max(0.0, duration / 2)) if duration is not None else 1.0
    command = [
        "ffmpeg", "-y", "-ss", f"{timestamp:.3f}", "-i", str(video_path),
        "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "3", str(thumbnail_path),
    ]
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0 or not thumbnail_path.exists():
        raise RuntimeError(f"Could not create thumbnail for {video_path.name}: {result.stderr[-500:]}")


def prepare_thumbnail(video_path: Path, thumbnail_path: Path, duration: float | None = None) -> None:
    custom_path = video_path.with_suffix(".png")
    if custom_path.exists():
        command = ["ffmpeg", "-y", "-i", str(custom_path), "-vf", "scale=640:-2", "-q:v", "3", str(thumbnail_path)]
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0 or not thumbnail_path.exists():
            raise RuntimeError(f"Could not convert custom thumbnail for {video_path.name}: {result.stderr[-500:]}")
        custom_path.unlink()
    else:
        extract_thumbnail(video_path, thumbnail_path, duration)


def probe_video(video_path: Path) -> dict[str, float] | None:
    """Return the primary video dimensions and duration, or None if probing fails."""
    command = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height:format=duration", "-of", "json", str(video_path),
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Could not inspect {video_path.name}; it will not be auto-classified as a Short.")
        return None

    try:
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        return {
            "width": float(stream["width"]),
            "height": float(stream["height"]),
            "duration": float(data["format"]["duration"]),
        }
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        print(f"Could not read metadata for {video_path.name}; it will not be auto-classified as a Short.")
        return None


def is_short_video(title: str, metadata: dict[str, float] | None) -> bool:
    """Classify tagged uploads or portrait/square videos up to three minutes as Shorts."""
    if re.search(r"(?:^|\s)#shorts\b", title, flags=re.IGNORECASE):
        return True
    if metadata is None:
        return False
    return metadata["height"] >= metadata["width"] and metadata["duration"] <= 180


def video_card(page_slug: str, title: str, meta: str = "New upload | just now") -> str:
    safe_title = html.escape(title, quote=True)
    safe_slug = html.escape(page_slug, quote=True)
    return f'''        <a class="video" data-video-slug="{safe_slug}" href="videos/{safe_slug}.html" data-title="{safe_title.lower()}">
          <img class="thumb" src="thumbnails/{safe_slug}.jpg" alt="{safe_title} thumbnail">
          <span class="video-title">{safe_title}</span><span class="meta">{meta}</span>
        </a>'''


def short_card(page_slug: str, title: str, duration: float | None) -> str:
    safe_title = html.escape(title, quote=True)
    safe_slug = html.escape(page_slug, quote=True)
    duration_label = f"{int(round(duration))} sec" if duration is not None else "New Short"
    return f'''        <a class="short-card" data-video-slug="{safe_slug}" href="videos/{safe_slug}.html">
          <img class="short-thumb" src="thumbnails/{safe_slug}.jpg" alt="{safe_title} thumbnail">
          <span class="short-title">{safe_title}</span><span class="short-meta">{duration_label} &middot; ArphixShorts</span>
        </a>'''


def replace_card_section(path: Path, start: str, end: str, cards: list[str]) -> None:
    current = path.read_text(encoding="utf-8")
    pattern = re.escape(start) + r".*?" + re.escape(end)
    if not re.search(pattern, current, flags=re.S):
        raise SystemExit(f"{path.name} is missing {start}/{end} markers")
    cards_html = "\n".join(cards)
    block = f"{start}\n{cards_html}\n      {end}" if cards_html else f"{start}\n      {end}"
    path.write_text(re.sub(pattern, block, current, flags=re.S), encoding="utf-8")


def prepend_new_cards(path: Path, start: str, end: str, cards: list[str]) -> None:
    """Prepend new cards without deleting earlier workflow imports or curated cards."""
    current = path.read_text(encoding="utf-8")
    pattern = re.escape(start) + r"(.*?)" + re.escape(end)
    match = re.search(pattern, current, flags=re.S)
    if match is None:
        raise SystemExit(f"{path.name} is missing {start}/{end} markers")

    existing = match.group(1).strip()
    additions = []
    for card in cards:
        slug_match = re.search(r'data-video-slug="([^"]+)"', card)
        if slug_match is None or f'data-video-slug="{slug_match.group(1)}"' not in existing:
            additions.append(card)

    if not additions:
        return
    body = "\n".join(additions + ([existing] if existing else []))
    block = f"{start}\n{body}\n      {end}"
    path.write_text(current[:match.start()] + block + current[match.end():], encoding="utf-8")


def update_hot_section(cards: list[str]) -> None:
    replace_card_section(INDEX, HOT_START, HOT_END, cards)


def update_featured_section(cards: list[str]) -> None:
    prepend_new_cards(INDEX, FEATURED_START, FEATURED_END, cards)


def update_shorts_section(cards: list[str]) -> None:
    prepend_new_cards(SHORTS, SHORTS_START, SHORTS_END, cards)


def main() -> int:
    files = sorted(
        [p for p in INCOMING.iterdir() if p.is_file() and p.suffix.lower() == ".mp4"],
        key=lambda p: p.name.lower(),
    )[:MAX_PER_RUN]
    if not files:
        print("No new MP4 files found in incoming/")
        return 0

    hot_cards: list[str] = []
    featured_cards: list[str] = []
    shorts_cards: list[str] = []
    for source in files:
        metadata = probe_video(source)
        video_destination = unique_destination(VIDEOS, source.name)
        shutil.move(str(source), str(video_destination))
        page_slug = slugify(video_destination.name)
        page_destination = unique_destination(VIDEOS, page_slug + ".html")
        title = Path(video_destination.name).stem.replace("_", " ").replace("-", " ").strip().title()
        thumbnail_destination = unique_destination(THUMBNAILS, page_destination.stem + ".jpg")
        duration = metadata["duration"] if metadata is not None else None
        prepare_thumbnail(video_destination, thumbnail_destination, duration)
        page_destination.write_text(page_for(video_destination.name, title, page_destination.stem), encoding="utf-8")

        hot_cards.append(video_card(page_destination.stem, title))
        featured_cards.append(video_card(page_destination.stem, title))
        if is_short_video(title, metadata):
            shorts_cards.append(short_card(page_destination.stem, title, duration))
        print(f"Imported {video_destination.name} -> {page_destination.name}")

    update_hot_section(hot_cards)
    update_featured_section(featured_cards)
    update_shorts_section(shorts_cards)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
