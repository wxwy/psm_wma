# R02 NVIDIA EGL NV_ATTRIB — Ruff format-only narrow remediation (Codex)

**Status: REQUEST_CHANGES / STATIC_GATE_ONLY.** Owner/DS feedback: formal Root `286573d2d592cbd7449930e6e93f188a3a9b037d` / Child+Gitlink `37558dcc71682304f3de1848923e6cedb9b77837` underwent an independent CPU test on DS server, **66 passed / 0 failed / 0 errors / 0 skipped**; Ruff check PASS; AST PASS; **Ruff format --check FAIL** on the exact two changed files. No GPU 1EP was run. This is **not** a new production correctness finding; current formal code is **not yet APPROVE_CODE** because the required static Gate is red.

## Scope and identity
- Both repos candidate branch `v3-eval-v2-egl-nvidia-attrib-20261103`. Formal technical target is Root `286573d2d592cbd7449930e6e93f188a3a9b037d`, Child `37558dcc71682304f3de1848923e6cedb9b77837`. Subsequent request/review/Inbox commits are bookkeeping and cannot replace those targets.
- Only source changes authorized:
  1. Child `cosmos_framework/simulation/robocasa/render_devices.py`
  2. Root `tools/v3/eval_v2_batch_tests/render_devices_test.py`
  3. Root `cosmos-framework` Gitlink advanced to the new Child SHA.
- **No semantic source modifications**: don't change NVIDIA `eglQueryDeviceAttribEXT`, CUDA-to-PCI mapping, physical proof, strict refusal, reset/context verification, test assertions, or model/action/media/TTT logic. Do not change the old discarded `v3-eval-v2-egl-index-fallback-20261103` branch.
- Root V3 official and official Child `v3-local-ttt` must remain unchanged; no GPU jobs, R02 Fresh, 900EP, train/resume, out2/NoTTT/H2/H3, old Evidence overwrite or process operations.

## Codex action — format the two files using Ruff **0.12.7**
In isolated clean candidate checkout with Root/Child exactly matching the Formal pair, preserving the existing clean worktree before the two intentional edits:

```bash
set -euo pipefail
cd "$ISOLATED_ROOT"
test "$(git rev-parse HEAD)" = "286573d2d592cbd7449930e6e93f188a3a9b037d"
test "$(git rev-parse HEAD:cosmos-framework)" = "37558dcc71682304f3de1848923e6cedb9b77837"
test "$(git -C cosmos-framework rev-parse HEAD)" = "37558dcc71682304f3de1848923e6cedb9b77837"
ruff --version  # must be ruff 0.12.7
# BEFORE formatting, save old AST fingerprints outside the checkout.
python - <<'PY'
import ast, hashlib, json
from pathlib import Path
files=[
 "cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py",
 "tools/v3/eval_v2_batch_tests/render_devices_test.py",
]
p=Path("/ABS/OWNED_NEW_FORMAT_EVIDENCE/ast_before.json")
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps({f:hashlib.sha256(ast.dump(ast.parse(Path(f).read_bytes()),include_attributes=False).encode()).hexdigest() for f in files},indent=2))
PY
# Use the actual project formatters/configs:
# Child: cosmos-framework/.ruff.toml line-length=120.
ruff format cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py
# Root: default formatter settings; do not force Child config onto Root tests.
ruff format tools/v3/eval_v2_batch_tests/render_devices_test.py
ruff check cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py tools/v3/eval_v2_batch_tests/render_devices_test.py
ruff format --check cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py tools/v3/eval_v2_batch_tests/render_devices_test.py
python - <<'PY'
import ast, hashlib, json
from pathlib import Path
files=[
 "cosmos-framework/cosmos_framework/simulation/robocasa/render_devices.py",
 "tools/v3/eval_v2_batch_tests/render_devices_test.py",
]
original=json.loads(Path("/ABS/OWNED_NEW_FORMAT_EVIDENCE/ast_before.json").read_text())
after={f:hashlib.sha256(ast.dump(ast.parse(Path(f).read_bytes()),include_attributes=False).encode()).hexdigest() for f in files}
assert after==original, "Format-only AST parity violated"
print("AST FORMAT PARITY PASS")
PY
```

**Replace the `/ABS/OWNED_NEW_FORMAT_EVIDENCE` placeholder with a real new directory outside every repo; never run placeholders literally.** The above formatting must result in AST identity. Record `ruff format --diff`, `ruff format --check` and `git diff --check` for both repos. If any diff is not purely whitespace/quotes/line wrapping or AST differs, STOP; do not silently accept changed semantics.

## Narrow CPU validation
Repeat only:
```bash
python -m pytest --noconftest -c /dev/null -q -p no:cacheprovider \
  tools/v3/eval_v2_batch_tests/render_devices_test.py \
  tools/v3/eval_v2_batch_tests/render_mapping_test.py \
  --junitxml /ABS/OWNED_NEW_FORMAT_EVIDENCE/junit.xml
```
Use same CPU-only/offline environment as previous DS test and an external pytest temp/cache directory. Expected **66/66 PASS** (no skips), Ruff check & format --check PASS, AST parity PASS, no unrelated file changes. Do not rerun unrelated379/122/42 or CPU probes/hardware just for formatting.

## Publication and STOP
1. Commit **Child** format-only change to the isolated Child branch and obtain its new SHA.
2. Commit Root format-only test change, update Root Gitlink **to that exact new Child SHA**; record the new exact Formal Root/Child pair.
3. Keep before/after AST fingerprints, original 66-PASS DS report link/path, new local JUnit/logs, Ruff0.12.7 outputs, SHA/diff, branch state; publish author handoff + source binding and request GPT **fresh incremental Code Gate** (format-only, rather than re-reviewing model architecture).
4. **STOP.** Do not ask DS to start R02 1EP until fresh source approval + DS independent CPU/static PASS and Owner authorization/resources. Do not claim GPU passed.

This request is a narrow static Gate remediation, not a production-code redesign.
