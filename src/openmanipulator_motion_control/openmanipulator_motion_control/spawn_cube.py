import os
import rclpy
from rclpy.node import Node

def main(args=None):
    rclpy.init(args=args)
    node = Node('cube_spawner')
    
    # XML for High-Friction Red Cube
    cube_xml = """<?xml version='1.0'?>
    <sdf version='1.6'>
      <model name='pick_cube'>
        <pose>0.20 0.0 0.015 0 0 0</pose>
        <link name='link'>
          <inertial>
            <mass>0.02</mass>
            <inertia>
              <ixx>0.0001</ixx><ixy>0</ixy><ixz>0</ixz>
              <iyy>0.0001</iyy><iyz>0</iyz>
              <izz>0.0001</izz>
            </inertia>
          </inertial>
          <collision name='collision'>
            <geometry>
              <box>
                <size>0.025 0.025 0.025</size>
              </box>
            </geometry>
            <surface>
              <friction>
                <ode>
                  <mu>1000.0</mu>
                  <mu2>1000.0</mu2>
                </ode>
              </friction>
            </surface>
          </collision>
          <visual name='visual'>
            <geometry>
              <box>
                <size>0.025 0.025 0.025</size>
              </box>
            </geometry>
            <material>
              <ambient>1 0 0 1</ambient>
              <diffuse>1 0 0 1</diffuse>
            </material>
          </visual>
        </link>
      </model>
    </sdf>
    """
    
    temp_file = '/tmp/pick_cube.sdf'
    with open(temp_file, 'w') as f:
        f.write(cube_xml)

    node.get_logger().info("Spawning Sticky Cube in 'empty' world...")
    
    # COMMAND UPDATE: Added '-world empty' to target your specific simulation
    cmd = f"ros2 run ros_gz_sim create -world empty -name pick_cube -file {temp_file} -z 0.02"
    os.system(cmd)
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
