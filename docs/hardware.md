# 硬件

> 接线图、上电流程、盘点结论。

## ZED 环境（2026-11-12）

- 版本决策：ZED SDK 5.5.1 / CUDA 12.8 / TensorRT 10.9 / NVIDIA 驱动 580.173.02

- 依据：ZED 官方 compatibility 表 + `nvidia-smi`（RTX 4050 Laptop；驱动支持到 CUDA 13.0，实际 toolkit 12.8）

- 相机：ZED-M（当前使用，S/N 15869919）；ZED 2 备用

  - ZED-M：USB3，Bus 002，5000M，`bcdUSB 3.00`；HD720@30
  - 首帧：`pc/vision/data/frame_0001.npz`（color 720×1280×4 uint8，depth 720×1280 float32；depth 有效率 51.5%，0.30–10.0 m）
  - 当前状态：ZED-M 出图成功

  

