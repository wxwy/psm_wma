# G2 B 公共接口、UND 与最终集成交接

## 固定来源与阶段

|批次|Root|Child/Gitlink|状态|
|---|---|---|---|
|当前正式基线|7a357620b4cc1f6817749c8a8275771cfbb4049c|d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2|只读来源；不回退新文档|
|C0|739d39cf6498543b59d487d5925ef2a329040ac3|ec9356fafd1fd18cc0bd552b7eb23428f59df7f6|作者CPU11 PASS，接口可用；非独立批准|
|B core|4f90c875eda0ca53d997f64111b41ed531ac2900|7e888f217dfcddc35ed73782f65c6e0890c72c3a|作者scoped CPU198 PASS；此固定阶段尚未合入A/C/D|
|当前部分集成|本文当前Root提交，完整SHA见#56发布回执|6d72d4d252c287fc8060bdc5a8db7f6cf959af1e|作者scoped CPU442 PASS/0skip；C训练控制器后继未交付，不能称最终全量集成|

两仓候选分支 `v3-g2-model-b-core-20261117`，工作区 `/workspace/work/g2-b-core`。
部分集成候选 `v3-g2-model-integration-20261117`、独立工作区 `/workspace/work/g2-integration`。
原 B-core 分支/工作区保留固定来源；无force push、无正式V3/v3-local-ttt推广。

## C0复现与范围

[唯一接口/shape/mask/缓存合同及文件归属](../../../build/PSM-WMA_G2_C0_Public_ABI_2026-11-17.md)。
Child三新增文件 `mot/g2_contracts.py`、`g2_contract_fixtures.py`、`g2_contracts_test.py`。
Root只新合同/handoff、原始CPU日志/JUnit/static、公共账本和Gitlink。不改现有formatter、trainer、cache、producer。

同合同CPU命令；输出 [pytest.log](../../../../artifacts/g2_model_b_c0/pytest.log)、[JUnit](../../../../artifacts/g2_model_b_c0/junit.xml)、[static](../../../../artifacts/g2_model_b_c0/static.log)。
11 ABI测试全部通过、零skip；合成 CPU不能作真实模型/端到端验收。

## 对接来源与缺口

- A ACK #56/6943452748，候选空间几何补充6943510790；Reader算法/projector由A唯一实现，B只注册/接线。
- C0发布后已核对 C ACK6943519070、D ACK6943531508；B-core阶段未合入三者。当前integration普通合入A4209b151ecc11ab2043b9d08037d43b5e3903618、C首批68d84e819d114c6ce817403afacad994b2fb8f35及后继f262d7ff4156d83356e1d7f790adea2a61e85c6d、D首批209749e5287c5030370464625a7e1f44dfb2ab6f及最终hooks后继6991142cb94256f497347db40f58ad0ee3f482aa。Root普通合入A35a2580efd296bcf782d7cae38d4cb482a225a70和D3d351fe37af111257543ab814f30222dd7e76da6的原始证据/交接；C最终Root交接仍待作者发布。
- #54 A2 `4ad0fe7394cb62c4b5692fecaf6ce52963b8852c` / Child d5c1ffc7 独立限定 APPROVE_CODE与真实两集样例PASS；#53仍Draft，旧VAE视觉人审已PASS，不重复。
- #54最新Owner静态episode语言、双top独立内容/引用已同步；旧clean/w_rbs显式映射，无路径猜测。DATA_B state15及DATA_C完整对齐仍待固定来源。无真实数据不阻塞本批fixture。

## 运行与待定参数

[B-core ABI/配置/FSDP/参数inventory与公开方法](../../../build/PSM-WMA_G2_B_Core_ABI_2026-11-17.md)。
198项CPU最终回归和C0旧源码逐位对照证据在 `artifacts/g2_model_b_core/`；其中FSDP注册是mock，
真实Local/服务跨Session闭环不属于B独立fixture。当前A/C/D源码组合的CPU证据在下节，保持与B-core阶段分开。

## 当前集成增量与严格状态

- 实际组合测试及最终22文件442 PASS见 `artifacts/g2_model_integration/README.md` 和JUnit；不是各路作者测试数相加。12项B-owned组合测试贯通实际A/B/C/D模块到native动作头，仍使用合成数据和CPU参考attention。D cache-on/off两Session三轮replan/正常与空文本的GEN动作输出可比；实际Local core执行是CPU。
- B-owned修正：3a5c6259f57dad9ccf9bc7fe9e594dee0d62cc00使Global-enabled训练在全缺席rank保留零图依赖，不插prefix/query、不调用缺席Reader，保障相同反向unit/参数梯度清单的必要前提；实际FSDP尚未验。显式G2若安装未验diffusion-layer residual cache则拒绝，旧配置优化不全局关闭。
- 82d73c53db39b569ac24e823db968c1c5c12737c的stack_g2_prepared允许B1空/有字dropout身份不同，保留dropped和所有source dropout IDs的组合hash，不重抽dropout；formatter/tokenizer协议仍须相同。无dataclass改名、无独立formatter/推理缓存副本。
- 6d72d4d252c287fc8060bdc5a8db7f6cf959af1e保持旧native QKV和norm执行顺序；C0源码none/Local-only×B1/mixed输出/梯度/RNG逐位复核PASS。共享causal attention/MLP/RoPE与当前GEN key norm边界保留。
- A生产文件、C文本/数据adapter、D服务/cache/hooks生产文件与上述各作者fixed blobs相等；祖先与diff证据在artifacts。唯一作者归属未移交；B没有替C实现阶段/optimizer或替D实现缓存。
- 实际mask内容由D唯一 `OnlineSpatialSnapshot.mask_content_ids` 保存，顺序对应C0 selected views，view/global key都绑定，miss校核loaded bool mask SHA256；C0 GlobalCacheSignature.mask_version仅算法/recipe。B提出的重复mask字段未发布、已撤回，沿用D完整provider快照，不另造缓存ABI。
- D当前Session cache构造/请求均拒绝world_size>1（含cache-off），不宣称分布式缓存支持。B模型FSDP方法/参数注册是不同范围，须执行侧用统一rank调用验证。
- 当前C adapter对单Room selected输入要求恰一mandatory top；A核心Reader只保证非空且同一configured variant，原注释“exactly one”指variant选择，未提供真实多Room数据/覆盖证明。多Room mandatory_top的基数/覆盖语义仍待DATA_C明确，不把可变view fixture当未来多Room验收，不在B猜场景拓扑。
- **未交付/未集成**：C warm-start/optimizer/TRAIN_A-B/checkpoint和Phase5 overlay后继固定提交；实际DATA_B/C provider/清单/版本；C最终Root handoff。M05及完整M07保持未完成。真实GPU/动作训练步/FSDP/A-B恢复/真实服务闭环/M08/M09均NOT_RUN。

## 执行侧 runbook 与参数边界

CPU小例和完整442项runner是已存在、可执行的命令，见artifacts README。只替换Python路径即可，不要把CPU参考kernel引入生产。
真实训练小例必须等待C的实际overlay/阶段CLI固定后引用该命令，**GA=1**；当前不能编造不存在的G2训练CLI。
服务已有 `cosmos_framework/scripts/action_policy_server_robocasa.py` 的 `--g2-profile g2_r1|g2_r2`、
`--g2-hooks-factory module:function`、R2 `--g2-provider-factory module:function`、`--g2-cache-enabled/--no-g2-cache-enabled`；
factory由执行侧已验证checkpoint/config loader与真实online provider提供。缺factory、Local事务配置、guidance=1或真实state15身份时明确失败，不用expert fallback。D最终handoff已明确真实provider及checkpoint/config versions factory尚未冻结，不编造可部署factory路径；其现有CPU复现脚本在D原始证据目录。不拿fixture factory冒充生产。
真实样例最低保存：>=3 decision windows、B1和混合B、有效/空文本、所有层G/L prefix长度/presence、action loss→Global梯度、Local inner更新/commit-abort、FSDP一致前后向、TRAIN_A/B恢复的模型/optimizer/Local/RNG、cache on/off逐步输出和Session隔离。checkpoint绝对路径与SHA、DATA_C清单/hash、VAE/geometry/membership/state15 recipe、实际FSDP/batch、S_A/S_B、warmup/decay、cache预算由执行侧显式填写；不默认为已测最优值。

真实checkpoint/GPU的UND hidden/KV parity、动作loss/Local inner/FSDP、TRAIN_A/B恢复、cache on/off和Session闭环均NOT_RUN；下节另列已运行的合成CPU动作头/Local core/cache组合，不混淆层级。
真实样例CLI须在B core与A/C/D实际接线后提供，不以未存在CLI伪造可运行命令。执行侧固定Root/Child运行，GA=1，3以上decision windows、B1/mixed B、正常/空文本、两top及更新/引用；保存逐层/逐步输出与梯度、参数/Local/RNG/恢复/缓存证据。
checkpoint绝对路径/SHA、DATA_C清单/recipe、几何编码版本、实际batch/FSDP、S_A/S_B、预热/衰减、缓存容量仍待M08/M09实测定稿。不自行GPU/训练/900EP、不服务器commit/push、不自动正式分支合并。
