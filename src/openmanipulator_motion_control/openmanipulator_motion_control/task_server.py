import time
import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Duration
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from std_msgs.msg import Float64MultiArray
from std_srvs.srv import Trigger

class TaskServer(Node):
    def __init__(self):
        super().__init__('task_server')
        
        # 1. Arm Publisher (Trajectory)
        self.arm_pub = self.create_publisher(JointTrajectory, '/simple_joint_controller/simple_trajectory', 10)
        
        # 2. Gripper Publisher (Position)
        # Note: We use Float64MultiArray because the controller expects a list of values
        self.grip_pub = self.create_publisher(Float64MultiArray, '/gripper_controller/commands', 10)
        
        self.srv = self.create_service(Trigger, 'perform_task', self.task_callback)
        self.get_logger().info('Task Server Ready (Arm + Gripper).')

    def move_arm(self, pose_list, duration_sec=2.0):
        msg = JointTrajectory()
        msg.joint_names = ["joint1", "joint2", "joint3", "joint4"]
        point = JointTrajectoryPoint()
        point.positions = pose_list
        point.time_from_start = Duration(sec=int(duration_sec), nanosec=0)
        msg.points.append(point)
        self.arm_pub.publish(msg)

    def move_gripper(self, state):
        msg = Float64MultiArray()
        if state == "OPEN":
            msg.data = [0.01]  # Open (positive value)
        elif state == "CLOSE":
            msg.data = [-0.01] # Close (negative/zero value)
        self.grip_pub.publish(msg)

    def task_callback(self, request, response):
        self.get_logger().info('Starting Pick and Place Sequence...')

        # Sequence: (Action Type, Data, Delay, Description)
        steps = [
            ('GRIP', 'OPEN', 1.0, 'Opening Gripper'),
            ('ARM',  [0.0, 0.0, 0.0, 0.0],  2.0, 'Home'),
            ('ARM',  [0.0, -0.8, 0.3, 0.0], 2.0, 'Ready (Up)'),
            ('ARM',  [0.0, 0.45, 0.7, 0.0], 3.0, 'Picking (Down)'), # Precision move
            ('GRIP', 'CLOSE', 2.0, 'Closing Gripper'),
            ('ARM',  [0.0, -0.8, 0.3, 0.0], 2.0, 'Lifting'),
            ('ARM',  [1.5, 0.0, 0.0, 0.0],  3.0, 'Placing (Rotate)'),
            ('GRIP', 'OPEN', 1.0, 'Releasing'),
            ('ARM',  [0.0, 0.0, 0.0, 0.0],  2.0, 'Home')
        ]

        for action, data, delay, desc in steps:
            self.get_logger().info(f'>> {desc}')
            if action == 'ARM':
                self.move_arm(data, duration_sec=delay)
            elif action == 'GRIP':
                self.move_gripper(data)
            time.sleep(delay)

        response.success = True
        response.message = "Task Completed!"
        return response

def main(args=None):
    rclpy.init(args=args)
    node = TaskServer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
