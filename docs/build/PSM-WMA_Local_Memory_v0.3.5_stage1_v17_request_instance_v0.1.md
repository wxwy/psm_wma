# Stage-1 v1.7 exact request instance v0.1

**Gate**：`G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`。

本文件与同名 JSON 是依据 v0.4 construction 令牌构造的唯一 docs-only request。它不授权、也不执行 Stage-1 materialization；v1.6 authority 已耗尽且不可复用。

## Freshness 与 replay binding

JSON绑定 formal parent `08d5828cdb4c12afa3b798ff01826c91ceb8755a`、child `93a89ba61306d840a008813f62f26a34d54850f4`、launcher base `af19a9eb66ecaf8bd0b92a48ab1867f105026658/18966/8b0fad...`、closed replay root `50b0bffe...`和canonical parser/outer bytes/SHA。

同名 JSON 为 `3054` bytes，SHA-256=`2fffb82a905f5e53d950c5cb3fc8235d6e58726a1144ca26a107a011d7c5a59d`；其闭包包括 selection/config/bootstrap/contract identities、owner-FD、六键环境名及 cwd/index/evidence targets。

本轮仅完成设计allowlist的只读观察：local authority ref returncode=1；V2与fixed authority-ref的两条`ls-remote`均returncode=0、stderr为空；authority-ref stdout为空。四个clean/index/evidence/pending路径均不存在。任一观察、stdout/stderr、returncode、base或path漂移均为`BLOCKED_AUTHORITY_NOT_CLOSED`。

## Boundary

本实例仍须取得 ChatGPT/MM/DS 对本身 exact pair 的独立最终批准后，才可能授权一次 Stage-1 attempt。此前及此后均禁止 launcher/materializer执行、source/checkpoint/manifest/data/cache I/O、child/runtime mutation、GPU/CUDA/torchrun、训练、评测、推理及LIBERO4IN1。
