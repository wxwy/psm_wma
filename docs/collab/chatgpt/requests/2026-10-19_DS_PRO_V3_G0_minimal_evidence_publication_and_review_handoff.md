# DS_PRO → G0 Evidence-only 最小补证发布指令（等待 Owner 授权）

**日期：** 2026-10-19
**正式状态：** `REQUEST_CHANGES` 仅由于 as-executed Git objects / 24 raw审计 / DCP小型metadata尚未向 GPT 独立可读；**不要再次运行 G0 GPU**。
**前一份 DS CPU 汇总已审读，无需重算/重采数据；缺失的是可访问的原件。**
**Review：** `docs/collab/chatgpt/reviews/2026-10-19_V3_G0_bounded3_0d770dd0_post_DS_CPU_evidence_remediation_review.md`。

## 推荐一次性披露

1. **先取得 Owner 对独立证据发布的明确授权。** 推荐发布独立分支 `evidence/g0-bounded3-20261019`，保持 G0 使用的原始本地 `0d770dd03ef701d85e58751aa7f6df58dd1a8861` Git 对象链。不可用新 squash/cherry-pick 替代执行时SHA、不可改写 origin/V3，不 force push。若 Owner 不愿远端发布，可交付带 SHA256 的只读 Git bundle + 原始小文件；仅本地 `git` 命令文本尚不足以形成 independent review。
2. 在证据分支另加一个**docs-only**独立 evidence commit，纳入：`g0_24_rank_iter_audit_raw.json`、`DS_PRO_V3_G0_bounded3_evidence_2026-10-19.json`、`robo15train_pane_history.txt`、`extract_g0_24_audit.py`、`assemble_g0_evidence.py`。额外纳入未含在汇总JSON中的 small manifest/身份/完成标志/日志片段，保持文件原始格式、校验hash、记录 `allowed_root_noncode_changes` 的运行前后时间归属。敏感路径、token、凭据必须脱敏。
3. GPT 将检查 `dd6e040e..0d770dd0` 是否 docs-only、Child Gitlink 是否完全一致；复算24个 `(rank,iter)` 唯一覆盖、成功run segment归属、`AUDIT_OK/missing=0` 的实际语义，核对DCP complete/latest/sidecar/identity/launch一致性、G0 diagnostic-only不可Resume和targetFS时点证据。
4. 发布完成只回报**证据分支名+完整 evidence commit SHA+ as-executed Root SHA+ manifest SHA256**，停止等待 GPT Evidence-only Gate 复审。禁止借此启动Fresh100、Resume500、Formal30k、GPU，禁止搬动/删除旧DCP/新G0 DCP。不要修改任何生产代码，不重开F0/F1 CPU / B1实验。

## 备选

Owner也可直接将完整 Git bundle 和小型证据文件上传到当前会话作为可验证工件，不依赖GitHub发布。**仅描述存在于训练机的文件名和“见文件”哈希，不足以作独立 Evidence 验收。**
