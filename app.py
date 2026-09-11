"""A small, self-contained YouTube downloader for personal, authorized use."""

from __future__ import annotations

import json
import os
import re
import subprocess
from urllib.parse import urlparse

from flask import Flask, Response, jsonify, render_template, request, stream_with_context

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be", "www.youtu.be"}
SAFE_FILENAME = re.compile(r"[^\w. -]+", re.UNICODE)


def is_youtube_url(value: str) -> bool:
    """Accept only normal YouTube watch, short, and music URLs."""
    try:
        parsed = urlparse(value.strip())
        host = (parsed.hostname or "").lower()
        return parsed.scheme in {"http", "https"} and host in YOUTUBE_HOSTS
    except ValueError:
        return False


def safe_filename(title: str, extension: str) -> str:
    cleaned = SAFE_FILENAME.sub("", title).strip(" .")[:100] or "youtube-download"
    return f"{cleaned}.{extension}"


def metadata(url: str) -> dict:
    completed = subprocess.run(
        ["yt-dlp", "--no-playlist", "--no-warnings", "--skip-download", "--dump-single-json", url],
        check=True,
        capture_output=True,
        text=True,
        timeout=45,
    )
    item = json.loads(completed.stdout)
    return {
        "title": item.get("title", "YouTube video"),
        "channel": item.get("channel") or item.get("uploader") or "YouTube",
        "thumbnail": item.get("thumbnail"),
        "duration": item.get("duration"),
    }


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/health")
def health() -> tuple[dict, int]:
    return {"status": "ok"}, 200


@app.post("/api/info")
def info() -> tuple[Response, int] | Response:
    url = (request.get_json(silent=True) or {}).get("url", "")
    if not isinstance(url, str) or not is_youtube_url(url):
        return jsonify(error="有効な YouTube URL を入力してください。"), 400
    try:
        return jsonify(metadata(url))
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return jsonify(error="動画情報を取得できませんでした。URL を確認してもう一度お試しください。"), 422


@app.post("/api/download")
def download() -> tuple[Response, int] | Response:
    data = request.get_json(silent=True) or request.form
    url = data.get("url", "")
    mode = data.get("mode", "video")
    if not isinstance(url, str) or not is_youtube_url(url):
        return jsonify(error="有効な YouTube URL を入力してください。"), 400
    if mode not in {"video", "audio"}:
        return jsonify(error="無効なダウンロード形式です。"), 400

    try:
        item = metadata(url)
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return jsonify(error="動画情報を取得できませんでした。"), 422

    if mode == "audio":
        command = ["yt-dlp", "--no-playlist", "--no-warnings", "-f", "bestaudio", "-x", "--audio-format", "mp3", "-o", "-", url]
        extension, mimetype = "mp3", "audio/mpeg"
    else:
        command = ["yt-dlp", "--no-playlist", "--no-warnings", "-f", "best[ext=mp4]/best", "--merge-output-format", "mp4", "-o", "-", url]
        extension, mimetype = "mp4", "video/mp4"

    def generate():
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            while chunk := process.stdout.read(64 * 1024):
                yield chunk
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()

    filename = safe_filename(item["title"], extension)
    return Response(
        stream_with_context(generate()),
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
