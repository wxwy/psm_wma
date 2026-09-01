"""CPU regression for R09-B2 P1 cache-window membership indexing."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.g0.build_r09_b2_stream_manifest import cache_exists


class CacheExistsTest(unittest.TestCase):
    def test_loads_each_episode_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "episodes" / "episode_000007.pt"
            path.parent.mkdir()
            path.touch()
            cache_windows: dict[int, set[str]] = {}
            with patch("tools.g0.build_r09_b2_stream_manifest.torch.load", return_value={"windows": {"2": {}, "3": {}}}) as load:
                self.assertTrue(cache_exists(root, 7, 2, cache_windows))
                self.assertTrue(cache_exists(root, 7, 3, cache_windows))
                self.assertFalse(cache_exists(root, 7, 4, cache_windows))
            load.assert_called_once_with(path, map_location="cpu", weights_only=True)


if __name__ == "__main__":
    unittest.main()
