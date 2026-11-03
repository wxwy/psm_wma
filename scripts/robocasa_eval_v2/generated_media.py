"""All-mode diagnostic completion, independent from scientific Core and SR."""

from cosmos_framework.evaluation.robocasa_v2.generated_video import read_receipt
from cosmos_framework.evaluation.robocasa_v2.store import read, write


def publish(store):
    tasks = []
    expected = saved = acknowledged = episodes = 0
    errors = []
    for task in store.manifest["task_order"]:
        for row in store.rows(task):
            episodes += 1
            count = row["replans"]
            expected += count
            directory = store._slot(task, row["episode"])
            try:
                path = directory / "generated_media_completion.json"
                if (
                    path.is_symlink()
                    or not path.is_file()
                    or path.stat().st_size > 256 * 1024
                ):
                    raise ValueError(
                        "ordinary bounded generated-media completion required"
                    )
                completion = read(path)
                if (
                    not isinstance(completion, dict)
                    or completion.get("status") != "COMPLETE"
                    or completion.get("task") != task
                    or completion.get("episode") != row["episode"]
                    or completion.get("attempt_id") != row["attempt_id"]
                    or completion.get("server_ack_required")
                    is not (
                        store.manifest.get("execution", {}).get("profile")
                        == "phase_b_native_batch_v1"
                    )
                    or any(
                        type(completion.get(k)) is not int or completion[k] != count
                        for k in ("expected", "saved", "acknowledged")
                    )
                    or completion.get("missing") != []
                ):
                    raise ValueError(
                        "MEDIA_INCOMPLETE: generated completion/count binding"
                    )
                media = directory / "media"
                names = {p.name for p in (media / "generated").glob("replan_*.mp4")}
                if names != {f"replan_{i:04d}.mp4" for i in range(count)}:
                    raise ValueError("MEDIA_INCOMPLETE: MP4 inventory mismatch")
                for index in range(count):
                    receipt = media / "generated" / f"replan_{index:04d}.receipt.json"
                    if receipt.is_symlink() or receipt.stat().st_size > 65536:
                        raise ValueError("ordinary bounded Encoder receipt required")
                    binding = read(receipt)["binding"]
                    episode = binding["episode"]
                    if not isinstance(episode, dict):
                        raise ValueError("MEDIA_INCOMPLETE: invalid Episode receipt")
                    if any(
                        episode.get(k) != row[k]
                        for k in ("task", "episode", "attempt_id", "generation")
                    ):
                        raise ValueError("MEDIA_INCOMPLETE: wrong Episode receipt")
                    read_receipt(
                        media, index, binding
                    )  # Hash the already fully decoded file; no FFmpeg here.
                saved += count
                acknowledged += count
                tasks.append(
                    {
                        "task": task,
                        "episode": row["episode"],
                        "status": "COMPLETE",
                        "replans": count,
                    }
                )
            except (OSError, ValueError, KeyError, TypeError) as error:
                if len(errors) < 64:
                    errors.append(
                        {
                            "task": task,
                            "episode": row["episode"],
                            "error": str(error)[:1024],
                        }
                    )
    total = len(store.manifest["task_order"]) * store.manifest["episodes_per_task"]
    result = {
        "schema": "psm_generated_media_summary_v1",
        "status": "COMPLETE"
        if not errors and episodes == total
        else "MEDIA_INCOMPLETE",
        "manifest_digest": store.manifest["digest"],
        "episodes": episodes,
        "expected_episodes": total,
        "expected": expected,
        "saved": saved,
        "acknowledged": acknowledged,
        "errors": errors,
        "independent_of_SR": True,
        "episodes_complete": tasks,
    }
    write(store.root / "media_summary.json", result, replace=True)
    return result
