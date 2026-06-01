#!/usr/bin/env python3
#derived from: https://github.com/ovgu-nit/nit_head_follower/blob/humble-devel/nit_head_follower/head_follower.py
import numpy as np

import rclpy
import rclpy.callback_groups
import rclpy.executors
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.wait_for_message import wait_for_message

import sensor_msgs.msg
import geometry_msgs.msg
import control_msgs.action


class HeadPointer(Node):
    """
    Moves Tiago head to focus on detected april tags using the PointHead action.
    Only updates the goal when a significant target position change is detected.
    """

    def __init__(self):
        super().__init__('head_pointer')

        # --- Constants ---
        self.time_to_point_sec = 0.2 # time to point, and time to wait till next action
        self.pixel_dist_thresh = 15
        self.topic_cube_pose = 'cube_pose'
        self.point_dist_thresh_m = 0.05 # minimum distance of new cube pose to old pose to trigger a point action

        # --- Parameters ---
        self.declare_parameters(
            namespace='',
            parameters=[
                ('topic_camera_info', '/head_front_camera/rgb/camera_info'),
                ('topic_detections', '/detections'),
                ('action_point_head', '/head_controller/point_head_action'),
            ]
        )
        self.topic_camera_info = self.get_parameter('topic_camera_info').value
        self.topic_detections = self.get_parameter('topic_detections').value
        self.action_point_head = self.get_parameter('action_point_head').value

        # --- Communication Setup ---
        self.callback_group = rclpy.callback_groups.ReentrantCallbackGroup()

        self.sub_cube_pose = self.create_subscription(
            msg_type=geometry_msgs.msg.PoseStamped,
            topic=self.topic_cube_pose,
            qos_profile=10,
            callback=self.cube_pose_callback,
            callback_group=self.callback_group
        )
        
        # Setup Action Client
        self._action_client = ActionClient(
            self, 
            control_msgs.action.PointHead, 
            self.action_point_head
        )
        self._action_client.wait_for_server()

        # --- Camera Info (Default Fallbacks) ---
        self.camera_frame_id = "head_front_camera_color_optical_frame"
        self.load_camera_info_once()

        # --- State ---
        self.last_point_msg = None
        self.goal_handle = None
        self.is_processing_goal = False  

        self.get_logger().info("Action server found. Head Pointer ready.")
    
    def load_camera_info_once(self):
        """Get camera info once via wait_for_message and keep defaults if unavailable."""
        success, msg = wait_for_message(
            sensor_msgs.msg.CameraInfo,
            self,
            self.topic_camera_info,
            time_to_wait=10.0,
        )

        if success:
            self.camera_frame_id = msg.header.frame_id
            self.get_logger().info(f"Camera loaded: frame={self.camera_frame_id}")
        else:
            self.get_logger().warn(
                f"No CameraInfo received within timeout on {self.topic_camera_info}. "
                "Using default camera parameters."
            )


    async def cube_pose_callback(self, cube_pose_msg: geometry_msgs.msg.PoseStamped):
        """
        Processes incoming AprilTag detections and sends an action goal 
        only if the target tag center moves past our threshold.
        """
        if self.is_processing_goal:
            return

        current_time = self.get_clock().now()
        
        # if self.last_point_msg is not None:
        #     last_point_time = rclpy.time.Time.from_msg(self.last_point_msg.header.stamp)
        #     time_since_last_goal = (current_time - last_point_time).nanoseconds / 1e9

        #     # give time to complete last action
        #     if time_since_last_goal < 2 * self.time_to_point_sec:
        #         return

        #     # Measure distance to last point
        #     lx, ly, lz = self.last_point_msg.point.x, self.last_point_msg.point.y, self.last_point_msg.point.z
        #     px, py, pz = cube_pose_msg.pose.position.x, cube_pose_msg.pose.position.y, cube_pose_msg.pose.position.z
            
        #     distance = ((px-lx)**2 + (py-ly)**2 + (pz-lz)**2)**.5
        #     self.get_logger().debug(f'{distance=}')

        #     if distance < self.point_dist_thresh_m:
        #         return

        new_point_msg = geometry_msgs.msg.PointStamped()
        new_point_msg.point = cube_pose_msg.pose.position
        new_point_msg.header.frame_id = cube_pose_msg.header.frame_id 
        
        new_point_msg.header.stamp.sec = 0
        new_point_msg.header.stamp.nanosec = 0
        
        self.last_point_msg = new_point_msg
        
        # FIXED: Flag now ONLY wraps the critical server handshake block
        try:
            self.is_processing_goal = True
            await self.send_point_head_goal(new_point_msg)
        finally:
            self.is_processing_goal = False


    async def send_point_head_goal(self, new_point_msg: geometry_msgs.msg.PointStamped):
        """Builds and sends a PointHead goal to the action server."""
        goal_msg = control_msgs.action.PointHead.Goal()
        goal_msg.target = new_point_msg
        
        goal_msg.pointing_axis.x = 0.0
        goal_msg.pointing_axis.y = 0.0
        goal_msg.pointing_axis.z = 1.0
        goal_msg.pointing_frame = self.camera_frame_id
        
        goal_msg.min_duration.sec = 0
        goal_msg.min_duration.nanosec = int(self.time_to_point_sec * 1e9) 
        goal_msg.max_velocity = 1.0 

        if self.goal_handle is not None:
            self.get_logger().debug("Canceling active head movement...")
            await self.goal_handle.cancel_goal_async() 
            self.goal_handle = None

        self.get_logger().debug("Sending point head goal...")
        goal_handle = await self._action_client.send_goal_async(goal_msg)
        
        if not goal_handle.accepted:
            self.get_logger().error("PointHead Goal was REJECTED!")
            return

        self.get_logger().debug("Goal accepted. Tracking execution...")
        self.goal_handle = goal_handle

        # Create an independent background task to wait for the execution result.
        # This keeps this specific call thread from holding onto execution states.
        self.executor.create_task(self.track_execution_result(goal_handle))


    async def track_execution_result(self, goal_handle):
        """Monitors the execution in the background, allowing the callback to stay responsive."""
        from action_msgs.msg import GoalStatus
        result_handle = await goal_handle.get_result_async()
        
        if result_handle.status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info("Head successfully reached target.")
        elif result_handle.status == GoalStatus.STATUS_CANCELED:
            self.get_logger().debug("Previous goal execution successfully canceled.")
        elif result_handle.status == GoalStatus.STATUS_ABORTED:
            self.get_logger().error("PointHead execution ABORTED mid-movement!")


def main(args=None):
    rclpy.init(args=args)
    node = HeadPointer()

    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

if __name__ == '__main__':
    main()