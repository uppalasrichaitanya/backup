from setuptools import setup

package_name = 'openmanipulator_motion_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # I removed the broken 'world' and 'launch' lines here to fix the build
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='ubuntu@todo.todo',
    description='OpenMANIPULATOR-X Exercises',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Previous Exercises
            'mover_node = openmanipulator_motion_control.mover_node:main',
            'interactive_mover = openmanipulator_motion_control.interactive_mover:main',
            'service_server = openmanipulator_motion_control.service_server:main',
            'service_client = openmanipulator_motion_control.service_client:main',
            'pose_server = openmanipulator_motion_control.pose_server:main',
            'pose_client = openmanipulator_motion_control.pose_client:main',
            'spawn_cube = openmanipulator_motion_control.spawn_cube:main',
            'pick_and_place_server = openmanipulator_motion_control.pick_and_place_server:main',
            'pick_and_place_client = openmanipulator_motion_control.pick_and_place_client:main',
            'task_server = openmanipulator_motion_control.task_server:main',
            'task_client = openmanipulator_motion_control.task_client:main',
            'feedback_server = openmanipulator_motion_control.feedback_server:main',
            'feedback_client = openmanipulator_motion_control.feedback_client:main',
            'action_server = openmanipulator_motion_control.action_server:main',
            'action_client = openmanipulator_motion_control.action_client:main',

            # NEW: MoveIt Exercises
            'ex10_moveit_quickstart = openmanipulator_motion_control.ex10_moveit_quickstart:main',
            'ex11_planning_scene = openmanipulator_motion_control.ex11_planning_scene:main',
        ],
    },
)
