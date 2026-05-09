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
                "-0.52211",
                "--y",
                "-0.326343",
                "--z",
                "1.04177",
                "--qx",
                "0.0103967",
                "--qy",
                "0.285458",
                "--qz",
                "0.170772",
                "--qw",
                "0.942997",
                # "--roll",
                # "3.04878",
                # "--pitch",
                # "2.56887",
                # "--yaw",
                # "-2.75594",
            ],
        ),
    ]
    return LaunchDescription(nodes)
