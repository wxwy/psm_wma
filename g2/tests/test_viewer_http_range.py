"""HTTP 206 seek contract for source MP4s without touching Viewer directories."""
from functools import partial
from http.server import ThreadingHTTPServer
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from g2.viewer.http_server import VideoRangeHandler, parse_byte_range


def test_single_range_parser():
    assert parse_byte_range("bytes=0-9", 100) == (0, 9)
    assert parse_byte_range("bytes=40-", 100) == (40, 99)
    assert parse_byte_range("bytes=-8", 100) == (92, 99)
    assert parse_byte_range("bytes=98-1000", 100) == (98, 99)
    for bad in ["bytes=100-", "bytes=9-3", "bytes=-0", "bytes=-",
                "bytes=0-1,5-9", "items=0-9", "bytes=ab-cd"]:
        assert parse_byte_range(bad, 100) is None


def test_mp4_ranges_and_directory_listing_with_symlink(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    source = tmp_path / "raw"
    source.mkdir()
    data = bytes(range(256)) * 4
    (source / "episode_000000.mp4").write_bytes(data)
    (root / "source_videos").symlink_to(source, target_is_directory=True)
    (root / "index.html").write_text("G2 viewer")

    class QuietRangeHandler(VideoRangeHandler):
        def log_message(self, _format, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0),
                                 partial(QuietRangeHandler, directory=str(root)))
    loop = threading.Thread(target=server.serve_forever, daemon=True)
    loop.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        url = base + "/source_videos/episode_000000.mp4"
        cases = [
            ("bytes=100-199", data[100:200], "bytes 100-199/1024"),
            ("bytes=1000-", data[1000:], "bytes 1000-1023/1024"),
            ("bytes=-16", data[-16:], "bytes 1008-1023/1024"),
            ("bytes=0-0", data[:1], "bytes 0-0/1024"),
        ]
        for spec, expected, content_range in cases:
            with urlopen(Request(url, headers={"Range": spec})) as response:
                assert response.status == 206
                assert response.headers["Content-Range"] == content_range
                assert response.headers["Accept-Ranges"] == "bytes"
                assert int(response.headers["Content-Length"]) == len(expected)
                assert response.read() == expected

        with urlopen(url) as response:
            assert response.status == 200
            assert response.headers["Accept-Ranges"] == "bytes"
            assert response.read() == data

        with urlopen(Request(url, method="HEAD", headers={
            "Range": "bytes=30-39"})) as response:
            assert response.status == 206
            assert response.headers["Content-Range"] == "bytes 30-39/1024"
            assert response.headers["Content-Length"] == "10"
            assert response.read() == b""

        try:
            urlopen(Request(url, headers={"Range": "bytes=100000-"}))
        except HTTPError as error:
            assert error.code == 416
            assert error.headers["Content-Range"] == "bytes */1024"
        else:
            raise AssertionError("invalid byte range must yield HTTP 416")

        with urlopen(base + "/") as response:
            assert response.status == 200
            assert response.read() == b"G2 viewer"
        with urlopen(base + "/source_videos/") as response:
            assert response.status == 200
            assert b"episode_000000.mp4" in response.read()
    finally:
        server.shutdown()
        server.server_close()
        loop.join(timeout=3)
