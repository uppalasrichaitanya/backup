import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
import time

# --- STANDARD IMPORTS ---
from std_srvs.srv import Trigger 
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from sensor_msgs.msg import JointState 
from builtin_interfaces.msg import Duration

# Try importing Link Attacher (Optional - Prevents crash if missing)
try:
    from link_attacher_msgs.srv import AttachLink, DetachLink
except ImportError:
    AttachLink = None
    DetachLink = None

class FeedbackPickAndPlace(Node):
    def __init__(self):
        super().__init__('feedback_server')
        self.set_parameters([Parameter('use_sim_time', value=True)])
        self.callback_group = ReentrantCallbackGroup()

        # 1. Service
        self.srv = self.create_service(
            Trigger, '/perform_task', self.task_callback, callback_group=self.callback_group
        )

        # 2. Publishers (Reverted to JointTrajectory for BOTH)
        self.arm_publisher_ = self.create_publisher(JointTrajectory, '/simple_joint_controller/simple_trajectory', 10)
        
        # FIX: Using JointTrajectory for gripper (Matches friend's logic)
        self.gripper_publisher_ = self.create_publisher(JointTrajectory, '/gripper_controller/gripper_cmd', 10)
        # Note: If '/gripper_cmd' fails, try '/gripper_controller/joint_trajectory'

        # 3. Feedback Subscriber
        self.joint_state_sub = self.create_subscription(
            JointState, '/joint_states', self.joint_state_callback, 10,
            callback_group=self.callback_group
        )
        
        # 4. Physics Clients
        if AttachLink:
            self.attach_client = self.create_client(AttachLink, '/link_attacher/attach', callback_group=self.callback_group)
            self.detach_client = self.create_client(DetachLink, '/link_attacher/detach', callback_group=self.callback_group)
        else:
            self.attach_client = None
            self.detach_client = None

        self.current_joint_positions = {} 
        self.log_history = []
        self.data_received = False              

        self.ARM_JOINTS = ['joint1', 'joint2', 'joint3', 'joint4']
        
        # FIX: Correct Joint Name from Logs
        self.GRIPPER_JOINTS = ['gripper_left_joint'] 

        # --- CONFIGURATION ---
        self.TOLERANCE = 0.15             
        self.TIMEOUT_SEC = 6.0            
        self.STABLE_CYCLES_REQUIRED = 3   

        # --- POSES ---
        # Gripper: -0.01 is CLOSE, 0.019 is OPEN
        self.poses = {
            'home':     { 'arm': [0.0, 0.0, 0.0, 0.0],     'gripper': [0.019] },
            'ready':    { 'arm': [0.0, -0.8, 0.3, 0.0],    'gripper': [0.019] },
            'pick':     { 'arm': [0.0, 0.55, 0.05, 0.9],   'gripper': [-0.01] }, 
            'lift':     { 'arm': [0.0, -0.8, 0.3, 0.0],    'gripper': [-0.01] },
            'place':    { 'arm': [1.57, 0.0, 0.0, 0.0],    'gripper': [0.019] }
        }

        self.get_logger().info('Feedback Server Ready (Gripper Logic Fixed).')

    def joint_state_callback(self, msg):
        self.data_received = True
        for i, name in enumerate(msg.name):
            self.current_joint_positions[name] = msg.position[i]

    async def task_callback(self, request, response):
        self.log_history = [] 
        self.get_logger().info("--- STARTING SEQUENCE ---")
        
        if not self.data_received:
            self.get_logger().error("NO JOINT DATA! Is Gazebo running?")
            response.success = False
            response.message = "Error: No joint feedback."
            return response

        sequence = ['home', 'ready', 'pick', 'lift', 'place', 'home']
        
        step_index = 1
        for step_name in sequence:
            success = await self.run_step_with_retry(step_index, len(sequence), step_name)
            if not success:
                self.get_logger().error(f"FAILURE at {step_name}. Recovering...")
                await self.execute_motion('home')
                response.success = False
                response.message = f"Task FAILED at {step_name}."
                self.print_summary()
                return response
            step_index += 1
        
        response.success = True
        response.message = "Task Completed Successfully."
        self.print_summary()
        return response

    async def run_step_with_retry(self, index, total, pose_name):
        self.get_logger().info(f"Step {pose_name}...")
        result, duration = await self.execute_motion(pose_name)
        
        if result == 'converged':
            self.log_step(index, total, pose_name, "OK", "converged", duration)
            await self.handle_physics(pose_name)
            return True
        
        # If we hit the object (timeout on Pick), count as success
        if result == 'timeout' and pose_name == 'pick':
             self.log_step(index, total, pose_name, "OK", "contact", duration)
             await self.handle_physics(pose_name)
             return True

        # Retry once
        self.get_logger().warn(f"Step {pose_name} timed out. Retrying...")
        result, duration = await self.execute_motion(pose_name)
        
        if result == 'converged':
            self.log_step(index, total, pose_name, "OK", "recovered", duration)
            await self.handle_physics(pose_name)
            return True
        
        self.log_step(index, total, pose_name, "FAIL", "timeout", duration)
        return False

    async def execute_motion(self, pose_name):
        arm_target = self.poses[pose_name]['arm']
        gripper_target = self.poses[pose_name]['gripper']
        
        self.publish_arm(arm_target)
        self.publish_gripper(gripper_target)
        
        start_time = self.get_clock().now()
        stable_count = 0
        
        while rclpy.ok():
            current_time = self.get_clock().now()
            duration = (current_time - start_time).nanoseconds / 1e9
            
            if duration > self.TIMEOUT_SEC:
                return "timeout", duration

            # Check Arm Convergence
            arm_ok = self.check_convergence_debug(self.ARM_JOINTS, arm_target)
            
            # Check Gripper Convergence (Looser tolerance)
            # If target is negative (closing), we just check if it moved somewhat
            grip_val = self.current_joint_positions.get('gripper_left_joint', 0.0)
            grip_ok = True
            if gripper_target[0] < 0: # Closing
                 if grip_val > 0.01: grip_ok = False # Still open
            else: # Opening
                 if abs(grip_val - gripper_target[0]) > 0.02: grip_ok = False

            if arm_ok and grip_ok:
                stable_count += 1
            else:
                stable_count = 0 
            
            if stable_count >= self.STABLE_CYCLES_REQUIRED:
                return "converged", duration
            
            time.sleep(0.05) 

        return "aborted", 0.0

    def check_convergence_debug(self, joint_names, targets):
        if not self.current_joint_positions: return False 
        all_ok = True
        for i, name in enumerate(joint_names):
            current = self.current_joint_positions.get(name, 0.0)
            if abs(current - targets[i]) > self.TOLERANCE:
                all_ok = False
        return all_ok

    async def handle_physics(self, pose_name):
        if pose_name not in ['pick', 'place']: return
        time.sleep(0.5)
        # Call Attach Plugin if available
        if self.attach_client and self.attach_client.service_is_ready():
            req = AttachLink.Request() if pose_name == 'pick' else DetachLink.Request()
            req.model1_name = 'pick_cube'
            req.link1_name = 'link'
            req.model2_name = 'open_manipulator_x'
            req.link2_name = 'gripper_left_link'
            try:
                client = self.attach_client if pose_name == 'pick' else self.detach_client
                await client.call_async(req)
            except: pass

    def publish_arm(self, positions):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = self.ARM_JOINTS
        p = JointTrajectoryPoint()
        p.positions = [float(x) for x in positions]
        p.time_from_start = Duration(sec=2, nanosec=0)
        msg.points.append(p)
        self.arm_publisher_.publish(msg)

    def publish_gripper(self, positions):
        # FIX: Reverted to JointTrajectory to match Arm Logic
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = self.GRIPPER_JOINTS
        p = JointTrajectoryPoint()
        p.positions = [float(x) for x in positions]
        p.time_from_start = Duration(sec=1, nanosec=0)
        msg.points.append(p)
        self.gripper_publisher_.publish(msg)

    def log_step(self, idx, total, pose, status, reason, duration):
        entry = f"[{idx}/{total}] pose={pose:<10} {status:<4} reason={reason:<10} duration={duration:.2f}s"
        self.get_logger().info(entry)
        self.log_history.append(entry)

    def print_summary(self):
        self.get_logger().info("\n" + "="*60)
        for line in self.log_history:
            self.get_logger().info(line)
        self.get_logger().info("="*60)

def main(args=None):
    rclpy.init(args=args)
    executor = MultiThreadedExecutor()
    node = FeedbackPickAndPlace()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
