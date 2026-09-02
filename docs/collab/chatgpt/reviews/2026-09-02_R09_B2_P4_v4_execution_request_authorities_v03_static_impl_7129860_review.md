# Independent Review — R09-B2 P4-v4 Execution Request `authorities` v0.3 static implementation remediation

- Review target implementation: `71298606989270640f9338c612ff3559882a7c9c`
- Request record HEAD inspected: `567577384076ae8d7252a83e390ba9620a9f969b`
- Approved design: `54830a20cab3e2d9995781faf1244684c6bd02d0`
- Previous ChatGPT review anchor: `bdf5574d3eb882e75e7e64254d7027133cccf5d7`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: root static tooling / stdlib CPU only. No real preflight, staging/materialize/candidate, record/refreeze, evidence publication, P5 authority/export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T or Local Memory training authorized.

## Verdict

`REQUEST_CHANGES`

The previous implementation-level TOCTOU issue is fixed: `_read_historical_artifact()` now opens the lexical path directly with `O_NOFOLLOW`, then uses the same fd for `fstat`, `/proc/self/fd/<fd>` containment, and raw read. I found no new main-validator blocker.

Closure is still blocked only because the approved v0.3 design explicitly froze a permanent CPU negative matrix and the submitted tests do not yet fully implement that matrix.

## Remaining closure blockers

### HIGH — Permanent authority fixture matrix is still incomplete

Approved v0.3 freezes all of the following as permanent fixtures: artifact/source/verifier binding path/sha/identity/revision/blob/host-Git argv/PATH shadow; regular/no-follow/TOCTOU; record canonical/backend/schema/status/self-digest; verification exact pretty bytes plus every nested layer added/missing/false/non-bool; record swap/duplicate path; environment projection/effective/native/P3; ambient `os.environ` independence.

The remediation materially improves coverage, including pair/source/verifier identity drift, duplicate binding, host-Git/PATH shadow exact argv, native/P3/missing environment, and record field drift. However these explicit branches remain unclosed:

1. **FIFO / non-regular artifact** — directory is covered, FIFO is not. Add an actual FIFO fixture and verify fail-closed without hanging.
2. **Single-open / explicit TOCTOU regression** — current code is structurally single-fd, but no permanent test asserts one lexical `os.open` and no pathname re-open/retarget after open. Add an `os.open` count/binding fixture or equivalent retarget-after-open test that proves the accepted bytes are fd-bound.
3. **Record non-canonical raw** — semantic field mutations are covered, but no fixture presents valid decoded historical record semantics with non-canonical raw bytes and proves rejection by the raw canonical equality branch.
4. **Verification exact pretty-byte binding** — nested semantic grammar is tested directly, but there is no full `validate_authorities_pair()` fixture that mutates only the historical `verification.json` raw formatting/bytes while preserving decoded object semantics and proves the fixed verification binding SHA rejects it.
5. **Verification nested roster exhaustiveness** — the design says every layer must reject added/missing/false/non-bool. Current test samples only: top added, checks added, `distinct_outputs=false`, matched non-bool, recurrent missing key, TTT non-bool. Add the missing branches so top/checks/matched/backend layers each exercise the frozen mutation classes, especially missing top/checks/matched, false matched/backend, and added backend keys.

Once those named branches are permanent CPU fixtures, this section can close. Do not change the historical-D005 authority model or main validator unless a new defect is discovered.

## Progress

Closed sections remain 4/8: `entry`, `source`, `interpreter`, `environment`. `authorities` remains in static implementation remediation; `run`, `candidates`, `backends` remain pending. No real execution is authorized.
