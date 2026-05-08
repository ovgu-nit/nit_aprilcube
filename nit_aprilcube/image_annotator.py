import cv2
import rclpy
import numpy as np

from rclpy.node import Node
from sensor_msgs.msg import Image
from apriltag_msgs.msg import AprilTagDetectionArray
from cv_bridge import CvBridge
import message_filters


class ImageAnnotator(Node):

    def __init__(self):
        super().__init__('image_annotator')

        self.bridge = CvBridge()

        # Publisher for /image_annotated
        self.publisher = self.create_publisher(Image, '/image_annotated', 10)

        # Subscribers for /image_raw and /detections
        self.image_sub = message_filters.Subscriber(self, Image, '/image_raw')
        self.detections_sub = message_filters.Subscriber(self, AprilTagDetectionArray, '/detections')

        # Synchronize the two topics
        self.sync = message_filters.ApproximateTimeSynchronizer(
            [self.image_sub, self.detections_sub],
            queue_size=10,
            slop=0.05, # 30 Hz -> 33ms, so 50ms should be safe
            allow_headerless=False,
        )
        self.sync.registerCallback(self.synced_callback)

        self.get_logger().info('ImageAnnotator initialized: synchronizing /image_raw and /detections')

    def synced_callback(self, image_msg: Image, detection_msg: AprilTagDetectionArray):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().warning(f'Failed to convert image to bgr8: {exc}')
            cv_image = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding='passthrough')
            if cv_image.ndim == 2:
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2BGR)
            elif cv_image.ndim == 3 and cv_image.shape[2] == 1:
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2BGR)
            elif cv_image.ndim == 3 and cv_image.shape[2] == 4:
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGRA2BGR)

        for detection in detection_msg.detections:
            center = (int(round(detection.centre.x)), int(round(detection.centre.y)))

            # Draw a circle at the center of the tag and put the tag ID as text
            cv2.circle(cv_image, center, radius=5, color=(0, 255, 0), thickness=-1)
            cv2.putText(
                cv_image, #image
                str(detection.id), #text
                (center[0] + 6, center[1] - 6), # origin, bottom-left corner of text
                cv2.FONT_HERSHEY_SIMPLEX, #font
                0.5, #font scale
                (0, 255, 0), #color
                1, #thickness
                cv2.LINE_AA, #line type
            )

            # corners are typically in detection.corners (4 points)
            pts = np.array([[int(corner.x), int(corner.y)] for corner in detection.corners], np.int32).reshape((-1, 1, 2))
            cv2.polylines(cv_image, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

        annotated_msg = self.bridge.cv2_to_imgmsg(cv_image, encoding='bgr8')
        annotated_msg.header = image_msg.header
        self.publisher.publish(annotated_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ImageAnnotator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()



if __name__ == '__main__':
    main()
