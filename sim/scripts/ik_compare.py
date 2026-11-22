"""W5-3：库 IK vs 解析 IK 的同一目标位姿对比。

运行：
    cd ~/arm-grasp && source .venv/bin/activate
    python sim/scripts/ik_compare.py

对比口径
--------
同一个 5D 目标 `(p, alpha, phi)`：
- p      : TCP 位置（base 系，m）
- alpha  : 工具轴仰角（rad；垂直向下 = -pi/2）
- phi    : 夹爪绕工具轴自转（rad）

解析 IK：`arm.kinematics.ik_analytic(p_mm, alpha, phi)`，DH 系，精确解。
库 IK  ：PyBullet `calculateInverseKinematics`，给 **targetPosition + targetOrientation**。
          targetOrientation 由解析解的 DH FK 得到（tool0 的 z 轴 = a(alpha)）。

为什么库 IK 要给 targetOrientation？
------------------------------------
W5-1 的库 IK 只给 targetPosition，它不知道 tool 要朝哪；
结果 tool_z 是歪的，误差也不是 IK 的真实能力。
W5-3 给完整目标位姿，才是公平对比。

注意
----
- URDF 的零位和 DH 零位差一个 theta_offset（还没标定），所以**关节角差不能严格比**；
  先比 TCP 位置、tool z 轴、整体姿态误差。
- URDF 的 limit 是占位值（0..range），这里临时改 [-pi, pi] 隔离限位；真实 limit 在 P2-W7 补。
- URDF 的 tool0 x/y 和 DH tool x/y 差一个常数 roll（90°）；q5 会差一个常数，属正常。
- `getNumJoints=7`（6 revolute + 1 fixed tool0）；只设置前 5 个臂关节。

读代码顺序
----------
1. `target_pose_from_dh()`：解析解 → DH 的 TCP 位姿（给库 IK 当目标）
2. `lib_ik()`：PyBullet 的 position + orientation IK
3. `pose_error()`：位置 / tool z / 整体姿态误差
4. `main()`：3 个目标，每个取 2 个肘解，逐行打印
"""
from __future__ import annotations

import math
import os
import sys
import time

import numpy as np
import pybullet as p
from scipy.spatial.transform import Rotation

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "pc"))

from arm.kinematics import fk_dh, ik_analytic  # noqa: E402

URDF = os.path.join(REPO, "sim", "urdf", "arm5.urdf")

# (x, y, z) m, alpha deg, phi deg
CASES = [
    (0.15, 0.00, 0.00, -90.0, 0.0),   # 垂直下抓基线
    (0.15, 0.00, 0.10, -45.0, 0.0),   # 斜抓：W5-1 里 tool-down 到不了的点
    (0.12, 0.05, 0.02, -60.0, 30.0),  # 斜抓 + 夹爪转 30°
]


def target_pose_from_dh(q_dh):
    """解析解的 DH 关节角 → 目标 TCP 位姿（m, 3x3 旋转）。

    `fk_dh` 返回 mm；PyBullet 用 m。
    """
    T = fk_dh(q_dh)
    p_m = T[:3, 3] / 1000.0
    R = T[:3, :3].copy()
    return p_m, R


def lib_ik(robot, target_p, target_R):
    """PyBullet 的 position + orientation IK。

    返回 (q[:5], solve_ms)。
    """
    quat = Rotation.from_matrix(target_R).as_quat()  # (x, y, z, w)
    lo = [-math.pi] * 6
    hi = [math.pi] * 6

    t0 = time.perf_counter()
    ik = p.calculateInverseKinematics(
        robot, 6, target_p,
        targetOrientation=quat,
        lowerLimits=lo, upperLimits=hi,
        jointRanges=[2 * math.pi] * 6,
        restPoses=[0.0] * 6,
        maxNumIterations=300,
        residualThreshold=1e-8,
    )
    dt_ms = (time.perf_counter() - t0) * 1000.0
    return np.array(ik[:5]), dt_ms


def pose_error(robot, target_p, target_R):
    """当前关节状态下，tool0 的位置 / tool z / 整体姿态误差。"""
    ls = p.getLinkState(robot, 6)
    pos = np.array(ls[4])
    R = np.array(p.getMatrixFromQuaternion(ls[5])).reshape(3, 3)

    pos_err_mm = float(np.linalg.norm(pos - target_p) * 1000.0)
    z_target = target_R[:, 2]
    z_actual = R[:, 2]
    cos_z = float(np.clip(np.dot(z_target, z_actual), -1.0, 1.0))
    z_err_deg = math.degrees(math.acos(cos_z))

    # 整体姿态误差：R_target^T R_actual 的旋转角
    R_rel = target_R.T @ R
    cos_ori = float(np.clip((np.trace(R_rel) - 1.0) / 2.0, -1.0, 1.0))
    ori_err_deg = math.degrees(math.acos(cos_ori))
    return pos_err_mm, z_err_deg, ori_err_deg, pos, R


def fmt_q(q_rad):
    return "[" + ", ".join(f"{math.degrees(v):7.2f}" for v in q_rad) + "]"


def main():
    p.connect(p.DIRECT)
    robot = p.loadURDF(URDF, useFixedBase=True)
    p.setGravity(0, 0, 0)  # 纯运动学，不需要重力

    print(f"{'case':4s} {'alpha':>6s} {'phi':>5s} {'elbow':5s} "
          f"{'pos_mm':>7s} {'z_err':>7s} {'ori_err':>8s} {'t_ms':>7s}  q_lib (deg)")
    print("-" * 135)

    for idx, (x, y, z, alpha_deg, phi_deg) in enumerate(CASES, start=1):
        alpha = math.radians(alpha_deg)
        phi = math.radians(phi_deg)

        sols = ik_analytic(x * 1000.0, y * 1000.0, z * 1000.0, alpha=alpha, phi=phi)
        if not sols:
            print(f"{idx:<4d} {alpha_deg:6.1f} {phi_deg:5.1f} 解析 IK 无解")
            continue

        for s in sols:
            target_p, target_R = target_pose_from_dh(s["q"])

            q_lib, t_ms = lib_ik(robot, target_p, target_R)
            for i in range(5):
                p.resetJointState(robot, i, q_lib[i])

            pos_err, z_err, ori_err, _, _ = pose_error(robot, target_p, target_R)
            print(f"{idx:<4d} {alpha_deg:6.1f} {phi_deg:5.1f} {s['elbow']:5s} "
                  f"{pos_err:7.2f} {z_err:7.2f} {ori_err:8.2f} {t_ms:7.2f}  "
                  f"{fmt_q(q_lib)}")

        print()  # 每个 case 空一行

    p.disconnect()


if __name__ == "__main__":
    main()
