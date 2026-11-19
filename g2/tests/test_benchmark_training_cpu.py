from collections import OrderedDict

import pytest
import torch

from g2.data.aligned_provider import _EpisodeData
from tools.g2.benchmark_training_cpu import _case_matrix, _schedule


class _Provider:
    def __init__(self):
        self.train_episode_keys = frozenset({("Pick", 0), ("Place", 3), ("Pick", 1)})
        rows = {
            key: {"key": key, "window_count": 1 if key == ("Pick", 1) else 3}
            for key in self.train_episode_keys
        }
        self.data = _EpisodeData(rows, lambda row: row["key"], 4)
        self._views = OrderedDict()
        self._language = OrderedDict()
        self.view_read_count = 0

    def read_common(self, *, task_class, episode_index, decision_frame):
        identity = self.data[task_class, episode_index]
        return {
            "identity": identity,
            "state15": torch.full((15,), episode_index + decision_frame),
            "static_task_text": f"fixed {task_class}",
        }

    def read_selected_views(self, identity, *, top_view_variant):
        self.view_read_count += 1
        return (
            {
                "identity": identity,
                "variant": top_view_variant,
                "latent": torch.full((2, 2, 2), float(identity[1])),
                "valid_mask": torch.ones((2, 2), dtype=torch.bool),
            },
        )

    def close(self):
        pass


def test_schedule_selects_only_sufficient_certified_train_windows():
    assert _schedule(_Provider(), 3, 2) == [
        (task, ep, frame)
        for frame in range(3)
        for task, ep in (("Pick", 0), ("Place", 3))
    ]
    with pytest.raises(ValueError, match="too few"):
        _schedule(_Provider(), 3, 3)


def test_explicit_replay_preserves_order_and_rejects_beyond_training_end():
    assert _schedule(_Provider(), 2, 8, ("Place/3/1", "Pick/0/0")) == [
        ("Place", 3, 1),
        ("Pick", 0, 0),
        ("Place", 3, 2),
        ("Pick", 0, 1),
    ]
    with pytest.raises(ValueError, match="exceeds the certified"):
        _schedule(_Provider(), 2, 8, ("Place/3/2",))


@pytest.mark.parametrize("top", (None, "with_robot"))
def test_provider_probe_preserves_sequence_and_tensor_bytes(top):
    schedule = _schedule(_Provider(), 3, 2)
    cases = _case_matrix(_Provider, schedule, (1, 2), (0, 2), 2, top)
    cold, warm = cases[0]["repeats"], cases[2]["repeats"]
    assert [r["joint_and_state15_misses"] for r in cold] == [6, 6]
    assert [r["joint_and_state15_misses"] for r in warm] == [2, 2]
    assert len({r["result_sha256"] for case in cases for r in case["repeats"]}) == 1
    assert all(
        r["selected_view_requests"] == (6 if top else 0)
        and r["selected_view_count"] == (6 if top else 0)
        for case in cases
        for r in case["repeats"]
    )


def test_probe_fails_if_cache_optimization_changes_data():
    class BadProvider(_Provider):
        def read_common(self, **key):
            result = super().read_common(**key)
            result["state15"] += self._episode_cache_size
            return result

    with pytest.raises(RuntimeError, match="result changed"):
        _case_matrix(BadProvider, _schedule(BadProvider(), 2, 2), (1, 2), (0,), 1, None)
