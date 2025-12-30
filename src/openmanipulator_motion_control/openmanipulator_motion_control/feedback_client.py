import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger

class FeedbackClient(Node):
    def __init__(self):
        super().__init__('feedback_client')
        self.client = self.create_client(Trigger, '/perform_task')
        
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for Feedback Server...')
        
        self.get_logger().info('Connected. Ready to trigger task.')

    def send_trigger(self):
        request = Trigger.Request()
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

def main(args=None):
    rclpy.init(args=args)
    client = FeedbackClient()

    try:
        while True:
            cmd = input("\nType 'task' to start, or 'quit' to exit: ").strip().lower()
            if cmd == 'quit':
                break
            if cmd == 'task':
                print("Sending trigger...")
                res = client.send_trigger()
                if res.success:
                    print(f"SUCCESS: {res.message}")
                else:
                    print(f"FAILED: {res.message}")
            else:
                print("Invalid command.")
    except KeyboardInterrupt:
        pass
    finally:
        client.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
