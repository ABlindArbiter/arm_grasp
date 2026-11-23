"""W6-1：关节空间梯形速度曲线。

用途
----
给一个关节从 q0 到 q1，在最大速度 vmax、最大加速度 amax 的限制下，
生成一条 **速度连续** 的 q(t)、v(t)、a(t)。

两种形状
--------
1. 梯形：距离够长，能到 vmax
       v
       │    ┌────────┐
       │   /          \
       │  /            \
       └─┴──────────────┴─→ t
         T_acc  T_const  T_dec

2. 三角形：距离太短，到不了 vmax
       v
       │     /\
       │    /  \
       └───┴────┴─→ t
          T_acc=T_dec

约定
----
- 长度/角度单位任意，只要 vmax、amax 与 dq 同单位。
- dq < 0 时，q/v/a 全部取反；dq = 0 时返回单点。
- 返回值都是 numpy 数组，时间从 0 到 T_total，包含两端。
- 速度在分段连接处连续；加速度在连接处可以跳变（梯形速度的固有特性）。
"""
from __future__ import annotations

import math

import numpy as np


def trapezoid_profile(dq: float, vmax: float, amax: float, dt: float):
    """生成一个关节的梯形速度曲线。

    参数：
        dq   : 目标位移（带符号）
        vmax : 最大速度（>0）
        amax : 最大加速度（>0）
        dt   : 采样周期（>0）

    返回：
        t, q, v, a : (N,) numpy 数组
        q[0]=0, q[-1]=dq, v[0]=v[-1]=0
    """
    if vmax <= 0.0 or amax <= 0.0 or dt <= 0.0:
        raise ValueError("vmax, amax, dt 必须 > 0")

    # 零距离：只有 t=0 一个点
    if abs(dq) < 1e-15:
        z = np.zeros(1)
        return z.copy(), z.copy(), z.copy(), z.copy()

    s = 1.0 if dq > 0.0 else -1.0     # 符号
    d = abs(dq)                       # 正的位移

    # ---- 1) 判断梯形还是三角形 ----
    t_acc = vmax / amax
    d_acc = 0.5 * amax * t_acc * t_acc

    if 2.0 * d_acc >= d:
        # 三角形：还没到 vmax 就要减速
        t_acc = math.sqrt(d / amax)
        v_peak = amax * t_acc
        t_const = 0.0
    else:
        # 梯形：有匀速段
        v_peak = vmax
        t_const = (d - 2.0 * d_acc) / v_peak

    t_total = 2.0 * t_acc + t_const

    # ---- 2) 采样：包含 0 和 t_total ----
    n = max(2, int(math.ceil(t_total / dt)) + 1)
    t = np.linspace(0.0, t_total, n)

    # ---- 3) 三段解析积分 ----
    def q_of(tt: float) -> float:
        if tt <= t_acc:
            return 0.5 * amax * tt * tt
        if tt <= t_acc + t_const:
            return 0.5 * amax * t_acc * t_acc + v_peak * (tt - t_acc)
        td = tt - (t_acc + t_const)
        return (0.5 * amax * t_acc * t_acc
                + v_peak * t_const
                + v_peak * td
                - 0.5 * amax * td * td)

    def v_of(tt: float) -> float:
        if tt <= t_acc:
            return amax * tt
        if tt <= t_acc + t_const:
            return v_peak
        return v_peak - amax * (tt - (t_acc + t_const))

    def a_of(tt: float) -> float:
        # 边界用 0 的加速度，避免同一时刻同时取到 +amax 和 -amax
        if tt < t_acc - 1e-12:
            return amax
        if tt < t_acc + t_const - 1e-12:
            return 0.0
        return -amax

    q = np.array([q_of(x) for x in t])
    v = np.array([v_of(x) for x in t])
    a = np.array([a_of(x) for x in t])

    # 浮点收尾：首尾精确
    q[0] = 0.0
    q[-1] = d
    v[0] = 0.0
    v[-1] = 0.0

    return t, s * q, s * v, s * a


def joint_trajectory(q0: float, q1: float, vmax: float, amax: float, dt: float):
    """把 `trapezoid_profile` 平移到 q0，返回 t, q, v, a。"""
    t, dq, v, a = trapezoid_profile(q1 - q0, vmax, amax, dt)
    return t, q0 + dq, v, a


if __name__ == "__main__":
    print("=== 梯形：dq=1, vmax=1, amax=2 ===")
    t, q, v, a = trapezoid_profile(1.0, 1.0, 2.0, 0.01)
    print(f"T={t[-1]:.4f}s  q[-1]={q[-1]:.6f}  "
          f"max|v|={np.max(np.abs(v)):.4f}  max|a|={np.max(np.abs(a)):.4f}")
    print(f"max |Δv| = {np.max(np.abs(np.diff(v))):.4f}  (应 <= amax*dt≈0.02)")

    print("\n=== 三角形：dq=0.1, vmax=1, amax=2 ===")
    t, q, v, a = trapezoid_profile(0.1, 1.0, 2.0, 0.001)
    print(f"T={t[-1]:.4f}s  q[-1]={q[-1]:.6f}  "
          f"max|v|={np.max(np.abs(v)):.4f}  vpeak≈{math.sqrt(0.1 * 2.0):.4f}")

    print("\n=== 零距离：dq=0 ===")
    t, q, v, a = trapezoid_profile(0.0, 1.0, 2.0, 0.01)
    print(f"len={len(t)}  q={q[0]}  v={v[0]}  a={a[0]}")

    print("\n=== 负方向：dq=-1 ===")
    t, q, v, a = trapezoid_profile(-1.0, 1.0, 2.0, 0.01)
    print(f"q[-1]={q[-1]:.6f}  min(v)={np.min(v):.4f}  max|a|={np.max(np.abs(a)):.4f}")
