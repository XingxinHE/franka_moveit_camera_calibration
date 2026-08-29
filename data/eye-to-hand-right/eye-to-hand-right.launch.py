""" Static transform publisher acquired via MoveIt 2 hand-eye calibration """
""" EYE-TO-HAND: fr3_link0 -> robot0_agentview_right_link """
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
                "fr3_link0",
                "--child-frame-id",
                "robot0_agentview_right_link",
                "--x",
                "-0.189686",
                "--y",
                "-0.677483",
                "--z",
                "0.798463",
                "--qx",
                "-0.0748766",
                "--qy",
                "0.21469",
                "--qz",
                "0.393789",
                "--qw",
                "0.890635",
                # "--roll",
                # "2.81624",
                # "--pitch",
                # "2.81222",
                # "--yaw",
                # "-2.25445",
            ],
        ),
    ]
    return LaunchDescription(nodes)
