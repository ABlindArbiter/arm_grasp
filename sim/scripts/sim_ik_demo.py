"""P0 仿真演示：加载现成 KUKA 机械臂，用 PyBullet IK 画一个圆。

运行：
    python3 sim/scripts/sim_ik_demo.py

输出：
    docs/media/sim_ik.gif   （约 10 秒）
    docs/media/sim_ik.png   （中间帧）
"""

import math
import os

import numpy as np
import pybullet as p
import pybullet_data
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GIF_PATH = os.path.join(REPO, "docs/media/sim_ik.gif")
PNG_PATH = os.path.join(REPO, "docs/media/sim_ik.png")

# 1. 起一个无界面仿真
p.connect(p.DIRECT)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.81)
p.setTimeStep(1.0 / 240.0)

# 2. 载入地面和现成机械臂（先不建自己的模型）
p.loadURDF("plane.urdf")
robot = p.loadURDF("kuka_iiwa/model.urdf", useFixedBase=True)
num_joints = p.getNumJoints(robot)
ee_link = num_joints - 1
joint_ids = list(range(num_joints))

# 3. 先移动到圆的第一点，等机械臂稳定，避免开头大幅摆动
first_target = [0.42, 0.0, 0.52]
first_ik = p.calculateInverseKinematics(
    robot,
    ee_link,
    first_target,
    maxNumIterations=200,
    residualThreshold=1e-6,
)
p.setJointMotorControlArray(
    robot,
    joint_ids,
    p.POSITION_CONTROL,
    targetPositions=first_ik[:num_joints],
    forces=[500.0] * num_joints,
)
for _ in range(200):
    p.stepSimulation()

# 4. 固定相机
view = p.computeViewMatrixFromYawPitchRoll(
    cameraTargetPosition=[0.35, 0.0, 0.45],
    distance=2.0,
    yaw=50,
    pitch=-20,
    roll=0,
    upAxisIndex=2,
)
proj = p.computeProjectionMatrixFOV(
    fov=60,
    aspect=640 / 480,
    nearVal=0.1,
    farVal=5.0,
)

# 5. 目标点走一个圆，逐帧 IK + 渲染
frames = []
errors_mm = []
frames_total = 100  # 10 fps -> 10 秒

for i in range(frames_total):
    theta = 2.0 * math.pi * i / (frames_total - 1)
    target = [
        0.42,
        0.22 * math.sin(theta),
        0.52 + 0.04 * math.cos(theta),
    ]

    ik = p.calculateInverseKinematics(
        robot,
        ee_link,
        target,
        maxNumIterations=200,
        residualThreshold=1e-6,
    )
    p.setJointMotorControlArray(
        robot,
        joint_ids,
        p.POSITION_CONTROL,
        targetPositions=ik[:num_joints],
        forces=[500.0] * num_joints,
    )
    for _ in range(10):
        p.stepSimulation()

    pos = p.getLinkState(robot, ee_link)[4]
    err = math.sqrt(sum((pos[k] - target[k]) ** 2 for k in range(3)))
    errors_mm.append(err * 1000.0)

    width, height, rgba, depth, seg = p.getCameraImage(
        640,
        480,
        view,
        proj,
        renderer=p.ER_TINY_RENDERER,
    )
    frame = np.reshape(rgba, (height, width, 4))[:, :, :3].astype(np.uint8)
    frames.append(frame)

# 6. 存 GIF 和一张 PNG
os.makedirs(os.path.dirname(GIF_PATH), exist_ok=True)
Image.fromarray(frames[len(frames) // 2]).save(PNG_PATH)

gif_frames = [Image.fromarray(f) for f in frames]
gif_frames[0].save(
    GIF_PATH,
    save_all=True,
    append_images=gif_frames[1:],
    duration=100,
    loop=0,
    optimize=True,
)

print("joints:", num_joints, "ee_link:", ee_link)
print("ik_error_mm: mean=%.2f max=%.2f last=%.2f" % (
    float(np.mean(errors_mm)),
    float(np.max(errors_mm)),
    float(errors_mm[-1]),
))
print("gif:", GIF_PATH, os.path.getsize(GIF_PATH), "bytes")
print("png:", PNG_PATH, os.path.getsize(PNG_PATH), "bytes")
p.disconnect()
