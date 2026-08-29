""" Static transform publisher acquired via MoveIt 2 hand-eye calibration """
""" EYE-TO-HAND: fr3_link0 -> robot0_agentview_left_link """
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
                "robot0_agentview_left_link",
                "--x",
                "-0.238565",
                "--y",
                "0.61678",
                "--z",
                "0.653357",
                "--qx",
                "0.0452855",
                "--qy",
                "0.114193",
                "--qz",
                "-0.362752",
                "--qw",
                "0.923753",
                # "--roll",
                # "0.170037",
                # "--pitch",
                # "0.179072",
                # "--yaw",
                # "-0.763686",
            ],
        ),
    ]
    return LaunchDescription(nodes)
