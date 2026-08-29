# ChatGPT Review — R09-A0 complete-reset closure @ root aa3bfbd / source 1fddced / submodule 6bf59c2

- Date: 2026-08-29
- Reviewer: ChatGPT
- Review request: `4ff6cdd007ac3ea5489eaa9e347189a06fc51ce6`
- Closure artifact commit: `aa3bfbd23e7e5e22313a97d25716ea8664be1092`
- Clean source root: `1fddcedc80d1e999719dfec15485c12ff304c67b`
- Submodule/Gitlink: `6bf59c27bfad72de13ef9b856e5786181b019a41`
- Verdict: **REQUEST_CHANGES**
- A1 / GPU / R09-B / multi-GPU / matched SR / backend freeze: **NOT APPROVED**

## Executive summary

The core selected-reset bug is fixed in implementation.

`RecurrentLocalMemoryBackend.reset_mask` now accepts the full persistent state:

```text
(latent, initialized)
```

and for selected samples performs:

```text
latent -> exact zero
initialized -> false
```

while preserving both components for non-selected samples.

The clean-source evidence flow is also correct:

```text
source root 1fddced
Gitlink     6bf59c2
submodule   6bf59c2
tracked_clean.root=true
tracked_clean.submodule=true
artifact committed separately in aa3bfbd
```

However, A0 still cannot close because several frozen hard assertions are not actually in the verifier/test PASS path.

## HIGH — reset-followup absence is claimed but not tested

The Inbox request says:

> 新增回归覆盖 reset 后全 mask 必须 absent

But neither the submodule test nor the verifier actually performs:

```text
reset full state
-> replay an all-masked next segment
-> assert selected sample present=false
```

Current test stops after checking:

```text
reset latent == 0
reset initialized == false
```

That proves reset-state mutation, but not the downstream observable behavior that originally motivated the bug.

### Required hard regression

For a selected sample with pre-reset:

```text
latent != 0
initialized = true
```

require:

```text
reset
-> latent == 0
-> initialized == false

then all-masked replay using reset state
-> present == false
-> token is absent/zero placeholder
-> latent remains zero
-> initialized remains false
```

For non-selected initialized samples in the same batch, the same all-masked replay must preserve:

```text
present == true
state unchanged
```

This should be part of verifier hard PASS and artifact assertions.

## MEDIUM-1 — provenance/clean still not part of hard PASS

Artifact values are currently clean and valid, which is good.

But verifier still computes:

```python
passed = all(checks.values()) and state_diff <= 1e-6 and token_diff <= 1e-6
```

The following are emitted but not required:

- root clean;
- submodule clean;
- Gitlink == submodule;
- provenance_valid.

Therefore a later dirty/mismatched run could still report `status=PASS`.

Since these values are already available, include them in `passed`.

## MEDIUM-2 — permutation isolation still does not verify all observable outputs

Current permutation check covers:

- latent;
- initialized.

It still does not independently compare:

- returned token;
- returned `present`.

The frozen A0 isolation contract applies to all backend outputs.

Require permutation equivalence for:

```text
latent
initialized
token
present
```

## MEDIUM-3 — finite assertion still omits normal-path backend parameters

Current `finite` assertion checks:

- latent;
- tokens.

The actual normal-path backend parameters are not included.

Add:

```text
all(backend.parameters finite)
and latent finite
and tokens finite
```

Meta-init finiteness is useful but is a separate initialization regression.

## MEDIUM-4 — command provenance is still a constant label hash

Current:

```python
hashlib.sha256("verify_r09_a0_contract".encode())
```

does not encode the actual invocation.

Record or hash a canonical structure containing at least:

```text
cwd
sys.executable
argv
output path
```

## Accepted closures

The following previous blockers are now accepted as closed:

- explicit persistent `initialized` state instead of latent-value inference;
- full-state reset clears selected latent + initialized;
- non-selected latent/presence preservation in reset API;
- clean-source two-stage artifact flow;
- root/submodule/Gitlink identity;
- meta -> to_empty deterministic init;
- state/token segment diff separation;
- masked-step inertness;
- nonzero selected reset precondition.

## Required next action

Keep **R09-A0 = REVIEW**.

CPU-only:

1. add reset -> all-masked-followup observable absence regression;
2. put that assertion in artifact hard PASS;
3. include clean/provenance in hard PASS;
4. extend permutation to token/present;
5. include normal-path parameter finiteness;
6. fix actual command provenance;
7. commit verifier/test changes first;
8. rerun from clean source;
9. commit artifact separately;
10. stop at REVIEW.

Do not start A1/GPU/R09-B/multi-GPU/long training/matched SR/backend freeze.

## Verdict

**REQUEST_CHANGES**
