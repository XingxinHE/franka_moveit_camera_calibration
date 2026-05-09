""" Static transform publisher acquired via MoveIt 2 hand-eye calibration """
""" EYE-IN-HAND: fr3_link8 -> robot0_eye_in_hand_link """
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    nodes = [
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            output="log",
            arguments=[
                "--frame-id",
                "fr3_link8",
                "--child-frame-id",
                "robot0_eye_in_hand_link",
                "--x",
                "0.0593266",
                "--y",
                "-0.0446972",
                "--z",
                "0.0196889",
                "--qx",
                "0.413819",
                "--qy",
                "-0.189952",
                "--qz",
                "0.81681",
                "--qw",
                "0.354251",
                # "--roll",
                # "0.800671",
                # "--pitch",
                # "0.572151",
                # "--yaw",
                # "2.07548",
            ],
        ),
    ]
    return LaunchDescription(nodes)
