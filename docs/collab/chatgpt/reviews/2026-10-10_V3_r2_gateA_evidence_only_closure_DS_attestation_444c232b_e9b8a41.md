# V3 r2 Gate A — Evidence-only closure on owner-accepted DS_PRO verification report

**Date:** 2026-10-10
**Reviewer:** ChatGPT
**Status:** **GATE_A_CLOSED — OWNER_ACCEPTED_DS_PRO_ATTESTATION**
**Nature:** Evidence-only closure of previously reviewed Gate A CPU/static scope, **not a new implementation/design technical review** and not a claim of direct inspection of DS original raw server artifacts.

## Formal implementation pair (unchanged)

- Root implementation SHA: `444c232b976e80ac68cde9e7370e73b9f6410f0e`
- Child/Gitlink SHA: `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
- Previously completed GPT Fresh Review: `docs/collab/chatgpt/reviews/2026-10-10_V3_r2_new_pair_static_fresh_review_444c232b_e9b8a41.md`.
- Current Root V3 commits after that pair are bookkeeping/Evidence records only and **must not** replace the formal implementation root. The Child remains unchanged.

## Closure authority and exact evidence basis

1. **Owner decision, 2026-10-10:** “不看原始证据了，我们相信ds对原始证据的判断。” The project owner explicitly directs reviewer to rely on the independent DS_PRO examination/attestation of raw evidence and to waive the further requirement that GPT itself obtain and re-inspect the original server `gate.json`, logs, JUnit and restoration witness for **this Gate A**.
2. **Independent execution source:** DS_PRO combined report, relayed by owner and saved verbatim in substantive content at `docs/collab/chatgpt/evidence/2026-10-10_V3_r2_gateA_DS/DS_PRO_GATE_A_PASS_NEWPAIR_COMBINED_2026-10-10_444C232B_E9B8A41.md`. This report is a signed/attributed executor attestation with run identifiers, exact pair, stage outcomes, test counts, environment and workspace-restoration checks, rather than an author self-test.
3. **Two same-pair executions independently reported PASS:**
   - Run1 external Evidence directory: `/tmp/psm_wma_v3_gateA_newpair_444c232b_20261010_124000/evidence/`.
   - Run2 authoritative: `/tmp/psm_wma_v3_gateA_newpair_444c232b_20261010_132247/evidence/`.
   - DS_PRO reports original unchanged runner `gate.json status=PASS` and exit 0 on both; `pair == pair_after` and frozen source SHA256 did not change during execution.
4. **Attested Gate A contract-to-behavior witness:**
   - exact Root/Child/Gitlink verified, Child clean and Root dirty allowlist respected;
   - `py_compile` 36 files;
   - Ruff 0.12.7 `check` PASS; `format --check` PASS, 28 files;
   - runner tests **8 passed**;
   - migration pytest **328 passed, 3 skipped**, 0 failed/errors on each run; 85.19 s / 90.81 s;
   - three `bash -n` launchers PASS;
   - required H3-F helper temporarily moved after independent SHA256/mode/mtime witness and restored after runs; matching `8b53ad9a01ee29d64420ff8995d1d40be57bdf99c45e96636913154715f732e0`, `SESSION.md`/`TODO.md` notes restored, previous worktree state preserved;
   - no training, GPU or DCP use.
5. Existing author's separate test logs/JUnit in `docs/collab/chatgpt/evidence/2026-10-10_V3_new_pair_author_check/` corroborate code-level syntax/Ruff/CPU results, but **were not substituted for DS_PRO independent execution**.

## Explicit transparency about verification level

**Directly checked by GPT:** GitHub formal Root/Child relationship and related review/report records, previous scoped code Fresh Review and author-attached logs from that review.

**Relied on as independent executor attestation by owner decision:** DS_PRO's reported raw `gate.json`, stage exits, pair-after and SHA256 witnesses, original JUnit, restoration records. Original DS raw files were **not** received or personally inspected by GPT; this is an explicitly **owner-waived second-reader requirement**, not a statement that those files have been verified by GPT.

Prior persistence note `docs/collab/chatgpt/reviews/2026-10-10_V3_r2_gateA_DS_report_evidence_intake_444c232b_e9b8a41.md` requested raw evidence; that follow-up requirement is **CLOSED by explicit owner instruction for this Gate A only**. Preserve the original DS host files where available; do not falsify or reconstruct them. **No additional Gate A execution or duplicate technical review is required for this same formal pair.**

## Skips and scope limits

Three explicit real-asset tests remain SKIPPED and OPEN (not treated as passes):
- `test_optional_real_data_debug_smoke`: real debug cache/source not provided;
- `test_optional_strict_real_data_grouped_smoke`: strict real cache/source not provided;
- `test_optional_real_strict_snapshot10_preflight`: real exact-window cache/source/Edge/base/VAE not provided.

Thus **Gate A CPU/static accepted and closed only**. This does **not** close MC-01 as an overall production readiness decision and does not approve Gate B (real RoboCasa source/action/state/latent/token/SequencePlan), Gate C (last complete DCP; Local, optimizer, scheduler, RNG and strict same-job Resume), Gate D (workers0/2/4 numeric and RSS/GPU profile), Gate E (real-policy online Local/simulator), Gate F (18-task screening), or original Formal30k Resume.

Expected frozen config digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` is **not newly measured**; the last complete formal checkpoint iteration remains **unknown**, never assume iter800. `formal_verified_index_30k` stays **STOPPED**. Next stage requires independent Gate B authorization and its own contract-bound Evidence. This owner's acceptance preference is **not a blanket waiver for future Gates**.
