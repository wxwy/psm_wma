# Authority-root launcher v0.7 temporary witness plan

本 witness 仅使用 `tempfile.TemporaryDirectory()`、临时 Git repo 与 forked 子进程。禁止使用
`/disk/rl/psm_wma` 的真实 `.git`、CLEAN、artifacts、source/checkpoint 或任何生产路径。

| witness | 注入点 | PASS |
|---|---|---|
| same/different FD | reader equals / differs target | target identity、bytes、offset 均正确 |
| extra FD | exec 前额外 regular FD | close-set 恰为 `{3,4,5}` |
| same-bytes replacement | reader open 后 rename 同 bytes inode | pathname/reader/target identity 不一致即拒绝 |
| mode drift | writer close 后 chmod | 非 `0600` 即拒绝 |
| commondir | preflight 或 Git 前后插入/替换 | ordinary route fail-closed |
| add boundary | mock nonzero/partial add、post-add route drift | 已证实 absence 才 ordinary FAIL，否则 `ROLLBACK_INCOMPLETE` |
| cleanup | foreign clean-root replacement / remove fail / normal remove | foreign/fail 为 `ROLLBACK_INCOMPLETE`，normal 后所有路径与 list entry absent |

每一 witness 必须绑定后续 immutable v0.7 payload 的 line-level seam；不得以描述、mock 未触及 seam 或旧 pair
结果替代。
