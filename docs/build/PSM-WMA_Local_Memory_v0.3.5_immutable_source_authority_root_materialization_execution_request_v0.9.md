# Immutable source authority-root materialization execution request v0.9

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`
**状态**：待三方审核；这是一份 exact execution request，不是新的 design Gate。

## Authority

唯一 candidate parent=`b3595395427114f73ff53a19a0c2b9180e39905f`，child Gitlink=
`93a89ba61306d840a008813f62f26a34d54850f4`，唯一 ref=
`refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`。批准后只允许一次 authority-root
materialization；成功后提交 authority tuple 并硬停。collection、receipt、source-evidence、publication、child、
GPU、训练、评测、推理与 LIBERO4IN1 不在本请求范围。

selection/config 的 frozen raw SHA-256 分别为
`8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd` 与
`43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d`。Git=`/usr/bin/git`
(`587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a`)，Python=
`/opt/conda/bin/python3` (`f3e3f561b473976be55d937616915d6c507dedcb3950c3ca72df786b28e8efdc`)；
remote 固定为 `https://github.com/wxwy/psm_wma.git`。启动前 clean root
`/disk/rl/psm_wma/.authority-root-materialization-b359539`、其 index/backing/evidence/pending 以及 local/remote
固定 ref 全部必须 absent；否则零 mutation fail-stop。

## FD8 child ABI 与 import closure

FD 3/4/5 是 selection/config/bootstrap-contract，FD8 是 clean owner。child argv 的 cwd、index、project root
严格是 `/proc/self/fd/8`、`/proc/self/fd/8/.authority-root.index`、`/proc/self/fd/8`，且含
`--bootstrap-owner-root-fd 8`。parser argv=2,336 bytes，SHA-256=
`51a82a6b2efb9aeee2cc2ecf057d5b7b16a6a841a1ed26c484e98b4a9f483e7d`；bootstrap observation=2,341 bytes，
SHA-256=`3227a514b8bcfe4e557d7ea890964a97cd8a978f208ed36d4671c8d5e680bbb8`；bootstrap contract=182 bytes，
SHA-256=`a434efd7eaa56d5217f88e0d0eee8697c523e38fb3fe625af4d0007f26ea1c5a`。

在 `sys.path` 或 project import 前，FD8 no-follow traversal 必须验证：

| path | blob | raw SHA-256 |
|---|---|---|
| `tools/psm_wma/materialize_immutable_source_authority_root.py` | `70b29267ea23dc4ca9d82d98ecd2b19423a9fc5e` | `fc346d8133871c81ffba539d8a748c015b81e8428f1fa094ec352e6be42851be` |
| `tools/psm_wma/immutable_source_authority_root.py` | `9937f74c49b14d489823c731aa2856b00c1a3d06` | `4ebf9fb8b0605bc30c45800bdfa7d367444ff97daee69926eba9aa5c9817f5d0` |
| `tools/psm_wma/immutable_source_collection.py` | `4e9f51a52e822e7e57b67aa6ff5eaab8613566c1` | `89eb3ee194f16665aea76ed4dcbaba803fc944d1e0b889d25be69d0831e68c67` |
| `tools/g0/audit_r09_b_ttt_root_gitlink_authority.py` | `d0020f067badfe591152fafa6336e20b485eb5ba` | `3db6376b35141d8ca5dc72c1bb38359943961db92545a88f320603121db4c39e` |

## Canonical payload overlay

payload base 是本 request parent tree 的
`docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`：blob
`615d6b117f810c4cb8c9459971caa32589352c93`、raw SHA-256
`3a5b4cd99730ddb01098ed53d4278f1f7b8ef142bc234405095df54de4ec7ea5`。runtime 仅可使用下列确定性 overlay：

1. 将 formal `9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5`（2处）、clean suffix
   `.authority-root-materialization-9dd2fb8`（4处）替换为本请求的 b359 值；
2. adapter blob/raw、collection blob/raw 替换为上表的 b359 值；
3. embedded parser argv 的 cwd/index/project-root 改为 FD8 ABI，并在 project-root 后插入
   `--bootstrap-owner-root-fd","8`；
4. embedded bootstrap length/SHA 改为
   `8351`/`57266c12d011921614b66b8faaf20815bb83c37ff01e0aef5be7686598fbcb89`，parser length/SHA 改为
   `2336`/`51a82a6b2efb9aeee2cc2ecf057d5b7b16a6a841a1ed26c484e98b4a9f483e7d`，contract SHA 改为
   `a434efd7eaa56d5217f88e0d0eee8697c523e38fb3fe625af4d0007f26ea1c5a`。

派生 payload 必须恰为 17,389 bytes，SHA-256=
`4b85f226f3de63821fcaa922cc353d3917983bcf00adfeff1bade448914b599a`；任一字节、计数或 SHA 漂移为
`BLOCKED_AUTHORITY_NOT_CLOSED`，零 mutation。

## Verdict

请求最终 verdict：

```text
APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT
```

或 `REQUEST_CHANGES(file:line)`。批准不授权任何下游 collection/receipt/source-evidence/publication 或运行。
