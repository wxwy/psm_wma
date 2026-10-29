"""Final Phase B CPU replay: all B1 + Phase A + native Batch/OS runtime tests."""

from pathlib import Path

from run_eval_v2_transactions_b1_cpu_gate import main

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    extra = [
        str(p.relative_to(root))
        for folder in ("scripts/robocasa_eval_v2", "tools/v3/eval_v2_batch_tests")
        for p in (root / folder).glob("*.py")
    ]
    raise SystemExit(
        main(
            extra_production=[
                "evaluation/robocasa_v2/contract.py",
                "inference/robocasa_batch_transactions.py",
                "inference/robocasa_batch_transactions_test.py",
                *[
                    f"simulation/robocasa/eval_v2_{s}.py"
                    for s in (
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
                "simulation/robocasa/eval_v2_transactions_test.py",
            ],
            extra_static=["tools/v3/run_eval_v2_batch_b2_cpu_gate.py", *sorted(extra)],
            extra_tests={"phase_b_runtime": ["tools/v3/eval_v2_batch_tests"]},
            gate_name="PHASE_B_FINAL_AUTHOR_OR_DS_CPU_ONLY_SYNTHETIC_NATIVE_BOUNDARIES",
        )
    )
