"""
Tag Printer (for Webcam Demo)

Subscribes to the AprilTag detections (/detections) and prints the pixel coordinates and the tag label. Easier to read than just echoing to the /detection topic.
"""

import rclpy
from rclpy.node import Node

from apriltag_msgs.msg import AprilTagDetectionArray

class TagPrinter(Node):

    def __init__(self):
        super().__init__(node_name="tag_printer")
        self.subscription = self.create_subscription(
            msg_type=AprilTagDetectionArray,
            topic='/detections',
            callback=self.detection_callback,
            qos_profile=10 # default: reliable, but not best effort)
        )
    
    def detection_callback(self, msg: AprilTagDetectionArray):
        n_detections = len(msg.detections)
        #self.get_logger().info(
        #    f'#detections: {n_detections}'
        #)
        self.get_logger().info(
            f'n={n_detections} [' + ' ,'.join([
                f'{d.id:2.0f}@({d.centre.x:3.0f},{d.centre.y:3.0f})' for d in msg.detections
            ]) + ']'
        )


def main(args=None):
    rclpy.init(args=args)
    node = TagPrinter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()





if __name__ == '__main__':
    main()
