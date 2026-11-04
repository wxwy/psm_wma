"""Exact-pair streaming CPU Gate; includes the established Phase A/B and media suites."""

from pathlib import Path

from run_eval_v2_transactions_b1_cpu_gate import main


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    static = [
        str(path.relative_to(root))
        for directory in (
            "scripts/robocasa_eval_v2",
            "tools/v3/eval_v2_batch_tests",
            "tools/v3/eval_v2_replan_tests",
            "tools/v3/eval_v2_streaming_tests",
        )
        for path in (root / directory).glob("*.py")
    ]
    raise SystemExit(
        main(
            extra_production=[
                "evaluation/robocasa_v2/contract.py",
                "evaluation/robocasa_v2/scheduler.py",
                "evaluation/robocasa_v2/store.py",
                "inference/robocasa_batch_transactions.py",
                "inference/robocasa_batch_transactions_test.py",
                "inference/robocasa_dual_mode_test.py",
                *[
                    f"simulation/robocasa/eval_v2_{name}.py"
                    for name in (
                        "adapter",
                        "slot",
                        "worker",
                        "transactions",
                        "transactions_test",
                    )
                ],
            ],
            extra_inference=[
                "inference/robocasa_batch_transactions_test.py",
                "inference/robocasa_dual_mode_test.py",
                "simulation/robocasa/eval_v2_transactions_test.py",
            ],
            extra_static=[
                "tools/v3/run_eval_v2_streaming_cpu_gate.py",
                "tools/v3/eval_v2_production_tests/slot_test.py",
                *sorted(static),
            ],
            extra_tests={
                "phase_b_runtime": ["tools/v3/eval_v2_batch_tests"],
                "media_replans": ["tools/v3/eval_v2_replan_tests"],
                "streaming": ["tools/v3/eval_v2_streaming_tests"],
            },
            gate_name="EVALV2_STREAMING_M32_AUTHOR_OR_DS_CPU_ONLY_SYNTHETIC_NATIVE_BOUNDARIES",
        )
    )
