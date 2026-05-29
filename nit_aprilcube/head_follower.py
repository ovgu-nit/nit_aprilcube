#!/usr/bin/env python3
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data, qos_profile_system_default
from rclpy.wait_for_message import wait_for_message

import apriltag_msgs.msg
import trajectory_msgs.msg
import sensor_msgs.msg


class HeadFollower(Node):

    def __init__(self):
        super().__init__('head_follower')

        self.declare_parameters(
            namespace='',
            parameters=[
                ('timer_period_sec', 0.05),
                ('pan_joint_name', 'head_1_joint'),
                ('tilt_joint_name', 'head_2_joint'),
                ('control_gain', 1e-3),
                ('smoothing_factor', 0.33),
            ]
        )
        self.timer_period_sec = self.get_parameter('timer_period_sec').value
        self.pan_joint_name = self.get_parameter('pan_joint_name').value
        self.tilt_joint_name = self.get_parameter('tilt_joint_name').value
        self.control_gain = self.get_parameter('control_gain').value
        self.smoothing_factor = self.get_parameter('smoothing_factor').value

        # --- Communication ---
        self.sub_joint_states = self.create_subscription(
            msg_type=sensor_msgs.msg.JointState,
            topic='joint_states',
            callback=self.sub_joint_state_callback,
            qos_profile=qos_profile_system_default,
        )
        self.sub_detections = self.create_subscription(
            msg_type=apriltag_msgs.msg.AprilTagDetectionArray,
            topic='detections',
            callback=self.sub_detections_callback,
            qos_profile=qos_profile_sensor_data,
        )
        self.pub_joint_trajectory = self.create_publisher(
            msg_type=trajectory_msgs.msg.JointTrajectory,
            topic='joint_trajectory',
            qos_profile=qos_profile_system_default,
        )
        self.timer = self.create_timer(
            timer_period_sec=self.timer_period_sec,
            callback=self.timer_callback,
        )

        self.camera_width = 640
        self.camera_height = 480
        self.load_camera_info_once()

        self._joint_indices_found = False
        self.pan_index = None
        self.tilt_index = None
        self.pan_now = 0.0
        self.tilt_now = 0.0
        self.pan_target = None
        self.tilt_target = None
        self._has_detection = False
        self._detection_x = 0.0
        self._detection_y = 0.0

    def sub_joint_state_callback(self, msg_joint_state):
        if not self._joint_indices_found:
            try:
                self.pan_index = msg_joint_state.name.index('head_1_joint')
                self.tilt_index = msg_joint_state.name.index('head_2_joint')
                self._joint_indices_found = True
            except ValueError:
                return
        self.pan_now = msg_joint_state.position[self.pan_index]
        self.tilt_now = msg_joint_state.position[self.tilt_index]
        if self.pan_target is None: self.pan_target = self.pan_now
        if self.tilt_target is None: self.tilt_target = self.tilt_now

    def sub_detections_callback(self, msg_detections):
        if len(msg_detections.detections) == 0:
            return
        self._detection_x = np.mean([tag.centre.x for tag in msg_detections.detections])
        self._detection_y = np.mean([tag.centre.y for tag in msg_detections.detections])
        self._has_detection = True

    def timer_callback(self):
        if not self._joint_indices_found:
            return
        if not self._has_detection:
            return
        self._has_detection = False
        x_err = (self.camera_width / 2) - self._detection_x
        y_err = (self.camera_height / 2) - self._detection_y
        raw_pan = self.pan_now + self.control_gain * x_err
        raw_tilt = self.tilt_now + self.control_gain * y_err
        self.pan_target += self.smoothing_factor * (raw_pan - self.pan_target)
        self.tilt_target += self.smoothing_factor * (raw_tilt - self.tilt_target)
        point = trajectory_msgs.msg.JointTrajectoryPoint()
        point.positions = [float(self.pan_target), float(self.tilt_target)]
        point.time_from_start.nanosec = int(self.timer_period_sec * 1e9)
        msg = trajectory_msgs.msg.JointTrajectory()
        msg.joint_names = [self.pan_joint_name, self.tilt_joint_name]
        msg.points.append(point)
        self.pub_joint_trajectory.publish(msg)
        self.get_logger().debug(f"""
pxl_err = ({x_err:.1f}, {y_err:.1f})
u_raw   = ({raw_pan:.3f}, {raw_tilt:.3f})
u_now   = ({self.pan_target:.3f}, {self.tilt_target:.3f})
y_now   = ({self.pan_now:.3f}, {self.tilt_now:.3f})
            """
        )


    def load_camera_info_once(self):
        success, msg = wait_for_message(
            msg_type=sensor_msgs.msg.CameraInfo,
            node=self,
            topic='camera_info',
            time_to_wait=10.0,
        )
        if success:
            self.camera_width = msg.width
            self.camera_height = msg.height
            self.get_logger().info(
                f"Camera calibrated with resolution=({self.camera_width}x{self.camera_height})."
            )
        else:
            self.get_logger().warn(
                "No CameraInfo received within timeout on camera_info. "
                "Using default camera parameters."
            )


def main(args=None):
    rclpy.init(args=args)
    node = HeadFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()
