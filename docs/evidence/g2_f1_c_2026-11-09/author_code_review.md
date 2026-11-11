# F1-C 作者侧独立只读代码复核

Reviewer：另一 Agent `/root/n6_independent_review`，只读代码/本地证据；不是 GPT 服务器验收。

最终：限定范围无未关闭 P0/P1/P2。

- P2 已关闭：`surface_sampling.py:125` 原先仅 edge==0 时恢复长度，遗漏平方范数下溢成较小非零值。反例 float64 边2.4e-162、spacing3.2e-162，旧平方范数错算3点，稳健最长边需要6点。现用原dtype `sqrt(tiny)` 限定稳定计算范围，新增 float32/float64 两项6点/预算3拒绝负控；普通原算术保留。
- `audit_surface` 仅精确零面进入 discarded；正面及面积下溢保留并明示。原溢出/非有限、全零、参数和预算保护保持。
- `surface_coverage` 不按浮点面积>0计数，零权重逐原face/点数明确记录；加权有效色比例留空。`color_evidence` 只有v2接受完整一致的整面下溢证据，v1/legacy仍要求正权重。
- 复读最终JUnit：291/291，0failure/error/skip；旧274 IDs无缺失；同字节新增17项在旧3b6全部FAIL。测试SHA256 `09d97abd77373a7bf393f88742099f5c29c180fce0c7bf64ba241e9fd975a84b`。
- 实读两帧 old/new cloud，各6244数据行逐字节一致；state对象和原几何SHA相同，producer epoch正常变化。
- source_geometry/source_roles/source_scope/texture_projection及四身份函数相对3b6未改；范围与源码空白检查通过。未访问私有服务器、native、GPU、模型或生产工作区。
