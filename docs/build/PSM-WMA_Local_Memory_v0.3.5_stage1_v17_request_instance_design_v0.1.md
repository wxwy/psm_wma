# Stage-1 v1.7 request-instance design v0.1

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`。

本设计只授权构造一份 docs-only exact request，供独立审核；不授权 materialization 或任何真实 I/O。
v1.6 authority 已耗尽，不能复用。

## 冻结依赖

- formal parent=`08d5828cdb4c12afa3b798ff01826c91ceb8755a`，launcher base blob=`af19a9eb66ecaf8bd0b92a48ab1867f105026658`，raw=`8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`，bytes=`18966`。
- frozen replay implementation root=`50b0bffeb4c94b0994d7c7bf705077fb51a9e48f`：module blob/raw=`74455fce6ca90ede8d9935d893a7a74f5667c687` / `8f55dc32a77810d848c10ac55501754f741d42bd3ef3fbc386f0814b2a6d5e82`；test blob/raw=`a38bd4536d48c5178c63c595e4e02980b15af998` / `af00b4a19c027f0a59e74eb3c30e772b9a1aaecf93f7d16d60a714a7cabccff3`。
- canonical replay output remains parser=`2336/1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333` and outer=`18875/658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`.

## Construction contract

Future construction is limited to one new root docs-only Markdown/JSON pair.  It must run the frozen pure helper against injected verified formal-parent blob bytes, then take one same-round, zero-mutation freshness snapshot and bind every observed value into canonical JSON.  It must not import the helper as an execution entrypoint, invoke a launcher, or create any Stage-1 runtime artifact.

The snapshot may read only the formal Git object/commit tree, the local `.git` identity and config bytes, fixed local/remote refs, and the designated clean-root/index/ref/evidence/pending path absences.  It must not open source/checkpoint/manifest/data/cache content, create directories, mutate refs, or contact runtime services.  The request must record the exact observation time and every raw-byte length/SHA needed to recompute: selection/config/bootstrap bytes, parser argv, six-key environment, owner-FD insertion, replay output, cwd/index/evidence targets, and its own canonical JSON whole bytes/SHA.

No fallback base, mixed formal parent, stale observation, inferred default, reordered argv/environment, duplicate owner-FD, or request-byte mismatch is permitted.  Each such condition must fail as `BLOCKED_AUTHORITY_NOT_CLOSED` before `os.execve`; no retry is permitted.  The resulting exact request still needs an independent same-pair three-party request review before it can grant a single Stage-1 attempt.  This design itself does not collect the snapshot or create JSON.

Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
