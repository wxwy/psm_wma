# R03 900EP：139 组原始语言指令完整分项表

[返回主报告](README.md)。来源：R03 已提交的900份 Core `result.json.body`；Run与版本身份见主报告。每行按 `(task, instruction)` 精确字符串分组，不翻译、不纠错、不归并同义词。正文保留原始英文措辞。

**核对合计：18 Task，139组，900 EP，454成功，446失败，总体SR=50.4444%。** N为本行样本数，S/F为成功/失败数；SR=S/N。EP为当前Task内的0–49，需用 `(Task, EP)` 定位，不能当作训练集global ID。`—` 表示空列表，不是缺失数据。

**小样本警告：62组仅1 EP；108组少于5 EP。** 这些组的0%/100%只描述本次观测，不证明稳定失败/成功。指令变化常伴随对象、设备、位置、操作方向或场景差异；不是控制变量的语言改写实验。分组顺序为冻结Task顺序、N降序、指令字典序；Txx-Ixxx仅为报告索引。

所有行的成功EP与失败EP互斥；每个Task加总恰好50个不同EP。视频路径：`<RUN_ROOT>/tasks/<Task>/episodes/ep_<EP:03d>/media/rollout.mp4`；其余追溯路径见主报告。

## T01 — CloseBlenderLid

总计4/50成功，SR=8.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T01-I001 | Close the lid blender by securely placing the lid on top. | 50 | 4 | 46 | 8.00 | 7,9,30,36 | 0,1,2,3,4,5,6,8,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,31,32,33,34,35,37,38,39,40,41,42,43,44,45,46,47,48,49 |

## T02 — CloseFridge

总计22/50成功，SR=44.00%，2组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T02-I001 | Close the fridge door. | 29 | 19 | 10 | 65.52 | 0,2,3,5,13,14,15,17,18,20,26,28,30,32,34,35,37,41,44 | 1,6,9,12,23,25,27,42,47,48 |
| T02-I002 | Close the fridge doors. | 21 | 3 | 18 | 14.29 | 22,40,45 | 4,7,8,10,11,16,19,21,24,29,31,33,36,38,39,43,46,49 |

## T03 — CloseToasterOvenDoor

总计30/50成功，SR=60.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T03-I001 | Close the toaster oven door. | 50 | 30 | 20 | 60.00 | 0,1,2,3,4,5,6,7,9,10,11,12,13,14,17,18,21,24,26,30,31,33,34,37,39,40,44,45,47,49 | 8,15,16,19,20,22,23,25,27,28,29,32,35,36,38,41,42,43,46,48 |

## T04 — CoffeeSetupMug

总计27/50成功，SR=54.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T04-I001 | Pick the mug from the counter and place it under the coffee machine dispenser. | 50 | 27 | 23 | 54.00 | 1,2,4,5,6,8,10,11,15,16,18,19,20,21,23,25,26,28,31,32,34,38,39,41,44,46,47 | 0,3,7,9,12,13,14,17,22,24,27,29,30,33,35,36,37,40,42,43,45,48,49 |

## T05 — NavigateKitchen

总计1/50成功，SR=2.00%，13组指令。唯一成功为toaster oven目标EP29。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T05-I001 | Navigate to the stand mixer. | 7 | 0 | 7 | 0.00 | — | 7,18,24,25,36,41,46 |
| T05-I002 | Navigate to the electric kettle. | 6 | 0 | 6 | 0.00 | — | 1,6,11,14,38,39 |
| T05-I003 | Navigate to the shelves. | 6 | 0 | 6 | 0.00 | — | 4,10,22,27,30,43 |
| T05-I004 | Navigate to the toaster. | 6 | 0 | 6 | 0.00 | — | 5,8,20,33,34,35 |
| T05-I005 | Navigate to the coffee machine. | 5 | 0 | 5 | 0.00 | — | 13,17,26,45,49 |
| T05-I006 | Navigate to the dishwasher. | 4 | 0 | 4 | 0.00 | — | 0,19,23,42 |
| T05-I007 | Navigate to the fridge. | 3 | 0 | 3 | 0.00 | — | 9,21,37 |
| T05-I008 | Navigate to the sink. | 3 | 0 | 3 | 0.00 | — | 12,16,31 |
| T05-I009 | Navigate to the stove. | 3 | 0 | 3 | 0.00 | — | 3,28,32 |
| T05-I010 | Navigate to the toaster oven. | 3 | 1 | 2 | 33.33 | 29 | 40,48 |
| T05-I011 | Navigate to the oven. | 2 | 0 | 2 | 0.00 | — | 2,44 |
| T05-I012 | Navigate to the microwave. | 1 | 0 | 1 | 0.00 | — | 47 |
| T05-I013 | Navigate to the range hood. | 1 | 0 | 1 | 0.00 | — | 15 |

## T06 — OpenCabinet

总计37/50成功，SR=74.00%，2组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T06-I001 | Open the cabinet doors. | 29 | 18 | 11 | 62.07 | 0,1,4,9,11,14,19,22,26,29,30,35,39,41,43,45,48,49 | 3,6,8,12,13,18,20,25,37,38,46 |
| T06-I002 | Open the cabinet door. | 21 | 19 | 2 | 90.48 | 2,5,7,10,15,16,17,23,27,28,31,32,33,34,36,40,42,44,47 | 21,24 |

## T07 — OpenDrawer

总计19/50成功，SR=38.00%，2组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T07-I001 | Open the right drawer. | 29 | 7 | 22 | 24.14 | 2,21,24,26,31,37,39 | 3,4,5,8,10,11,14,15,16,17,18,19,20,27,32,33,34,35,36,38,45,47 |
| T07-I002 | Open the left drawer. | 21 | 12 | 9 | 57.14 | 1,6,7,12,13,28,40,41,43,44,48,49 | 0,9,22,23,25,29,30,42,46 |

## T08 — OpenStandMixerHead

总计33/50成功，SR=66.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T08-I001 | Open the stand mixer head. | 50 | 33 | 17 | 66.00 | 0,1,2,3,5,6,8,9,13,14,15,16,17,18,19,20,21,22,23,25,26,28,30,31,32,33,36,38,40,41,42,43,46 | 4,7,10,11,12,24,27,29,34,35,37,39,44,45,47,48,49 |

## T09 — PickPlaceCounterToCabinet

总计24/50成功，SR=48.00%，43组指令。多数对象只出现1次，不能用单次0%/100%概括对象能力。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T09-I001 | Pick the jug from the counter and place it in the cabinet. | 3 | 1 | 2 | 33.33 | 1 | 35,36 |
| T09-I002 | Pick the bell pepper from the counter and place it in the cabinet. | 2 | 2 | 0 | 100.00 | 21,30 | — |
| T09-I003 | Pick the hot dog from the counter and place it in the cabinet. | 2 | 1 | 1 | 50.00 | 33 | 22 |
| T09-I004 | Pick the juice from the counter and place it in the cabinet. | 2 | 1 | 1 | 50.00 | 41 | 45 |
| T09-I005 | Pick the mug from the counter and place it in the cabinet. | 2 | 1 | 1 | 50.00 | 26 | 4 |
| T09-I006 | Pick the paprika from the counter and place it in the cabinet. | 2 | 0 | 2 | 0.00 | — | 9,47 |
| T09-I007 | Pick the avocado from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 10 |
| T09-I008 | Pick the baguette from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 19 |
| T09-I009 | Pick the bottled drink from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 31 | — |
| T09-I010 | Pick the bottled water from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 3 | — |
| T09-I011 | Pick the bowl from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 18 |
| T09-I012 | Pick the boxed food from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 7 | — |
| T09-I013 | Pick the bread from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 23 |
| T09-I014 | Pick the can from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 44 | — |
| T09-I015 | Pick the carrot from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 12 |
| T09-I016 | Pick the cheese from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 42 | — |
| T09-I017 | Pick the chicken drumstick from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 0 | — |
| T09-I018 | Pick the egg from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 28 | — |
| T09-I019 | Pick the eggplant from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 8 | — |
| T09-I020 | Pick the glass cup from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 32 |
| T09-I021 | Pick the honey bottle from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 5 |
| T09-I022 | Pick the hotdog bun from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 11 | — |
| T09-I023 | Pick the jam from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 29 | — |
| T09-I024 | Pick the jar from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 13 |
| T09-I025 | Pick the lemon wedge from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 46 | — |
| T09-I026 | Pick the liquor from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 40 |
| T09-I027 | Pick the marshmallow from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 25 |
| T09-I028 | Pick the mayonnaise from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 27 |
| T09-I029 | Pick the mushroom from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 15 |
| T09-I030 | Pick the mustard from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 43 | — |
| T09-I031 | Pick the orange from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 14 | — |
| T09-I032 | Pick the peeler from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 2 | — |
| T09-I033 | Pick the pitcher from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 24 |
| T09-I034 | Pick the salt/pepper shaker from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 39 | — |
| T09-I035 | Pick the saucepan lid from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 17 |
| T09-I036 | Pick the sponge from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 20 |
| T09-I037 | Pick the spray from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 48 |
| T09-I038 | Pick the straw from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 34 |
| T09-I039 | Pick the sugar cube from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 49 | — |
| T09-I040 | Pick the tomato from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 37 | — |
| T09-I041 | Pick the turmeric from the counter and place it in the cabinet. | 1 | 1 | 0 | 100.00 | 6 | — |
| T09-I042 | Pick the water bottle from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 16 |
| T09-I043 | Pick the wooden spoon from the counter and place it in the cabinet. | 1 | 0 | 1 | 0.00 | — | 38 |

## T10 — PickPlaceCounterToStove

总计39/50成功，SR=78.00%，21组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T10-I001 | Pick the lemon wedge from the plate and place it in the pan. | 5 | 4 | 1 | 80.00 | 12,38,41,42 | 11 |
| T10-I002 | Pick the marshmallow from the plate and place it in the pan. | 5 | 5 | 0 | 100.00 | 1,2,21,27,44 | — |
| T10-I003 | Pick the chicken drumstick from the plate and place it in the pan. | 4 | 2 | 2 | 50.00 | 24,39 | 0,17 |
| T10-I004 | Pick the bell pepper from the plate and place it in the pan. | 3 | 3 | 0 | 100.00 | 9,18,46 | — |
| T10-I005 | Pick the broccoli from the plate and place it in the pan. | 3 | 1 | 2 | 33.33 | 31 | 10,28 |
| T10-I006 | Pick the mushroom from the plate and place it in the pan. | 3 | 2 | 1 | 66.67 | 5,37 | 49 |
| T10-I007 | Pick the squash from the plate and place it in the pan. | 3 | 3 | 0 | 100.00 | 13,19,30 | — |
| T10-I008 | Pick the tomato from the plate and place it in the pan. | 3 | 2 | 1 | 66.67 | 14,34 | 36 |
| T10-I009 | Pick the corn from the plate and place it in the pan. | 2 | 2 | 0 | 100.00 | 16,40 | — |
| T10-I010 | Pick the eggplant from the plate and place it in the pan. | 2 | 2 | 0 | 100.00 | 26,33 | — |
| T10-I011 | Pick the hot dog from the plate and place it in the pan. | 2 | 0 | 2 | 0.00 | — | 43,48 |
| T10-I012 | Pick the lemon from the plate and place it in the pan. | 2 | 2 | 0 | 100.00 | 3,45 | — |
| T10-I013 | Pick the lime from the plate and place it in the pan. | 2 | 2 | 0 | 100.00 | 8,35 | — |
| T10-I014 | Pick the onion from the plate and place it in the pan. | 2 | 2 | 0 | 100.00 | 23,29 | — |
| T10-I015 | Pick the potato from the plate and place it in the pan. | 2 | 2 | 0 | 100.00 | 4,32 | — |
| T10-I016 | Pick the steak from the plate and place it in the pan. | 2 | 1 | 1 | 50.00 | 20 | 25 |
| T10-I017 | Pick the apple from the plate and place it in the pan. | 1 | 1 | 0 | 100.00 | 7 | — |
| T10-I018 | Pick the cheese from the plate and place it in the pan. | 1 | 1 | 0 | 100.00 | 47 | — |
| T10-I019 | Pick the garlic from the plate and place it in the pan. | 1 | 1 | 0 | 100.00 | 15 | — |
| T10-I020 | Pick the mango from the plate and place it in the pan. | 1 | 1 | 0 | 100.00 | 6 | — |
| T10-I021 | Pick the shrimp from the plate and place it in the pan. | 1 | 0 | 1 | 0.00 | — | 22 |

## T11 — PickPlaceDrawerToCounter

总计15/50成功，SR=30.00%，9组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T11-I001 | Pick the rolling pin from the drawer and place it on the counter. | 10 | 4 | 6 | 40.00 | 3,10,18,41 | 6,15,19,21,31,38 |
| T11-I002 | Pick the peeler from the drawer and place it on the counter. | 9 | 1 | 8 | 11.11 | 9 | 4,7,12,24,26,39,40,49 |
| T11-I003 | Pick the ladle from the drawer and place it on the counter. | 8 | 1 | 7 | 12.50 | 42 | 0,1,13,29,37,45,48 |
| T11-I004 | Pick the measuring cup from the drawer and place it on the counter. | 7 | 3 | 4 | 42.86 | 11,28,35 | 16,22,32,36 |
| T11-I005 | Pick the pizza cutter from the drawer and place it on the counter. | 4 | 2 | 2 | 50.00 | 8,46 | 23,34 |
| T11-I006 | Pick the tongs from the drawer and place it on the counter. | 4 | 1 | 3 | 25.00 | 33 | 20,30,44 |
| T11-I007 | Pick the whisk from the drawer and place it on the counter. | 4 | 1 | 3 | 25.00 | 14 | 27,43,47 |
| T11-I008 | Pick the wooden spoon from the drawer and place it on the counter. | 3 | 1 | 2 | 33.33 | 17 | 2,25 |
| T11-I009 | Pick the dish brush from the drawer and place it on the counter. | 1 | 1 | 0 | 100.00 | 5 | — |

## T12 — PickPlaceSinkToCounter

总计29/50成功，SR=58.00%，29组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T12-I001 | Pick the carrot from the sink and place it on the plate located on the counter. | 3 | 2 | 1 | 66.67 | 1,11 | 44 |
| T12-I002 | Pick the fish from the sink and place it on the plate located on the counter. | 3 | 2 | 1 | 66.67 | 32,35 | 40 |
| T12-I003 | Pick the lemon from the sink and place it on the plate located on the counter. | 3 | 2 | 1 | 66.67 | 5,9 | 15 |
| T12-I004 | Pick the lemon wedge from the sink and place it on the plate located on the counter. | 3 | 3 | 0 | 100.00 | 12,13,18 | — |
| T12-I005 | Pick the milk from the sink and place it on the plate located on the counter. | 3 | 1 | 2 | 33.33 | 3 | 0,27 |
| T12-I006 | Pick the pear from the sink and place it on the plate located on the counter. | 3 | 3 | 0 | 100.00 | 2,17,30 | — |
| T12-I007 | Pick the potato from the sink and place it on the plate located on the counter. | 3 | 2 | 1 | 66.67 | 6,10 | 41 |
| T12-I008 | Pick the avocado from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00 | 29 | 46 |
| T12-I009 | Pick the cucumber from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00 | 48 | 39 |
| T12-I010 | Pick the garlic from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00 | 33 | 28 |
| T12-I011 | Pick the mango from the sink and place it on the plate located on the counter. | 2 | 0 | 2 | 0.00 | — | 16,31 |
| T12-I012 | Pick the peach from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00 | 47 | 14 |
| T12-I013 | Pick the shrimp from the sink and place it on the plate located on the counter. | 2 | 0 | 2 | 0.00 | — | 20,37 |
| T12-I014 | Pick the tangerine from the sink and place it on the plate located on the counter. | 2 | 1 | 1 | 50.00 | 21 | 19 |
| T12-I015 | Pick the apple from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00 | 7 | — |
| T12-I016 | Pick the banana from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00 | 23 | — |
| T12-I017 | Pick the bell pepper from the sink and place it on the plate located on the counter. | 1 | 0 | 1 | 0.00 | — | 22 |
| T12-I018 | Pick the broccoli from the sink and place it on the plate located on the counter. | 1 | 0 | 1 | 0.00 | — | 25 |
| T12-I019 | Pick the cheese from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00 | 42 | — |
| T12-I020 | Pick the corn from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00 | 38 | — |
| T12-I021 | Pick the cream cheese stick from the sink and place it on the plate located on the counter. | 1 | 0 | 1 | 0.00 | — | 4 |
| T12-I022 | Pick the egg from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00 | 26 | — |
| T12-I023 | Pick the eggplant from the sink and place it on the plate located on the counter. | 1 | 0 | 1 | 0.00 | — | 34 |
| T12-I024 | Pick the lime from the sink and place it on the plate located on the counter. | 1 | 0 | 1 | 0.00 | — | 49 |
| T12-I025 | Pick the onion from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00 | 45 | — |
| T12-I026 | Pick the orange from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00 | 8 | — |
| T12-I027 | Pick the steak from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00 | 36 | — |
| T12-I028 | Pick the tomato from the sink and place it on the plate located on the counter. | 1 | 1 | 0 | 100.00 | 24 | — |
| T12-I029 | Pick the yogurt from the sink and place it on the plate located on the counter. | 1 | 0 | 1 | 0.00 | — | 43 |

## T13 — PickPlaceToasterToCounter

总计37/50成功，SR=74.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T13-I001 | Place the toasted item on a plate. | 50 | 37 | 13 | 74.00 | 0,1,2,3,4,5,7,9,11,13,14,15,16,18,19,20,21,22,23,24,26,27,28,29,30,31,32,33,35,36,38,40,41,45,46,47,49 | 6,8,10,12,17,25,34,37,39,42,43,44,48 |

## T14 — SlideDishwasherRack

总计26/50成功，SR=52.00%，2组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T14-I001 | Fully slide the top dishwasher rack out. | 26 | 20 | 6 | 76.92 | 0,2,5,7,8,9,10,12,13,14,20,25,29,39,42,43,45,46,47,49 | 1,11,27,30,34,48 |
| T14-I002 | Fully slide the top dishwasher rack in. | 24 | 6 | 18 | 25.00 | 3,17,26,32,33,35 | 4,6,15,16,18,19,21,22,23,24,28,31,36,37,38,40,41,44 |

## T15 — TurnOffStove

总计11/50成功，SR=22.00%，8组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T15-I001 | Turn off the rear right burner of the stove. | 12 | 3 | 9 | 25.00 | 30,36,49 | 9,26,28,31,32,35,38,40,48 |
| T15-I002 | Turn off the front right burner of the stove. | 10 | 5 | 5 | 50.00 | 2,21,24,37,41 | 4,6,8,19,43 |
| T15-I003 | Turn off the rear left burner of the stove. | 10 | 2 | 8 | 20.00 | 29,44 | 1,22,23,25,27,34,42,46 |
| T15-I004 | Turn off the front left burner of the stove. | 9 | 0 | 9 | 0.00 | — | 5,7,10,15,16,17,39,45,47 |
| T15-I005 | Turn off the front center burner of the stove. | 4 | 0 | 4 | 0.00 | — | 0,3,14,33 |
| T15-I006 | Turn off the left burner of the stove. | 3 | 0 | 3 | 0.00 | — | 13,18,20 |
| T15-I007 | Turn off the center burner of the stove. | 1 | 1 | 0 | 100.00 | 12 | — |
| T15-I008 | Turn off the rear center burner of the stove. | 1 | 0 | 1 | 0.00 | — | 11 |

## T16 — TurnOnElectricKettle

总计21/50成功，SR=42.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T16-I001 | Press down the lever to turn on the electric kettle. | 50 | 21 | 29 | 42.00 | 0,2,3,7,10,13,18,20,21,26,27,29,32,33,35,36,39,42,43,44,45 | 1,4,5,6,8,9,11,12,14,15,16,17,19,22,23,24,25,28,30,31,34,37,38,40,41,46,47,48,49 |

## T17 — TurnOnMicrowave

总计45/50成功，SR=90.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T17-I001 | Press the start button on the microwave. | 50 | 45 | 5 | 90.00 | 0,1,2,3,4,5,6,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,40,41,43,44,47,48,49 | 7,39,42,45,46 |

## T18 — TurnOnSinkFaucet

总计34/50成功，SR=68.00%，1组指令。

| ID | Instruction（原文） | N | S | F | SR% | 成功EP | 失败EP |
|---|---|---:|---:|---:|---:|---|---|
| T18-I001 | Turn on the sink faucet. | 50 | 34 | 16 | 68.00 | 0,1,2,3,4,6,7,9,10,12,13,14,15,16,18,20,21,23,24,25,28,30,32,33,36,37,38,39,40,41,42,45,46,48 | 5,8,11,17,19,22,26,27,29,31,34,35,43,44,47,49 |

---

## 附表使用说明

可从任何一行选择成功和失败EP，在同Task/同指令下查看原始rollout与scene_provenance。跨指令对比之前还需检查布局、目标对象/设备和初态是否匹配。此表没有视频级行为错误标签；不能把“失败EP”直接称为“抓错物体”“左右理解错误”或“记忆失效”。

后续新增轮次应单独建报告，不覆写本表、不将新Episode混入R03的分母。
