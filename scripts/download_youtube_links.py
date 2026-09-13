#!/usr/bin/env python3
"""Download authorized YouTube URLs listed in incoming/youtube-links.txt."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "incoming"
LINKS = INCOMING / "youtube-links.txt"
MAX_PER_RUN = 20
MAX_FILE_SIZE = "95M"


def urls_from_file():
    if not LINKS.exists():
        return []
    return [line.strip() for line in LINKS.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def main() -> int:
    urls = urls_from_file()
    if not urls:
        print("No YouTube links found in incoming/youtube-links.txt")
        return 0

    remaining = list(urls)
    for url in urls[:MAX_PER_RUN]:
        before = {p.name for p in INCOMING.glob("*.mp4")}
        command = [
            "yt-dlp", "--no-playlist", "--restrict-filenames",
            "--format", "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]",
            "--merge-output-format", "mp4", "--max-filesize", MAX_FILE_SIZE,
            "--output", str(INCOMING / "%(id)s.%(ext)s"), url,
        ]
        print(f"Downloading: {url}")
        result = subprocess.run(command, cwd=ROOT)
        after = {p.name for p in INCOMING.glob("*.mp4")}
        if result.returncode == 0 and after - before:
            remaining.remove(url)
            print(f"Downloaded successfully: {url}")
        else:
            print(f"Download failed or exceeded {MAX_FILE_SIZE}: {url}")

    LINKS.write_text(
        "# Paste one authorized public YouTube URL per line. Successful downloads are removed automatically.\n"
        + "\n".join(remaining) + ("\n" if remaining else ""),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
