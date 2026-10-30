"""Author handoff/append-only ledgers; no project/test execution."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path('/workspace/work/psm-wma-dual-mode')
REL='docs/collab/codex/evidence/2026-10-30_eval_v2_dual_mode_author_cpu'
OUT=ROOT/REL
summary=json.loads((OUT/'summary.json').read_text())
assert summary['status']=='PASS' and summary['counts']['collected']==324
R=summary['formal_pair']['root']; C=summary['formal_pair']['child']
readme=f'''# EvalV2 No-TTT + Local-TTT：作者定向 CPU 与新 Pair 交接

日期：2026-10-30（CST）。这是作者 CPU 证据与窄增量 Code Gate 申请，不是 GPT verdict 或 DS/GPU 验收。

- **Formal Root：`{R}`**；**Child/Gitlink：`{C}`**。
- Root source parent：`608f55dccff6077e276e78644af6a578b4087781`，其生产基线为已批准 F5 `7c74dc26ac4837f193727ecf847b9b64554c18b2`。Child parent：`53c3c95202e14d3b72d236eee6899a80acf82989`。
- 权威需求：[Owner 双模式最终要求](https://github.com/wxwy/psm_wma/blob/56d8ba870b39e12cf7e2a4b8d9a25dcb31883cf0/docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_PhaseB_DualMode_NoTTT_LocalTTT_Owner_Requirement_Correction.md)。两次单模式建议撤回；旧 F5 APPROVE_CODE 保留，不冒充本增量批准。
- 隔离分支（Root/Child 同名）：`v3-eval-v2-dual-mode-20261030`。本证据/ledger 的后继提交不是 Formal Root；没有提升 V3 或 `v3-local-ttt`。

## 行为和边界

复用同一 Runtime、RoundScheduler、SimSlot、Session lease、executor、bounded queue/native batch、ACK/replay、原始 deadline、End、媒体与 owned-only cleanup。通过 EvalV2 config/CLI `local_memory_mode: off|required`（`--local-memory-mode`）选择。旧配置仍默认 required；**No-TTT 使用公共 `phase_b` 事务链路，cap=1 为 B1、cap>=2 为动态 Batch；旧 phase_a 维持原 required-only 合同**。没有另建 No-TTT 仿真框架。

No-TTT 最小配置增量：

```yaml
execution_profile: phase_b
local_memory_mode: off
sims_per_gpu: 2
max_infer_batch_size: 2
```

Local-TTT 使用同一配置结构，将 mode 显式设为 `required`，使用自身匹配的 checkpoint/config；不是遇错自动降级。模式写入 Manifest 的既有 `protocol.local_memory` 字段并参与 digest/Resume 严格相等；required Manifest 和 required wire `robocasa.session-transactions.b1.v1` 保持原语义。No-TTT 新 wire 为 `robocasa.session-transactions.no-ttt.v1`，以通用 `inference` Session/Episode/request_index 绑定请求，不伪造 Local consumer/evidence。No-TTT 的注册 ACK 必须带明确 mode/profile；required v1 客户端保留旧 ACK 读取兼容。新实际 INFO、ACK、Worker READY、actor settings 均带模式，并做错配拒绝。

事务层以自己的 COW `_responses` 保存已提交请求序号、payload SHA 与同一 response bytes；admission/result/ACK/replay 不读取 Local fast/response snapshot。required 为保持既有 Local 原子快照兼容，仍向 Local snapshot 镜像同一个 cached response 对象。整批响应/缓存预分配先于 Local commit；device drain/fence 后在同一个 actor lock 内执行真实 Local atomic commit，再发布公共字典。No-TTT 不创建 MemorySnapshot/Fast/Visual/Local update，也不调用 Local prepare/commit/abort/reset/status/prefixes 或向 native generator 注入 `_local_memory_prefixes`。

Server 公共构造入口核对显式 config bool、loaded net capability、实际 DCP Local tensor inventory 与完整参数 shape。按真实加载器选择权重树：MODULE/EMA 选择 net_ema；YAML/JSON 使用 net，即使 `use_ema_weights=True`。合法 regular+EMA 双树不会因重复 suffix 被误拒；缺失/shape 错和配置/模式冲突 fail-closed。原 required raw15/state15/H16/K4/local32、scan/tokenizer/FSDP/evidence chronology 保留。

Sim 在 No-TTT 时不创建 Local client，native action loop 走原 None 分支。公共 Session End ACK 成功才可完成 Episode。Core validator 按已绑定 Manifest 区分：required 旧证据不放宽；off 要求通用事务绑定、明确无 Local status/canonical Local evidence 和真实 End witness。历史文件名 `local_memory.json`、返回键 `local_session` 保留兼容，在 off 下只记录公共 Session 的关闭与 `off/not_instantiated`，不宣称 Local adaptation/prefix 成功。Store 只在 commit/read 两调用点传 mode，原 atomic persistence/limits 不变。

## 最终作者验证

**324/324 unique testcase PASS；0 failure/error/skip；Shell exit 0；source_unchanged=true。** Pytest 212.66s，外部 harness 218.34s。干净 Formal Pair 前后相同，44 个源码指纹保持一致。16 个测试文件，新增双模式 47 项（Child35 + Root12），受影响旧回归277项；不累计开发过程或启动修复的通过数。

- 公共 Session/Client/dispatcher 与真实 native tensor 构建：两模式 × B1/B2；单次 native call、request replay/ACK 丢包、changed payload/foreign Session、隔离、真实 Local fast 更新与 off 无 Local、timeout/End/生成故障。
- 两模式公共 ActionModelService.__init__、真实微型 CPU DCP inventory、regular+EMA selected-tree 正负例；Wan/diffusion/CUDA/distributed 初始化是显式 CPU doubles，未加载真实 checkpoint。
- 公共 CLI + real identity/Manifest/Store Fresh→Resume，模式变化拒绝，原 anchor/Core bytes 保留；vendor/library/execution 为合成 CPU 边界，未改真实 Source guard。
- No-TTT Core 五类损坏在 Store.commit 和读回两路径拒绝；第二个公共缓存分配失败、required 第二个 Local validate_commit 失败均无半提交。
- 真实 OS No-TTT G1×N2×M2×B2：1 Server/2 Sim，4 Core、8 replans，histogram B1×4+B2×2；不同 Episode Session，D5/Resume/进程关闭全部通过。
- 原 Local-TTT 三种 OS 拓扑及 F3 保留：G1N2E2 histogram B1×2+B2×3；G2N3E1 B1×4+B2×1；G1N3E1 B1×6，合法动态窗口不强制最后一者出现 B2。原多 Sim overlap/映射/Session/D5/Resume 断言通过。
- F3 原 cap1 故障仍在两个 Slot 分别 GENERATING/QUEUED 时确定触发，Server 原始 returncode=23、两 Sim=-15，0 Core；全部3 owned groups关闭，无 live group/remaining PID。foreign 存活由原通过测试中的 `poll() is None` 断言证明，不虚构单独快照。
- Ruff0.12.7 check21文件、format20文件及 legacy Queue 已改验证函数范围、compile21、Root/Child diff check、scope/AST/原真实 Source admission/import origin 检查通过。Queue 既有未改区域格式不扩大清理。

保护：vendor 逐资产 SHA、Runtime digest、F5 64MiB writer 和普通256KiB JSON、`verify_source()`、Model/Config/Manifest/Resume、共享 GPU 资源策略、Local 算法/训练/模型权重/Batch authority均保持。未运行旧435/完整900；未运行真实 GPU/仿真/Canary/训练，未接触当前 NoTTT Job 或其 checkpoint。

## 原件与可追溯性

- `raw/final/`：完整 JUnit、console、exact argv/env、Shell exit、前后 clean/指纹。`raw/static-final/`：检查日志、增量 diff、真实 source guard/import smoke。
- `summary.json`：逐测试文件计数、五个 OS 场景数据；`source_gitblob_bindings.json`：44个 Git Blob/SHA256。`original_to_published.json`：633份原件逐字节复制映射。
- `os_runs/`：原始日志、Manifest、Core、scheduler、process registry/closure、runtime proof；`cli_runs/`：两模式 identity/Core/Resume 文件；`tiny_synthetic_DCP/`：仅本测试写出的微型 CPU DCP metadata/shards，无真实 checkpoint。
- 不复制 mini Git 仓库、缓存、server capability 文件或整个 pytest tmp。
- 开发中失败原样保留：focused=21PASS/3FAIL（新 anchor 路径/父时钟 fixture）；focused2=132PASS/2FAIL（Core required 耦合、旧 huge frontier 拒绝位置）；focused3=31PASS/5FAIL（新 startup import、合成 Core fixture）；focused4=45PASS/2FAIL（新 startup fixture 的 use_state 层级）。startup-fix2=4PASS 只作修复检查。外部 recorder 最初不识别 `::nodeid` 的启动前失败未执行 pytest，不是 Gate；随后的静态/最终结果独立完整。未把这些中间版本结果加到324。
- 独立作者侧只读审查关闭 EMA 兼容 finding，检查新的原子性/清理/证据边界；这不是 GPT verdict 或 DS 独立测试。

## 交接

请求 GPT 只审核本双模式生产增量与定向证据，新 Pair 未经本会话自批。其后真实 GPU 必须分别验证 No-TTT 与 Local-TTT，各自稳定完整且匹配的 checkpoint/config、fresh namespace、单GPU双Sim/实测 B2、Episode/MP4/清理。两模式不相互替代。按 Owner 在新 Code Gate 后冻结的执行范围交 DS；本交接不自动授权8 Episode、重启当前 run、900评测或训练/资源策略变更。
'''
(OUT/'README.md').write_text(readme)
shutil.copyfile(Path(__file__),OUT/'instrumentation/record.py')
entry=f'''\n\n## 2026-10-30 — EvalV2 双模式生产增量 Code Gate 请求\n\n- **Formal Root `{R}` / Child+Gitlink `{C}`**，源基线7c74dc26/53c3c952（Root parent608f55dc为旧Evidence）。后继docs提交不是Formal Root。权威Owner双模式需求56d8ba87覆盖两次单模式建议；旧F5已批准，不重复审核或435。\n- 显式off|required进入Manifest/Resume、Server INFO/注册ACK/Sim READY。公共transaction COW response/frontier独立于Local，保留同一调度/Batch/lease/ACK/deadline/End/媒体/cleanup；off独立no-ttt.v1无Local state/evidence/prefix，required原v1/atomic Local/evidence严检保留。NoTTT需phase_b(cap1亦可)，phase_a保持required-only；不另建仿真框架。实际配置/loaded capability/DCP selected-tree完整shape交叉核对，YAML regular与MODULE EMA行为匹配，冲突不降级。\n- **最终干净Pair作者CPU324/324 PASS=新47+旧277，0fail/error/skip，shell0，source_unchanged=true/44指纹一致**；Ruff/format/语法21+scope/真实source guard PASS。公开CLI两模式FreshResume、B1/B2/native单调用、真实Local fast更新/NoTTT无Local、replay隔离/timeout/End、缓存/Local提交失败、Core两路径损坏拒绝；真实OS NoTTT双Sim B2四Core，原Local三拓扑/F3 exit23双Slot/foreign隔离全部通过。所有中间失败与原始日志保留，不累计。\n- Evidence：`{REL}/README.md`，含633原件映射、完整JUnit/OS/process/Core/微型syntheticDCP/source绑定。作者侧只读审查无剩余生产阻断，不是GPT/DS批准。\n- 请求 **APPROVE_CODE / REQUEST_CHANGES（仅本双模式增量）**；随后DS按Owner单独冻结范围分别真实GPU验两mode/匹配稳定checkpoint与config/独立namespace/单GPU双Sim实测B2+MP4+清理。未启动DS/GPU/Canary，未重跑435/900，未改共享GPU、训练/Checkpoint，未合并V3/v3-local-ttt，不回复旧Issue #8。\n'''
inbox=ROOT/'docs/collab/chatgpt/CODEX_INBOX.md'
assert len(inbox.read_bytes())+len(entry.encode()) <= 131072
with inbox.open('a') as f:f.write(entry)
with (ROOT/'SESSION.md').open('a') as f:f.write(f'''\n\n## 2026-10-30 — 双模式 source freeze / 作者 CPU handoff\n\n- V3-EVAL-V2-DUAL-MODE REVIEW; FormalRoot{R}/Child-Gitlink{C}; isolatedv3-eval-v2-dual-mode-20261030 only. 9Root路径(含Gitlink)/13Child路径；新增Core mode validation+Store两调用点为实际公开NoTTT提交所必需，Store其它保护AST不变。模式、公共事务响应与Local状态解耦；NoTTT新协议/无Local，required严格原行为，Mode/DCP真实加载树绑定。\n- FinalcleanPair324PASS/0failure,error,skip/shell0/source44hashstable；47new+277affectedold，非435复跑/非900。静态21+SourceGuard实际positive/import证据PASS，Queue仅验证函数format范围。开发失败4轮原件保留，最终不加旧数。独立作者审查EMA问题已修正，无剩余发现，不自批GPT/DS。\n- Evidence {REL}/README.md +633original mappings，最终JUnit/日志/OSNoTTT4Core8reqB2×2、Local三拓扑、原F3exit23/twoSlot/cleanup/foreign原断言；syntheticCPU only。44source GitBlobbindings；source前后clean。\n- Prepublishfresh V3 fetch/advertised/tracking1a0f6ec4a9cede5fa5a69406d002904a6daacc83 unchanged from开始检查，候选分叉故不merge。Owner roles当前GPTreview/CodexCPU/DSrealexecution取代旧V2/MM/Kimi要求。新exactPair CanonicalInbox申请，发布Child→Root并remote回读；不将旧APPROVE_CODE移植到本增量，不发布重复Review/Issue回复。\n- No435/GPU/Canary/900/train/checkpoint/sharedGPU变更或V3/v3-local-ttt合并；GPT窄CodeGate后Owner冻结GPU范围，DS独立分别两mode，禁止自动额外8Episode。源码SHA已提交，后继Evidence/ledgerSHA仅bookkeeping。\n''')
with (ROOT/'TODO.md').open('a') as f:f.write(f'''\n\n- **V3-EVAL-V2-DUAL-MODE** — REVIEW; Codex; FormalRoot{R}/Child{C}。最终clean定向324PASS(47new+277old)/0fail,error,skip/shell0/source44stable/static21+sourceguardPASS；原F3/Local三拓扑保留、NoTTT四Core/B2公共链通过；{REL}/README.md。新GPT窄CodeGate，DS后续分别真实两mode待Owner执行范围，未GPU/435/900/train/merge。\n''')
# Hash every published artifact after all documentation/instrumentation is final.
manifest={str(p.relative_to(OUT)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
          for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='artifact_sha256.json'}
(OUT/'artifact_sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'evidence':str(OUT),'hash_entries':len(manifest),'inbox_bytes':inbox.stat().st_size,
                  'formal_root':R,'child':C}))
