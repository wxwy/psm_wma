# G2 Initial Spatial Language — Independent Versioned Generator (review-v1)

Owner-driven independent update of enhanced instructions. This is a working
review candidate, NOT a frozen training prompt. The source of truth is
PSM-WMA_G2_detailed_design_v2.0_2026-11-16.md sections 10.1–10.5 / 17.1.

## 1. Why separate from Stage A

Current g2/offline/language_context.py TextBank.add() redoes the old text
formatter for every spatial state and persists language.json inside the sealed
Stage A output. Rewriting it would disturb current View/SG/VAE production and
source checks. The old template also lacks bbox geometry and emits long source
instance IDs. The independent producer MUST NOT rewrite Stage A files.

New files:
- g2/language/initial_context.py — pure build_initial_language(), sealed
  load_initial_episode_language(), atomic write, strict verify, and independent
  versioned-language Reader API.
- tools/g2/generate_initial_language.py — explicit CLI preview/write/verify,
  one task with selected episodes, or --all-ready. No background loop, VAE,
  renderer, simulator, LLM or model invocation.
- g2/data/aligned_provider.py — optional initial_language_root plus
  initial_language_recipe_id; old DATA_C joint_index and G1/SG/VAE are
  immutable; selecting a new recipe updates its model identity, checks real
  source and content hashes, but does not mark model training ready.
- DATA_C compatibility: the legacy incremental corpus producer previously
  omitted the joint recipe_id from manifest.json although Provider required
  it. Strictly derive/verify every episode's actual canonical recipe when
  reading legacy data, and include it in future producer revisions. Existing
  DATA_C outputs are not changed by these source edits.

## 2. Episode initial facts and output template

Input = original G1 Verified 20Hz task instruction + producer-sealed frame 0
Scene Graph and initial task entity roles; NOT per-decision SG/future outcomes.

Format:

    Task: <verbatim original>
    Initial spatial context (world frame; metres; episode frame 0):
    - <name> [<entity_id>]: role=<role>; room=R0;
      bbox_center=(x,y,z); bbox_size=(sx,sy,sz).
    Ambiguity: <role, label, room> has N same-label candidates;
    M are shown, N-M omitted.

- BBox is world-axis-aligned from min/max, not mass centroid, contact or
  target grasp point; actual source Island ID may be a string.
- No inferred on/inside, contact, open/closed, ownership, task success or
  future action planning. Initial Room 'contains' is NOT evidence of
  object-in-drawer/fridge.
- When identical same-category objects exist in the same Room, candidate
  ambiguity is shown. If there is one semantically unique target object,
  alternative source/destination candidates are listed in proximity order
  using initial world box centers, NOT GT oracle IDs. Proximity is display
  ranking, never a factual on/inside relation.
- Default cap four per candidate group and show omitted counts; never silently
  drop ambiguity. The original is never truncated; fail if even one object
  per role exceeds budget 4096 Unicode characters.
- Model prompt excludes long source_instance_id, which remains in structured
  source-bound audit facts. Prompt retains entity IDs for references.
- The output is deterministic, 20Hz source-bound and recomputable. This
  Full Map GT mode is not automatically equivalent to online perception.

Review recipe (4 candidates/group):
115569530be3d219d4ae3997b3ef5b05b10da701aebab4f184ea9912014cd8f6

## 3. Versioned independent storage

Root:
  /mnt/data1/data_v2_0617/robocasa365_v3_flat/
    robocasa365-target-atomic-g2-language/

Per-recipe layout:
  OUTPUT_IDENTITY.json (G1 source binding, independent of template version)
  recipes/<recipe_sha256>/RECIPE.json
  recipes/<recipe_sha256>/tasks/<task>/episodes/episode_xxxxxx/
    initial_context.json
    COMPLETE.json (hash, source, recipe/text identity, training_ready=false)

Changing the template parameters yields a NEW recipe path, never replaces
previous episode files. Other repo structures, View/SG/VAE and existing
joint_index.json are untouched.

Example standalone CLI:

    python -m tools.g2.generate_initial_language \
      --source-root /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic \
      --g1-verified-index /mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1 \
      --g1-cache-root /mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window \
      --views-root /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-6views \
      --output-root /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-g2-language \
      --mode preview --task-class PickPlaceDrawerToCounter --episodes 5099

Change mode to write to publish source-sealed episode text, verify to compare
and check receipt, or select --all-ready for an explicit separate run.
--max-candidates-per-group 2 creates a second coexisting recipe.
No automatic full-corpus backfill has been started.

## 4. Actual real-data tests and Gate limitations

- Five original earlier random task episodes saved under the default review
  recipe; CloseBlenderLid/104 also saved to test model Reader.
- 14 actual distinct task classes with a sealed initial SG sampled and
  verified from original G1. Covers true Island string IDs and ambiguity.
- Actual DATA_C Candidate Reader with explicit language override on the same
  CloseBlenderLid real windows 16,32,48 changed text and data identity while
  state15 and selected VAE View owners stayed identical.
- Two recipe versions coexisted in the same root; old file SHA did not change.
- Existing View, SG, original language.json, legacy DATA_C and production
  model/VAE tasks were not modified. PR candidate code is isolated.
- Still NOT train-ready: review recipe has production_template_frozen=false
  and training_ready=false, and Provider has candidate evidence scope.
  Owner must approve wording/ambiguity before text freeze, then formal
  train/val split and actual G2 Phase5 trained-model gate.

Design caveat: listing up to four same-label alternatives is conservative,
but could include irrelevant fixtures and omit some relevant ones. Do not
silently upgrade to a full production prompt until this policy is reviewed.
