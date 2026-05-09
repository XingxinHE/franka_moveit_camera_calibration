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
                "-0.545561",
                "--y",
                "0.284255",
                "--z",
                "1.06165",
                "--qx",
                "0.135788",
                "--qy",
                "0.255555",
                "--qz",
                "-0.203395",
                "--qw",
                "0.935352",
                # "--roll",
                # "0.406096",
                # "--pitch",
                # "0.436566",
                # "--yaw",
                # "-0.519514",
            ],
        ),
    ]
    return LaunchDescription(nodes)
