# Stage-1 authority-root materialization request v1.6

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

**状态**：docs-only v1.5 execution-boundary 最小整改 request；待独立三方审核。

## 1. Supersession 与唯一 authority

本文件和同名 canonical JSON 替代历史 v1.1--v1.5 request instance。唯一 formal parent 是
`08d5828cdb4c12afa3b798ff01826c91ceb8755a`；child/Gitlink 为
`93a89ba61306d840a008813f62f26a34d54850f4`。除 §5 明确 execution boundary 外，v1.6 保持 v1.5 的
rebound-parent、freshness、FD、closure 与 replay identities 不变。

## 2. Rebound launcher 与唯一 owner-FD 插入

base path=`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`，blob
`af19a9eb66ecaf8bd0b92a48ab1867f105026658`，SHA-256
`8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd`，bytes=`18966`。
它的 `RAW[2]` 必须含零个 owner-FD flag；既存/孤立 occurrence 一律
`BLOCKED_AUTHORITY_NOT_CLOSED`。只可替换 formal parent 和 cwd/index/bootstrap-root owner-FD paths，紧随
`--bootstrap-project-root` value 插入唯一相邻 `--bootstrap-owner-root-fd`, `8`，并替换 adapter/collection
blob/raw identities。canonical parser array 必须恰有该一对，随后只按 JSON `ordered_replay` splice/substitute；
任何base/path/blob/raw/length/fallback/mixed-parent drift 均 fail-close。

## 3. Same-round zero-mutation freshness

2026-09-14 15:59 CST 构造轮重新观测：`.git`=`dev=1048655,ino=9223372050462812349,directory`；
`.git/config`=`dev=1048655,ino=3075283643,regular,size=477`, SHA-256=
`f15e655f21ecf517b9074fbf99b6ebccd4aff99489735776769ecb510cb8b611`；local fixed ref=`absent_rc_1`，remote
fixed ref=`absent_zero_lines`；clean root/index/evidence/pending 四路径均 absent。`.git` directory size 不绑定，
因为 Git bookkeeping 合法可变。只使用stat/SHA/ref read/remote read/test，未执行 launcher、未创建任何对象。
future runtime 必须重新观测并逐项匹配，drift 在 mutation 前拒绝。

## 4. Recomputed identities 与 whole-request binding

- parser=`2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333`；
- bootstrap=`9406 / ccd8ee2772d666707c919e6a20376c997771b9ff068fe0432fdaa96c686ab097`；
- bootstrap argv=`2341 / 85ac67c8a062399dfbface5f9c42867401ffab45320f802697c704061be8df9d`；
- contract=`182 / bec6a57aab61fd888ef0eedce37adce227a38a299a9faded53b252c8b5901702`；
- outer payload=`18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8`；
- sibling canonical JSON=`8622 bytes / 2a82314c9b8594230229ef2c875b0611e2131377bbe267b589c762a588fd4421`。

runtime 必须先重算 sibling JSON exact bytes/SHA，再进入 freshness、FD 或其他检查；JSON冻结four-module
closure、FD3/4/5/8、Git/Python/env/metadata，runtime只能拒绝drift。

## 5. 唯一 post-approval execution authority

三方对本文件所属 exact pair 全批准前，禁止执行。三方同pair全批准后，只授权**此 exact request 的一次**
Stage-1 materialization attempt：任何 request/base/freshness/FD/path/ref 的 pre-mutation drift 都必须以
`BLOCKED_AUTHORITY_NOT_CLOSED` 零 mutation 拒绝；成功只可产生 authority tuple 并立即硬停。attempt失败或
已消耗后，必须新建 exact request 并取得新的独立三方批准。明确不授权retry/second attempt、Stage-2、
collection/receipt/record/package/publication、child/runtime/config mutation、GPU/CUDA/torchrun、训练、评测、
推理或LIBERO4IN1。

请求最终 verdict：`APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` 或
`REQUEST_CHANGES(file:line)`。
