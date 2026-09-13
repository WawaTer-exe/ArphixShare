# Incoming videos

Paste one authorized public YouTube URL per line into `youtube-links.txt`. The GitHub Actions importer checks approximately every 8 minutes, downloads up to 20 links per run, and removes only successful downloads.

You can also upload MP4 files directly into this folder. The workflow imports up to 20 MP4s per run into `videos/`, extracts a JPEG frame at about one second into `thumbnails/`, creates playable HTML pages from `videos/example.html`, and refreshes the Hot Videos section on the homepage with each generated thumbnail.

Only submit videos that you own or are explicitly authorized to download and republish. Downloads are capped at 720p and 95 MB per file to protect the repository from oversized assets. Failed links remain in `youtube-links.txt` for retry.
