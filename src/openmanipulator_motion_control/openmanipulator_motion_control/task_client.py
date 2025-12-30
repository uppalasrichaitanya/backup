import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
import sys

class TaskClient(Node):
    def __init__(self):
        super().__init__('task_client')
        self.cli = self.create_client(Trigger, 'perform_task')
        
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for Task Server...')
            
        self.req = Trigger.Request()

    def send_request(self):
        print("Sending Task Request...")
        future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

def main(args=None):
    rclpy.init(args=args)
    client = TaskClient()
    response = client.send_request()
    print(f"Task Result: {response.message}")
    client.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
