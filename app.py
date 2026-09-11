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
YTDLP_BASE_COMMAND = [
    "yt-dlp",
    "--no-playlist",
    "--no-warnings",
    "--socket-timeout",
    "20",
    "--retries",
    "2",
]


class MetadataError(Exception):
    """An expected yt-dlp metadata failure that can be shown to the user."""


def user_facing_ytdlp_error(error: subprocess.CalledProcessError) -> str:
    """Turn common extractor failures into useful, non-sensitive guidance."""
    output = (error.stderr or "").lower()
    if "confirm you're not a bot" in output or "sign in to confirm" in output:
        return "YouTube が Render の共有サーバーからのアクセスを制限しています。時間をおいて再試行してください。"
    if "private video" in output or "video is private" in output:
        return "この動画は非公開のため、サーバーから情報を取得できません。"
    if "video unavailable" in output or "not available" in output:
        return "この動画は現在利用できないか、お住まいの地域では再生できません。"
    if "unsupported url" in output:
        return "この形式の YouTube URL には対応していません。動画ページの URL を入力してください。"
    return "動画情報を取得できませんでした。Render のログに yt-dlp の詳細を記録しました。"


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
    try:
        completed = subprocess.run(
            [*YTDLP_BASE_COMMAND, "--skip-download", "--dump-single-json", url],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.CalledProcessError as error:
        app.logger.warning("yt-dlp metadata request failed: %s", error.stderr)
        raise MetadataError(user_facing_ytdlp_error(error)) from error
    except subprocess.TimeoutExpired as error:
        app.logger.warning("yt-dlp metadata request timed out: %s", error)
        raise MetadataError("動画情報の取得がタイムアウトしました。時間をおいて再試行してください。") from error
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
    except (MetadataError, json.JSONDecodeError) as error:
        return jsonify(error=str(error)), 422


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
    except (MetadataError, json.JSONDecodeError) as error:
        return jsonify(error=str(error)), 422

    if mode == "audio":
        command = [*YTDLP_BASE_COMMAND, "-f", "bestaudio", "-x", "--audio-format", "mp3", "-o", "-", url]
        extension, mimetype = "mp3", "audio/mpeg"
    else:
        command = [*YTDLP_BASE_COMMAND, "-f", "best[ext=mp4]/best", "--merge-output-format", "mp4", "-o", "-", url]
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
