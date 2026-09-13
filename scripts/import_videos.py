#!/usr/bin/env python3
"""Import MP4 files from incoming/ into the static ArphixTube site."""
from pathlib import Path
import html
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "incoming"
VIDEOS = ROOT / "videos"
THUMBNAILS = ROOT / "thumbnails"
INDEX = ROOT / "index.html"
TEMPLATE = VIDEOS / "example.html"
MAX_PER_RUN = 20

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


def extract_thumbnail(video_path: Path, thumbnail_path: Path) -> None:
    command = [
        "ffmpeg", "-y", "-ss", "00:00:01", "-i", str(video_path),
        "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "3", str(thumbnail_path),
    ]
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0 or not thumbnail_path.exists():
        raise RuntimeError(f"Could not create thumbnail for {video_path.name}: {result.stderr[-500:]}")


def prepare_thumbnail(video_path: Path, thumbnail_path: Path) -> None:
    custom_path = video_path.with_suffix(".png")
    if custom_path.exists():
        command = ["ffmpeg", "-y", "-i", str(custom_path), "-vf", "scale=640:-2", "-q:v", "3", str(thumbnail_path)]
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0 or not thumbnail_path.exists():
            raise RuntimeError(f"Could not convert custom thumbnail for {video_path.name}: {result.stderr[-500:]}")
        custom_path.unlink()
    else:
        extract_thumbnail(video_path, thumbnail_path)


def hot_card(page_slug: str, title: str) -> str:
    safe_title = html.escape(title, quote=True)
    safe_slug = html.escape(page_slug, quote=True)
    return f'''        <a class="video" href="videos/{safe_slug}.html" data-title="{safe_title.lower()}">\n          <img class="thumb" src="thumbnails/{safe_slug}.jpg" alt="{safe_title} thumbnail">\n          <span class="video-title">{safe_title}</span><span class="meta">New upload | just now</span>\n        </a>'''


def update_hot_section(cards: list[str]) -> None:
    current = INDEX.read_text(encoding="utf-8")
    start = "      <!-- AUTO-HOT-START -->"
    end = "      <!-- AUTO-HOT-END -->"
    if start not in current or end not in current:
        raise SystemExit("index.html is missing AUTO-HOT-START/AUTO-HOT-END markers")
    block = start + "\n" + "\n".join(cards) + "\n      " + end
    current = re.sub(re.escape(start) + r".*?" + re.escape(end), block, current, flags=re.S)
    INDEX.write_text(current, encoding="utf-8")


def main() -> int:
    files = sorted(
        [p for p in INCOMING.iterdir() if p.is_file() and p.suffix.lower() == ".mp4"],
        key=lambda p: p.name.lower(),
    )[:MAX_PER_RUN]
    if not files:
        print("No new MP4 files found in incoming/")
        return 0

    cards = []
    for source in files:
        video_destination = unique_destination(VIDEOS, source.name)
        shutil.move(str(source), str(video_destination))
        page_slug = slugify(video_destination.name)
        page_destination = unique_destination(VIDEOS, page_slug + ".html")
        title = Path(video_destination.name).stem.replace("_", " ").replace("-", " ").strip().title()
        thumbnail_destination = unique_destination(THUMBNAILS, page_destination.stem + ".jpg")
        prepare_thumbnail(video_destination, thumbnail_destination)
        page_destination.write_text(page_for(video_destination.name, title, page_slug), encoding="utf-8")
        cards.append(hot_card(page_destination.stem, title))
        print(f"Imported {video_destination.name} -> {page_destination.name}")

    update_hot_section(cards)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
