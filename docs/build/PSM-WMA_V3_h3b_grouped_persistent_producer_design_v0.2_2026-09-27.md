# PSM-WMA V3 H3-B — grouped producer 设计 v0.2（epoch rollover 修正）

- 日期：2026-09-27；状态：H3-B CPU/static 实现 authority。
- 以同目录 v0.1 为基础；本文件**仅替换** v0.1「rank、slot、category 与两个 GA member」中“下一 epoch 只在当前 epoch 全部 episode 消费并全部 slot terminal 后开始”的规则。其余 contract 不变。

## 修正原因与规则

每 rank 的 episode 数未必是 8 的倍数；若要求 8 个 slot 同时 terminal 才换 epoch，尾部可分配 UID 不足时会永久停在无法组成 B_stream=8 的状态。

现在规定：当前 epoch 队列全部**分配**后，即可生成下一 epoch 的确定性洗牌队列；已绑定的旧 epoch episode 仍在各自 slot 连续消费。新绑定不得与任一 live 或同一 candidate window 已预留的 UID 同时重复；遇到冲突按新 epoch 的队列顺序跳过到其后可分配 UID，跳过项保留原相对顺序供后续绑定。若完整扫描后仍不足 8 个独立绑定，明确 fail closed，不静默减 B_stream、复制样本或推进 live frontier。

epoch、各 task 队列位置、被跳过的 UID、slot→episode binding、cursor、segment_id、候选预留集合都属于 candidate catalog state；只有 H3-C 的 optimizer 成功后才原子发布，失败时逐字保持 live state。checkpoint/resume 在 H3-D 保存这些字段。每个 UID 在同一 epoch 只分配一次；跨 epoch 重用须带 epoch 身份，恢复时不能混淆。

H3-B CPU fixture 除 v0.1 验收外，增加 rank episode 总数不能被 8 整除的尾部跨 epoch 场景，断言 B8 不缩水、无并发重复 UID、失败后 cursor/queue/epoch 不变。
