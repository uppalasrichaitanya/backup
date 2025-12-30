import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
import time
from example_interfaces.action import Fibonacci
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from sensor_msgs.msg import JointState
from builtin_interfaces.msg import Duration

class ActionTaskServer(Node):
    def __init__(self):
        super().__init__('action_task_server')
        self.callback_group = ReentrantCallbackGroup()
        
        self._action_server = ActionServer(
            self, Fibonacci, 'pick_place_action', self.execute_callback,
            callback_group=self.callback_group,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback
        )

        self.arm_publisher_ = self.create_publisher(JointTrajectory, '/simple_joint_controller/simple_trajectory', 10)
        self.gripper_publisher_ = self.create_publisher(JointTrajectory, '/gripper_controller/gripper_cmd', 10)
        self.joint_state_sub = self.create_subscription(JointState, '/joint_states', self.joint_state_callback, 10, callback_group=self.callback_group)

        self.current_joint_positions = {}
        self.ARM_JOINTS = ['joint1', 'joint2', 'joint3', 'joint4']
        self.GRIPPER_JOINTS = ['gripper_left_joint']
        
        self.TOLERANCE = 0.15             
        self.TIMEOUT_SEC = 6.0            
        
        self.poses = {
            'home':     { 'arm': [0.0, 0.0, 0.0, 0.0],     'gripper': [0.019] },
            'ready':    { 'arm': [0.0, -0.8, 0.3, 0.0],    'gripper': [0.019] },
            # UPDATE: Squeeze tighter (-0.02) to force physics grip
            'pick':     { 'arm': [0.0, 0.55, 0.05, 0.9],   'gripper': [-0.02] }, 
            'lift':     { 'arm': [0.0, -0.8, 0.3, 0.0],    'gripper': [-0.02] },
            'place':    { 'arm': [1.57, 0.0, 0.0, 0.0],    'gripper': [0.019] }
        }
        
        self.step_map = ['home', 'ready', 'pick', 'lift', 'place', 'home']
        self.get_logger().info('Action Task Server Ready (Featherweight Physics Mode).')

    def joint_state_callback(self, msg):
        for i, name in enumerate(msg.name):
            self.current_joint_positions[name] = msg.position[i]

    def goal_callback(self, goal_request): return GoalResponse.ACCEPT
    def cancel_callback(self, goal_handle): return CancelResponse.ACCEPT

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Executing Goal...')
        feedback_msg = Fibonacci.Feedback()
        feedback_msg.sequence = []
        result = Fibonacci.Result()
        step_id = 0
        
        for step_name in self.step_map:
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                return result
            
            step_id += 1
            feedback_msg.sequence.append(step_id)
            goal_handle.publish_feedback(feedback_msg)
            self.get_logger().info(f'Step {step_id}: {step_name}')

            success = await self.move_to_pose(step_name, goal_handle)
            if not success:
                goal_handle.abort()
                return result

            # Wait longer after pick to let physics settle
            if step_name == 'pick': time.sleep(1.5)
            else: time.sleep(0.5)

        goal_handle.succeed()
        result.sequence = feedback_msg.sequence
        return result

    async def move_to_pose(self, pose_name, goal_handle=None):
        arm_target = self.poses[pose_name]['arm']
        gripper_target = self.poses[pose_name]['gripper']
        self.publish_arm(arm_target)
        self.publish_gripper(gripper_target)
        
        start_time = self.get_clock().now()
        while rclpy.ok():
            if goal_handle and goal_handle.is_cancel_requested: return False 
            duration = (self.get_clock().now() - start_time).nanoseconds / 1e9
            if duration > self.TIMEOUT_SEC:
                if pose_name in ['pick', 'place']: return True 
                return False
            if self.check_convergence(self.ARM_JOINTS, arm_target, self.TOLERANCE): return True 
            time.sleep(0.1)
        return False

    def check_convergence(self, joints, targets, tolerance):
        if not self.current_joint_positions: return False
        for i, name in enumerate(joints):
            if name not in self.current_joint_positions: continue
            if abs(self.current_joint_positions[name] - targets[i]) > tolerance: return False
        return True

    def publish_arm(self, pos):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = self.ARM_JOINTS
        p = JointTrajectoryPoint(); p.positions = [float(x) for x in pos]; p.time_from_start = Duration(sec=2, nanosec=0)
        msg.points.append(p); self.arm_publisher_.publish(msg)

    def publish_gripper(self, pos):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = self.GRIPPER_JOINTS
        p = JointTrajectoryPoint(); p.positions = [float(x) for x in pos]; p.time_from_start = Duration(sec=1, nanosec=0)
        msg.points.append(p); self.gripper_publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    executor = MultiThreadedExecutor()
    node = ActionTaskServer()
    executor.add_node(node)
    try: executor.spin()
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.shutdown()

if __name__ == '__main__': main()
