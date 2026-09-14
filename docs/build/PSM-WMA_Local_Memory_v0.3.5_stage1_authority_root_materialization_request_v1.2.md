# Stage-1 authority-root materialization request v1.2

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`
**状态**：docs-only payload-binding correction；待独立三方审核，绝不执行。

## 1. 替代范围与零 mutation 结论

本文件及同名 canonical JSON 仅替代 v1.1 对 launcher `-c` payload、embedded parser、bootstrap
observed argv 和 bootstrap-contract 的错误 byte bindings。candidate parent
`b3595395427114f73ff53a19a0c2b9180e39905f`、child Gitlink
`93a89ba61306d840a008813f62f26a34d54850f4`、fixed ref、selection/config、FD3/4/5/8 ABI、route
snapshot、tool closure、metadata、环境和 hard-stop 均保持 v1.1 原样。

v1.1 的三方批准只授权其**精确** canonical bytes；由于实际 pre-exec replay 不等于其 payload
binding，未执行 launcher，也没有创建 worktree、backing/index/ref/evidence 或读取 source/checkpoint/
manifest/data/cache。本 v1.2 是新 request instance，必须重新获得同 pair 三方 final verdict；此前
`BLOCKED_AUTHORITY_NOT_CLOSED` 继续生效。

## 2. 已证实的 v0.9/v1.1 binding 缺陷

从 formal parent 的 base blob `615d6b117f810c4cb8c9459971caa32589352c93`（17,480 bytes，
SHA-256=`3a5b4cd99730ddb01098ed53d4278f1f7b8ef142bc234405095df54de4ec7ea5`）只读重放后，v0.9/v1.1
声明的 parser SHA `51a82a...`、bootstrap observed-argv SHA `3227a...`、contract SHA `a434...`和
payload SHA `4b85...`均不能由该 base 与声明规则推出。它们不是可执行 instance，不能以“接近”或
运行时重建补足。

## 3. v1.2 ordered replay（唯一允许的推导）

1. 在任何 source 文本替换前，解析 formal base `RAW[2]` 的 JSON argv array。
2. 只在该 array 内把 `--formal-root` 改为 b359 parent，`--cwd` 改为 `/proc/self/fd/8`，`--index`
   改为 `/proc/self/fd/8/.authority-root.index`，`--bootstrap-project-root` 改为
   `/proc/self/fd/8`；紧随其值插入 `--bootstrap-owner-root-fd`,`8`。以
   `json.dumps(..., separators=(",", ":"), ensure_ascii=False)` 序列化。
3. 将该序列化字节串在 source 的 original `RAW[2]` literal 位置恰替换一次；随后全局替换 formal
   root、clean suffix、adapter blob/raw、collection blob/raw。
4. 替换 bootstrap raw length/SHA、embedded `RAW[2]` expected length/SHA、以及 bootstrap-contract SHA。
   新 contract 是 canonical UTF-8 JSON，绑定实际 bootstrap raw 与实际 observed argv。

该顺序的唯一结果为：parser `2,336 bytes` /
`f50e925c55fc3e953649fe5311a300f1fd67fd35ceb5bd1a93ef202b99f821c8`；bootstrap observed argv
`2,341 bytes` / `2b4fa86035a8d6a90e602ec496e54ee39fcdf97e894cabfcc8f6b8db98716861`；bootstrap contract
`182 bytes` / `2b8ccfa6b5f3ed5c2a812749f915f965771d4c740875f30aee34d766e90a1580`；outer `-c` payload
`17,389 bytes` / `f3171fc64911e33be643a392854c3dc20c808c9dd1b02f5e091769655806f9a9`。

## 4. Canonical instance 与审查请求

唯一 canonical artifact 是
`PSM-WMA_Local_Memory_v0.3.5_stage1_authority_root_materialization_request_v1.2.json`：compact
sorted UTF-8 JSON 加一个 LF，**8,427 bytes**，SHA-256=
`56780b494ed03cc15a07d0b16690ef6f9434fb2621a0659420a0ebd5a1e365b3`。它包含完整 literal
argv、输入 raw bytes、FD ABI、closure、route snapshot 及 ordered replay。运行时只能重放并拒绝
drift，绝不得构造另一 instance。

请求最终 verdict：

```text
APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT
```

或 `REQUEST_CHANGES(file:line)`。即使批准也仅允许一次 Stage-1 materialization；PASS 只产生
authority tuple 后硬停。collection/receipt/record/package/publication、child/runtime、GPU/CUDA/
torchrun、训练、评测、推理与 LIBERO4IN1 全部不在范围内。
