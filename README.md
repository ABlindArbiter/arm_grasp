# arm-grasp

5 自由度舵机臂 + ZED-M 的视觉抓取项目。

## 当前状态（2026-11-17）

- 阶段：**P1-W5**（运动学 / IK）；P0 已通过，P1-W4 完成。
- 当前任务：5D 任务空间 `(x, y, z, α, φ)`；解析 IK 已支持 α（`α=-90°` 是基线特例）；W5-3 对比库 IK。
- 证据入口：总账 `docs/plan/01_进度台账.md`；DH 表 `docs/dh_table.md`；关节树 `sim/urdf/stock_tree.txt`；测试 `pc/tests/`；ZED 首帧 `pc/vision/data/frame_0001.npz`（本地，未进 git）。
- 运行前提：Ubuntu 22.04 + ROS2 Humble + NVIDIA 40 系（`nvidia-smi` 正常）+ ZED-M；仿真/运动学用项目 `.venv`（见“快速开始”）。
- 当前边界：不接线通电（P2 才上电）；`firmware/` 仍为空。

## 架构

```
PC（视觉 / 抓取 / 运动学） --USB--> STM32（安全转发层） --> ZLink --> 舵机
                ^
                └── ZED-M
```

## 快速开始

### Python 环境（W4 起，仿真 / 运动学）

项目用独立 venv，避免和 ROS2 Humble 的系统 Python 冲突：

```bash
cd ~/arm-grasp
/usr/bin/python3 -m virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

验证：

```bash
python -c "import numpy, scipy, yourdfpy, robot_descriptions; print(numpy.__version__, scipy.__version__)"
pytest -q pc/tests
```

> **ROS2 节点（P2 起）仍用系统 Python**；跑 `ros2` 前不要 `source .venv/bin/activate`。

### 加载现成臂 / 看关节树

```python
from robot_descriptions.loaders.yourdfpy import load_robot_description

robot = load_robot_description("so_arm101_description", load_meshes=False)
print(robot.actuated_joint_names)
```

W4-2 的实际输出存在 `sim/urdf/stock_tree.txt`。

## 结果

（待填：成功率、误差表、视频链接）

## 目录

- `pc/` 上位机
- `firmware/` STM32
- `sim/` PyBullet；`sim/urdf/` 关节树与 `arm5.urdf`
- `docs/` 文档与调试记录
