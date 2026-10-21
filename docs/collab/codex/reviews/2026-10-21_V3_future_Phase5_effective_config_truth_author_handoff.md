# Future Corrected Phase5 Config truth — isolated candidate handoff

日期：2026-10-21。仅未来新Job候选；**不合并V3/v3-local-ttt、不迁移G1、不授权训练/GPU**。

| 项目 | 精确版本 |
| --- | --- |
| Implementation Root（候选） | `fa6471c0e9d12c54fa72a425d06abfc80ea491cc` |
| Child/Gitlink（候选） | `35b0ea1ccee9ee26653ed6589c484f0997d1c586` |
| Root/Child隔离分支 | `v3-phase5-config-truth-20261021` |
| Root父提交（HIGH07证据HEAD） | `ab1f277e8cec125abeb24b2850eac3e555b47522` |
| Child父提交 | `2d128ed5a07601cdd424974f99b67832eafeeb41` |
| HIGH07独立生产实现（未混入本批diff） | Root `320fda57c2cf450fbf0042183d7761a70b56f215` / Child `2d128ed5a07601cdd424974f99b67832eafeeb41` |

两个候选ref均已非强推发布；后续文档SHA不替代Implementation。此Root只改Gitlink和SESSION/TODO；Child只改下列范围。禁止把本候选Root/Child或数据快照原位替换运行中G1。

## 1. 最小实现与失败语义

- `examples/psm_wma_robocasa_corrected_phase5.py:572–576`：仅Corrected overlay调用独立helper，将明确的继承Stage-A32兼容字段同步为实际contract16；不改其它recipe或全局Dataset/Server默认值。允许标准节点单值32→16或已有16；同节点相同值的chunk_length/num_action_per_chunk别名同步；混合16/32、额外dataset/list节点、字符串/bool/零/未知值和缺失字段全部fail-closed，不靠首个字段优先级掩盖冲突。其它fps/camera/state/raw等兼容字段先检查后修改。
- 新 `examples/psm_wma_robocasa_effective_config.py`：集中镜像、校验和版本化provenance。原Cache→`CorrectedRoboCasaPolicyContract.from_cache_catalog`已校验chunk16/fps20；preflight再以实际 `catalog.raw.contract` 和有效Config交叉生成metadata。
- `preflight()`报告新增`effective_data_source`；真实来源链明确为 `get_action_robocasa_exact_window_cached_sft_dataset → ExactWindowSegmentProducer → GroupedLocalMemoryTrainer.bind_grouped_stream`，legacy dataloader **仅通用Config/推理兼容，不是正式样本Producer**。launch.json保存 `schema=corrected_phase5_effective_data_v1`、raw/state15、H16、chunk16、frames17、fps20、独立Local-TTT T和兼容字段路径/值。
- `JobLifecycle.write_config()`保持原namespace检查在先；在任何Fresh mkdir前检查live Config与metadata，原序列化器保存后再次解析刚写出的YAML，确认有效geometry与记录一致，之后才能发布canonical config.yaml/config.pkl及v3_job_identity。失败保留partial launch证据，不发布canonical或完整Job Identity。生产路径不读取外部pickle；CPU测试仅反序列化自己刚保存的合成PKL。

本批没有修改训练的真实Producer/sequence算法、Local-TTT、Loss、Optimizer、Checkpoint/RNG、Action Server或评测Queue；不修optim，不读取真实DCP，不接触G1运行工区。删除新import/hook/provenance键后整个Phase5 AST与旧Child一致，见scope_proof。

## 2. 配置、身份与历史边界

- 原 `corrected_phase5_f0_v1` Job Identity schema、`training_identity()`、`config_digest()`、namespace/hash检查及strict same-source Resume实现不变。选择launch.json记录versioned来源，避免新增Config dataclass字段或重写历史Job schema。
- 未来新Config中legacy32变16，**新canonical YAML/PKL SHA自然改变**；新Root/Child进入原semantic identity，因此最终config_digest自然不同。不能把候选绑定到旧Root/Child历史Job，也不能把G1 identity或旧Config哈希重新签成新Job。
- 同一新Pair Fresh→Resume仅建立新的launch副本，原canonical YAML/PKL/Identity bytes保持不变；CPU覆盖该生命周期。这个测试对checkpoint路径解析做外部边界替身，**不是实际DCP Resume**。完整依赖Config.validate/真实数据/多Rank运行留待GPT授权后的DS独立验证。
- G1旧config32并不证明正式训练使用32；训练H16来源仍为Exact-Window contract。当前G1迭代4000推理仍仅依赖独立HIGH07显式CLI16。任何历史解释说明都不得改写旧config.yaml/config.pkl/v3_job_identity、Checkpoint或来源SHA。

## 3. CPU证据与限制

目录：`docs/collab/codex/evidence/2026-10-21_V3_future_Phase5_config_truth_author_cpu/`。

- **47 passed =19新case+28既有F0方法，32 subtests PASS；0failure/error/skip，3.691s**。JUnit79包括subtests。Ruff0.12.7 check、format --check、syntax、diff PASS。20个warnings来自引入旧cache测试fixture时未注册的level marker，不是跳过项。
- Python3.12.14、OmegaConf2.3.0/attrs25.4.0与仓库锁定一致；真实LazyConfig序列化到临时attrs/OmegaConf配置、回读YAML+PKL、Child原解析函数均16。真实tiny-cache Catalog/Reader检查17帧identity；执行原PolicyContract/SequencePlan及builder AST，验证state条件帧[0]+16个预测动作。T测试取8，明确不同于H16。
- 原Child overlay确实32→仍32，`baseline-red.log`保留32!=16。额外CPU负例覆盖类型/alias/list/额外Dataset冲突、cache错误chunk/fps、live/YAML漂移/缺来源阻止canonical发布、历史合成资产与其它未应用overlay的recipe保持32、新Job canonical保护和双进程独占Fresh claim。原F0九个Trainer测试在本作者依赖隔离方式下全部执行，非完整V2环境独立验收。
- 旧corrected Phase5测试93条及F0测试83条assertion AST完整不变，仅补真实Dataset/provenance fixture，未skip/xfail/删除或放宽断言。旧corrected Phase5完整测试文件只作Ruff/语法与断言AST比对，本云环境没有运行它依赖的全模型导入。
- 作者外置pytest bootstrap只隔离datasets/__init__.py无关eager注册；Cache/Reader/serializer为原模块。PolicyContract/SequencePlan/Child parser为原AST，隔离重模型导入和固定Edge tokenizer能力fixture，不声称完整模型/Pydantic工厂已经验证。action Tensor为合成geometry见证，不是真实GPU Producer或动作数值验收。
- 初次collect缺SciPy、tokenizer480 fixture及spawn bootstrap/F0 fixture失败均保留，修正后再完整运行；没有改生产语义迁就fixture。早期OmegaConf2.4 green不是最终证据，最终按锁定2.3重新GREEN。gate.json/manifest记录完整版本、命令、env、RC、source和产物SHA。

## 4. GPT/Owner下一步

请只对本隔离新Pair做Config-truth增量审核，裁决是否允许后续DS完整依赖CPU/真实Config preflight。必要的DS CPU命令模板（外置日志、CUDA_VISIBLE_DEVICES=''、clean detached新Pair）：

```bash
python -m pytest --noconftest -c <EXTERNAL_PYTEST_INI> -q -s -p no:cacheprovider \
  examples/psm_wma_robocasa_effective_config_test.py \
  examples/psm_wma_robocasa_phase5_f0_test.py
```

工作目录Child。完整依赖环境可直接导入，作者最小云环境应复用已提交pytest_cpu.py并修正其本地路径；不把bootstrap视为完整环境验收。对五个Child改动文件做Ruff0.12.7 check/format；完整配置/真实缓存只读交叉验证需另行指定新Job候选路径，不准读写G1原配置来生成“修复后”文件。真实CPU preflight不得生成、启动或恢复训练。

**STOP：隔离候选已交付，未合并主线，等待GPT独立审核与Owner后续范围裁决。不启动GPU/Action Server/仿真，不操作G1。**
