# Incoming videos

Use [ytUltra’s YouTube Video Downloader](https://www.ytultra.com/en/youtube-video-downloader/) manually for each authorized link in `youtube-links.txt`. After downloading a video, upload the resulting `.mp4` file into this `incoming/` folder.

The GitHub Actions workflow checks approximately every 8 minutes. It processes up to 20 MP4 files per run, moves them into `videos/`, extracts a JPEG frame at about one second into `thumbnails/`, creates playable HTML pages from `videos/example.html`, and refreshes the **Hot Videos** section on the homepage.

Every imported upload is also inserted at the top of the homepage’s **Featured Videos** section and remains there when later uploads are published. The import classifies an upload as an **ArphixShort** when its filename contains `#shorts`, or when it is square/portrait and no more than three minutes long. Short uploads are also added to `shorts.html` automatically.

Only upload videos that you own or are explicitly authorized to download and republish. Keep individual files below 95 MB so they remain compatible with the repository workflow. The link list is a manual queue; the workflow does not contact YouTube or operate ytUltra automatically.
