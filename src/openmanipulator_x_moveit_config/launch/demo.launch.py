import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import yaml

def generate_launch_description():
    # --- 1. SETUP PATHS ---
    omx_description_pkg = get_package_share_directory('open_manipulator_description')
    moveit_config_pkg = get_package_share_directory('openmanipulator_x_moveit_config')
    
    xacro_file = os.path.join(omx_description_pkg, 'urdf', 'open_manipulator_x', 'open_manipulator_x.urdf.xacro')
    srdf_file = os.path.join(moveit_config_pkg, 'config', 'open_manipulator_x.srdf')
    rviz_config = os.path.join(moveit_config_pkg, 'config', 'moveit.rviz')
    kinematics_file = os.path.join(moveit_config_pkg, 'config', 'kinematics.yaml')

    # --- 2. LOAD FILES ---
    doc = xacro.process_file(xacro_file)
    robot_desc = doc.toxml()
    
    with open(srdf_file, 'r') as f:
        robot_srdf = f.read()
        
    with open(kinematics_file, 'r') as f:
        kinematics_config = yaml.safe_load(f)

    # --- 3. DEFINE PARAMETERS (FLAT DOT NOTATION) ---
    # This explicitly sets the OMPL parameters without relying on nesting
    moveit_params = {
        'robot_description': robot_desc,
        'robot_description_semantic': robot_srdf,
        'robot_description_kinematics': kinematics_config,
        'use_sim_time': False,
        
        # PLANNER CONFIGURATION
        'planning_pipelines': ['ompl'],
        'ompl.planning_plugin': 'ompl_interface/OMPLPlanner',
        'ompl.request_adapters': [
            'default_planner_request_adapters/AddTimeOptimalParameterization',
            'default_planner_request_adapters/ResolveConstraintFrames',
            'default_planner_request_adapters/FixWorkspaceBounds',
            'default_planner_request_adapters/FixStartStateBounds',
            'default_planner_request_adapters/FixStartStateCollision',
            'default_planner_request_adapters/FixStartStatePathConstraints',
        ],
        'ompl.start_state_max_bounds_error': 0.1,
    }

    # --- 4. DEFINE NODES ---
    
    # Move Group (The Brain)
    run_move_group = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[moveit_params]
    )

    # RViz (The Visuals)
    run_rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        arguments=['-d', rviz_config],
        parameters=[
            {'robot_description': robot_desc},
            {'robot_description_semantic': robot_srdf},
            {'robot_description_kinematics': kinematics_config},
            # Pass planner config to RViz too
            {'planning_pipelines': ['ompl']},
            {'ompl.planning_plugin': 'ompl_interface/OMPLPlanner'},
        ]
    )

    # Robot State Publisher
    run_rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[{'robot_description': robot_desc}]
    )

    # Static TF
    run_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'world', 'link1']
    )

    return LaunchDescription([
        run_tf,
        run_rsp,
        run_move_group,
        run_rviz
    ])
