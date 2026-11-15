# 硬件

> 接线图、上电流程、盘点结论。

## ZED 环境（2026-11-14）

- 版本决策：ZED SDK 5.5.1 / CUDA 12.8 / TensorRT 10.9 / NVIDIA 驱动 580.173.02
- 依据：ZED 官方 compatibility 表 + `nvidia-smi`（RTX 4050 Laptop；驱动支持到 CUDA 13.0，实际 toolkit 12.8）
- 相机：ZED-M（当前使用，S/N 15869919）；ZED 2 备用
- ZED-M：USB3，Bus 002，5000M，`bcdUSB 3.00`；HD720@30
- 首帧：`pc/vision/data/frame_0001.npz`（color 720×1280×4 uint8，depth 720×1280 float32；depth 有效率 51.5%，0.30–10.0 m）
- 当前状态：ZED-M 出图成功；ZED 2 经 Hub 时曾出现画面撕裂，直连后再复测

## 资料核对（2026-11-15）

| 资料 | 有/无/需逆向 | 来源 | 结论 |
|---|---|---|---|
| ZLink V1.0.3 专属手册 | 无 | 卖家只给 Windows 上位机 | 需按幻尔协议做只读验证 |
| 幻尔总线舵机控制板协议 | 有 | [二次开发文档](https://wiki.hiwonder.com/projects/Bus-Servo-Controller/en/latest/docs/2.Bus_Servo_Controller_Secondary_Development.html) | 控制器串口 9600，帧头 `0x55 0x55` |
| 舵机 LX-15D 参数 | 有 | [Switch Science 对比表](https://pages.switch-science.com/comparison/hiwonder-servos) | 6–8.4V，堵转 2.4–3A，240°，总线 115200 |
| 舵机 LX-225 / 25KG 参数 | 部分 | [Hiwonder LX-225](https://www.hiwonder.com/collections/all-product/products/lx-225) | 25KG，6–8.4V；堵转电流待产品页确认 |
| STM32 例程 | 有（参考） | 幻尔文档 2.4 STM32 Development | 可改，但不是 ZLink 专属 |

## 关键结论

- **两个波特率不要混**：STM32/PC ↔ ZLink 控制器是 **9600**；ZLink ↔ 舵机总线是 **115200**。
- **舵机 ID 0–253，默认 1**；当前 6 个舵机 ID 为 6/5/4/3/2/1，P2 上电先只读确认。
- **反馈**：LX-15D/LX-225 支持位置、温度、电压回读；P2 的堵转检测可直接用。
- **电流风险**：LX-15D 堵转 2.4–3A；5 个舵机按 `5 × 2.4 × 0.6 ≈ 7.2A` 估算，而 ZLink 板载标称 **5A**。P2 必须限速、分时动作、加 1000–2200µF 电容，并实测电源跌压。
- **资料缺口**：ZLink V1.0.3 没有专属协议手册；先用幻尔协议做只读（读位置/电压），确认后再写角度。
