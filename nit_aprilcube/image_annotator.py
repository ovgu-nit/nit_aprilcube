import cv2
import rclpy
import numpy as np
import time

import rclpy.node
import sensor_msgs.msg
import apriltag_msgs.msg
import cv_bridge
import message_filters


class ImageAnnotator(rclpy.node.Node):

    def __init__(self):
        super().__init__('image_annotator')

        # --- Communication ---
        self.sub_input_image = message_filters.Subscriber(
            self, 
            msg_type=sensor_msgs.msg.Image, 
            topic='image_raw'
        )
        self.sub_detections = message_filters.Subscriber(
            self, 
            msg_type=apriltag_msgs.msg.AprilTagDetectionArray,
            topic='detections'
        )
        self.sync = message_filters.ApproximateTimeSynchronizer(
            [self.sub_input_image, self.sub_detections],
            queue_size=10,
            slop=0.05,
            allow_headerless=False,
        )
        self.sync.registerCallback(self.annotate_image_callback)

        self.pub_output_image = self.create_publisher(
            msg_type=sensor_msgs.msg.Image, 
            topic='image_annotated', 
            qos_profile=10
        )


        # --- Image Processing Utility ---
        self.bridge = cv_bridge.CvBridge()

        # --- Starvation Watchdog ---
        self._last_stamp = time.time()
        self._warned_starvation = False
        self.create_timer(5.0, self._starvation_watchdog)
        
        # --- Logging ---
        self.get_logger().info('ImageAnnotator initialized: synchronizing image_raw and detections, publishing annotated image to image_annotated.')

    def _starvation_watchdog(self):
        dt = time.time() - self._last_stamp
        if dt > 4.0 and not self._warned_starvation:
            self.get_logger().warning(
                f'No synchronized data for {dt:.0f}s on topics:\n'
                '  image:      image_raw\n'
                '  detections: detections\n'
                'Check the YAML setup or launch overrides.')
            self._warned_starvation = True

    def annotate_image_callback(
            self, 
            image_msg: sensor_msgs.msg.Image, 
            detection_msg: apriltag_msgs.msg.AprilTagDetectionArray
    ):
        self._last_stamp = time.time()
        self._warned_starvation = False

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
        annotated_msg.header.stamp = image_msg.header.stamp
        annotated_msg.header.frame_id = image_msg.header.frame_id
        self.pub_output_image.publish(annotated_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ImageAnnotator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

if __name__ == '__main__':
    main()
