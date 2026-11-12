"""齐次变换最小工具集。

约定：
    T_ab 表示把 b 系的点变到 a 系：
        p_a = T_ab @ p_b
    因此：
        compose(T_01, T_12) == T_01 @ T_12 == T_02
"""

import numpy as np


def rot_z(deg): # 旋转
    """绕 +z 轴旋转，右手系，角度单位是度。"""
    th = np.deg2rad(deg)  # 角度转弧度
    c, s = np.cos(th), np.sin(th)
    return np.array([
        [c, -s, 0.0],
        [s,  c, 0.0],
        [0.0, 0.0, 1.0],
    ])


def make_T(R, t):   # 拼变换
    """用 3x3 旋转 R 和 3 维平移 t 拼出 4x4 齐次变换。"""
    T = np.eye(4)              # 先建单位阵，最后一行自然是 [0, 0, 0, 1]
    T[:3, :3] = np.asarray(R, dtype=float)  # 左上角放旋转
    T[:3, 3] = np.asarray(t, dtype=float).reshape(3)  # 右上角放平移
    return T


def inv_T(T):   # 求逆
    """齐次变换求逆：[R^T, -R^T t; 0, 1]。"""
    T = np.asarray(T, dtype=float)
    R = T[:3, :3]
    t = T[:3, 3]
    Ti = np.eye(4)
    Ti[:3, :3] = R.T           # 旋转的逆就是转置
    Ti[:3, 3] = -R.T @ t       # 平移的逆是 -R^T t
    return Ti


def compose(T1, T2):    # 复合
    """复合变换：T_02 = T_01 @ T_12。"""
    return np.asarray(T1, dtype=float) @ np.asarray(T2, dtype=float)


def apply(T, p):    # 作用到点
    """把 T 作用到一个 3D 点，或 (N, 3) 的点数组。"""
    T = np.asarray(T, dtype=float)
    p = np.asarray(p, dtype=float)
    R = T[:3, :3]
    t = T[:3, 3]
    if p.ndim == 1:
        return R @ p + t       # 单个点：R @ p + t
    return p @ R.T + t         # N 个点：每行一个点
