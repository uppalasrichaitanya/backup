import time
import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Duration
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from std_msgs.msg import Float64MultiArray
from std_srvs.srv import Trigger

class PickAndPlaceServer(Node):
    def __init__(self):
        super().__init__('pick_and_place_server')
        self.arm_pub = self.create_publisher(JointTrajectory, '/simple_joint_controller/simple_trajectory', 10)
        self.grip_pub = self.create_publisher(Float64MultiArray, '/gripper_controller/commands', 10)
        self.srv = self.create_service(Trigger, 'pick_and_place', self.execute_callback)
        self.get_logger().info('Exercise 7: Pick & Place Server Ready.')

    def move_arm(self, pose, sec=2.0):
        msg = JointTrajectory()
        msg.joint_names = ["joint1", "joint2", "joint3", "joint4"]
        point = JointTrajectoryPoint()
        point.positions = pose
        point.time_from_start = Duration(sec=int(sec), nanosec=0)
        msg.points.append(point)
        self.arm_pub.publish(msg)

    def move_gripper(self, open=True):
        msg = Float64MultiArray()
        # Tighter close command (-0.01) to force grip
        msg.data = [0.01] if open else [-0.01]
        self.grip_pub.publish(msg)

    def execute_callback(self, request, response):
        self.get_logger().info('Starting Sequence...')

        # Updated Poses for Closer Cube (0.2m)
        home = [0.0, 0.0, 0.0, 0.0]
        ready = [0.0, 0.2, 0.0, 1.3]    # Prepare above
        
        # Exact pose for x=0.2m cube
        pick = [0.0, 0.6, 0.1, 0.85]    
        
        place = [1.57, 0.0, 0.0, 0.0] 

        # 1. Home
        self.move_arm(home)
        self.move_gripper(open=True) 
        time.sleep(2.5)

        # 2. Ready
        self.move_arm(ready)
        time.sleep(2.5)

        # 3. Pick (Descend)
        self.get_logger().info('Picking...')
        self.move_arm(pick, sec=3.0)
        time.sleep(3.5)

        # 4. Grab
        self.get_logger().info('Closing Gripper...')
        self.move_gripper(open=False)
        time.sleep(1.5)

        # 5. Lift
        self.get_logger().info('Lifting...')
        self.move_arm(ready)
        time.sleep(2.5)

        # 6. Place
        self.move_arm(place, sec=3.0)
        time.sleep(3.5)

        # 7. Release
        self.move_gripper(open=True)
        time.sleep(1.0)

        # 8. Home
        self.move_arm(home)
        time.sleep(2.5)

        response.success = True
        response.message = "Task Complete"
        return response

def main(args=None):
    rclpy.init(args=args)
    node = PickAndPlaceServer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
