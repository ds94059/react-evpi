from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rviz2',
            namespace='rviz',
            executable='rviz2',
            name='rviz2'
        )
    ])
