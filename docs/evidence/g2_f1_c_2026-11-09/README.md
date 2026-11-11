# F1-C 作者 CPU 证据

仅自建输入和作者侧只读复核，不是整屋/GPT独立服务器验收。

- `source_inventory.json`：全部36个G2源/配置/测试文件的SHA256、Git blob SHA与字节数。
- `n6_f1c_full.log/xml`：最终291/291，0failure/error/skip。
- `n6_f1c_red.log/xml`：同字节17项在精确3b6旧源全部FAIL。
- `test_retention.json`：全部原274 ID保留，按Owner新策略改变的6个旧案例断言，新增17 ID。
- `own_positive_parity.json/log` 和复用脚本：原R1与候选六几何，两帧各6244行XYZRGB/valid逐字节一致，geometry/state/bounds一致；新verifier检查旧v1和新v2磁盘证据，producer身份正常变化。
- `author_code_review.md`：另一Agent只读复核，已关闭非零平方下溢预算P2。
- `author_cpu_results.json`：机器摘要。`protected_refs_before.json`：本轮开始发布前远端引用，不把已由其他任务推进的V3认作本轮修改。
- `*_initial_fixture.*` / `n6_f1c_targeted.*`：开发初始的checker颜色预期/内存manifest误作磁盘接口错误，原样保存，不计作正式RED或代码缺陷。
- `n6_f1c_full_before_review.*`：修正复核P2前的289项通过记录，已由291项最终结果替代，不覆盖原日志。

服务器私有MJCF/assets/states/images/clouds/逐部件审计未读取、复制或发布。Layout1/10真实四帧、完整native、普通结构/六图/Island仍由GPT与人工独立验收，training_ready=false。
