"""5 DOF 臂的 DH 正/逆运动学（tool 竖直向下）。

约定
----
- 长度单位 mm，角度单位 rad。
- DH 表见 `docs/dh_table.md`；标准 DH：
      T_i = Rz(theta_i) · Tz(d_i) · Tx(a_i) · Rx(alpha_i)
- `q = [q1..q5]` 是 **DH 关节角**，不是舵机角，也不是 URDF 角。
  URDF 的零位和 DH 的零位差一个 `theta_offset`（W5/P2 再对齐）。
- `ik_analytic(x, y, z, yaw)` 假设 **tool 轴竖直向下**；
  返回 elbow-up / elbow-down 两组候选解；不可达时返回 []。
- `yaw` 是夹爪开口方向（rad），先按 `q5 = yaw - q1` 约定；
  这个约定 W5-3 用 FK 验证，可能差一个常数。

阅读顺序
--------
1. `dh_transform` / `fk_dh`：先确认 4 个 FK 检查点。
2. `_wrist_target`：为什么 tool 竖直向下时 z_w = z + L4。
3. `_planar_2r`：余弦定理、两解、可达性。
4. `ik_analytic`：q1 → q2/q3 → q4 → q5。
5. `__main__`：4 个 FK 检查点 + IK 回代 + 你 W5-1 的 3 个 target 为什么无解。
"""
from __future__ import annotations

import math

import numpy as np

# ---- DH 参数（mm）----
D1 = 23.0    # 底座台面 -> J2
A2 = 100.0   # J2 -> J3
A3 = 98.0    # J3 -> J4
L4 = 135.0   # J4 -> TCP（tool 偏移）

# ---- 你的占位 limit（度，DH 角从机械下限算起）----
LIMITS_DEG = [(0.0, 300.0), (0.0, 180.0), (0.0, 250.0), (0.0, 240.0), (0.0, 240.0)]


def _wrap(a: float) -> float:
    """把角度折到 [-pi, pi)。"""
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def rot_x(t: float) -> np.ndarray:
    c, s = math.cos(t), math.sin(t)
    return np.array([[1.0, 0.0, 0.0],
                     [0.0, c, -s],
                     [0.0, s, c]])


def rot_z(t: float) -> np.ndarray:
    c, s = math.cos(t), math.sin(t)
    return np.array([[c, -s, 0.0],
                     [s, c, 0.0],
                     [0.0, 0.0, 1.0]])


def dh_transform(a: float, alpha: float, d: float, theta: float) -> np.ndarray:
    """标准 DH 单行：T = Rz(theta) · Tz(d) · Tx(a) · Rx(alpha)。"""
    ct, st = math.cos(theta), math.sin(theta)
    ca, sa = math.cos(alpha), math.sin(alpha)
    return np.array([
        [ct, -st * ca,  st * sa, a * ct],
        [st,  ct * ca, -ct * sa, a * st],
        [0.0, sa,       ca,      d],
        [0.0, 0.0,      0.0,     1.0],
    ])


def fk_dh(q) -> np.ndarray:
    """DH 正解：输入 5 个 DH 角（rad），返回 T_0_tool（mm）。"""
    T = np.eye(4)
    rows = [
        (0.0, -math.pi / 2, D1, q[0]),
        (A2,  0.0,          0.0, q[1]),
        (A3,  0.0,          0.0, q[2]),
        (0.0,  math.pi / 2, 0.0, q[3]),
        (0.0,  0.0,         0.0, q[4]),
        (0.0,  0.0,         L4,  0.0),   # tool 行：Tz(135)
    ]
    for a, alpha, d, theta in rows:
        T = T @ dh_transform(a, alpha, d, theta)
    return T


def _wrist_target(x: float, y: float, z: float) -> tuple[float, float, float]:
    """tool 竖直向下时，J4 的位置。

    TCP 在 J4 正下方 L4：
        p_tcp = p_J4 + (0, 0, -L4)
    =>  p_J4 = (x, y, z + L4)
    """
    r = math.hypot(x, y)
    z_w = z + L4
    # 平面 2R 的 y 坐标：肩部在 z=D1，wrist 在 z_w
    h = D1 - z_w
    return r, h, z_w


def _planar_2r(r: float, h: float):
    """平面 2R 逆解：返回 [(q2, q3), ...]，0/2 组。

    r = A2 cos(q2) + A3 cos(q2+q3)
    h = A2 sin(q2) + A3 sin(q2+q3)
    余弦定理：
        cos(q3) = (r^2 + h^2 - A2^2 - A3^2) / (2 A2 A3)
        q3 = ± acos(...)
        q2 = atan2(h, r) - atan2(A3 sin q3, A2 + A3 cos q3)
    """
    c3 = (r * r + h * h - A2 * A2 - A3 * A3) / (2.0 * A2 * A3)
    if c3 < -1.0 - 1e-9 or c3 > 1.0 + 1e-9:
        return []                      # 太远 / 太近，2R 够不到
    c3 = max(-1.0, min(1.0, c3))
    q3_abs = math.acos(c3)
    sols = []
    for q3 in (q3_abs, -q3_abs):
        q2 = math.atan2(h, r) - math.atan2(A3 * math.sin(q3), A2 + A3 * math.cos(q3))
        sols.append((q2, q3))
    return sols


def ik_analytic(x: float, y: float, z: float, yaw: float = 0.0):
    """tool 竖直向下的 5 DOF 解析逆解。

    参数：TCP 目标 (x, y, z) mm，夹爪 yaw rad。
    返回：[{"q": [q1..q5], "elbow": "up"/"down"}, ...]
          不可达时返回 []。

    注意：
    - q1 = atan2(y, x)。目标在基座正上方（r=0）时 q1 任意，这里取 0。
    - q4 = pi - q2 - q3，让 tool 轴 = (0,0,-1)。
    - q5 = yaw - q1，让夹爪绕 tool 轴转到目标 yaw（约定待 FK 验证）。
    """
    r, h, _ = _wrist_target(x, y, z)

    # r=0 时 atan2(0,0) 没有意义；这是 J1 奇异，取 q1=0 作为代表解
    q1 = math.atan2(y, x) if r > 1e-9 else 0.0

    sols = []
    for q2, q3 in _planar_2r(r, h):
        q4 = math.pi - q2 - q3          # tool 竖直向下
        q5 = yaw - q1                   # 夹爪 yaw（约定）
        sols.append({
            "q": [_wrap(q1), _wrap(q2), _wrap(q3), _wrap(q4), _wrap(q5)],
            "elbow": "up" if q3 >= 0.0 else "down",
        })
    return sols


def within_placeholder_limits(q, tol_deg: float = 1e-6) -> bool:
    """按台账的占位 limit（0..range，度）检查 DH 角。

    仅用于 W5 自检；真正的 limit 要等 theta_offset/舵机方向校准后再用。
    """
    for qi, (lo, hi) in zip(q, LIMITS_DEG):
        deg = math.degrees(qi) % 360.0
        if deg < lo - tol_deg or deg > hi + tol_deg:
            return False
    return True


def _fmt_q(q) -> str:
    return "[" + ", ".join(f"{math.degrees(v):7.2f}" for v in q) + "]"


if __name__ == "__main__":
    print("=== 1) FK 检查点（DH 系，mm）===")
    cases = [
        ([0, 0, 0, 0, 0],          (198.0, 0.0, 158.0), (0.0, 0.0, 1.0)),
        ([0, 0, 0, math.pi / 2, 0], (333.0, 0.0, 23.0),  (1.0, 0.0, 0.0)),
        ([0, 0, 0, -math.pi / 2, 0], (63.0, 0.0, 23.0),  (-1.0, 0.0, 0.0)),
        ([0, math.pi / 2, 0, 0, 0], (135.0, 0.0, -175.0), (1.0, 0.0, 0.0)),
    ]
    for q, p_exp, z_exp in cases:
        T = fk_dh(q)
        p = T[:3, 3]
        z = T[:3, 2]
        ep = float(np.linalg.norm(p - np.array(p_exp)))
        ez = float(np.linalg.norm(z - np.array(z_exp)))
        print(f"q={_fmt_q(q)}  TCP={np.round(p, 3)}  err_p={ep:.2e} mm  "
              f"tool_z={np.round(z, 3)}  err_z={ez:.2e}")

    print("\n=== 2) IK 回代（tool 竖直向下，可达点）===")
    targets = [(150.0, 0.0, 0.0), (100.0, 0.0, 0.0), (120.0, 50.0, 20.0)]
    for x, y, z in targets:
        sols = ik_analytic(x, y, z, yaw=0.0)
        print(f"\ntarget=({x}, {y}, {z})  ->  {len(sols)} solution(s)")
        for s in sols:
            T = fk_dh(s["q"])
            err = float(np.linalg.norm(T[:3, 3] - np.array([x, y, z])))
            tz = T[:3, 2]
            ok = within_placeholder_limits(s["q"])
            print(f"  {s['elbow']:4s} q={_fmt_q(s['q'])}  "
                  f"err={err:.2e} mm  tool_z={np.round(tz, 3)}  "
                  f"limits={'OK' if ok else 'OUT'}")

    print("\n=== 3) 你 W5-1 的 3 个 target：tool 竖直向下时 ===")
    for x, y, z in [(150.0, 0.0, 100.0), (120.0, 100.0, 120.0), (180.0, -50.0, 80.0)]:
        sols = ik_analytic(x, y, z, yaw=0.0)
        print(f"target=({x}, {y}, {z})  ->  {len(sols)} solution(s)  "
              f"{'（2R 够不到，库 IK 能到是因为它把 tool 倾了）' if not sols else ''}")
