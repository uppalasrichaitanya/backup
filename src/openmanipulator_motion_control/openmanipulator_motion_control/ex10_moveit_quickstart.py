import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint

class MoveItQuickstart(Node):
    def __init__(self):
        super().__init__('ex10_moveit_quickstart')
        self.move_group_client = ActionClient(self, MoveGroup, 'move_action')
        # Poses defined in your SRDF
        self.named_poses = ['home', 'ready', 'pick', 'place', 'home']

    def send_goal(self, pose_name):
        self.get_logger().info(f'Planning to: {pose_name}...')
        self.move_group_client.wait_for_server()

        goal = MoveGroup.Goal()
        goal.request.group_name = 'arm'
        goal.request.allowed_planning_time = 5.0
        goal.request.num_planning_attempts = 10
        goal.request.max_velocity_scaling_factor = 0.5
        goal.request.max_acceleration_scaling_factor = 0.5

        # Create a constraint that matches the Named Target
        # (This relies on MoveIt knowing what "home" means from the SRDF)
        # Note: Direct named target support via Action Client is tricky in some versions,
        # so we rely on the constraints list or manual joint targets.
        # Here we manually approximate if SRDF lookup is complex in pure python.
        
        # DEFINING TARGETS MANUALLY TO ENSURE IT WORKS WITHOUT SRDF LOOKUP ISSUES
        targets = {
            'home':  [0.0, -1.0, 0.3, 0.7],
            'ready': [0.0, -0.8, 0.0, 0.0],
            'pick':  [0.0, 0.5, 0.0, 0.9],
            'place': [1.57, 0.0, 0.0, 0.0]
        }
        
        vals = targets.get(pose_name, [0.0, 0.0, 0.0, 0.0])
        
        c = Constraints()
        c.name = pose_name
        for i, joint_name in enumerate(['joint1', 'joint2', 'joint3', 'joint4']):
            jc = JointConstraint()
            jc.joint_name = joint_name
            jc.position = vals[i]
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            c.joint_constraints.append(jc)
            
        goal.request.goal_constraints.append(c)

        future = self.move_group_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        res = future.result()
        
        if not res.accepted:
            self.get_logger().error('Goal Rejected!')
            return

        res_future = res.get_result_async()
        rclpy.spin_until_future_complete(self, res_future)
        result = res_future.result().result
        
        if result.error_code.val == 1:
            self.get_logger().info(f'Success: Reached {pose_name}')
        else:
            self.get_logger().error(f'Failed: Error Code {result.error_code.val}')

def main(args=None):
    rclpy.init(args=args)
    node = MoveItQuickstart()
    try:
        for pose in node.named_poses:
            node.send_goal(pose)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
