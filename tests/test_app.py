from unittest.mock import patch

from app import app, is_youtube_url, safe_filename


def test_youtube_url_validation():
    assert is_youtube_url("https://www.youtube.com/watch?v=abc")
    assert is_youtube_url("https://youtu.be/abc")
    assert not is_youtube_url("https://youtube.com.evil.example/watch?v=abc")
    assert not is_youtube_url("file:///etc/passwd")


def test_filename_removes_unsafe_characters():
    assert safe_filename('My: video / test', 'mp4') == 'My video  test.mp4'


def test_info_rejects_non_youtube_url():
    response = app.test_client().post("/api/info", json={"url": "https://example.com/video"})
    assert response.status_code == 400


@patch("app.metadata", return_value={"title": "A video", "channel": "A channel", "thumbnail": None, "duration": 1})
def test_info_returns_metadata(mock_metadata):
    response = app.test_client().post("/api/info", json={"url": "https://youtu.be/abc"})
    assert response.status_code == 200
    assert response.json["title"] == "A video"
    mock_metadata.assert_called_once_with("https://youtu.be/abc")
