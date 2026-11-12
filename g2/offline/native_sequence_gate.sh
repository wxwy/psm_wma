#!/usr/bin/env bash
# Native nav_sg source GT Room/SG + 10mm color worker, on a private ROS master.
# Called only by manual g2.offline.atomic_6views_run production executor.
set -euo pipefail
if [[ $# != 7 ]]; then
  echo 'usage: native_sequence_gate.sh CATKIN_SETUP NATIVE_BINARY SEQUENCE_PATH OUTPUT_ROOT PORT MIN_Z MAX_Z' >&2
  exit 2
fi
setup="$(realpath "$1")"
binary="$(realpath "$2")"
plan="$(realpath "$3")"
output="$(realpath -m "$4")"
port="$5"
min_z="$6"
max_z="$7"
[[ "$port" =~ ^[0-9]+$ && "$port" -gt 1024 && "$port" -lt 65536 ]] || {
  echo 'invalid isolated ROS port' >&2
  exit 2
}
[[ -f "$setup" && -x "$binary" && -f "$plan" && ! -e "$output" ]] || {
  echo 'native worker inputs are missing or destination already exists' >&2
  exit 2
}
# Isolate Noetic/Python 3.12 from the parent MuJoCo 3.3.7 Python 3.13
# runtime; catkin reconstructs its own package import paths.
unset PYTHONPATH
set +u
source "$setup"
set -u
export ROS_MASTER_URI="http://127.0.0.1:$port"
export ROS_IP=127.0.0.1
export ROS_HOME="${output}_ros_home"
python3 - <<'PY'
import rosgraph
if rosgraph.is_master_online():
    raise SystemExit("isolated ROS master is already in use")
PY
mkdir -p "$ROS_HOME"
roscore -p "$port" > "$ROS_HOME/roscore.log" 2>&1 &
master=$!
cleanup() {
  kill -TERM "$master" 2>/dev/null || true
  wait "$master" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
python3 - <<'PY'
import rosgraph,time
end=time.monotonic()+30
while not rosgraph.is_master_online():
    if time.monotonic()>end:
        raise SystemExit("native worker isolated master timeout")
    time.sleep(.05)
PY
# Use nav_sg's own launch profile; direct execution would omit the
# Room/SG configuration and silently change the native segmentation policy.
launch_pkg="$(realpath "$(rospack find mapping)")"
expected_pkg="$(realpath "$(dirname "$setup")/../src/mapping")"
[[ "$launch_pkg" == "$expected_pkg" ]] || {
  echo 'ROS mapping package resolves outside the configured nav_sg repository' >&2
  exit 2
}
expected_binary="$(realpath "$(dirname "$setup")/lib/mapping/gt_direct_color_episode")"
[[ "$binary" == "$expected_binary" ]] || {
  echo 'native worker binary must come from the same nav_sg catkin source' >&2
  exit 2
}
roslaunch mapping g2_gt_direct_color_episode.launch \
  plan:="$plan" output:="$output" \
  projection_min_z:="$min_z" projection_max_z:="$max_z" \
  emit_native_color_view_binary:=true
test -f "$output/F24_NATIVE_FULL_EPISODE_COMPLETE.json"
echo "G2_NATIVE_COLOR_DUALMAP_COMPLETE $output"
