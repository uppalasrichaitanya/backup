import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from example_interfaces.action import Fibonacci # Using Standard Action
import time

class ActionTaskClient(Node):
    def __init__(self):
        super().__init__('action_task_client')
        # Updated to use Fibonacci standard action
        self._action_client = ActionClient(self, Fibonacci, 'pick_place_action')
        
        # Helper to make logs look nice (Number -> Name)
        self.step_map = ['Home', 'Ready', 'Pick', 'Lift', 'Place', 'Home']

    def send_goal(self):
        self.get_logger().info('Waiting for Action Server...')
        self._action_client.wait_for_server()

        goal_msg = Fibonacci.Goal()
        goal_msg.order = 1 # Dummy value to start the task

        self.get_logger().info('Sending Goal... (Press Ctrl+C to CANCEL Task)')
        
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected :(')
            return

        self.get_logger().info('Goal accepted! Executing...')
        self._goal_handle = goal_handle
        
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        # Translate the Number (sequence) back to a Name
        seq = feedback_msg.feedback.sequence
        if seq:
            step_id = seq[-1]
            if 0 < step_id <= len(self.step_map):
                step_name = self.step_map[step_id-1]
                self.get_logger().info(f'[Feedback] Step {step_id}: {step_name}')

    def get_result_callback(self, future):
        result = future.result().result
        # The standard result is just a list of numbers, so we check if it's not empty
        if result.sequence:
            self.get_logger().info(f'Result: Task Finished! Steps Completed: {len(result.sequence)}')
        else:
            self.get_logger().info('Result: Task Failed or Empty.')
            
        # We can shutdown cleanly now
        raise SystemExit

    def cancel_goal(self):
        """This function runs when you press Ctrl+C"""
        if hasattr(self, '_goal_handle'):
            self.get_logger().warn('Canceling Goal...')
            future = self._goal_handle.cancel_goal_async()
            rclpy.spin_until_future_complete(self, future)
            self.get_logger().info('Cancel request sent.')

def main(args=None):
    rclpy.init(args=args)
    action_client = ActionTaskClient()
    action_client.send_goal()

    try:
        rclpy.spin(action_client)
    except KeyboardInterrupt:
        # 1. Catch Ctrl+C
        print("\nCtrl+C detected!")
        # 2. Send the Cancel Request
        action_client.cancel_goal()
        # 3. Wait briefly for the server to process it
        time.sleep(1.0)
    except SystemExit:
        pass
    
    action_client.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
