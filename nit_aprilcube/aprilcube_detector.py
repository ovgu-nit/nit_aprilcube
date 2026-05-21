#!/usr/bin/env python3
import rclpy
import rclpy.node
import tf2_ros

from ._aprilcube_scene import AprilcubeScene
from ._aprilcube_perceive import AprilcubePerceive


class AprilcubeDetector(rclpy.node.Node):
    def __init__(self):
        super().__init__('nit_pick_place')

        # --- PARAMETERS ---
        self.declare_parameters(
            namespace='',
            parameters=[
                ('timer_period_sec', 1.0),
                ('base_frame', 'base_footprint'),
                ('cube_side_length', 0.05),
                ('forget_thresh_sec', 5.0),
                ('novelty_thresh_m', 0.001),
                ('end_effector_link', 'gripper_grasping_frame'),
                ('planning_group', 'arm_torso'),
            ]
        )
        self.timer_period_sec = self.get_parameter('timer_period_sec').value
        self.base_frame = self.get_parameter('base_frame').value
        self.cube_side_length = self.get_parameter('cube_side_length').value
        self.forget_thresh_sec = self.get_parameter('forget_thresh_sec').value
        self.novelty_thresh_m = self.get_parameter('novelty_thresh_m').value
        self.end_effector_link = self.get_parameter('end_effector_link').value
        self.planning_group = self.get_parameter('planning_group').value


        # --- STATE ---
        self.t_last_update = self.get_clock().now()
        self.remembered_cube_pose = None

        # --- ROS SETUP ---
        self.timer = self.create_timer(
            timer_period_sec=self.timer_period_sec,
            callback=self.timer_callback,
        )

        # Setup TF Listener to get tag pose estimations
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = None

        # --- SUB-MODULES ---

        self.scene = AprilcubeScene(node=self)

        self.perceive = AprilcubePerceive(
            node=self,
            found_cube_callback=self.found_cube_callback,
            forget_cube_callback=self.forgot_cube_callback,
        )

    def timer_callback(self):
        # perception
        self.perceive.perceive()


    # --- CALLBACKS ---

    def activate(self) -> bool:
        self.timer.reset()

        # Create a TF listener to excess pose frames
        self.tf_listener = tf2_ros.TransformListener(
            buffer=self.tf_buffer, 
            node=self
        )

        if not self.perceive.activate(): return False

        return True

    def deactive(self) -> bool:
        self.timer.cancel()
        # Let olf listener be garbage collected
        self.tf_listener = None
        self.perceive.deactivate()
        self.scene.remove_collision_objects()
        return True

    def found_cube_callback(self):
        self.get_logger().info('Cube detected; updating planning scene and opening gripper.')
        if self.perceive.cube_pose is not None:
            self.scene.update_collision_objects(self.perceive.cube_pose)

    def forgot_cube_callback(self):
        self.get_logger().info('Cube lost; removing planning scene objects and closing gripper.')
        self.scene.remove_collision_objects()


def main(args=None):
    rclpy.init(args=args)
    node = AprilcubeDetector()
    node.activate()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.deactive()

    if rclpy.ok():
        node.deactive()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
