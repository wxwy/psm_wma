"""Read-only source/owned cleanup checks; server artifacts remain private."""

import hashlib
import json
import os
from pathlib import Path
import subprocess

BASE = Path(
    "/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue35_attention_20261109"
)
ROOT = BASE.parent / "_codex_issue31_prefix_pack_20261109/root2"


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def groups(pgid):
    members = []
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            tail = (item / "stat").read_text().rsplit(")", 1)[1].split()
            if int(tail[2]) == pgid:
                members.append(int(item.name))
        except (OSError, ValueError):
            pass
    return members


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            value.update(chunk)
    return value.hexdigest()


def main():
    before = json.loads((BASE / "capture01/source_before.json").read_text())
    after = dict(
        root=git(ROOT, "rev-parse", "HEAD"),
        child=git(ROOT / "cosmos-framework", "rev-parse", "HEAD"),
        gitlink=git(ROOT, "rev-parse", "HEAD:cosmos-framework"),
        root_status=git(ROOT, "status", "--porcelain"),
        child_status=git(ROOT / "cosmos-framework", "status", "--porcelain"),
    )
    assert before == after
    internal = BASE / "capture01/k1/run/_internal"
    records = list((internal / "processes").glob("*.json"))
    receipts = []
    for path in records:
        record = json.loads(path.read_text())["body"]
        receipt = json.loads((internal / "process_closed" / path.name).read_text())[
            "body"
        ]
        assert receipt["record"] == record
        assert receipt["cleanup"]["live_group"] is False
        assert not groups(record["identity"]["pgid"])
        receipts.append(dict(kind=record["kind"], closed=True, live_group=False))
    node = Path("/dev/dri/renderD132")
    derivative = dict(
        status="BLOCKED_REAL_INPUT_CAPTURE_NOT_GATE_PASS",
        formal_pair=after,
        source_unchanged=True,
        capture=dict(
            k1_target_source_step=32,
            k16_target_source_step=64,
            k1_completed=False,
            k16_attempted=False,
            frozen_request_count=len(
                list((BASE / "capture01/k1/capture").glob("request_*.pt"))
            ),
            env_step_executed=False,
            episode_sr_reportable=False,
            stop_reason="native physical EGL device proof unavailable before render/reset",
            original_driver_label_correction="capture01 intentional_early_stop=true was erroneous; actual capture never became ready",
        ),
        owned_cleanup=receipts,
        selected_render_node=dict(
            node=node.name,
            physical_pci=Path("/sys/class/drm/renderD132/device").resolve().name,
            uid=os.getuid(),
            groups=os.getgroups(),
            gid=node.stat().st_gid,
            mode=oct(node.stat().st_mode & 0o777),
            readable=os.access(node, os.R_OK),
            writable=os.access(node, os.W_OK),
        ),
        bootstrap=json.loads((BASE / "bootstrap02/result.json").read_text()),
        trace_reduction_sha256=sha(BASE / "trace_reduction.json"),
        input_capture_hook_model_validated=False,
        code_change_required_by_evidence=False,
        no_ttt_executed=False,
        no_production_change=True,
    )
    derivative["selected_gpu_status"] = subprocess.check_output(
        [
            "nvidia-smi",
            "--id=4,6",
            "--query-gpu=index,uuid,memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        text=True,
    ).splitlines()
    index = {}
    for path in sorted(BASE.rglob("*")):
        if path.is_file() and not path.is_symlink():
            index[str(path.relative_to(BASE))] = dict(
                bytes=path.stat().st_size, sha256=sha(path)
            )
    with (BASE / "server_artifact_index02.json").open("x") as f:
        json.dump(index, f, indent=2)
        f.write("\n")
    derivative["private_artifact_count"] = len(index)
    derivative["private_artifact_index_sha256"] = sha(
        BASE / "server_artifact_index02.json"
    )
    derivative["supersedes_metadata_only"] = (
        "status01 no_ttt_rerun=false was a mislabeled field; no No-TTT process was executed"
    )
    with (BASE / "diagnostic_status02.json").open("x") as f:
        json.dump(derivative, f, indent=2)
        f.write("\n")
    print(json.dumps(derivative))


if __name__ == "__main__":
    main()
