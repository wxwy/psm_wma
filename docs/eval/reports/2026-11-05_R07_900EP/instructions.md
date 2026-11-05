# R07 900EP：原始语言指令分项索引（138 组）

[返回跨Checkpoint总报告](../PSM-WMA_V3_RoboCasa365_Local_TTT_Evaluation_Report.md)。来源为 R07 完成的900份 `result.json.body`；对应 Local-TTT checkpoint `iter_000027700`，正式根仓 `3bd1404cf...`、子仓 `1ca30805...`。本表仅归档观测结果。

**校验合计：18个Task，每Task50EP，138组原始指令，900EP，580成功 / 320失败，SR=64.4444%。** 138是本次实际评测出现的精确字符串数，不是Target-Atomic训练集的所有指令；历史R03是139组，二者只有111组精确原文重合。

**统计定义**：严格使用 `(task, instruction)` 原样分组；不翻译、不纠错、不合并同义词，N为该指令实际EP数，SR=S/N。每组的成功/失败EP编号在同一Task内编号0–49，必须结合Task定位。每个Task的组汇总恰好50EP。

**样本限制**：63组只有1个EP，107组少于5EP；个别指令0%/100%并不能代表稳定能力。不同指令通常还改变任务对象、布局或动作方向，不能据此认定纯语言理解的因果效果。本轮使用 `independent_slot_environment_seed_then_continuous_reset_v4`，不同于R03的v3，不是配对场景对照。

**无媒体注意**：R07设置 `save_rollout_mp4=false`、`save_generated_video=none`，因此没有MP4可供直接回看。本表仅用于定位本地文本、动作、场景证据，绝不虚构视频路径。

结果根目录：

```text
/mnt/data1/data_v2_0617/robocasa_eval_runs/local_ttt_robocasa_raw15/packed128_droid_fresh_g1_20261019/R07_900ep_iter27700_m16b8_v3_nomedia_20261105
```

任一EP索引：`<RUN_ROOT>/tasks/<Task>/episodes/ep_<EP:03d>/result.json`，`predictions.jsonl`，`scene_provenance.json`。机器审计统计见 [R07 JSON归档](audit_summary.json)。

## T01 — CloseBlenderLid

合计 14/50 成功，SR=28.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T01-I001 | Close the lid blender by securely placing the lid on top. | 50 | 14 | 36 | 28.00% | 2,10,11,14,16,25,27,28,30,31,34,42,47,48 | 0,1,3,4,5,6,7,8,9,12,13,15,17,18,19,20,21,22,23,24,26,29,32,33,35,36,37,38,39,40,41,43,44,45,46,49 |

## T02 — CloseFridge

合计 31/50 成功，SR=62.00%，2组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T02-I001 | Close the fridge door. | 31 | 21 | 10 | 67.74% | 0,1,2,4,5,8,10,12,13,16,17,21,28,29,33,38,40,42,43,45,46 | 7,18,20,24,25,30,32,35,36,49 |
| T02-I002 | Close the fridge doors. | 19 | 10 | 9 | 52.63% | 3,6,19,23,26,27,37,41,47,48 | 9,11,14,15,22,31,34,39,44 |

## T03 — CloseToasterOvenDoor

合计 44/50 成功，SR=88.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T03-I001 | Close the toaster oven door. | 50 | 44 | 6 | 88.00% | 0,1,2,3,4,5,6,7,8,9,10,11,12,13,15,16,17,18,20,21,22,23,24,25,26,27,30,31,32,33,34,35,36,37,38,40,41,42,43,45,46,47,48,49 | 14,19,28,29,39,44 |

## T04 — CoffeeSetupMug

合计 31/50 成功，SR=62.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T04-I001 | Pick the mug from the counter and place it under the coffee machine dispenser. | 50 | 31 | 19 | 62.00% | 1,2,3,4,5,7,9,10,14,16,17,19,20,21,23,26,27,29,30,31,32,35,36,37,40,43,44,45,46,47,49 | 0,6,8,11,12,13,15,18,22,24,25,28,33,34,38,39,41,42,48 |

## T05 — NavigateKitchen

合计 8/50 成功，SR=16.00%，13组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T05-I001 | Navigate to the stand mixer. | 10 | 2 | 8 | 20.00% | 19,33 | 4,5,21,27,32,34,39,42 |
| T05-I002 | Navigate to the electric kettle. | 7 | 2 | 5 | 28.57% | 25,49 | 1,12,15,40,45 |
| T05-I003 | Navigate to the toaster. | 6 | 2 | 4 | 33.33% | 31,41 | 17,26,28,47 |
| T05-I004 | Navigate to the shelves. | 4 | 0 | 4 | 0.00% | — | 16,18,20,38 |
| T05-I005 | Navigate to the toaster oven. | 4 | 1 | 3 | 25.00% | 44 | 3,30,48 |
| T05-I006 | Navigate to the fridge. | 3 | 0 | 3 | 0.00% | — | 29,35,37 |
| T05-I007 | Navigate to the range hood. | 3 | 0 | 3 | 0.00% | — | 11,13,23 |
| T05-I008 | Navigate to the sink. | 3 | 0 | 3 | 0.00% | — | 36,43,46 |
| T05-I009 | Navigate to the stove. | 3 | 0 | 3 | 0.00% | — | 6,7,10 |
| T05-I010 | Navigate to the dishwasher. | 2 | 0 | 2 | 0.00% | — | 0,2 |
| T05-I011 | Navigate to the microwave. | 2 | 0 | 2 | 0.00% | — | 14,22 |
| T05-I012 | Navigate to the oven. | 2 | 1 | 1 | 50.00% | 9 | 8 |
| T05-I013 | Navigate to the coffee machine. | 1 | 0 | 1 | 0.00% | — | 24 |

## T06 — OpenCabinet

合计 43/50 成功，SR=86.00%，2组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T06-I001 | Open the cabinet doors. | 35 | 28 | 7 | 80.00% | 0,1,2,5,9,10,12,13,14,16,17,20,22,26,27,28,32,33,34,36,38,39,40,41,43,44,45,48 | 4,8,11,18,24,46,47 |
| T06-I002 | Open the cabinet door. | 15 | 15 | 0 | 100.00% | 3,6,7,15,19,21,23,25,29,30,31,35,37,42,49 | — |

## T07 — OpenDrawer

合计 32/50 成功，SR=64.00%，2组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T07-I001 | Open the right drawer. | 28 | 17 | 11 | 60.71% | 1,2,7,8,13,16,21,23,24,29,30,31,38,41,42,43,45 | 3,11,14,15,17,18,25,26,27,46,48 |
| T07-I002 | Open the left drawer. | 22 | 15 | 7 | 68.18% | 4,6,9,10,20,22,33,34,35,37,39,40,44,47,49 | 0,5,12,19,28,32,36 |

## T08 — OpenStandMixerHead

合计 32/50 成功，SR=64.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T08-I001 | Open the stand mixer head. | 50 | 32 | 18 | 64.00% | 0,1,2,3,6,7,8,9,11,12,13,14,17,18,19,20,21,23,24,29,31,32,34,36,37,38,41,44,45,46,47,49 | 4,5,10,15,16,22,25,26,27,28,30,33,35,39,40,42,43,48 |

## T09 — PickPlaceCounterToCabinet

合计 28/50 成功，SR=56.00%，43组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T09-I001 | Pick the straw from the counter and place it in the cabinet. | 3 | 1 | 2 | 33.33% | 23 | 2,36 |
| T09-I002 | Pick the boxed food from the counter and place it in the cabinet. | 2 | 1 | 1 | 50.00% | 30 | 4 |
| T09-I003 | Pick the condiment bottle from the counter and place it in the cabinet. | 2 | 1 | 1 | 50.00% | 48 | 37 |
| T09-I004 | Pick the eggplant from the counter and place it in the cabinet. | 2 | 1 | 1 | 50.00% | 31 | 7 |
| T09-I005 | Pick the mug from the counter and place it in the cabinet. | 2 | 1 | 1 | 50.00% | 3 | 18 |
| T09-I006 | Pick the tongs from the counter and place it in the cabinet. | 2 | 1 | 1 | 50.00% | 11 | 34 |
| T09-I007 | Pick the aluminum foil from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 17 |
| T09-I008 | Pick the avocado from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 39 |
| T09-I009 | Pick the beer from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 41 | — |
| T09-I010 | Pick the bottled water from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 10 | — |
| T09-I011 | Pick the can from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 6 | — |
| T09-I012 | Pick the candle from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 13 |
| T09-I013 | Pick the carrot from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 45 | — |
| T09-I014 | Pick the cereal from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 15 | — |
| T09-I015 | Pick the cheese from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 25 | — |
| T09-I016 | Pick the chicken drumstick from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 0 | — |
| T09-I017 | Pick the honey bottle from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 19 |
| T09-I018 | Pick the hotdog bun from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 40 | — |
| T09-I019 | Pick the ice cube from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 24 | — |
| T09-I020 | Pick the jar from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 26 |
| T09-I021 | Pick the jug from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 46 |
| T09-I022 | Pick the ketchup from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 28 |
| T09-I023 | Pick the kiwi from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 44 | — |
| T09-I024 | Pick the ladle from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 16 | — |
| T09-I025 | Pick the mango from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 21 | — |
| T09-I026 | Pick the measuring cup from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 33 | — |
| T09-I027 | Pick the milk from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 42 |
| T09-I028 | Pick the mushroom from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 47 | — |
| T09-I029 | Pick the mustard from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 35 |
| T09-I030 | Pick the paprika from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 38 |
| T09-I031 | Pick the peach from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 5 | — |
| T09-I032 | Pick the pear from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 12 |
| T09-I033 | Pick the peeler from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 8 | — |
| T09-I034 | Pick the pitcher from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 27 |
| T09-I035 | Pick the pot from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 22 |
| T09-I036 | Pick the reamer from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 1 | — |
| T09-I037 | Pick the rolling pin from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 9 | — |
| T09-I038 | Pick the saucepan lid from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 29 |
| T09-I039 | Pick the sugar cube from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 43 | — |
| T09-I040 | Pick the teapot from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00% | — | 49 |
| T09-I041 | Pick the tomato from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 14 | — |
| T09-I042 | Pick the turmeric from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 20 | — |
| T09-I043 | Pick the water bottle from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00% | 32 | — |

## T10 — PickPlaceCounterToStove

合计 40/50 成功，SR=80.00%，24组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T10-I001 | Pick the chicken drumstick from the plate and place it in the pan. | 7 | 6 | 1 | 85.71% | 1,4,10,18,33,44 | 41 |
| T10-I002 | Pick the lemon from the plate and place it in the pan. | 5 | 4 | 1 | 80.00% | 0,5,9,11 | 3 |
| T10-I003 | Pick the bell pepper from the plate and place it in the pan. | 4 | 3 | 1 | 75.00% | 2,36,43 | 7 |
| T10-I004 | Pick the lemon wedge from the plate and place it in the pan. | 4 | 2 | 2 | 50.00% | 25,45 | 39,48 |
| T10-I005 | Pick the garlic from the plate and place it in the pan. | 3 | 2 | 1 | 66.67% | 22,30 | 24 |
| T10-I006 | Pick the squash from the plate and place it in the pan. | 3 | 2 | 1 | 66.67% | 21,40 | 49 |
| T10-I007 | Pick the tomato from the plate and place it in the pan. | 3 | 3 | 0 | 100.00% | 27,34,46 | — |
| T10-I008 | Pick the egg from the plate and place it in the pan. | 2 | 2 | 0 | 100.00% | 6,23 | — |
| T10-I009 | Pick the lime from the plate and place it in the pan. | 2 | 2 | 0 | 100.00% | 29,47 | — |
| T10-I010 | Pick the marshmallow from the plate and place it in the pan. | 2 | 1 | 1 | 50.00% | 8 | 32 |
| T10-I011 | Pick the mushroom from the plate and place it in the pan. | 2 | 2 | 0 | 100.00% | 12,19 | — |
| T10-I012 | Pick the apple from the plate and place it in the pan. | 1 | 1 | 0 | 100.00% | 28 | — |
| T10-I013 | Pick the broccoli from the plate and place it in the pan. | 1 | 0 | 1 | 0.00% | — | 37 |
| T10-I014 | Pick the carrot from the plate and place it in the pan. | 1 | 1 | 0 | 100.00% | 42 | — |
| T10-I015 | Pick the cheese from the plate and place it in the pan. | 1 | 1 | 0 | 100.00% | 14 | — |
| T10-I016 | Pick the corn from the plate and place it in the pan. | 1 | 1 | 0 | 100.00% | 38 | — |
| T10-I017 | Pick the fish from the plate and place it in the pan. | 1 | 1 | 0 | 100.00% | 31 | — |
| T10-I018 | Pick the hot dog from the plate and place it in the pan. | 1 | 1 | 0 | 100.00% | 35 | — |
| T10-I019 | Pick the hotdog bun from the plate and place it in the pan. | 1 | 1 | 0 | 100.00% | 15 | — |
| T10-I020 | Pick the mango from the plate and place it in the pan. | 1 | 1 | 0 | 100.00% | 20 | — |
| T10-I021 | Pick the potato from the plate and place it in the pan. | 1 | 1 | 0 | 100.00% | 16 | — |
| T10-I022 | Pick the shrimp from the plate and place it in the pan. | 1 | 0 | 1 | 0.00% | — | 13 |
| T10-I023 | Pick the steak from the plate and place it in the pan. | 1 | 1 | 0 | 100.00% | 26 | — |
| T10-I024 | Pick the sweet potato from the plate and place it in the pan. | 1 | 1 | 0 | 100.00% | 17 | — |

## T11 — PickPlaceDrawerToCounter

合计 28/50 成功，SR=56.00%，9组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T11-I001 | Pick the peeler from the drawer and place it on the counter. | 10 | 4 | 6 | 40.00% | 33,38,39,46 | 14,18,20,24,27,29 |
| T11-I002 | Pick the rolling pin from the drawer and place it on the counter. | 9 | 5 | 4 | 55.56% | 5,17,31,34,42 | 9,11,19,21 |
| T11-I003 | Pick the ladle from the drawer and place it on the counter. | 7 | 4 | 3 | 57.14% | 0,1,13,43 | 26,28,47 |
| T11-I004 | Pick the measuring cup from the drawer and place it on the counter. | 7 | 7 | 0 | 100.00% | 2,3,25,35,40,41,44 | — |
| T11-I005 | Pick the pizza cutter from the drawer and place it on the counter. | 5 | 2 | 3 | 40.00% | 30,37 | 32,36,48 |
| T11-I006 | Pick the wooden spoon from the drawer and place it on the counter. | 4 | 0 | 4 | 0.00% | — | 4,6,7,12 |
| T11-I007 | Pick the dish brush from the drawer and place it on the counter. | 3 | 3 | 0 | 100.00% | 15,16,23 | — |
| T11-I008 | Pick the whisk from the drawer and place it on the counter. | 3 | 2 | 1 | 66.67% | 10,49 | 45 |
| T11-I009 | Pick the tongs from the drawer and place it on the counter. | 2 | 1 | 1 | 50.00% | 8 | 22 |

## T12 — PickPlaceSinkToCounter

合计 40/50 成功，SR=80.00%，25组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T12-I001 | Pick the avocado from the sink and place it on the plate located on the counter. | 4 | 4 | 0 | 100.00% | 2,22,37,46 | — |
| T12-I002 | Pick the carrot from the sink and place it on the plate located on the counter. | 4 | 4 | 0 | 100.00% | 1,3,17,44 | — |
| T12-I003 | Pick the banana from the sink and place it on the plate located on the counter. | 3 | 3 | 0 | 100.00% | 27,29,30 | — |
| T12-I004 | Pick the cream cheese stick from the sink and place it on the plate located on the counter. | 3 | 3 | 0 | 100.00% | 11,23,34 | — |
| T12-I005 | Pick the lemon from the sink and place it on the plate located on the counter. | 3 | 2 | 1 | 66.67% | 13,33 | 12 |
| T12-I006 | Pick the onion from the sink and place it on the plate located on the counter. | 3 | 2 | 1 | 66.67% | 6,26 | 36 |
| T12-I007 | Pick the potato from the sink and place it on the plate located on the counter. | 3 | 3 | 0 | 100.00% | 24,28,35 | — |
| T12-I008 | Pick the tomato from the sink and place it on the plate located on the counter. | 3 | 3 | 0 | 100.00% | 19,21,41 | — |
| T12-I009 | Pick the apple from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00% | 14 | 25 |
| T12-I010 | Pick the chicken drumstick from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00% | 31 | 18 |
| T12-I011 | Pick the garlic from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00% | 5 | 38 |
| T12-I012 | Pick the lemon wedge from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00% | 47 | 45 |
| T12-I013 | Pick the milk from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00% | 0 | 9 |
| T12-I014 | Pick the peach from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00% | 48 | 40 |
| T12-I015 | Pick the steak from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00% | 4 | 20 |
| T12-I016 | Pick the bell pepper from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00% | 15 | — |
| T12-I017 | Pick the cheese from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00% | 10 | — |
| T12-I018 | Pick the cucumber from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00% | 43 | — |
| T12-I019 | Pick the eggplant from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00% | 42 | — |
| T12-I020 | Pick the mushroom from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00% | 7 | — |
| T12-I021 | Pick the orange from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00% | 32 | — |
| T12-I022 | Pick the pear from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00% | 8 | — |
| T12-I023 | Pick the sweet potato from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00% | 39 | — |
| T12-I024 | Pick the tangerine from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00% | 16 | — |
| T12-I025 | Pick the yogurt from the sink and place it on the plate located on the counter. | 1 | 0 | 1 | 0.00% | — | 49 |

## T13 — PickPlaceToasterToCounter

合计 49/50 成功，SR=98.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T13-I001 | Place the toasted item on a plate. | 50 | 49 | 1 | 98.00% | 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49 | 25 |

## T14 — SlideDishwasherRack

合计 37/50 成功，SR=74.00%，2组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T14-I001 | Fully slide the top dishwasher rack in. | 27 | 16 | 11 | 59.26% | 1,3,4,7,10,11,12,13,20,22,24,28,32,34,42,48 | 2,5,17,18,21,25,31,33,35,38,40 |
| T14-I002 | Fully slide the top dishwasher rack out. | 23 | 21 | 2 | 91.30% | 0,6,8,9,15,16,19,23,26,27,29,30,37,39,41,43,44,45,46,47,49 | 14,36 |

## T15 — TurnOffStove

合计 15/50 成功，SR=30.00%，8组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T15-I001 | Turn off the front right burner of the stove. | 14 | 3 | 11 | 21.43% | 29,32,40 | 3,5,14,15,22,28,31,34,37,38,39 |
| T15-I002 | Turn off the rear right burner of the stove. | 12 | 6 | 6 | 50.00% | 6,12,13,21,33,46 | 10,16,18,19,25,27 |
| T15-I003 | Turn off the front left burner of the stove. | 8 | 1 | 7 | 12.50% | 20 | 7,23,26,30,35,41,42 |
| T15-I004 | Turn off the front center burner of the stove. | 6 | 0 | 6 | 0.00% | — | 0,2,4,9,24,48 |
| T15-I005 | Turn off the rear left burner of the stove. | 5 | 1 | 4 | 20.00% | 8 | 1,11,36,49 |
| T15-I006 | Turn off the left burner of the stove. | 3 | 2 | 1 | 66.67% | 17,47 | 43 |
| T15-I007 | Turn off the center burner of the stove. | 1 | 1 | 0 | 100.00% | 45 | — |
| T15-I008 | Turn off the rear center burner of the stove. | 1 | 1 | 0 | 100.00% | 44 | — |

## T16 — TurnOnElectricKettle

合计 31/50 成功，SR=62.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T16-I001 | Press down the lever to turn on the electric kettle. | 50 | 31 | 19 | 62.00% | 0,1,2,5,8,9,10,13,14,15,16,17,18,21,24,26,29,30,32,34,35,36,37,38,40,42,43,44,45,46,47 | 3,4,6,7,11,12,19,20,22,23,25,27,28,31,33,39,41,48,49 |

## T17 — TurnOnMicrowave

合计 45/50 成功，SR=90.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T17-I001 | Press the start button on the microwave. | 50 | 45 | 5 | 90.00% | 0,1,2,4,5,6,7,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,28,30,31,32,33,34,35,36,37,38,39,40,41,42,43,45,46,47,48,49 | 3,8,27,29,44 |

## T18 — TurnOnSinkFaucet

合计 32/50 成功，SR=64.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T18-I001 | Turn on the sink faucet. | 50 | 32 | 18 | 64.00% | 0,1,3,4,5,6,7,8,10,12,13,14,16,17,18,21,22,24,28,30,33,37,38,39,40,41,42,43,45,46,48,49 | 2,9,11,15,19,20,23,25,26,27,29,31,32,34,35,36,44,47 |

---

R07相关的原始数据、摘要和数值来源SHA见总报告、R07 JSON归档；本页由独立只读聚合生成，无训练/仿真重跑。
