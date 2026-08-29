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
                "-0.074592",
                "--y",
                "0.0638447",
                "--z",
                "0.0337364",
                "--qx",
                "-0.180003",
                "--qy",
                "-0.40466",
                "--qz",
                "-0.34059",
                "--qw",
                "0.829366",
                # "--roll",
                # "2.38451",
                # "--pitch",
                # "-2.5609",
                # "--yaw",
                # "2.1257",
            ],
        ),
    ]
    return LaunchDescription(nodes)
