"""F22 source-level static/dynamic color merger parity, without server paths."""
import unittest

import numpy as np

from g2.offline.fast_static_dynamic_merge import aggregate, combine, check_equivalence


def reference_full_scene(layers, specs):
    keys = np.concatenate([layers[s["g"]][0] for s in specs if layers.get(s["g"]) is not None])
    rgb = np.concatenate([layers[s["g"]][1] for s in specs if layers.get(s["g"]) is not None])
    owners = np.concatenate([
        np.full(len(layers[s["g"]][0]), s["owner"], np.int32)
        for s in specs if layers.get(s["g"]) is not None
    ])
    unique, inverse = np.unique(keys, axis=0, return_inverse=True)
    count = np.bincount(inverse, minlength=len(unique))
    sums = np.column_stack([
        np.bincount(inverse, weights=rgb[:, channel], minlength=len(unique))
        for channel in range(3)
    ])
    colors = np.rint(sums / count[:, None]).astype(np.uint8)
    owner_min = np.full(len(unique), np.iinfo(np.int32).max, dtype=np.int32)
    owner_max = np.full(len(unique), -2, dtype=np.int32)
    np.minimum.at(owner_min, inverse, owners)
    np.maximum.at(owner_max, inverse, owners)
    merged_owners = np.where(owner_min == owner_max, owner_min, -1).astype(np.int32)
    xyz = (unique.astype(np.float64) + .5) * .01
    return xyz, colors, np.ones(len(xyz), bool), merged_owners, {}


class DirectColorMergeParity(unittest.TestCase):
    def setUp(self):
        self.specs = [dict(g=i, owner=o) for i, o in [(0, 1), (1, 2), (2, -1), (3, 5)]]
        self.layers = {
            0: (np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]], np.int32),
                np.array([[1, 2, 3], [3, 4, 5], [5, 6, 7]], np.uint8)),
            1: (np.array([[0, 0, 0], [1, 1, 1]], np.int32),
                np.array([[100, 110, 120], [9, 10, 11]], np.uint8)),
            2: (np.array([[1, 1, 1]], np.int32), np.array([[33, 44, 55]], np.uint8)),
            3: (np.array([[-12, -5, 2]], np.int32), np.array([[12, 23, 34]], np.uint8)),
        }

    def check_reference(self):
        slow = reference_full_scene(self.layers, self.specs)
        fixed, _ = aggregate(self.layers, self.specs, {0, 2})
        moving, _ = aggregate(self.layers, self.specs, {1, 3})
        fast, _ = combine(fixed, moving)
        self.assertTrue(check_equivalence(slow, fast))
        self.assertTrue(np.array_equal(np.sort(slow[3]), np.sort(fast[3])))

    def test_initial_color_merge(self):
        self.check_reference()

    def test_dynamic_geom_replace_no_ghost(self):
        self.layers[1] = (
            np.array([[7, 7, 7], [8, 8, 8]], np.int32),
            np.array([[10, 20, 30], [12, 22, 32]], np.uint8),
        )
        self.check_reference()

    def test_ownership_conflicts(self):
        self.layers[3] = (
            np.array([[1, 0, 0], [-12, -5, 2]], np.int32),
            np.array([[45, 67, 89], [12, 23, 34]], np.uint8),
        )
        self.check_reference()

    def test_only_static_map(self):
        fixed, _ = aggregate(self.layers, self.specs, {0, 1, 2, 3})
        actual, _ = combine(fixed, None)
        self.assertTrue(check_equivalence(reference_full_scene(self.layers, self.specs), actual))

    def test_only_dynamic_map(self):
        moving, _ = aggregate(self.layers, self.specs, {0, 1, 2, 3})
        actual, _ = combine(None, moving)
        self.assertTrue(check_equivalence(reference_full_scene(self.layers, self.specs), actual))

    def test_random_3000_cells_with_overlap(self):
        rng = np.random.RandomState(12)
        keys = rng.randint(-100, 100, (3000, 3)).astype(np.int32)
        unique = np.unique(keys, axis=0)
        self.assertEqual(len(unique), 3000)
        self.layers[0] = (unique, rng.randint(0, 255, (3000, 3), dtype=np.uint8))
        self.layers[1] = (unique[:40].copy(), rng.randint(0, 255, (40, 3), dtype=np.uint8))
        self.layers[2] = (np.array([[-5, -5, -5]], np.int32),
                          np.array([[0, 0, 0]], np.uint8))
        self.check_reference()


if __name__ == "__main__":
    unittest.main()
