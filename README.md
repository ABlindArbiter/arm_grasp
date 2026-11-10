# arm-grasp

5 自由度舵机臂 + ZED-M 的视觉抓取项目。

## 当前状态（2026-11-10）

- 阶段：P0-W1 地基（硬件盘点 / ZED 环境 / 齐次变换 / 仓库），尚无抓取功能。
- 证据入口：总账 `docs/plan/01_进度台账.md`；测试 `pc/tests/`；文档与照片 `docs/`；ZED 首帧 `pc/vision/data/frame_0001.npz`（Day 4 生成，本地文件，未进 git）。
- 运行前提：Ubuntu 22.04 + ROS2 Humble + NVIDIA 40 系（`nvidia-smi` 正常）+ ZED-M。
- 当前边界：P0 不接线通电；`firmware/` 与 `sim/` 暂为空，运动学从 P1、上电从 P2 开始。

## 架构

```
PC（视觉 / 抓取 / 运动学） --USB--> STM32（安全转发层） --> ZLink --> 舵机
                ^
                └── ZED-M
```

## 快速开始

（待填：环境依赖、启动命令）

## 结果

（待填：成功率、误差表、视频链接）

## 目录

- `pc/` 上位机
- `firmware/` STM32
- `sim/` PyBullet
- `docs/` 文档与调试记录
