# Development history (author CPU, immutable raw results)

All inputs are public-repository synthetic fixtures / FakeEncoder. No private server files.

- First focus: 32PASS/10FAIL. New reader required explicit sealed-source filename dispatch; legacy reader previously hardwired final episode COMPLETE. Fixed without weakening legacy source checks.
- Second focus: 38PASS/4FAIL. PNG-disabled owner path needed explicit canonical temporary-input allowance only in new schema.
- Third focus:42PASS; later recovery focus46PASS. These overlap final cases and are not summed.
- full_round1: core283PASS, StageA125PASS/10skip/1FAIL. Old A1 missing-COMPLETE negative caught overly broad recovery; fixed with a durable exact publication journal. Original test unchanged.
- full_round2: core283PASS, StageA133PASS/10skip, related42PASS/3skip and static PASS. Protocol diagnostic failed because it incorrectly required independently regenerated source/gzip and serialized .pt files to be byte-identical. Corrected diagnostic copies exact sealed source input bytes, then compares source/recipe/logical index/canonical metadata/record hashes/tensors. Serialized pickle envelopes may differ while values and metadata agree. This diagnostic failure is not a renderer/VAE numerical defect.

Final scope adds legitimate source-release symlink rejection, disabled-profile preflight and concurrent read-only spool attachment. Final results live in ../final; raw earlier logs/JUnit retain original paths, failures and counts. Previous GPT evidence is untouched. Local missing native dependencies remain explicitly skipped; no substitutions/installations.
