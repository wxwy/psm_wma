# G2-N6-F1-A：官方来源身份与完成范围修复

任务：[Issue #26 的 F1 指令](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6719814733)。本批从 `f1e4f1f0e3f2a48c3361987fabf58e406b313c7b` 派生 `codex/g2-n6-f1-source-gate`。原 N6 runtime 为 `c7ebb429`；nav_sg 保持 `2009fae35d86579bb22c273fb97ec1bf0835b533`，Gitlink 保持 `1ca308055fc41fb69efaeb9efaa23808f164a18e`。

本批修复 F1-A 及其紧邻的范围门禁，提供后续 F1-B 的完整 geom 审计。真实 Layout 1/10 四帧、普通 Floor/Wall、真实模型流程和六图人工验收均未由本批执行或关闭。原 N6 合成结果不替代这些 Gate。停止在固定源码和 GPT 独立服务器复验交接，不进入 PSS、Cosmos、GPU 或训练。

## 缺陷、行为变化与复用入口

旧代码对任何 `ep_meta` 记录都检查 `record.name`。官方 fixture 是 `fixtures[name] = {"cls": ...}`，身份位于 key；`object_cfgs` 才是带 `name` 的 list。现在：

- `/fixtures/<escaped-key>`：严格匹配解码后的 key、可选的记录内 name 和实际 `cls`。
- `/object_cfgs/<canonical-index>`：严格匹配唯一 name，保留原始 `obj_groups`、`obj_type` 或 `cls` 的字段名与值。groups 不被改写为推断类别。
- `source_category` / `source_category_field` 若提供，必须与官方字段精确一致；缺失、纯空白、类型错误和矛盾身份拒绝。
- RFC 6901 的 `~0/~1` 正确解码；非法 escape、负索引、前导零、标量穿透、缺项和嵌套伪记录拒绝。Fixture-list 旧测试替身不作为官方格式兼容。
- fixture/object 来源不能声明 robot 角色；官方来源字段不能通过改成 `source_kind=mjcf` 静默绕过。
- `source_body_name` 若提供，必须是实际 compiled geom 的祖先。官方 fixture/object 不能用 world 根代替所属 body。该检查证明声明 body 属于实际祖先链，fixture 与 body 的来源对应关系仍需独立审核。

原有 `source_geometry.load_model/apply_state/surface_colors` 继续负责资产闭包、状态恢复和真实 UV/albedo；不改点云颜色算法，不重建环境，不生成相机或虚构位姿。native API、Room/Island、训练及 Gitlink 无改动。

## 声明子集与整屋来源分开

合法局部导出继续保留 `COMPLETE` 和 `status=COMPLETE`，其新增明确含义是：

```json
{
  "completion_scope": "DECLARED_VISUAL_GEOMS_ONLY",
  "training_ready": false,
  "gates": {"full_scene_source_certified": false}
}
```

每个 compiled geom 都进入 `geom_audit`，包括被排除的 collision/robot/auxiliary：原生 ID/name、body 祖先、实际 world 位姿、尺寸、几何类型、group、碰撞位、材质 ID/name、原始/有效 RGBA、官方来源、分类理由和颜色状态。`geom_audit_sha256` 固定审计内容。汇总包括角色与类别来源分布、已采样点颜色有效率、unsupported 模式/几何类型与逐 geom 缺口。颜色有效率的分母明确是**声明范围内已采样表面点**，不能解读成整屋覆盖率。

`classification_reason` 缺失、官方 body 未绑定或有 unsupported appearance 时，`full_scene_review_eligible=false`。eligible 仅表示可供来源审核，仍然不是整屋认证。某个可见 geom 是否被错列 auxiliary，必须对照实际 MJCF/body/material 做独立来源审核，不能仅靠角色表完整而认定正确。

普通 `g2.nav_bridge.recorded` 默认拒绝仅有 COMPLETE 的输入，要求独立 source/role/material review。合法子集必须显式使用 `--allow-declared-subset`，结果标为 `DIAGNOSTIC_SUBSET_PLAN_ONLY_NOT_EXECUTED`，不具整屋来源认证。

审核记录绑定原始 manifest SHA、geom audit SHA、scene/source/visual SHA 和确切 frame。校验会重算来源身份、完整资产闭包和审计，逐 geom 重新核对官方记录、body 声明与分类理由，核对点云文件哈希和头部、坐标系及帧类型。记录示例仅作格式模板，**PENDING 必须由实际独立审核者完成审核后决定，代码不会自动改成 APPROVED**：

```json
{
  "schema": "g2_full_scene_source_review_v1",
  "scope": "FULL_SCENE_SOURCE",
  "review_kind": "SOURCE_ROLE_AND_MATERIAL_REVIEW",
  "decision": "PENDING",
  "reviewer": "<independent reviewer>",
  "reviewed_utc": "<ISO8601 with timezone>",
  "scene_id": "<actual scene>",
  "frame_id": 0,
  "source_sha256": "<actual shared source SHA256>",
  "visual_source_sha256": "<actual visual source SHA256>",
  "manifest_sha256": "<exact manifest file SHA256>",
  "geom_audit_sha256": "<exact audit SHA256>"
}
```

这是精确工件绑定的外部审核声明，不是密码学执行证明，也不代表普通结构、模型、人工六图或 training_ready 已通过。

## 快照与视图的机械门禁

`native_run` 中自行填写的 reviewed scope 不被信任。普通快照需要实际匹配的 native RGB-D/model audit；若要保留审核过的完整来源，还必须显式传入：

```bash
python -m g2.nav_bridge.snapshot --native-directory "$NATIVE_FRAME" \
  --native-run "$RUN/native_run.json" --output "$NEW_BUNDLE" \
  --prescan-manifest "$COLOR0/manifest.json" --full-scene-review "$SOURCE_REVIEW0"
```

审核过的普通 bundle 除原生四文件外，封存 `source_evidence/manifest.json`、`review.json`、`precolored.txt`。capture/load/render 共用实物复验，关联 native 最初输入的实际 cloud/visual SHA、scene、world 和 frame 0。它不复制 MJCF、模型权重或原始 RGB-D。原始预着色输入最多仍受导出器 500 万点预算约束；封存会增加本地磁盘占用。上述私有证据仅在服务器本地保留，不上传 GitHub。

旧 bundle 和缺少审核的 prescan 保留未认证状态。字段伪造、缺实物、拒绝的 review、重算 bundle 自描述哈希或 audit 内部矛盾不能升级。原生结构完整时，未经来源审核的 prescan 视图仍为 `BLOCKED_FULL_SCENE_SOURCE_REVIEW`；结构不完整则仍为 `BLOCKED_NATIVE_STRUCTURAL_ROOTS`。Oracle 始终是独立诊断，不能获得普通路径认证。

## 作者 CPU 验证

环境复用本地隔离 Python 3.12 / MuJoCo 3.3.7 / NumPy 2.3.5，无新依赖、GPU、模型推理或服务器连接。

```bash
# PROBE_DIR 为新的本地临时目录；OLD_SOURCE 固定为 f1e4f1f0。
mkdir -p "$PROBE_DIR"
cp "$F1_SOURCE/g2/tests/test_source_identity.py" "$PROBE_DIR/"
cp "$F1_SOURCE/g2/tests/test_recorded.py" "$PROBE_DIR/"
# 两次使用字节相同的 31 项探针；旧源码应出现预期 RED：
(cd "$OLD_SOURCE"; PYTHONPATH="$OLD_SOURCE" python -m pytest \
  "$PROBE_DIR/test_source_identity.py" \
  "$PROBE_DIR/test_recorded.py::test_complete_marker_alone_cannot_create_full_scene_plan" -q)
(cd "$F1_SOURCE"; PYTHONPATH="$F1_SOURCE" python -m pytest \
  "$PROBE_DIR/test_source_identity.py" \
  "$PROBE_DIR/test_recorded.py::test_complete_marker_alone_cannot_create_full_scene_plan" -q)
# 完整新源码测试：
(cd "$F1_SOURCE"; python -m pytest g2/tests -q --junitxml="$NEW_LOCAL_JUNIT")
```

历史 RED 的测试是在修改生产函数前实际运行；旧 COMPLETE 直通用例在 detached `f1e4f1f0` worktree 通过同一测试文件单独复现。具体命令、测试文件/source SHA、JUnit 和日志摘要见 `docs/evidence/g2_n6_f1_a_2026-11-08/`。新增覆盖：官方字典/list、指针、类别/角色负控、源/坐标/审计一致性、子集完成标志、实际审核工件封存与篡改，以及自建 FULLPHYSICS frame 0/200 身份保持/0.2 m 位移。它们不是原始 Layout 数据或正式模型执行。

## GPT 服务器复验交接

沿用已有隔离 CPU 环境与原始私有资产，不编辑服务器正式代码仓；在新的隔离源码副本验证固定 SHA，所有输入只读，输出必须是新目录。无需重建环境。原始 MJCF/状态、ep_meta、颜色输出、图片和报告均留服务器，不回传本工作区或 GitHub。

对 Layout 1/10 各自的 frame 0/200：

```bash
python -m g2.sim.prescan --mjcf "$MODEL" --metadata "$N6_ROLES" \
  --ep-meta "$EP_META" --states "$STATES" --state-format mujoco_fullphysics \
  --asset-root "$ASSET_ROOT" --frame "$FRAME" --spacing "$SPACING" \
  --native-manifest "$MATCHING_N5_MANIFEST" --allow-partial-color --output "$NEW_PRIVATE_OUTPUT"
```

`N6_ROLES` 必须是独立审核的 `g2_sim_prescan_v1` 全 geom 表，不能直接把旧 N5 include 格式当作新表。使用现有 rebased source 与 N5 manifest 可做诊断对照；不能把 rebased XML 静默当作原始 `model.xml.gz` 的同字节录制来源，录制适配器原有源哈希等式仍须满足。

先重跑公开 schema 测试与 `/fixtures/outlet_room` 的原始正/负控，再核对全 geom 数、所有 role/body/官方实例、四帧 state row 与 N5 source、动态 ID/位姿，以及颜色有效率的分母和逐项排除/unsupported 原因。若仍仅为 4/5 个附件，允许声明子集 COMPLETE，但 full-scene source 必须保持未认证。partial appearance 不写 COMPLETE。不得将任何测试数字硬编码成真实通过条件。

审核后可在服务器本地独立检查 scope：

```bash
python - "$COLOR/manifest.json" "$SOURCE_REVIEW" <<'PY'
import sys
from g2.sim.source_scope import verify_full_scene_review
result = verify_full_scene_review(sys.argv[1], sys.argv[2])
print(result["status"])
PY
```

回填需逐场景/帧记录固定 PSM/native SHA、source/model/state/audit SHA、总数与角色分布、颜色缺口、声明/整屋审核状态和失败原因。图像对照与完整 JSON 仅留 data。作者自测不代替 GPT 独验。待本批复验后，再推进 nav_sg #8 的普通结构根和后续六图人工 Gate；本批不关闭 Issue #26/#8。
