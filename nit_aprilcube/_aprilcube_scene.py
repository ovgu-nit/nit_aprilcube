import numpy as np

import geometry_msgs.msg
import moveit_msgs.msg
import moveit_msgs.srv
import shape_msgs.msg

from ._aprilcube_utils import xyz_from_pose


class AprilcubeScene:
    """
    Updates the Planning Scene from Moveit with suitable collision objects using the ApplyPlanningScene-Service
    """

    def __init__(
            self, 
            node
        ):
        self.node = node

        # --- CONSTANTS ---
        self.dist_to_table = 0.35 # [m] as high as possible but max 0.4 
        
        # --- ApplyPlanningScene Client ---
        self.srv_APS_client = self.node.create_client(
            srv_type=moveit_msgs.srv.ApplyPlanningScene,
            srv_name='/apply_planning_scene',
        )
        # Wait for service to be available
        while not self.srv_APS_client.wait_for_service(timeout_sec=1.0):
            self.node.get_logger().info('Waiting for /apply_planning_scene service...')
        self.node.get_logger().info('Connected to /apply_planning_scene service')


    def update_collision_objects(self, cube_pose: geometry_msgs.msg.Pose):
        request = moveit_msgs.srv.ApplyPlanningScene.Request()
        request.scene.is_diff = True

        # Cube obejct
        cube_obj = moveit_msgs.msg.CollisionObject()
        cube_obj.header.frame_id = self.node.base_frame
        cube_obj.id = 'cube'
        cube_obj.operation = moveit_msgs.msg.CollisionObject.ADD

        cube_box = shape_msgs.msg.SolidPrimitive()
        cube_box.type = shape_msgs.msg.SolidPrimitive.BOX
        cube_box.dimensions = [self.node.cube_side_length] * 3
        cube_obj.primitives.append(cube_box)
        cube_obj.primitive_poses.append(cube_pose)

        # Table object
        table_obj = moveit_msgs.msg.CollisionObject()
        table_obj.header.frame_id = self.node.base_frame
        table_obj.id = 'table'
        table_obj.operation = moveit_msgs.msg.CollisionObject.ADD
        table_box = shape_msgs.msg.SolidPrimitive()
        table_box.type = shape_msgs.msg.SolidPrimitive.BOX

        table_depth = 1.0
        table_width = 2.0
        table_height = max(
            0.01,
            max(1e-2, cube_pose.position.z - (self.node.cube_side_length / 2) - 0.008),
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

    def remove_collision_objects(self):
        request = moveit_msgs.srv.ApplyPlanningScene.Request()
        request.scene.is_diff = True

        for object_id in ['cube', 'table']:
            obj = moveit_msgs.msg.CollisionObject()
            obj.header.frame_id = self.node.base_frame
            obj.id = object_id
            obj.operation = moveit_msgs.msg.CollisionObject.REMOVE
            request.scene.world.collision_objects.append(obj)

        self.srv_APS_client.call_async(request)
