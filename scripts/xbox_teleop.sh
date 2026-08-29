#!/usr/bin/env bash
set -euo pipefail

project_root="${PIXI_PROJECT_ROOT:-$(cd "${BASH_SOURCE[0]%/*}/.." && pwd)}"
controller_config="$project_root/config/crisp_controller.yaml"
teleop_pid=""
joy_pid=""
crisp_active=false

cleanup() {
  status=$?
  trap - EXIT INT TERM

  if [[ -n "$teleop_pid" ]]; then
    kill "$teleop_pid" 2>/dev/null || true
    wait "$teleop_pid" 2>/dev/null || true
  fi

  if [[ "$crisp_active" == true ]]; then
    ros2 control switch_controllers \
      --controller-manager /controller_manager \
      --deactivate cartesian_controller \
      --activate fr3_arm_controller \
      --strict || true
  fi

  if [[ -n "$joy_pid" ]]; then
    kill "$joy_pid" 2>/dev/null || true
    wait "$joy_pid" 2>/dev/null || true
  fi

  exit "$status"
}
trap cleanup EXIT INT TERM

ros2 param set /controller_manager \
  cartesian_controller.type crisp_controllers/CartesianController

ros2 run controller_manager spawner cartesian_controller \
  --controller-manager /controller_manager \
  --controller-manager-timeout 60 \
  --param-file "$controller_config" \
  --controller-ros-args "--remap target_pose:=/cartesian_controller/target_pose" \
  --inactive

ros2 control switch_controllers \
  --controller-manager /controller_manager \
  --deactivate fr3_arm_controller \
  --activate cartesian_controller \
  --strict
crisp_active=true

ros2 run joy joy_node &
joy_pid=$!
python "$project_root/scripts/xbox_teleop.py" "$@" &
teleop_pid=$!

wait -n "$joy_pid" "$teleop_pid"
