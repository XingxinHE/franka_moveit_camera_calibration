from __future__ import annotations

import importlib.util
import math
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "xbox_teleop.py"
SPEC = importlib.util.spec_from_file_location("xbox_teleop", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
xbox_teleop = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = xbox_teleop
SPEC.loader.exec_module(xbox_teleop)

Pose = xbox_teleop.Pose
XboxPoseMapper = xbox_teleop.XboxPoseMapper


def neutral_axes() -> list[float]:
    return [0.0, 0.0, 1.0, 0.0, 0.0, 1.0]


def buttons(*pressed: int) -> list[int]:
    values = [0] * 6
    for index in pressed:
        values[index] = 1
    return values


class XboxPoseMapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = Pose((0.4, 0.0, 0.5), (0.0, 0.0, 0.0, 1.0))
        self.mapper = XboxPoseMapper()
        self.mapper.seed(self.identity)

    def assertPoseAlmostEqual(self, actual: Pose, expected: Pose) -> None:
        for actual_value, expected_value in zip(
            (*actual.position, *actual.orientation),
            (*expected.position, *expected.orientation),
            strict=True,
        ):
            self.assertAlmostEqual(actual_value, expected_value)

    def test_neutral_input_holds_seeded_pose(self) -> None:
        target = self.mapper.update(
            self.identity, axes=neutral_axes(), buttons=buttons()
        )
        self.assertPoseAlmostEqual(target, self.identity)

    def test_triggers_move_along_base_x(self) -> None:
        positive_axes = neutral_axes()
        positive_axes[5] = -1.0
        positive = self.mapper.update(
            self.identity, axes=positive_axes, buttons=buttons()
        )
        self.assertAlmostEqual(positive.position[0], 0.475)

        self.mapper.seed(self.identity)
        negative_axes = neutral_axes()
        negative_axes[2] = -1.0
        negative = self.mapper.update(
            self.identity, axes=negative_axes, buttons=buttons()
        )
        self.assertAlmostEqual(negative.position[0], 0.325)

    def test_right_stick_moves_along_base_y_and_z(self) -> None:
        axes = neutral_axes()
        axes[3] = 1.0
        axes[4] = -0.5
        target = self.mapper.update(self.identity, axes=axes, buttons=buttons())
        norm = math.sqrt(1.0 + 0.25)
        self.assertAlmostEqual(target.position[1], 0.075 / norm)
        self.assertAlmostEqual(target.position[2], 0.5 - 0.0375 / norm)

    def test_deadzone_removes_small_motion(self) -> None:
        axes = neutral_axes()
        axes[3] = 0.09
        target = self.mapper.update(self.identity, axes=axes, buttons=buttons())
        self.assertPoseAlmostEqual(target, self.identity)

    def test_bumpers_rotate_about_base_yaw(self) -> None:
        positive = self.mapper.update(
            self.identity, axes=neutral_axes(), buttons=buttons(5)
        )
        self.assertAlmostEqual(positive.orientation[2], math.sin(0.15 / 2.0))
        self.assertAlmostEqual(positive.orientation[3], math.cos(0.15 / 2.0))

        self.mapper.seed(self.identity)
        negative = self.mapper.update(
            self.identity, axes=neutral_axes(), buttons=buttons(4)
        )
        self.assertAlmostEqual(negative.orientation[2], -math.sin(0.15 / 2.0))
        self.assertAlmostEqual(negative.orientation[3], math.cos(0.15 / 2.0))

    def test_active_axis_reanchors_to_latest_measurement(self) -> None:
        axes = neutral_axes()
        axes[3] = 1.0
        self.mapper.update(self.identity, axes=axes, buttons=buttons())
        measured = Pose((0.4, 0.01, 0.5), self.identity.orientation)
        target = self.mapper.update(measured, axes=axes, buttons=buttons())
        self.assertAlmostEqual(target.position[1], 0.085)

    def test_release_latches_realized_axis_once(self) -> None:
        axes = neutral_axes()
        axes[3] = 1.0
        self.mapper.update(self.identity, axes=axes, buttons=buttons())

        released_measurement = Pose((0.4, 0.02, 0.5), self.identity.orientation)
        released = self.mapper.update(
            released_measurement, axes=neutral_axes(), buttons=buttons()
        )
        drifted_measurement = Pose((0.4, 0.03, 0.5), self.identity.orientation)
        held = self.mapper.update(
            drifted_measurement, axes=neutral_axes(), buttons=buttons()
        )
        self.assertAlmostEqual(released.position[1], 0.02)
        self.assertAlmostEqual(held.position[1], 0.02)

    def test_base_frame_rotation_premultiplies_measured_orientation(self) -> None:
        half_yaw = math.pi / 4.0
        measured = Pose(
            self.identity.position,
            (0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw)),
        )
        self.mapper.seed(measured)
        target = self.mapper.update(
            measured, axes=neutral_axes(), buttons=buttons(5)
        )
        expected_yaw = math.pi / 2.0 + 0.15
        self.assertAlmostEqual(target.orientation[2], math.sin(expected_yaw / 2.0))
        self.assertAlmostEqual(target.orientation[3], math.cos(expected_yaw / 2.0))

    def test_hold_and_reseed_drop_old_target(self) -> None:
        axes = neutral_axes()
        axes[3] = 1.0
        self.mapper.update(self.identity, axes=axes, buttons=buttons())
        measured = Pose((0.41, 0.02, 0.49), self.identity.orientation)
        self.assertPoseAlmostEqual(self.mapper.hold(measured), measured)
        self.assertPoseAlmostEqual(
            self.mapper.update(measured, axes=neutral_axes(), buttons=buttons()),
            measured,
        )

    def test_invalid_joy_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Xbox"):
            self.mapper.update(self.identity, axes=[math.nan], buttons=[])
        with self.assertRaisesRegex(ValueError, "buttons"):
            self.mapper.update(self.identity, axes=neutral_axes(), buttons=[2])


if __name__ == "__main__":
    unittest.main()
