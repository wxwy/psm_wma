# F1-C 分类来源分析：作者证据

仅公开代码与明确标为TEST_ONLY的自建输入。未访问或分类真实Layout1/10的590个未知部件；不代表GPT服务器验收。

- `source_inventory.json`：全部38个G2源/配置/测试文件，原采样固定版本36文件逐一未变。
- `n6_f1c_roles_full.log/xml`：336/336 PASS，0failure/error/skip；`test_retention.json`核对原291与新增45的精确集合。
- `n6_f1c_roles_targeted.log/xml`：新45项定向正反控。
- `n6_f1c_roles_before_review.*`：早期27项通过记录，不替代最终结果。
- `n6_f1c_roles_context_fixture_initial.*`：测试开始修改第0个source（原本就是asset）未真正制造XML故障造成的1fail/41pass；已改为明确选择root.xml。保留原日志，不计作实现缺陷或正式RED。
- `public_source_identity.json`：九个公开原始文件的repo/commit/path/bytes/SHA256/Git blob；代码未vendoring进项目，也未在本轮执行。
- `public_catalog_own_check.py/json/log`：实际自建两帧与公开catalog原哈希匹配。只有一个explicit evidence-bound candidate，四个unknown仍四个、实际角色写入0，adapter SHA保持冻结版本。
- `own_test_only_component_ledger.json`：上述自建四部件的逐项分析示例，scene_id为TEST_ONLY，不是真实590项结果。
- `author_code_review.md`：另一Agent只读复核和P2闭环。`author_cpu_results.json`含机器摘要。
- `protected_refs_before.json`及发布回执：原V3/native/采样候选等分支未被本轮更新；新分类分支独立发布，无PR/merge。

角色候选始终保留UNCLASSIFIED/PENDING_GPT，已有声明也仅DECLARED_NOT_RE_REVIEWED。training_ready/full_scene_source_certified=false。真实逐部件审计、状态、图片、点云仍留服务器，须GPT原位验证后才能更新整屋角色结论。
