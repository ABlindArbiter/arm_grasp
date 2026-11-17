"""W5-1 baseline: PyBullet library IK on arm5.urdf.

运行：
    cd ~/arm-grasp && source .venv/bin/activate
    python sim/scripts/ik_lib_baseline.py

观察三件事：
1. `ik_len`：6 个 actuated joint（5 臂 + 1 夹爪）；只把前 5 个写进臂。
2. `err_mm`：TCP 到目标的位置误差。为什么不是 0？
3. `tool_z`：tool 轴在世界系的方向。是不是 (0,0,-1)？
   如果不是，说明 position-only IK 没有约束姿态，5 DOF 的 tool 没保持竖直。

注意：
- 这里把 joint limits 临时改成 [-pi, pi]，因为 URDF 的 0..range 是占位值，
  且 URDF 零位 ≠ 你的机械下限（theta_offset 还没做）。W5-1 先隔离“限位”和“IK”。
- ee = 6 是 `tool0` 的 link index（fixed joint 6 的 child link），不是第 7 个自由度。
"""
import math
import os

import pybullet as p

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
URDF = os.path.join(REPO, "sim", "urdf", "arm5.urdf")

# 工作空间内的 3 个目标点（base 系，米）
TARGETS = [
    (0.15, 0.00, 0.10),
    (0.12, 0.10, 0.12),
    (0.18, -0.05, 0.08),
]

p.connect(p.DIRECT)
robot = p.loadURDF(URDF, useFixedBase=True)
ee = 6  # tool0 link index

lo = [-math.pi] * 6
hi = [math.pi] * 6
ranges = [2 * math.pi] * 6
rest = [0.0] * 6

print(f"{'target (m)':28s} {'err_mm':>8s}  {'q1..q5 (deg)':38s}  tool_z")
print("-" * 110)
for t in TARGETS:
    ik = p.calculateInverseKinematics(
        robot, ee, t,
        lowerLimits=lo, upperLimits=hi,
        jointRanges=ranges, restPoses=rest,
        maxNumIterations=200, residualThreshold=1e-6,
    )
    for i in range(5):
        p.resetJointState(robot, i, ik[i])

    ls = p.getLinkState(robot, ee)
    pos, orn = ls[4], ls[5]
    R = p.getMatrixFromQuaternion(orn)
    tool_z = (R[2], R[5], R[8])
    err = math.dist(pos, t) * 1000.0
    q = [round(math.degrees(x), 1) for x in ik[:5]]
    print(f"{str(t):28s} {err:8.2f}  {str(q):38s}  "
          f"({tool_z[0]:.2f}, {tool_z[1]:.2f}, {tool_z[2]:.2f})")

p.disconnect()
