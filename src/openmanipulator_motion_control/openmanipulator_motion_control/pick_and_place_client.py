import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
import sys

class PickAndPlaceClient(Node):
    def __init__(self):
        super().__init__('pick_and_place_client')
        self.cli = self.create_client(Trigger, 'pick_and_place')
        
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for Pick & Place Server...')
            
        self.req = Trigger.Request()

    def send_request(self):
        print("Requesting Pick & Place Task...")
        future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

def main(args=None):
    rclpy.init(args=args)
    client = PickAndPlaceClient()
    response = client.send_request()
    print(f"Result: {response.message}")
    client.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
