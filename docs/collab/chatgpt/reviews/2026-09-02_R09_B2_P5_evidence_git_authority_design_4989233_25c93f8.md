# R09-B2 P5 Evidence Git Authority design review

## Request / design

- Request commit: `4989233e187dbfe120166e738586b2b1d32099ef`
- Design commit: `25c93f8234faef81938abfd18c6658cad6a050fb`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`REQUEST_CHANGES`

`APPROVE_TO_IMPLEMENT_P5_EVIDENCE_GIT_AUTHORITY_STATIC` is not authorized.

## Findings

### HIGH — HEAD/current equality does not make the committed evidence revision authoritative

`docs/build/PSM-WMA_R09_B2_P5_evidence_git_authority_design_v1.0_2026-09-02.md:3` requires a full-clean Git evidence root and `git show HEAD:<path>` bytes == current bytes for the fixed P4-v4 request/result/verification files, then states that a shared replacement of all three files must FAIL.

That conclusion does not follow from the proposed checks. An attacker or accidental workflow can replace all three JSON files consistently, commit them, and present a clean checkout at that new commit. The files are then tracked, canonical, and `HEAD` bytes equal current bytes, so every stated Git-authority check still passes. Merely recording the observed evidence-root HEAD/Gitlink is observation, not an independently frozen authorization.

Required fix: define an out-of-band/verifier-owned authority for the accepted evidence publication. After the separately reviewed record/refreeze commit exists, P5 must bind to an independently frozen evidence identity such as an exact approved evidence commit/tree plus the three fixed blob SHA256 values, or an equivalent closure manifest whose own expected digest is pinned in reviewed verifier tooling. The three evidence files cannot authorize the commit that contains them. Add a permanent negative test that commits a mutually consistent replacement of all three files into a new clean Git HEAD and still requires FAIL.

### HIGH — submodule clean state is not an explicit Gitlink identity proof

The same design line requires both `evidence_root` and `cosmos-framework` to be full-clean and says the verifier records the root Gitlink, but it does not require the exact equality chain:

`git ls-tree HEAD cosmos-framework` == `git -C cosmos-framework rev-parse HEAD` == frozen/authorized Gitlink.

A clean detached submodule checkout is not itself an authority proof. The consumer must independently bind the parent Gitlink and actual submodule HEAD, not merely record them.

Required fix: make the equality mandatory before reading P4-v4 evidence, and add a negative fixture with a clean submodule checkout at the wrong revision.

### MEDIUM — publication authority must distinguish the evidence commit from later unrelated descendants

Once an authorized evidence identity is introduced, define whether P5 accepts only the exact detached evidence commit or may accept descendants. If descendants are permitted, the verifier must independently prove ancestry from the authorized evidence commit and exact equality of the fixed evidence blobs/Gitlink; simply trusting the descendant HEAD reopens the shared-replacement hole.

## Positive observations

- Correctly rejects non-Git, untracked, symlinked, dirty, and blob/current-drift evidence roots.
- Correctly moves CPU fixtures from arbitrary temporary directories toward real temporary Git checkouts.
- Scope remains static verifier/tests only; no preflight, staging, refreeze, export, compose, GPU, or training is authorized.

## Gate decision

Revise the P5 evidence-authority design to add an independently frozen publication identity and explicit parent-Gitlink/submodule-HEAD equality. No P4-v4 implementation or execution authorization follows from this review.
