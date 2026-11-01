# Owner GPU resource-policy change — narrow author handoff

Status: REVIEW, separate fresh incremental Code Gate requested.

| Object | SHA |
|---|---|
| New Formal Root | `4b581493db805c92964cb27e740c736db87c0329` |
| Child/Gitlink, unchanged | `9a8cd6183424bfce245fbca393ca25ed59919ea6` |
| Previously approved Root | `6484dd83efc512e6801470790eb84ac7349c127a` |
| Candidate documentation base | `b0b6e8ca1bf3b4a5ca12771dd71b34b4f9666e72` |
| Branch | `v3-eval-v2-render-media-20261101` |

The prior exact-Pair APPROVE_CODE and RM-M01 closure remain valid. This request
only covers the Owner's new GPU admission policy, not a second review of Media,
rendering or DS mixed-interpreter acceptance. Evidence/receipt successors are
not implementation SHAs. No V3 promotion or runtime authority is requested.

## Owner policy and implementation

Only production file `scripts/robocasa_eval_v2/resources.py` changes:

- Removed external CUDA process query and foreign-workload BLOCKED_RESOURCE.
- Removed memory.used/total query and used+reserve/fraction GPU admission.
- Probe only selected index/UUID. Missing, duplicate, unselected or invalid device
  identities remain rejected. Target selector is4,5,6,7; no GPU0-3 query/work.
- Kept gpu_identity's UUID/PCI lookup, render role mapping and owned-only RSS
  budget. Child EGL device/actual Context verification and registered-process
  safety cleanup are byte-identical. Actual driver/CUDA/EGL execution errors
  retain existing propagation/handling; no capacity prediction or task management.

No new option is required. `before_models` is retained for call compatibility;
legacy GPU-budget config keys remain accepted but ignored by admission. Resource
diagnostics now return index->UUID, owned_pids and owned RSS, without unqueried
memory/reserve fields. Production callers only consume probe success. Config,
Runtime, model/Local-TTT, Media, Scheduler/Store, inference/Checkpoint/training,
Vendor, target2Server/16Sim M8/B2 and all video settings are unchanged. The Owner
instruction supersedes only the older design's two retired admission clauses;
frozen historical design/evidence/review files are preserved.

## Author CPU evidence

**70 PASS,0failure/error/skip**, clean Pair, Python3.13.5. Ruff0.12.7 check,
format, six-file syntax and source diff-check PASS.15 new policy cases +33
render-mapping cases +20 device/Context controls +2 entry resource cases.
Old memory/foreign-task blocking tests now assert the explicitly changed Owner
policy; missing device, malformed/ambiguous identity and owned RSS safety stay
negative tests. GPU-budget-key reads and any memory/process-list probe trip an
assertion in the new doubles, before and after model startup, EGL and OSMesa.

No actual NVML/nvidia-smi, GPU/EGL/FFmpeg/model/Server/RoboCasa, training, DCP or
active out2/NoTTT/shared directory/log access. No new DS independent execution.
Existing192/206/29 suites not rerun. Pure CPU probes and temporary own-proc,
fake metadata/config and EGL doubles only. All6 source bindings and
27 raw artifact hashes retained at `docs/collab/codex/evidence/2026-11-01_eval_v2_owner_gpu_policy_author_cpu`; source hashes/status
unchanged during test, Child commit unchanged. Scope proof retains old approval.

```bash
# cwd: /workspace/psm-wma-eval-render-media
/tmp/psm-eval-render-media-20261101/python313/bin/python \
  /tmp/psm-eval-owner-gpu-policy-20261101/run_cpu.py formal \
  /tmp/psm-eval-owner-gpu-policy-20261101/final
```

Explicit CPU/offline flags and external HF/Matplotlib/XDG/Ruff caches plus exact
commands are in final/invocation.json and commands.json. Original raw JUnit,
logs and zero-context Diff included. Development70 remains separate from final70.
Review only this resource-policy delta. Publish candidate/read back and STOP for
GPT narrow review; no automatic V3 merge, GPU/Canary/evaluation/out2 Resume or
training/DS dispatch. Runtime resource placement is the Owner's decision.
