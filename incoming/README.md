# Incoming videos

Use [ytUltra’s YouTube Video Downloader](https://www.ytultra.com/en/youtube-video-downloader/) manually for each authorized link in `youtube-links.txt`. After downloading a video, upload the resulting `.mp4` file into this `incoming/` folder.

The GitHub Actions workflow checks approximately every 8 minutes. It processes up to 20 MP4 files per run, moves them into `videos/`, extracts a JPEG frame at about one second into `thumbnails/`, creates playable HTML pages from `videos/example.html`, and refreshes the Hot Videos section on the homepage.

Only upload videos that you own or are explicitly authorized to download and republish. Keep individual files below 95 MB so they remain compatible with the repository workflow. The link list is a manual queue; the workflow does not contact YouTube or operate ytUltra automatically.
