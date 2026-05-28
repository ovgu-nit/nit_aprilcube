import numpy as np

import geometry_msgs.msg
import rclpy
import tf2_ros

from ._aprilcube_utils import (
    R_from_quat,
    quat_from_tf,
    pose_from_np,
    xyz_from_tf,
    distance_of_poses,
)

class AprilcubePerceive:
    """
    Handles the aprilcube perception and memory of the cube pose.
    """


    def __init__(
        self,
        node: rclpy.node.Node,
        found_cube_callback=None,
        forget_cube_callback=None,
    ):
        self.node = node
        self.found_cube_callback = found_cube_callback
        self.forget_cube_callback = forget_cube_callback

        # --- CONSTANTS ---
        self.tag_frame_names = [
            'tag0_top',
            'tag1_front',
            'tag2_left',
            'tag3_right',
            'tag4_back',
            'tag5_bottom',
        ]

        self.base_frame = node.base_frame
        self.tf_buffer = node.tf_buffer
        self.forget_thresh_sec = node.forget_thresh_sec
        self.novelty_thresh_m = node.novelty_thresh_m

        # --- STATE ---
        self.cube_pose = None
        self.t_found = None


    # --- ACTIVATION ---

    def activate(self) -> bool: return True

    def deactivate(self) -> bool:
        self.forget_cube()
        return True
    

    # --- STATE CHANGE ---

    def forget_cube(self):
        # self.node.get_logger().info('Forgetting cube.')
        self.cube_pose = None
        self.t_found = None
        if self.forget_cube_callback is not None:
            self.forget_cube_callback()

    def found_cube(
        self,
        cube_pose: geometry_msgs.msg.Pose,
        t_found=None,
    ):
        # self.node.get_logger().info(
        #     f'Found new cube at {xyz_from_pose(cube_pose)}'
        # )
        self.cube_pose = cube_pose
        self.t_found = self.node.get_clock().now() if t_found is None else t_found
        if self.found_cube_callback is not None:
            self.found_cube_callback()

    # --- TIMER UPDATE ---

    def perceive(self):
        t_now = self.node.get_clock().now()
        new_poses = self._cube_pose_candidates()

        if len(new_poses) == 0:
            if self.cube_pose is None:
                return

            t_elapsed_sec = (t_now - self.t_found).nanoseconds / 1e9
            if t_elapsed_sec > self.forget_thresh_sec:
                self.forget_cube()

            return

        if self.cube_pose is None:
            self.found_cube(new_poses[0], t_found=t_now)
            return

        distances = [distance_of_poses(self.cube_pose, p) for p in new_poses]
        i_closest = int(np.argmin(distances))
        d_closest = distances[i_closest]
        p_closest = new_poses[i_closest]

        if d_closest > self.node.novelty_thresh_m:
            self.found_cube(p_closest, t_found=t_now)
            return

        # self.cube_pose = p_closest


    # --- HELPER FUNCTIONS ---

    def _cube_pose_from_tag_transform(
            self,
            tag_transform: tf2_ros.TransformStamped,
    ) -> geometry_msgs.msg.Pose:
        """
        Estimates the cube pose at half the cube side length down the normal of the tag frame. The frames are estimated so that the z axis is orthogonal to the tag plane.
        """
        quat = quat_from_tf(tag_transform)
        R = R_from_quat(quat)
        normal = R @ [0, 0, 1]
        xyz = xyz_from_tf(tag_transform) 
        xyz -= (self.node.cube_side_length / 2) * normal
        return pose_from_np(xyz, quat)

    def _is_frame_too_old(
            self,
            tag_transform: tf2_ros.TransformStamped,
    ) -> bool:
        """
        Checks if the received transform is recent. TF keep transform in the buffer for longer as they exist. Check only work if this node also uses simulation time.
        """
        now = self.node.get_clock().now()
        stamp = rclpy.time.Time.from_msg(tag_transform.header.stamp)
        age_sec = (now - stamp).nanoseconds / 1e9
        age_thresh_sec = 2 * self.node.timer_period_sec

        if abs(age_sec) > 1e4:
            self.node.get_logger().warn(
                f"{tag_transform.child_frame_id}'s frame age of {age_sec}sec is unrealistic. Please run node with '--ros-args -p use_sim_time:=true'"
            )
            return True
        
        elif age_sec > age_thresh_sec or age_sec < 0:
            return True
        
        return False
    
    def _cube_pose_candidates(self) -> list[geometry_msgs.msg.Pose]:
        """
        Queries the TF buffer for all tag transforms and returns a list of valid cube poses.
        """
        pose_candidates = []
        for tag_frame in self.tag_frame_names:
            if not self.node.tf_buffer.can_transform(
                self.node.base_frame, tag_frame, rclpy.time.Time()
            ):
                continue

            try:
                transform = self.node.tf_buffer.lookup_transform(
                    self.node.base_frame,
                    tag_frame,
                    rclpy.time.Time(),
                    timeout=rclpy.duration.Duration(seconds=0.0),
                )

                if self._is_frame_too_old(transform):
                    continue

                pose_candidates.append(self._cube_pose_from_tag_transform(transform))
            except (
                tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException,
            ):
                continue

        return pose_candidates