"""Small source-controlled static Viewer server with MP4 byte-range support.

Python's stock SimpleHTTPRequestHandler returns 200/full-file for Range,
which disrupts browser seeking and Replay when Right/Wrist load an MP4.
Directory listings and all non-MP4 URLs retain the stdlib behavior.
"""
from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import re


_SINGLE_RANGE = re.compile(r"^bytes=(\d*)-(\d*)$")


def parse_byte_range(header: str, size: int) -> tuple[int, int] | None:
    """Parse one inclusive HTTP byte range, or reject unsatisfiable syntax."""
    match = _SINGLE_RANGE.fullmatch(header.strip())
    if match is None or size <= 0:
        return None
    before, after = match.groups()
    if not before and not after:
        return None
    if before:
        first = int(before)
        if first >= size:
            return None
        last = min(int(after), size - 1) if after else size - 1
        if last < first:
            return None
        return first, last
    suffix = int(after)
    if suffix <= 0:
        return None
    return max(0, size - suffix), size - 1


class VideoRangeHandler(SimpleHTTPRequestHandler):
    """Serve MP4s with HTTP 206/Content-Range; leave directory views alone."""

    def send_head(self):
        self._range_remaining = None
        path = self.translate_path(self.path)
        if not path.lower().endswith(".mp4") or not os.path.isfile(path):
            return super().send_head()
        try:
            media = open(path, "rb")
        except OSError:
            return self.send_error(404, "Video unavailable")

        stat = os.fstat(media.fileno())
        size = stat.st_size
        requested = self.headers.get("Range")
        if_range = self.headers.get("If-Range")
        last_modified = self.date_time_string(stat.st_mtime)
        if if_range and if_range != last_modified:
            requested = None
        if requested:
            span = parse_byte_range(requested, size)
            if span is None:
                media.close()
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                return None
            first, last = span
            code = 206
        else:
            first, last = 0, size - 1
            code = 200

        self.send_response(code)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(max(0, last - first + 1)))
        self.send_header("Last-Modified", last_modified)
        if code == 206:
            self.send_header("Content-Range", f"bytes {first}-{last}/{size}")
        self.end_headers()
        media.seek(first)
        self._range_remaining = max(0, last - first + 1)
        return media

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_range_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        while remaining:
            data = source.read(min(65536, remaining))
            if not data:
                break
            outputfile.write(data)
            remaining -= len(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18765)
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    if not root.is_dir():
        parser.error("directory must be an existing folder")
    handler = partial(VideoRangeHandler, directory=str(root))
    with ThreadingHTTPServer((args.bind, args.port), handler) as server:
        print(f"G2_VIEWER_RANGE_SERVER {args.bind}:{args.port} {root}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
