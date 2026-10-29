# Offline analysis of already archived Compact v2 evidence

Source snapshot: wxwy/psm_wma V3 at 66a5b99c0a23312525ccbdc0fadb4655bc7d0b19.
Historical training implementation: root 49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9 / child 746c5cf2f2324104a62fb71510343aa40d3976c5.

The adjacent Python script reads only the four archived JSON files, checks their SHA256 against the original reconstruction README, checks rank identity and group counts, and summarizes recorded metrics. It uses Python standard-library modules only. It does not import the project or PyTorch, contact a server, run a model, or modify raw evidence.

Reproduce from the repository root (no GPU or external network):

```bash
python3 docs/collab/chatgpt/evidence/2026-10-29_V3_NoTTT_Compact_v2_Offline_Analysis/analyze_compact_v2_existing_evidence.py \
  --input-dir docs/collab/chatgpt/evidence/2026-10-29_V3_NoTTT_Compact_GPU_v2_Reassembled \
  --output /tmp/compact_v2_existing_evidence_analysis.json
```

The checked-in JSON was produced by this script. No original gradient tensors are available: reported allclose outcomes, max_abs and relative L2 cannot be independently recomputed from tensors. Failure lists are truncated to 50, worst10 is selected by max_abs, and diagnostic all-parameter dictionaries were not retained. The output preserves those limitations.

Historical strict parity remains FAIL_PARITY. Compact-specific causal attribution is INCONCLUSIVE. The S2 execution authorization is a separate Owner-approved engineering decision in ../../reviews/2026-10-29_V3_NoTTT_Compact_Parity_Disposition_and_S2_Resume10_Authorization.md; this analysis alone does not change permissions.
