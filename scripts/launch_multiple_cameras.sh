#!/usr/bin/env bash
set -euo pipefail

PIDS=()

cleanup() {
  for pid in "${PIDS[@]:-}"; do
    if kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" 2>/dev/null || true
    fi
  done
  wait || true
}

trap cleanup EXIT INT TERM

launch_camera() {
  local name="$1"
  local serial="$2"
  local do_reset="$3"

  ros2 launch realsense2_camera rs_launch.py \
    camera_namespace:=/ \
    camera_name:="${name}" \
    serial_no:="_${serial}" \
    initial_reset:="${do_reset}" \
    enable_depth:=false \
    rgb_camera.color_profile:=640x480x30 &

  PIDS+=("$!")
}

wait_for_topic() {
  local topic="$1"
  local timeout_s="${2:-20}"
  local start
  start="$(date +%s)"
  while true; do
    if ros2 topic list | grep -q "^${topic}$"; then
      return 0
    fi
    if (( $(date +%s) - start >= timeout_s )); then
      echo "[camera-triple] Timeout waiting for topic: ${topic}" >&2
      return 1
    fi
    sleep 0.5
  done
}

launch_camera "robot0_agentview_left" "342522074350" "false"
wait_for_topic "/robot0_agentview_left/color/image_raw" 30

launch_camera "robot0_agentview_right" "347622071856" "false"
wait_for_topic "/robot0_agentview_right/color/image_raw" 30

launch_camera "robot0_eye_in_hand" "336222070633" "false"
wait_for_topic "/robot0_eye_in_hand/color/image_raw" 30

echo "All cameras topics are up."

wait
