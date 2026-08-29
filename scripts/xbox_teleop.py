#!/usr/bin/env python3
"""Direct Xbox-to-CRISP Cartesian teleoperation for FR3 camera calibration."""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass
from typing import Sequence

AXIS_LEFT_X = 0
AXIS_LEFT_Y = 1
AXIS_LT = 2
AXIS_RIGHT_X = 3
AXIS_RIGHT_Y = 4
AXIS_RT = 5
BUTTON_LB = 4
BUTTON_RB = 5


def _finite_vector(values: Sequence[float], length: int, *, name: str) -> list[float]:
    result = [float(value) for value in values[:length]]
    if any(not math.isfinite(value) or not -1.0 <= value <= 1.0 for value in result):
        raise ValueError(f"{name} values must be finite and in [-1, 1]")
    result.extend([0.0] * (length - len(result)))
    return result


def _buttons(values: Sequence[int], length: int) -> list[float]:
    result = [float(value) for value in values[:length]]
    if any(not math.isfinite(value) or value not in (0.0, 1.0) for value in result):
        raise ValueError("Xbox buttons must contain only 0 or 1")
    result.extend([0.0] * (length - len(result)))
    return result


def _deadzone(value: float, threshold: float) -> float:
    return 0.0 if abs(value) < threshold else value


def _clip_unit_norm(vector: Sequence[float]) -> tuple[float, float, float]:
    norm = math.sqrt(sum(value * value for value in vector))
    scale = 1.0 / norm if norm > 1.0 else 1.0
    return tuple(value * scale for value in vector)  # type: ignore[return-value]


def _normalize_quaternion(quaternion: Sequence[float]) -> tuple[float, float, float, float]:
    values = tuple(float(value) for value in quaternion)
    if len(values) != 4 or any(not math.isfinite(value) for value in values):
        raise ValueError("Pose quaternion must contain four finite values")
    norm = math.sqrt(sum(value * value for value in values))
    if norm < 1e-9:
        raise ValueError("Pose quaternion is degenerate")
    return tuple(value / norm for value in values)  # type: ignore[return-value]


def _quaternion_multiply(
    left: Sequence[float], right: Sequence[float]
) -> tuple[float, float, float, float]:
    lx, ly, lz, lw = left
    rx, ry, rz, rw = right
    return _normalize_quaternion(
        (
            lw * rx + lx * rw + ly * rz - lz * ry,
            lw * ry - lx * rz + ly * rw + lz * rx,
            lw * rz + lx * ry - ly * rx + lz * rw,
            lw * rw - lx * rx - ly * ry - lz * rz,
        )
    )


def _euler_xyz_quaternion(euler_xyz: Sequence[float]) -> tuple[float, float, float, float]:
    """Return the extrinsic XYZ delta used by the reference teleoperator."""

    roll, pitch, yaw = euler_xyz
    qx = (math.sin(roll / 2.0), 0.0, 0.0, math.cos(roll / 2.0))
    qy = (0.0, math.sin(pitch / 2.0), 0.0, math.cos(pitch / 2.0))
    qz = (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))
    return _quaternion_multiply(qz, _quaternion_multiply(qy, qx))


@dataclass(frozen=True)
class Pose:
    position: tuple[float, float, float]
    orientation: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if any(not math.isfinite(value) for value in self.position):
            raise ValueError("Pose position must contain three finite values")
        if len(self.position) != 3:
            raise ValueError("Pose position must contain three finite values")
        object.__setattr__(self, "orientation", _normalize_quaternion(self.orientation))


@dataclass
class XboxPoseMapper:
    max_linear_step_m: float = 0.075
    max_rotation_step_rad: float = 0.15
    deadzone: float = 0.10

    def __post_init__(self) -> None:
        if not math.isfinite(self.max_linear_step_m) or self.max_linear_step_m <= 0.0:
            raise ValueError("max_linear_step_m must be positive and finite")
        if not math.isfinite(self.max_rotation_step_rad) or self.max_rotation_step_rad <= 0.0:
            raise ValueError("max_rotation_step_rad must be positive and finite")
        if not math.isfinite(self.deadzone) or not 0.0 <= self.deadzone < 1.0:
            raise ValueError("deadzone must be finite and in [0, 1)")
        self._desired_position: list[float] | None = None
        self._desired_orientation: tuple[float, float, float, float] | None = None
        self._linear_active = [False, False, False]
        self._angular_active = False

    def seed(self, measured: Pose) -> Pose:
        self._desired_position = list(measured.position)
        self._desired_orientation = measured.orientation
        self._linear_active = [False, False, False]
        self._angular_active = False
        return measured

    def hold(self, measured: Pose) -> Pose:
        return self.seed(measured)

    def update(
        self,
        measured: Pose,
        *,
        axes: Sequence[float],
        buttons: Sequence[int],
    ) -> Pose:
        if self._desired_position is None or self._desired_orientation is None:
            raise RuntimeError("Mapper must be seeded from the measured link8 pose")

        xbox_axes = _finite_vector(axes, 6, name="Xbox axis")
        xbox_buttons = _buttons(buttons, 6)
        linear = _clip_unit_norm(
            tuple(
                _deadzone(value, self.deadzone)
                for value in (
                    0.5 * (xbox_axes[AXIS_LT] - xbox_axes[AXIS_RT]),
                    xbox_axes[AXIS_RIGHT_X],
                    xbox_axes[AXIS_RIGHT_Y],
                )
            )
        )
        angular = _clip_unit_norm(
            tuple(
                _deadzone(value, self.deadzone)
                for value in (
                    xbox_axes[AXIS_LEFT_X],
                    xbox_axes[AXIS_LEFT_Y],
                    xbox_buttons[BUTTON_RB] - xbox_buttons[BUTTON_LB],
                )
            )
        )

        linear_active = [value != 0.0 for value in linear]
        for index, active in enumerate(linear_active):
            if active:
                self._desired_position[index] = (
                    measured.position[index] + linear[index] * self.max_linear_step_m
                )
            elif self._linear_active[index]:
                self._desired_position[index] = measured.position[index]
        self._linear_active = linear_active

        angular_active = any(value != 0.0 for value in angular)
        if angular_active:
            delta = _euler_xyz_quaternion(
                tuple(value * self.max_rotation_step_rad for value in angular)
            )
            self._desired_orientation = _quaternion_multiply(delta, measured.orientation)
        elif self._angular_active:
            self._desired_orientation = measured.orientation
        self._angular_active = angular_active

        return Pose(tuple(self._desired_position), self._desired_orientation)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--joy-topic", default="/joy")
    parser.add_argument("--target-topic", default="/cartesian_controller/target_pose")
    parser.add_argument("--base-frame", default="fr3_link0")
    parser.add_argument("--end-effector-frame", default="fr3_link8")
    parser.add_argument("--rate-hz", type=float, default=15.0)
    parser.add_argument("--linear-step-m", type=float, default=0.075)
    parser.add_argument("--rotation-step-rad", type=float, default=0.15)
    parser.add_argument("--deadzone", type=float, default=0.10)
    parser.add_argument("--stale-timeout-s", type=float, default=0.25)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if not math.isfinite(args.rate_hz) or args.rate_hz <= 0.0:
        raise ValueError("rate-hz must be positive and finite")
    if not math.isfinite(args.stale_timeout_s) or args.stale_timeout_s <= 0.0:
        raise ValueError("stale-timeout-s must be positive and finite")

    import rclpy
    from geometry_msgs.msg import PoseStamped
    from rclpy.duration import Duration
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from rclpy.time import Time
    from sensor_msgs.msg import Joy
    from tf2_ros import Buffer, TransformException, TransformListener

    class XboxTeleopNode(Node):
        def __init__(self) -> None:
            super().__init__("franka_calibration_xbox_teleop")
            self._mapper = XboxPoseMapper(
                max_linear_step_m=args.linear_step_m,
                max_rotation_step_rad=args.rotation_step_rad,
                deadzone=args.deadzone,
            )
            self._tf_buffer = Buffer(cache_time=Duration(seconds=1.0))
            self._tf_listener = TransformListener(self._tf_buffer, self)
            self._publisher = self.create_publisher(PoseStamped, args.target_topic, 1)
            self.create_subscription(Joy, args.joy_topic, self._on_joy, qos_profile_sensor_data)
            self.create_timer(1.0 / args.rate_hz, self._control_tick)
            self._joy_axes: tuple[float, ...] | None = None
            self._joy_buttons: tuple[int, ...] | None = None
            self._joy_received_s: float | None = None
            self._seeded = False
            self._input_stale = False
            self._last_warning_s = 0.0
            self.get_logger().info(
                f"Xbox teleop: {args.base_frame} -> {args.end_effector_frame}, "
                f"publishing {args.target_topic} at {args.rate_hz:g} Hz"
            )

        def _warn(self, message: str) -> None:
            now_s = time.monotonic()
            if now_s - self._last_warning_s >= 1.0:
                self.get_logger().warning(message)
                self._last_warning_s = now_s

        def _on_joy(self, message: Joy) -> None:
            self._joy_axes = tuple(message.axes)
            self._joy_buttons = tuple(message.buttons)
            self._joy_received_s = time.monotonic()

        def _measured_pose(self) -> Pose | None:
            try:
                transform = self._tf_buffer.lookup_transform(
                    args.base_frame, args.end_effector_frame, Time()
                )
            except TransformException as exc:
                self._warn(f"Waiting for link8 TF: {exc}")
                return None
            translation = transform.transform.translation
            rotation = transform.transform.rotation
            try:
                return Pose(
                    (translation.x, translation.y, translation.z),
                    (rotation.x, rotation.y, rotation.z, rotation.w),
                )
            except ValueError as exc:
                self._warn(str(exc))
                return None

        def _publish(self, target: Pose) -> None:
            message = PoseStamped()
            message.header.stamp = self.get_clock().now().to_msg()
            message.header.frame_id = args.base_frame
            message.pose.position.x, message.pose.position.y, message.pose.position.z = (
                target.position
            )
            (
                message.pose.orientation.x,
                message.pose.orientation.y,
                message.pose.orientation.z,
                message.pose.orientation.w,
            ) = target.orientation
            self._publisher.publish(message)

        def _control_tick(self) -> None:
            measured = self._measured_pose()
            if measured is None:
                return
            if not self._seeded:
                self._mapper.seed(measured)
                self._seeded = True
            if (
                self._joy_axes is None
                or self._joy_buttons is None
                or self._joy_received_s is None
            ):
                return

            age_s = time.monotonic() - self._joy_received_s
            if age_s > args.stale_timeout_s:
                if not self._input_stale:
                    self._publish(self._mapper.hold(measured))
                    self._warn(
                        f"Xbox input is {age_s:.3f}s old; holding the measured link8 pose"
                    )
                self._input_stale = True
                return
            if self._input_stale:
                self._mapper.seed(measured)
                self._input_stale = False
                self.get_logger().info("Fresh Xbox input received; target reseeded from link8")

            try:
                target = self._mapper.update(
                    measured, axes=self._joy_axes, buttons=self._joy_buttons
                )
            except (RuntimeError, ValueError) as exc:
                if not self._input_stale:
                    self._publish(self._mapper.hold(measured))
                self._input_stale = True
                self._warn(str(exc))
                return
            self._publish(target)

    rclpy.init()
    node = XboxTeleopNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
