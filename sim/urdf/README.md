# arm5.urdf

> P1-W4：拿现成 SO-ARM101 URDF 改成自己的 5 DOF + 夹爪。
> 运动学尺寸来自实测；mesh 是 SO-ARM101 占位，后面可换。

## 1. 结构

```text
base
 └─ joint 1 (J1 yaw) → shoulder
     └─ joint 2 (J2 pitch) → upper_arm
         └─ joint 3 (J3 pitch) → lower_arm
             └─ joint 4 (J4 pitch) → wrist
                 └─ joint 5 (J5 roll) → gripper
                     ├─ joint 6 (夹爪) → jaw
                     └─ tool0_fixed → tool0 (TCP)
```

- `tool0_fixed` 是 fixed joint，不是第 7 个自由度；`getNumJoints=7` 里包含它。
- `joint 6` 是夹爪占位（SO-ARM101 的 revolute jaw）；你的夹爪是平行夹爪，P2/P4 再换。

## 2. DH ↔ URDF 对照

| DH i | URDF joint | parent → child | origin xyz (m) | axis | limit (rad) | 说明 |
|---|---|---|---|---|---|---|
| 1 | joint 1 | base → shoulder | 0 0 0 | 0 0 1 | 0 .. 5.23599 | J1 yaw；原点在八角台面 |
| 2 | joint 2 | shoulder → upper_arm | 0 0 -0.023 | 0 0 1 | 0 .. 3.14159 | J2；`d1=23mm`（写在 shoulder 系，R1 后到 base +z） |
| 3 | joint 3 | upper_arm → lower_arm | -0.100 0 0 | 0 0 1 | 0 .. 4.36332 | J3；`L2=100mm` |
| 4 | joint 4 | lower_arm → wrist | -0.098 0 0 | 0 0 1 | 0 .. 4.18879 | J4；`L3=98mm` |
| 5 | joint 5 | wrist → gripper | 0 0 0 | 0 0 1 | 0 .. 4.18879 | J5 roll；与 J4 共点（DH 约定） |
| — | tool0_fixed | gripper → tool0 | 0 0 0.135 | — | fixed | `L4=135mm` 到 TCP |
| — | joint 6 | gripper → jaw | stock | 0 0 1 | -0.174533 .. 1.74533 | 夹爪占位 |

> `origin xyz` 是**父 link 系**里的平移；`rpy` 保留 stock 值（它决定关节轴方向，不在这里展开）。
> 所有 `axis` 都是 `[0,0,1]` 是关节局部系；物理方向由 `rpy` 决定，这是 URDF 的正常写法。

## 3. 关键约定

- **基座系**：原点在 J1 八角台面中心；桌面 → 台面的 `base_height≈28mm`（8mm 底板 + 八角厚 ~20mm）**不在 URDF 里**，作为单独的 fixed transform 用。
- **limits 是占位值**：J1 0–300°、J2 0–180°、J3 0–250°、J4/J5 0–240°；`theta_offset` 还没做（W5 用 FK 对齐）。
- **mesh 是 stock SO-ARM101 占位**，不是你的臂；视觉后面换，运动学尺寸已经是你的。
- **轴符号**是 stock 的；P2 用舵机方向确认，必要时改 `rpy`。

## 4. 验证

```bash
source .venv/bin/activate
python - <<'PY'
import yourdfpy
r = yourdfpy.URDF.load("sim/urdf/arm5.urdf", load_meshes=False)
print(r.robot.name, r.num_actuated_joints, r.actuated_joint_names)
PY
```

实际输出见 `sim/urdf/arm5_tree.txt`。

## 5. 已知 TODO

- [ ] limits：J1 300°/J3 250° 与 LX-15D 标称 240° 待复核。
- [ ] `theta_offset`：URDF 零位 ≠ 关节零位；W5 用 FK 对齐。
- [ ] axis 符号：stock rpy 保留；P2 用舵机方向确认。
- [ ] mesh：换成自己的臂/夹爪。
- [ ] `base_height`：八角厚度 / 桌面→台面，待卡尺。
