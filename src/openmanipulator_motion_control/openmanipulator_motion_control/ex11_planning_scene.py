import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import PlanningScene, CollisionObject, AttachedCollisionObject, Constraints, JointConstraint
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose
import time

class PlanningSceneDemo(Node):
    def __init__(self):
        super().__init__('ex11_planning_scene')
        self.scene_pub = self.create_publisher(PlanningScene, '/planning_scene', 10)
        self.move_group_client = ActionClient(self, MoveGroup, 'move_action')
        time.sleep(1.0)
        self.setup_scene()

    def setup_scene(self):
        self.get_logger().info('Adding Table and Cube...')
        scene_msg = PlanningScene()
        scene_msg.is_diff = True
        
        # 1. Table
        table = CollisionObject()
        table.header.frame_id = 'world'
        table.id = 'table'
        prim = SolidPrimitive()
        prim.type = SolidPrimitive.BOX
        prim.dimensions = [1.0, 1.0, 0.05]
        pose = Pose(); pose.position.z = -0.05
        table.primitives.append(prim); table.primitive_poses.append(pose)
        table.operation = CollisionObject.ADD
        
        # 2. Cube
        cube = CollisionObject()
        cube.header.frame_id = 'world'
        cube.id = 'pick_cube'
        prim_cube = SolidPrimitive()
        prim_cube.type = SolidPrimitive.BOX
        prim_cube.dimensions = [0.04, 0.04, 0.04]
        pose_cube = Pose(); pose_cube.position.x = 0.24; pose_cube.position.z = 0.02
        cube.primitives.append(prim_cube); cube.primitive_poses.append(pose_cube)
        cube.operation = CollisionObject.ADD
        
        scene_msg.world.collision_objects = [table, cube]
        self.scene_pub.publish(scene_msg)
        self.get_logger().info('Scene Published.')

    def modify_attachment(self, attach=True):
        scene_msg = PlanningScene()
        scene_msg.is_diff = True
        aco = AttachedCollisionObject()
        aco.link_name = 'gripper_left_link'
        aco.object.header.frame_id = 'world'
        aco.object.id = 'pick_cube'
        aco.object.operation = CollisionObject.ADD if attach else CollisionObject.REMOVE
        
        if not attach:
            # Re-add to world when detaching
            detach_obj = CollisionObject()
            detach_obj.header.frame_id = 'world'
            detach_obj.id = 'pick_cube'
            detach_obj.operation = CollisionObject.ADD
            scene_msg.world.collision_objects.append(detach_obj)

        scene_msg.robot_state.attached_collision_objects.append(aco)
        self.scene_pub.publish(scene_msg)
        self.get_logger().info(f'Object {"Attached" if attach else "Detached"}.')

    def move_arm(self, target_name, joints):
        self.get_logger().info(f'Moving to {target_name}...')
        goal = MoveGroup.Goal()
        goal.request.group_name = 'arm'
        goal.request.max_velocity_scaling_factor = 0.5
        
        c = Constraints()
        c.name = target_name
        for i, name in enumerate(['joint1', 'joint2', 'joint3', 'joint4']):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = joints[i]
            jc.tolerance_above = 0.01; jc.tolerance_below = 0.01; jc.weight = 1.0
            c.joint_constraints.append(jc)
        goal.request.goal_constraints.append(c)
        
        self.move_group_client.wait_for_server()
        future = self.move_group_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)
        return True

def main(args=None):
    rclpy.init(args=args)
    node = PlanningSceneDemo()
    
    # 1. Ready
    node.move_arm('ready', [0.0, -0.8, 0.0, 0.0])
    
    # 2. Pick (Approach)
    node.move_arm('pick', [0.0, 0.5, 0.0, 0.9])
    
    # 3. ATTACH (Logical Grasp)
    node.modify_attachment(attach=True)
    time.sleep(1.0)
    
    # 4. Place
    node.move_arm('place', [1.57, 0.0, 0.0, 0.0])
    
    # 5. DETACH
    node.modify_attachment(attach=False)
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
