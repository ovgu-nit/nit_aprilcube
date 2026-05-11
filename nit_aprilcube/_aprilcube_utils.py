import numpy as np

import geometry_msgs
import tf2_ros


# --- ROTATION CONVERSION ---

def R_from_quat(q: np.ndarray) -> np.ndarray:
    from scipy.spatial.transform import Rotation as R
    return R.from_quat(q).as_matrix()

def quat_from_R(matrix: np.ndarray) -> np.ndarray:
    from scipy.spatial.transform import Rotation as R
    return R.from_matrix(matrix).as_quat()


# --- TF CONVERSION ---

def xyz_from_tf(transform: tf2_ros.TransformStamped) -> np.ndarray:
    return np.array([
        transform.transform.translation.x,
        transform.transform.translation.y,
        transform.transform.translation.z,
    ])

def quat_from_tf(transform: tf2_ros.TransformStamped) -> np.ndarray:
    return np.array([
        transform.transform.rotation.x,
        transform.transform.rotation.y,
        transform.transform.rotation.z,
        transform.transform.rotation.w,
    ])

def R_from_tf(transform: tf2_ros.TransformStamped) -> np.ndarray:
    return R_from_quat(quat_from_tf(transform))


# --- geometry_msgs.msg.Point MSG CONVERSION ---

def xyz_from_point(point: geometry_msgs.msg.Point) -> np.ndarray:
    return np.array([
        point.x,
        point.y,
        point.z,
    ])

def point_from_xyz(xyz: np.ndarray) -> geometry_msgs.msg.Point:
    return geometry_msgs.msg.Point(
        x=xyz[0],
        y=xyz[1],
        z=xyz[2],
    )

# --- geometry_msgs.msg.Quaternion MSG CONVERSION ---

def quat_msg_from_np(quat: np.ndarray) -> geometry_msgs.msg.Quaternion:
    return geometry_msgs.msg.Quaternion(
        x=quat[0],
        y=quat[1],
        z=quat[2],
        w=quat[3],
    )

def quat_np_from_msg(quat_msg: geometry_msgs.msg.Quaternion) -> np.ndarray:
    return np.array([
        quat_msg.x,
        quat_msg.y,
        quat_msg.z,
        quat_msg.w,
    ])


def quat_msg_from_R(R: np.ndarray) -> np.ndarray:
    return quat_msg_from_np(quat_from_R(R))


# --- geometry_msgs.msg.Pose MSG CONVERSION ---

def xyz_from_pose(pose: geometry_msgs.msg.Pose) -> np.ndarray:
    return xyz_from_point(pose.position)

def quat_from_pose(pose: geometry_msgs.msg.Pose) -> np.ndarray:
    return quat_np_from_msg(pose.orientation)

def R_from_pose(pose: geometry_msgs.msg.Pose) -> np.ndarray:
    return R_from_quat(quat_from_pose(pose))

def pose_from_np(
        xyz: np.ndarray, 
        quat: np.ndarray
    ) -> geometry_msgs.msg.Pose:
    pose = geometry_msgs.msg.Pose()
    pose.position = point_from_xyz(xyz)
    pose.orientation = quat_msg_from_np(quat)
    return pose


# --- DISTANCE ---

def distance_of_poses(
        poseA: geometry_msgs.msg.Pose,
        poseB: geometry_msgs.msg.Pose,
):
    return np.linalg.norm(
        xyz_from_pose(poseA) - xyz_from_pose(poseB)
    )