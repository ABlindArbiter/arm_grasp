# 硬件

> 接线图、上电流程、盘点结论。

## ZED 环境（2026-11-12）

- 版本决策：ZED SDK 5.5.1 / CUDA 12.8 / TensorRT 10.9 / NVIDIA 驱动 580.173.02
- 依据：ZED 官方 compatibility 表 + `nvidia-smi`（RTX 4050 Laptop；驱动支持到 CUDA 13.0，实际 toolkit 12.8）
- 相机：ZED 2；USB3，Bus 002，5000M，`bcdUSB 3.00`
- 当前状态：SDK 安装成功，`pyzed` 5.5.1；出图受 USB Hub/HID reset 影响，等直连 USB-C 新线
