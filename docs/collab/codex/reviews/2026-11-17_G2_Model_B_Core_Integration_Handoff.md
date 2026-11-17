# G2 B 公共接口、UND 与最终集成交接

## 固定来源与阶段

|批次|Root|Child/Gitlink|状态|
|---|---|---|---|
|当前正式基线|7a357620b4cc1f6817749c8a8275771cfbb4049c|d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2|只读来源；不回退新文档|
|C0|本实现提交，#56发布回执登记完整SHA|ec9356fafd1fd18cc0bd552b7eb23428f59df7f6|作者CPU11 PASS，接口可用；非独立批准|
|B core|未提交|未提交|UND/prefix接续实现中|
|A/C/D固定集成|未集成|未集成|缺各作者固定提交|

两仓候选分支 `v3-g2-model-b-core-20261117`，工作区 `/workspace/work/g2-b-core`。
最终集成候选预留 `v3-g2-model-integration-20261117`；本批不创建虚假的最终集成结果。

## C0复现与范围

[唯一接口/shape/mask/缓存合同及文件归属](../../../build/PSM-WMA_G2_C0_Public_ABI_2026-11-17.md)。
Child三新增文件 `mot/g2_contracts.py`、`g2_contract_fixtures.py`、`g2_contracts_test.py`。
Root只新合同/handoff、原始CPU日志/JUnit/static、公共账本和Gitlink。不改现有formatter、trainer、cache、producer。

同合同CPU命令；输出 [pytest.log](../../../../artifacts/g2_model_b_c0/pytest.log)、[JUnit](../../../../artifacts/g2_model_b_c0/junit.xml)、[static](../../../../artifacts/g2_model_b_c0/static.log)。
11 ABI测试全部通过、零skip；合成 CPU不能作真实模型/端到端验收。

## 对接来源与缺口

- A ACK #56/6943452748，候选空间几何补充6943510790；Reader算法/projector由A唯一实现，B只注册/接线。
- C/D在本批发布前未核对作者ACK或固定提交，公共状态TODO；不推断其他会话是否已执行。
- #54 A2 `4ad0fe7394cb62c4b5692fecaf6ce52963b8852c` / Child d5c1ffc7 独立限定 APPROVE_CODE与真实两集样例PASS；#53仍Draft，旧VAE视觉人审已PASS，不重复。
- #54最新Owner静态episode语言、双top独立内容/引用已同步；旧clean/w_rbs显式映射，无路径猜测。DATA_B state15及DATA_C完整对齐仍待固定来源。无真实数据不阻塞本批fixture。

## 运行与待定参数

GPU、真实 UND hidden/KV parity、动作loss反传、Local inner、实际FSDP、TRAIN_A/B恢复、cache on/off、Session隔离均NOT_RUN。
真实样例CLI须在B core与A/C/D实际接线后提供，不以未存在CLI伪造可运行命令。执行侧固定Root/Child运行，GA=1，3以上decision windows、B1/mixed B、正常/空文本、两top及更新/引用；保存逐层/逐步输出与梯度、参数/Local/RNG/恢复/缓存证据。
checkpoint绝对路径/SHA、DATA_C清单/recipe、几何编码版本、实际batch/FSDP、S_A/S_B、预热/衰减、缓存容量仍待M08/M09实测定稿。不自行GPU/训练/900EP、不服务器commit/push、不自动正式分支合并。
