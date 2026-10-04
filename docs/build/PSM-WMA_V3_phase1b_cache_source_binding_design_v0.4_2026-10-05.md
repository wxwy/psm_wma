
# PSM-WMA V3 Corrected — Phase 1B Cache-to-Source Binding Design v0.4

日期：2026-10-05  
状态：**GPT frozen sub-design；supersede v0.3；待 cx 只读复核后提交 authority。未授权 production/GPU/训练/仿真。**

## 1. 目标

Phase 1A 已正式关闭：训练 corpus membership 只由指定 `exact_window_v1` cache manifest 决定。

Phase 1B 只解决：

```text
cache ExactWindowEpisodeKey / start_frame
        ↓ exact identity binding
flat RoboCasa365 LeRobot v3 source
        ↓
raw action12[t:t+16]
state16[t:t+17]
natural-language instruction at anchor t
underlying RoboCasa task-class witness
```

本阶段不做 raw15/state15、ActionSFT、model cache-hit、Local visual、TTT/trainer、inference/eval。

---

## 2. Authority

### 2.1 Corpus authority

唯一 corpus authority：

`RoboCasaExactWindowCacheCatalog`

source 仅为 cache 已接受的 episode/window 补 non-visual fields；source extra episodes 永远不能进入 cache-driven index。

### 2.2 Payload reader authority

实际 action/state delta-window 读取必须复用官方：

`lerobot.datasets.lerobot_dataset.LeRobotDataset`

不得用 pyarrow 手写 action/state temporal sampling。

### 2.3 Identity/provenance scan

启动时可以用：

- `LeRobotDatasetMetadata`
- read-only parquet/arrow

只扫描 identity/provenance 列，不实现 action/state payload 语义。

### 2.4 Task class vs instruction

V2 exact-window builder 已确认：

- `annotation.human.task_name` = underlying RoboCasa task class 的 global task-table index；
- LeRobot 标准 `task_index` / `item["task"]` = natural-language phrasing；
- 二者不可互换。

underlying task class resolver：

```text
meta.tasks["task_index"] == annotation.human.task_name
→ 必须唯一命中一行
→ row index/name = task class string
```

---

## 3. Source layout：只接受 flat LeRobot v3

只接受 cache builder 原始 contract 的 flat root：

```text
source_root/
  meta/info.json
  meta/tasks.parquet
  meta/episodes/...
  data/...
  videos/...      # 可存在；Phase1B 不读
```

若 root 本身没有 flat `meta/info.json`，但看起来是 latest `<task>/<date>/lerobot` 多 shard root，明确拒绝并提示需要单独 migration/fingerprint Gate；不得 silent discovery/remap。

manifest 的 `source_dataset` 只是 provenance，不要求 runtime absolute path 相同。

---

## 4. Local-only / no-Hub 硬合同

v0.2/v0.3 的 blocker 已确认：LeRobot metadata 与 dataset constructor 都有 Hub fallback；official `_check_cached_episodes_sufficient()` 还会无条件要求 selected episode 的视频文件存在，`download_videos=False` 不能改变这一检查。

### 4.1 在任何 LeRobot 对象构造前强制 offline

复用 current project 已存在的 `cosmos3_action_lerobot._ensure_hf_hub_offline()`，并要求它在 metadata/dataset factory 前执行。Phase1B 不新增另一套网络开关。

### 4.2 metadata local preflight

在 metadata constructor 前要求：
- `meta/info.json` 是 file；
- `meta/tasks.parquet` 是 file；
- `meta/episodes/` 是 directory 且至少存在 parquet；
- `data/` 是 directory。

`meta/stats.json` 可缺。缺 mandatory metadata 时直接 fail-closed，不进入 LeRobot constructor。

### 4.3 metadata construction

仅在 preflight 后构造 `LeRobotDatasetMetadata(repo_id="local", root=source_root, revision="local", force_cache_sync=False)`。若失败直接报错，不得切换 remote repo/revision。

### 4.4 cache episode_index flat-global uniqueness

Phase1B 要求 cache catalog 中 episode_index 全局唯一；跨 task 重复 episode_index 直接 fail-closed。

### 4.5 bound data-file local preflight

对所有 cache episode，用 metadata 的 `get_data_file_path(episode_index)` 推导 selected data parquet；这些 selected local files 必须全部存在且为 file。只要求 cache-bound episode 的 data file，source extra episode 不属于 corpus requirement。

## 5. Minimal local non-visual LeRobot seam

### 5.1 只允许一个极薄 subclass

在 Phase1B project module 内定义 private/minimal `_LocalNonVisualLeRobotDataset(LeRobotDataset)`，只允许 override 两个 method。

#### A. `_check_cached_episodes_sufficient()`

在调用 official `super()._check_cached_episodes_sufficient()` 前，仅修改该 reader instance 的 metadata feature view，移除 `dtype=="video"` 的 entries，然后调用 `super()`。

这样 official super 仍检查 hf_dataset 非空和 requested episode 全存在；由于该 instance 的 `meta.video_keys` 为空，不再把 mp4 文件存在性当作 source 充分条件；后续 official `__getitem__` 也不会进入 `_query_videos()`；disk 上 `info.json` 不修改。

禁止复制 official `_check_cached_episodes_sufficient` 的 episode-sufficiency 逻辑。

#### B. `download(...)`

override 为直接 fail-closed（例如抛 `FileNotFoundError`），明确 Phase1B 只接受完整本地 non-visual source，禁止 Hub fallback。

除此之外不得 override `__init__`、`__getitem__`、delta-query、caption、padding 或 hf dataset loading，因此 payload semantics 仍由 official LeRobotDataset 提供。

### 5.2 official dataset construction

构造参数：
- `repo_id="local"`
- `root=source_root`
- `episodes=sorted(bound_cache_episode_indices)`
- `delta_timestamps=NON_VISUAL_DELTA_TIMESTAMPS`
- `revision="local"`
- `force_cache_sync=False`
- `download_videos=False`

`episodes=` 是精确 cache episode set，不是 raw-source split；source extra episodes 不加载、不进入 index。constructor 返回后、第一次 `__getitem__` 前必须 assert `dataset.meta.video_keys == []`。

### 5.3 为什么仍保留 offline guard 和 preflight

dataset-level `download()` 已禁止，但 metadata constructor 仍有 `pull_from_repo(meta/)` fallback。因此顺序固定为：offline guard → local metadata preflight → metadata construction → selected data-file preflight → local non-visual official Dataset construction。

### 5.4 必须证明的行为

formal CPU tests 要证明：
- selected episode 的 mp4 完全不存在时 valid local source 仍能构造并读取 non-visual window；
- valid path 上 `LeRobotDatasetMetadata.pull_from_repo` 0 calls；
- valid path 上 Dataset `download` 0 calls；
- selected data 缺失/不足时 overridden `download` 立即 fail，不访问 Hub；
- `_query_videos` 0 calls；
- subclass 只 override上述两个 method，official `__getitem__`/delta-query 未复制。
## 6. Source contract

flat source 必须：

- codebase_version startswith `v3`；
- source FPS == cache FPS（当前20Hz）；
- features 至少：
  - `action`
  - `observation.state`
  - `annotation.human.task_name`
  - `index`
  - `episode_index`
  - `frame_index`
  - `task_index`
- `meta.tasks` 存在并含 `task_index`。

camera/video features 可以存在，不是 Phase1B required payload。

---

## 7. Episode binding identity

每个 cache episode 必须唯一绑定 flat source episode。

验证：

1. cache episode_index 全局唯一；
2. episode_index 在 source metadata 中存在；
3. source `length == dataset_to_index - dataset_from_index`；
4. 若 cache 有 source_video_frames：source length 精确相等；
5. `source length - 16 == cache.window_count`；
6. episode 内 `annotation.human.task_name` 唯一；
7. annotation resolver 唯一得到 task class；
8. resolved task class == cache task_class；
9. source data-file relative path、row bounds、first/terminal row witness稳定；
10. 0 match / >1 match / mismatch 均 fail-closed。

不得按 frame count、task name、最近 episode、path basename 猜 identity。

---

## 8. Phase1B mandatory global-row witness

Phase1A 为兼容允许 `global_row_indices` optional；Phase1B 必须要求每个实际绑定 window 含该字段。

允许向 Phase1A module 增**向后兼容** identity API，例如 frozen dataclass：

`ExactWindowIdentity`

包含：

- key
- start_frame
- global_row_indices[17]
- window_frame_indices[17]
- latent_source_frame_indices[5]

保留 Phase1A：

`read_window(key,start) -> latent`

完全不变。

---

## 9. Startup identity scan

Layer A 启动只读 scan：

- source episode metadata；
- identity parquet columns：
  - index
  - episode_index
  - frame_index
  - annotation.human.task_name

不读 action/state/video。

每个 cache episode至少 probe：

- first window start=0
- terminal window start=window_count-1

要求：

```text
cache global_row_indices[17]
==
source index[17]
```

并核：

- episode_index
- frame_index
- annotation/task class

startup probe 只是 fail-fast，不替代 runtime per-window validation。

---

## 10. Non-visual delta timestamps

基于已经核对一致的 FPS：

```text
action:
  offsets 0..15       # 16

observation.state:
  offsets 0..16       # 17

index:
  offsets 0..16       # 17

episode_index:
  offsets 0..16       # 17

frame_index:
  offsets 0..16       # 17

annotation.human.task_name:
  offsets 0..16       # 17
```

不要把 camera/video keys 放入。

不要把 `task_index` 放入 delta timestamps：

official `LeRobotDataset.__getitem__` 最后需要 anchor scalar `task_index.item()` 来生成 `item["task"]`；若 query 成17帧会破坏 official caption path。

---

## 11. Absolute→relative anchor mapping

因为 `LeRobotDataset(episodes=cache_episode_set)` 只加载子集，`__getitem__(idx)` 的 idx 是 filtered dataset relative index。

Phase1B 禁止把 cache `global_row_indices[0]` 直接作为 `__getitem__` 参数。

构造 official dataset 后，从：

`dataset.hf_dataset["index"]`

建立显式 frozen mapping：

```text
absolute source index -> relative hf_dataset index
```

要求：

- 每个 absolute index 唯一；
- 所有 cache global-row witnesses 均可映射；
- 无 duplicate；
- mapping 仅服务 cache-bound episode set。

读取 window：

```text
abs_anchor = cache global_row_indices[0]
relative_anchor = abs_to_relative[abs_anchor]
item = dataset[relative_anchor]
```

official LeRobot delta-query 内部仍以 item 的 absolute `index` 计算 query，并使用自身 absolute→relative mapping获取所选 episode的数据。

---

## 12. Runtime window contract

对 cache `(key,start=t)`：

读取 official item 后验证：

- queried `index[17]` == cache global_row_indices；
- queried `episode_index[17]` 全等 key.episode_index；
- queried `frame_index[17]` == arange(t,t+17)；
- queried annotation[17] 全一致；
- resolved task class == cache task_class。

所有 query pad masks 必须全 false：

- action 16
- state 17
- index 17
- episode_index 17
- frame_index 17
- annotation 17

任一 true => fail-closed。

---

## 13. Output dataclass

`ExactWindowRawSourceWindow` 至少：

- key
- start_frame
- global_row_indices
- action12
- state16
- ai_caption
- task_index（phrasing index，仅 audit）
- task_class
- source binding metadata

### action12

- finite floating
- exact [16,12]
- contiguous float32
- no normalization
- no raw15/rot6d

### state16

- finite floating
- exact [17,16]
- contiguous float32
- no state15 conversion

### ai_caption

- official `item["task"]`
- non-empty str
- natural-language phrasing
- 禁止用作 underlying class witness

### task_class

只来自 annotation resolver。

---

## 14. Cache-driven index facade

建议提供：

`CacheDrivenFlatWindowIndex`

硬合同：

- len == Phase1A exact_window_count；
- 顺序 = sorted cache episodes + start 0..window_count-1；
- get_shuffle_blocks 每个 block精确一个 cache episode；
- source extra episodes不影响 length/blocks；
- 不使用 source train/val split；
- lookup只返回 cache key/start，source reader exact bind。

---

## 15. Source-binding digest / summary

summary：

- cache corpus_digest
- runtime source_root display-only
- source codebase_version
- source FPS
- source total episodes
- selected/bound cache episodes
- bound windows
- mismatch counters
- source_binding_digest
- runtime_window_validation = every_read
- offline_only = true
- loaded_episode_policy = exact_cache_episode_set

digest 不含 absolute source_root。

至少绑定：

- cache corpus_digest
- source codebase_version/FPS
- task-table semantic fingerprint
- 每个 bound episode：
  - task class
  - episode index
  - frame count
  - relative data-file
  - dataset_from/to index
  - first+terminal index witness
  - resolved annotation index

若无 reliable source revision，记录 `unknown`；不要伪造。

这是 identity-binding digest，不是 source-byte hash。

---

## 16. 实现文件

新增：

- `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source.py`
- `robocasa_exact_window_source_test.py`

Phase1A cache module只允许最小兼容 extension：

- window identity API

禁止改变已关闭 Phase1A 的 membership/digest/read_window/strict audit语义。

---

## 17. Dependency injection

synthetic tests 可注入：

- metadata factory
- dataset factory
- identity scanner

production defaults必须绑定 official LeRobot symbols。

若注入 fake dataset，不得让 fake-only API渗入 production contract。

---

## 18. CPU tests

至少覆盖：

1. valid flat source+cache all bind；
2. cache episode_index 跨 task 重复 fail；
3. source extra episodes 不改变 cache-driven length；
4. source missing cache episode fail；
5. episode frame count/window count mismatch fail；
6. FPS mismatch fail；
7. required feature missing fail；
8. annotation/task table 0-match/>1-match/mismatch/non-scalar/multi-class fail；
9. cache `global_row_indices` missing fail；
10. startup first global index mismatch fail；
11. startup terminal global index mismatch fail；
12. runtime middle-window global index mismatch fail；
13. episode_index[17] drift fail；
14. frame_index[17] drift fail；
15. annotation[17] drift fail；
16. action/state/identity 任一 pad mask true fail；
17. raw action wrong shape/nonfloating/nonfinite fail；
18. state wrong shape/nonfloating/nonfinite fail；
19. empty/missing caption fail；
20. natural-language `item["task"]` 与 underlying task_class 明确分工；
21. machine source_root relocation 不改变 source_binding_digest；
22. multi-shard/non-flat root 明确拒绝；
23. cache-driven index length/blocks 只来自 cache；
24. offline guard 在任何 metadata/dataset factory 前生效；
25. missing local metadata 在 metadata constructor 前 fail；
26. selected bound data parquet 缺失 preflight fail；
27. production reader 是 official `LeRobotDataset` subclass，且只 override `_check_cached_episodes_sufficient` + `download`；
28. selected episode 的视频文件完全缺失时 valid non-visual source 仍可构造；
29. valid path `LeRobotDatasetMetadata.pull_from_repo` 0 calls；
30. valid path Dataset `download` 0 calls；
31. selected data insufficient 时 overridden `download` fail-closed；
32. `episodes=` == exact cache episode set；
33. `download_videos=False`；
34. delta timestamps 无 camera/video key；
35. `task_index` 不在 delta timestamps；
36. constructor 完成后、首次 getitem 前 `video_keys==[]`；
37. spy `_query_videos` == 0 calls；
38. absolute→relative mapping exact/unique；
39. Phase1B module 不实现/导入 raw15/rot6d action conversion、Wan/VAE、Local visual；
40. Phase1A tests 全回归通过。
## 19. 非目标

Phase1B 禁止：

- OmniMoTModel
- ActionSFT video_latent注入
- raw12→raw15
- state16→state15
- Local visual/producer
- B_stream/T/GA
- trainer/DCP
- inference/server/eval
- cache rebuild
- GPU/训练/仿真
- 训练服务器资产修改

---

## 20. Gate

cx：

1. 全文读 v3.0 + Phase0 mapping + v0.4；
2. root TODO/SESSION认领；
3. child实现+CPU tests；
4. 同时回归 Phase1A tests；
5. Ruff check / format check / diff-check；
6. child commit/push；
7. root Gitlink + SESSION/TODO + Inbox；
8. root commit/push；
9. 不自授 approve。

GPT：fresh source review。

ds：仅收到 GPT exact-pair execution authorization 后跑 CPU/static；不修代码。

Phase1B closure 后进入 Phase2：

**official raw12→raw15 + state16→state15 + H_pred16 resolved config。**
