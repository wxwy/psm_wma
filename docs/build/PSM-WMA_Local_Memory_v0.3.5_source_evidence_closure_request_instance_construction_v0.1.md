# Source-evidence closure request instance construction v0.1

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`

本文件只冻结一次性构造清单，不是 execution request，且不授权创建输入、执行命令或真实 I/O。

## 已盘点的只读身份

- root tree：`16220cb9bd7b2323504582501e8589dbcd96a7b9`
- child Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`
- Python：`/opt/conda/bin/python3.11`，SHA-256=`f3e3f561b473976be55d937616915d6c507dedcb3950c3ca72df786b28e8efdc`
- Git：`/usr/bin/git`，SHA-256=`587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a`
- authority adapter blob/raw SHA-256：`70b29267ea23dc4ca9d82d98ecd2b19423a9fc5e` / `fc346d8133871c81ffba539d8a748c015b81e8428f1fa094ec352e6be42851be`

## 构造时必须新鲜绑定

不得从本文或环境推导：selection/config FD identity 与 raw bytes、bootstrap contract/owner FD、formal root 的全工具 allowlist、cwd/remote/index/evidence 路径、sanitized env、commit metadata、完整 argv、local/remote ref 双端 absent observation。任一字段缺失或漂移即 `BLOCKED_AUTHORITY_NOT_CLOSED`，零 source open、零 Git mutation。

实例只能在上述字段同轮读取后 canonicalize 并计算 request SHA-256；随后独立三方审核该 exact SHA。批准不等于执行，执行后也必须在独立 receipt-root review 前停止。
