"""5 DOF 臂的 DH 正/逆运动学（工具轴仰角 alpha 是入参）。

约定
----
- 长度单位 mm，角度单位 rad。
- DH 表见 `docs/dh_table.md`；标准 DH：
      T_i = Rz(theta_i) · Tz(d_i) · Tx(a_i) · Rx(alpha_i)
- `q = [q1..q5]` 是 **DH 关节角**，不是舵机角，也不是 URDF 角。
  URDF 的零位和 DH 的零位差一个 `theta_offset`（W5/P2 再对齐）。
- 任务空间是 **5 维**：`(x, y, z, alpha, phi)`
      alpha：工具轴相对水平面的仰角；垂直向下 = -pi/2，水平朝外 = 0
      phi  ：夹爪绕工具轴的自转（开口方向）
  工具轴在 J1 的竖直平面内：方位角被 J1 锁死，仰角自由。
- `alpha = -pi/2` 就是“垂直下抓”特例，原 baseline 不用推翻。

阅读顺序
--------
1. `dh_transform` / `fk_dh`：先确认 4 个 FK 检查点。
2. `tool_axis` / `_wrist_target`：为什么 `w = p - L4 * a(alpha)`。
3. `_planar_2r`：余弦定理、两解、可达性。
4. `ik_analytic`：q1 → 2R → q4 → q5。
5. `__main__`：FK 检查点 + tool-down / 斜抓回代。
"""
from __future__ import annotations

import math

import numpy as np

# ---- DH 参数（mm）----
D1 = 19.0    # 八角台面 -> J2（2026-11-22 实测；旧 23 作废）
A2 = 100.0   # J2 -> J3
A3 = 98.0    # J3 -> J4
L4 = 135.0   # J4 -> TCP（工具偏移）

# ---- 你的占位 limit（度，DH 角从机械下限算起）----
LIMITS_DEG = [(0.0, 300.0), (0.0, 180.0), (0.0, 250.0), (0.0, 240.0), (0.0, 240.0)]


def _wrap(a: float) -> float:
    """把角度折到 [-pi, pi)。"""
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def rot_x(t: float) -> np.ndarray:
    # 基础旋转矩阵，绕 X 轴旋转 t 弧度（未使用）
    c, s = math.cos(t), math.sin(t)
    return np.array([[1.0, 0.0, 0.0],
                     [0.0, c, -s],
                     [0.0, s, c]])


def rot_z(t: float) -> np.ndarray:
    # 基础旋转矩阵，绕 Z 轴旋转 t 弧度（未使用）
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


def tool_axis(alpha: float, q1: float) -> np.ndarray:
    """工具轴单位向量 a(alpha)，在 J1 的竖直平面内。

    alpha = -pi/2 -> (0, 0, -1)   垂直向下
    alpha = 0     -> (cos q1, sin q1, 0)  水平朝外
    alpha = pi    -> (-cos q1, -sin q1, 0) 水平朝基座
    """
    c, s = math.cos(alpha), math.sin(alpha)
    return np.array([c * math.cos(q1), c * math.sin(q1), s])


def _wrist_target(x: float, y: float, z: float, alpha: float):
    """把带姿态的目标化成腕点：w = p - L4 * a(alpha)。

    返回 (q1_arm, r_w, h, alpha_arm, ok)：
    - q1_arm  ：腕点所在竖直平面的方位角（FK 里的 J1）
    - r_w, h  ：平面 2R 的两个坐标
    - alpha_arm：FK 里让工具轴等于 a(alpha) 的仰角（通常 = alpha；
                 腕点在目标反侧时 = pi - alpha）
    """
    r = math.hypot(x, y)
    q1 = math.atan2(y, x) if r > 1e-9 else 0.0
    a = tool_axis(alpha, q1)

    wx = x - L4 * a[0]
    wy = y - L4 * a[1]
    wz = z - L4 * a[2]

    r_w = math.hypot(wx, wy)
    if r_w < 1e-9:
        # 腕点落在基座轴上：J1 奇异，没有唯一 q1
        return q1, 0.0, D1 - wz, alpha, False

    q1_arm = math.atan2(wy, wx)
    if math.cos(q1_arm - q1) < 0.0:
        # 腕点在目标反侧：a(pi - alpha) at q1+pi == a(alpha) at q1
        alpha_arm = math.pi - alpha
    else:
        alpha_arm = alpha

    return q1_arm, r_w, D1 - wz, alpha_arm, True


def _planar_2r(r: float, h: float):
    """平面 2R 逆解：返回 [(q2, q3), ...]，0 或 2 组。

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

    # 求肘角 q3
    c3 = max(-1.0, min(1.0, c3))
    q3_abs = math.acos(c3)
    sols = []
    for q3 in (q3_abs, -q3_abs):
        # 求肩角 q2
        q2 = math.atan2(h, r) - math.atan2(A3 * math.sin(q3), A2 + A3 * math.cos(q3))
        sols.append((q2, q3))
    return sols


def ik_analytic(x: float, y: float, z: float, alpha: float = -math.pi / 2, phi: float = 0.0):
    """5 DOF 解析逆解：目标 = TCP (x,y,z) + 工具仰角 alpha + 夹爪自转 phi。

    返回：[{"q": [q1..q5], "elbow": "up"/"down", "alpha": alpha}, ...]
          不可达时返回 []。

    q4 用 DH 系推导：
        tool z = (sin(q234) cos q1, sin(q234) sin q1, cos(q234))
        令 q234 = pi/2 - alpha，则 tool z = (cos alpha cos q1, ..., sin alpha)
        => q4 = pi/2 - alpha - q2 - q3
    计划里的 `J4 = alpha - (J2+J3) - 零位偏置` 是关节角约定，
    和这里的 DH q4 差一个常数，偏置吸收。
    """
    q1_arm, r_w, h, alpha_arm, ok = _wrist_target(x, y, z, alpha)
    if not ok:
        return []

    sols = []
    for q2, q3 in _planar_2r(r_w, h):
        q4 = math.pi / 2 - alpha_arm - q2 - q3
        q5 = phi - q1_arm
        sols.append({
            "q": [_wrap(q1_arm), _wrap(q2), _wrap(q3), _wrap(q4), _wrap(q5)],
            "elbow": "up" if q3 >= 0.0 else "down",
            "alpha": alpha,
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
        ([0, 0, 0, 0, 0],           (198.0, 0.0, 154.0), (0.0, 0.0, 1.0)),
        ([0, 0, 0, math.pi / 2, 0], (333.0, 0.0, 19.0),  (1.0, 0.0, 0.0)),
        ([0, 0, 0, -math.pi / 2, 0], (63.0, 0.0, 19.0),  (-1.0, 0.0, 0.0)),
        ([0, math.pi / 2, 0, 0, 0], (135.0, 0.0, -179.0), (1.0, 0.0, 0.0)),
    ]
    for q, p_exp, z_exp in cases:
        T = fk_dh(q)
        p = T[:3, 3]
        z = T[:3, 2]
        ep = float(np.linalg.norm(p - np.array(p_exp)))
        ez = float(np.linalg.norm(z - np.array(z_exp)))
        print(f"q={_fmt_q(q)}  TCP={np.round(p, 3)}  err_p={ep:.2e} mm  "
              f"tool_z={np.round(z, 3)}  err_z={ez:.2e}")

    print("\n=== 2) tool-down（alpha=-90）可达点 ===")
    for x, y, z in [(150.0, 0.0, 0.0), (100.0, 0.0, 0.0), (120.0, 50.0, 20.0)]:
        sols = ik_analytic(x, y, z, alpha=-math.pi / 2)
        print(f"\ntarget=({x}, {y}, {z})  ->  {len(sols)} solution(s)")
        for s in sols:
            T = fk_dh(s["q"])
            err = float(np.linalg.norm(T[:3, 3] - np.array([x, y, z])))
            print(f"  {s['elbow']:4s} q={_fmt_q(s['q'])}  err={err:.2e} mm  "
                  f"tool_z={np.round(T[:3, 2], 3)}  "
                  f"limits={'OK' if within_placeholder_limits(s['q']) else 'OUT'}")

    print("\n=== 3) 斜抓（alpha=-45）===")
    for x, y, z in [(150.0, 0.0, 0.0), (150.0, 0.0, 100.0)]:
        sols = ik_analytic(x, y, z, alpha=-math.pi / 4)
        print(f"\ntarget=({x}, {y}, {z})  ->  {len(sols)} solution(s)")
        for s in sols:
            T = fk_dh(s["q"])
            err = float(np.linalg.norm(T[:3, 3] - np.array([x, y, z])))
            print(f"  {s['elbow']:4s} q={_fmt_q(s['q'])}  err={err:.2e} mm  "
                  f"tool_z={np.round(T[:3, 2], 3)}  "
                  f"limits={'OK' if within_placeholder_limits(s['q']) else 'OUT'}")

    print("\n=== 4) W5-1 的 (150,0,100)：alpha=-90 vs alpha=-45 ===")
    for a_deg in (-90, -45):
        sols = ik_analytic(150.0, 0.0, 100.0, alpha=math.radians(a_deg))
        print(f"alpha={a_deg:4d} deg  ->  {len(sols)} solution(s)")
