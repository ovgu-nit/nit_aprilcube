#!/usr/bin/env python3
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_system_default
import rclpy.time
import rclpy.duration

import geometry_msgs.msg
import moveit_msgs.msg
import moveit_msgs.srv
import shape_msgs.msg
import tf2_ros


class AprilcubeDetector(Node):

    def __init__(self):
        super().__init__('nit_pick_place')

        self.declare_parameters(
            namespace='',
            parameters=[
                # ('use_sim_time', False),
                ('timer_period_sec', 1.0),
                ('base_frame', 'base_footprint'),
                ('cube_side_length', 0.05),
                ('forget_thresh_sec', 5.0),
                ('novelty_thresh_m', 0.01),
                ('end_effector_link', 'gripper_grasping_frame'),
                ('planning_group', 'arm_torso'),
                ('publish_pose_enabled', False),
            ]
        )
        # self.use_sim_time = self.get_parameter('use_sim_time').value
        self.timer_period_sec = self.get_parameter('timer_period_sec').value
        self.base_frame = self.get_parameter('base_frame').value
        self.cube_side_length = self.get_parameter('cube_side_length').value
        self.forget_thresh_sec = self.get_parameter('forget_thresh_sec').value
        self.novelty_thresh_m = self.get_parameter('novelty_thresh_m').value
        self.end_effector_link = self.get_parameter('end_effector_link').value
        self.planning_group = self.get_parameter('planning_group').value
        self.publish_pose_enabled = self.get_parameter('publish_pose_enabled').value

        # --- ROS setup ---
        self.timer = self.create_timer(
            timer_period_sec=self.timer_period_sec,
            callback=self.perceive,
        )
        
        if self.publish_pose_enabled:
            self.pub_cube_pose = self.create_publisher(
                msg_type=geometry_msgs.msg.PoseStamped,
                topic='cube_pose',
                qos_profile=qos_profile_system_default,
            )
        else:
            self.pub_cube_pose = None

        # --- TF setup ---
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(
            buffer=self.tf_buffer,
            node=self
        )

        # --- Planning scene service ---
        self.srv_APS_client = self.create_client(
            srv_type=moveit_msgs.srv.ApplyPlanningScene,
            srv_name='/apply_planning_scene',
        )
        while not self.srv_APS_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /apply_planning_scene service...')
        self.get_logger().info('Connected to /apply_planning_scene service')

        # --- Tag frame names ---
        self.tag_frame_names = [
            'tag0_top',
            'tag1_front',
            'tag2_left',
            'tag3_right',
            'tag4_back',
            'tag5_bottom',
        ]

        # --- State ---
        self.cube_pose = None
        self.t_found = self.get_clock().now()
        self.dist_to_table = 0.35

        self.get_logger().info('Aprilcube Detector initialized.')

    # --- Perception logic ---

    def perceive(self):
        t_now = self.get_clock().now()
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

        distances = [self._distance_of_poses(self.cube_pose, p) for p in new_poses]
        i_closest = int(np.argmin(distances))
        d_closest = distances[i_closest]
        p_closest = new_poses[i_closest]

        if d_closest > self.novelty_thresh_m:
            self.found_cube(p_closest, t_found=t_now)

    def found_cube(self, cube_pose, t_found=None):
        self.cube_pose = cube_pose
        self.t_found = self.get_clock().now() if t_found is None else t_found
        
        x, y, z = self.cube_pose.position.x, self.cube_pose.position.y, self.cube_pose.position.z
        self.get_logger().info(f'Cube detected @ (x={x:.2f}, y={y:.2f}, z={z:.2f}).')
        
        self._update_collision_objects(self.cube_pose)
        
        if self.pub_cube_pose:
            msg = geometry_msgs.msg.PoseStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = self.base_frame
            msg.pose = self.cube_pose
            self.pub_cube_pose.publish(msg)

    def forget_cube(self):
        self.get_logger().info('Cube lost; removing planning scene objects.')
        self.cube_pose = None
        self.t_found = None
        self._remove_collision_objects()

    # --- Collision scene management ---

    def _update_collision_objects(self, cube_pose):
        request = moveit_msgs.srv.ApplyPlanningScene.Request()
        request.scene.is_diff = True

        # Cube object
        cube_obj = moveit_msgs.msg.CollisionObject()
        cube_obj.header.frame_id = self.base_frame
        cube_obj.id = 'aprilcube'
        cube_obj.operation = moveit_msgs.msg.CollisionObject.ADD

        cube_box = shape_msgs.msg.SolidPrimitive()
        cube_box.type = shape_msgs.msg.SolidPrimitive.BOX
        cube_box.dimensions = [self.cube_side_length] * 3
        cube_obj.primitives.append(cube_box)
        cube_obj.primitive_poses.append(cube_pose)

        # Table object
        table_obj = moveit_msgs.msg.CollisionObject()
        table_obj.header.frame_id = self.base_frame
        table_obj.id = 'table'
        table_obj.operation = moveit_msgs.msg.CollisionObject.ADD
        table_box = shape_msgs.msg.SolidPrimitive()
        table_box.type = shape_msgs.msg.SolidPrimitive.BOX

        table_depth = 1.0
        table_width = 2.0
        table_height = max(
            0.01,
            max(1e-2, cube_pose.position.z - (self.cube_side_length / 2) - 0.008),
        )
        table_box.dimensions = [table_depth, table_width, table_height]

        cube_xy = np.array([cube_pose.position.x, cube_pose.position.y])
        cube_r = np.linalg.norm(cube_xy)
        if cube_r < 1e-6:
            cube_dir = np.array([1.0, 0.0])
        else:
            cube_dir = cube_xy / cube_r

        table_center_distance = self.dist_to_table + table_depth / 2.0
        table_pose = geometry_msgs.msg.Pose()
        table_pose.position.x = float(cube_dir[0] * table_center_distance)
        table_pose.position.y = float(cube_dir[1] * table_center_distance)
        table_pose.position.z = table_height / 2.0

        yaw = np.arctan2(cube_dir[1], cube_dir[0])
        half_yaw = yaw / 2.0
        table_pose.orientation.x = 0.0
        table_pose.orientation.y = 0.0
        table_pose.orientation.z = float(np.sin(half_yaw))
        table_pose.orientation.w = float(np.cos(half_yaw))

        table_obj.primitives.append(table_box)
        table_obj.primitive_poses.append(table_pose)

        request.scene.world.collision_objects.append(cube_obj)
        request.scene.world.collision_objects.append(table_obj)

        self.srv_APS_client.call_async(request)

    def _remove_collision_objects(self):
        request = moveit_msgs.srv.ApplyPlanningScene.Request()
        request.scene.is_diff = True

        for object_id in ['aprilcube', 'table']:
            obj = moveit_msgs.msg.CollisionObject()
            obj.header.frame_id = self.base_frame
            obj.id = object_id
            obj.operation = moveit_msgs.msg.CollisionObject.REMOVE
            request.scene.world.collision_objects.append(obj)

        self.srv_APS_client.call_async(request)

    # --- TF and pose helpers ---

    def _cube_pose_from_tag_transform(self, tag_transform):
        from scipy.spatial.transform import Rotation as R

        quat = np.array([
            tag_transform.transform.rotation.x,
            tag_transform.transform.rotation.y,
            tag_transform.transform.rotation.z,
            tag_transform.transform.rotation.w,
        ])
        
        rotation = R.from_quat(quat)
        normal = rotation.as_matrix() @ [0, 0, 1]
        
        xyz = np.array([
            tag_transform.transform.translation.x,
            tag_transform.transform.translation.y,
            tag_transform.transform.translation.z,
        ])
        
        xyz -= (self.cube_side_length / 2) * normal
        
        pose = geometry_msgs.msg.Pose()
        pose.position.x = xyz[0]
        pose.position.y = xyz[1]
        pose.position.z = xyz[2]
        pose.orientation.x = quat[0]
        pose.orientation.y = quat[1]
        pose.orientation.z = quat[2]
        pose.orientation.w = quat[3]
        
        return pose

    def _is_frame_too_old(self, tag_transform):
        now = self.get_clock().now()
        stamp = rclpy.time.Time.from_msg(tag_transform.header.stamp)
        age_sec = (now - stamp).nanoseconds / 1e9
        age_thresh_sec = 2 * self.timer_period_sec

        if abs(age_sec) > 1e4:
            self.get_logger().warn(
                f"{tag_transform.child_frame_id}'s frame age of {age_sec}sec is unrealistic. Please run node with '--ros-args -p use_sim_time:=true'"
            )
            return True
        elif age_sec > age_thresh_sec or age_sec < 0:
            return True
        
        return False

    def _cube_pose_candidates(self):
        pose_candidates = []
        for tag_frame in self.tag_frame_names:
            if not self.tf_buffer.can_transform(
                self.base_frame, tag_frame, rclpy.time.Time()
            ):
                continue

            try:
                transform = self.tf_buffer.lookup_transform(
                    self.base_frame,
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

    def _distance_of_poses(self, poseA, poseB):
        xyzA = np.array([poseA.position.x, poseA.position.y, poseA.position.z])
        xyzB = np.array([poseB.position.x, poseB.position.y, poseB.position.z])
        return np.linalg.norm(xyzA - xyzB)


def main(args=None):
    rclpy.init(args=args)
    node = AprilcubeDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()