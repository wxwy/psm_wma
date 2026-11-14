# G2 stove cutaway A/B — isolated diagnostic

Status: **source-code and synthetic-dataflow checks only**. No real RoboCasa render is claimed. The experiment does not modify V3 production files, generated sixview PNGs, Scene Graphs or running workers.

## Scope

Four source-backed NavigateKitchen examples: layout 2 / episode 2104; layout 4 / episode 2119; layout 7 / episode 2103; layout 9 / episode 2101.

The experiment loads the exact original model.xml.gz and states.npz from the immutable 9126-entry plan, converts it using the existing V3 source asset mapping, then uses the same G2 FP64 EGL raster and MaterialResolver to render the stove-area crop at 1cm/pixel in two passes:

- Original: nearest opaque source Visual Geom hit, including overhead hood and cabinets.
- Cutaway: same source/camera/ray/material, but excludes any entire opaque Visual Geom whose minimum world height is greater than stovetop_max_z + 0.25m. No geom name determines which surfaces are removed.
- The stovetop source prefix is used only to select the diagnostic crop/reference height. It is not a general scene segmentation rule.
- Translucent source parts are excluded equally in both variants; therefore this is not full-F27 parity. Thin-geometry limits remain to be evaluated.

Each episode produces original.png, cutaway.png, comparison.png and report.json; index.html plus summary.json are produced at the output root. Results include source SHA256 and per-geom visible-pixel counts.

## Run without changing the active production checkout

In a separate shell on server data, after checking GPU load, run these commands from psm_wma_v3:

    cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3
    git fetch origin g2-stove-cutaway-ab-20261114
    git show origin/g2-stove-cutaway-ab-20261114:tools/g2/stove_cutaway_ab.py > /tmp/g2_stove_cutaway_ab_20261114.py

    export PYTHONPATH="$PWD/.g2_runtime_deps_py313:$PWD"
    export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
    "$PWD/cosmos-framework/.venv/bin/python" -u /tmp/g2_stove_cutaway_ab_20261114.py --gpu 4 --output /mnt/data1/data_v2_0617/robocasa365_v3_flat/.g2_stove_cutaway_ab_20261114

GPU 4 is an EXAMPLE: choose a card with free capacity; production is currently using GPUs 4–7. The script refuses an existing output directory. It writes only the new experiment output and the /tmp script copy, never the source files or formal sixview output.

After a successful run, assuming the existing local HTTP server still publishes the /data1 symlink, the expected (NOT yet verified) preview location is:

    http://127.0.0.1:18765/data1/data_v2_0617/robocasa365_v3_flat/.g2_stove_cutaway_ab_20261114/index.html

Compare all four layouts visually before considering integration. The grate/rail features may be embedded in the source Body001 mesh; the ~3–4cm knobs may be limited by 1cm/pixel resolution independently of the overhead occlusion.
