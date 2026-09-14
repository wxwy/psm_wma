# Stage-1 authority-root materialization request v1.5

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

**状态**：docs-only v1.4 最小整改 request；待独立三方审核，绝不执行。

## 1. Supersession 与唯一 authority

本文件及同名 canonical JSON 替代历史 v1.1--v1.4 request instance。唯一 formal parent 是已关闭
config-grammar remediation 的 `08d5828cdb4c12afa3b798ff01826c91ceb8755a`；child/Gitlink 不变为
`93a89ba61306d840a008813f62f26a34d54850f4`。它不复制旧 parent
`b3595395427114f73ff53a19a0c2b9180e39905f` 的任何 authority 数值。

## 2. Rebound launcher、唯一 owner-FD 插入与完整重演

canonical JSON 冻结 new-parent formal tree 内
`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`：blob
OID=`af19a9eb66ecaf8bd0b92a48ab1867f105026658`、raw SHA-256=
`8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`、bytes=`18966`。

ordered replay 必须先只读验证该 base path/blob/raw/length，再解析其 `RAW[2]` JSON array。该 exact base
中必须有零个 `--bootstrap-owner-root-fd`；出现任一既存 pair 或孤立 flag/value 均
`BLOCKED_AUTHORITY_NOT_CLOSED`。仅随后执行这些变换：替换 formal parent 与 cwd/index/bootstrap-root
owner-FD paths；在 `--bootstrap-project-root` 的对应 value **之后立即**插入唯一
`--bootstrap-owner-root-fd`, `8`；替换 adapter/collection blob/raw identities；以
`json.dumps(separators=(",", ":"), ensure_ascii=False)` canonical serialize。最终 parser array 必须恰有一个
相邻 `--bootstrap-owner-root-fd`, `8` pair，其他值或位置均 fail-close。再依序 splice parser，并且只做
JSON 中 `ordered_replay` 所列 source-level substitution；必须重算并匹配 parser、bootstrap、contract、outer
payload 和本节 whole-request identity。old base、fallback、mixed parent 或任一路径/blob/raw/length drift 均
`BLOCKED_AUTHORITY_NOT_CLOSED`。

## 3. 本构造轮 fresh zero-mutation observation

以下观测在 **2026-09-14 15:59 CST** 的 v1.5 构造轮重新取得；仅调用 local `stat`/SHA-256、Git ref
查询、remote ref read 和 `test`，没有执行 launcher 或创建任何 authority/worktree/index/ref/evidence。
`.git` directory 的 size 特意不绑定，因为 Git bookkeeping 可合法改变；仍绑定 stable dev/inode/type。

| target | 本轮观察 |
|---|---|
| `.git` | `dev=1048655`, `ino=9223372050462812349`, `directory` |
| `.git/config` | `dev=1048655`, `ino=3075283643`, `regular`, `size=477`, SHA-256=`f15e655f21ecf517b9074fbf99b6ebccd4aff99489735776769ecb510cb8b611` |
| local fixed ref | `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`: `absent_rc_1` |
| remote fixed ref | 同 ref：`absent_zero_lines` |
| clean/index/evidence/pending | `.authority-root-materialization-08d5828`, `.authority-root-materialization-08d5828/.authority-root.index`, `artifacts/g0/r09/authority_root_materialization_evidence_v1.json`, 其`.pending`均 absent |

这些 exact observations 已写入 sibling JSON `fresh_snapshot`。未来 runtime 必须先重新观测并逐项匹配，任何
drift 在 mutation 前拒绝；不能以新 snapshot 或 fallback 覆盖本 request。

## 4. 已重算 identities 与 canonical whole-request binding

- parser=`2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`；
- bootstrap=`9406 / ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097`；
- bootstrap argv=`2341 / 85ac67c8a062399dfbface5f9c42867401ffab45320f802697c704061be8df9d`；
- contract=`182 / bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702`；
- outer payload=`18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`；
- sibling canonical JSON=`8618 bytes / 6579bca17667803ddcd14cc49a5522ef0b9538753dd3ca3e872258a5848d1f30`。

最后一项是此 exact request 的 authority binding：runtime 必须先以 UTF-8 exact bytes 重算 sibling JSON
的 byte length/SHA-256 并匹配，才可进入 freshness、retained-FD 或其他检查。JSON 同时冻结 four-module
closure、FD3/4/5/8、Git/Python identity、环境、metadata 和 authority-tuple-only stop；runtime 只能拒绝 drift，
不能生成替代 request。

## 5. 停止条件与审核范围

三方对本文件所属新 exact pair 全批准前不得执行。即使未来获批，Stage-1 PASS 也只允许产生 authority tuple
后硬停；不授权 materialization/retry、source/checkpoint/manifest/data/cache I/O、collection/receipt/record/
package/publication、child/runtime、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。

请求最终 verdict：`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` 或
`REQUEST_CHANGES(file:line)`。
