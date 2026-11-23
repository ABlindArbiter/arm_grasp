import math

import numpy as np

from arm.trajectory import joint_trajectory, trapezoid_profile


def test_trapezoid_shape():
    """距离够长：梯形，能到 vmax。"""
    t, q, v, a = trapezoid_profile(1.0, 1.0, 2.0, 0.01)

    assert abs(t[-1] - 1.5) < 1e-9          # 2*0.5 + 0.5
    assert abs(q[0]) < 1e-12
    assert abs(q[-1] - 1.0) < 1e-9
    assert abs(v[0]) < 1e-12
    assert abs(v[-1]) < 1e-12
    assert np.max(np.abs(v)) <= 1.0 + 1e-9
    assert np.max(np.abs(a)) <= 2.0 + 1e-9


def test_triangular_shape():
    """距离太短：三角形，到不了 vmax。"""
    t, q, v, a = trapezoid_profile(0.1, 1.0, 2.0, 0.001)

    t_expect = 2.0 * math.sqrt(0.1 / 2.0)
    v_peak = math.sqrt(0.1 * 2.0)           # vpeak = sqrt(dq*amax)

    assert abs(t[-1] - t_expect) < 1e-9
    assert abs(q[-1] - 0.1) < 1e-9
    assert np.max(np.abs(v)) <= v_peak + 1e-6
    assert np.max(np.abs(v)) > 0.99 * v_peak
    assert np.max(np.abs(a)) <= 2.0 + 1e-9


def test_zero_distance():
    """dq=0：只有一个点。"""
    t, q, v, a = trapezoid_profile(0.0, 1.0, 2.0, 0.01)

    assert len(t) == 1
    assert t[0] == 0.0
    assert q[0] == 0.0
    assert v[0] == 0.0
    assert a[0] == 0.0


def test_negative_distance():
    """负方向：q/v 取反，速度下限 -vmax。"""
    t, q, v, a = trapezoid_profile(-1.0, 1.0, 2.0, 0.01)

    assert abs(q[-1] + 1.0) < 1e-9
    assert np.min(v) >= -1.0 - 1e-9
    assert np.max(np.abs(a)) <= 2.0 + 1e-9


def test_velocity_continuity():
    """速度连续：相邻采样点的速度差不超过 amax*dt（允许一点浮点余量）。"""
    dt = 0.01
    t, q, v, a = trapezoid_profile(1.0, 1.0, 2.0, dt)

    dv = np.abs(np.diff(v))
    assert np.max(dv) <= 2.0 * dt * 1.5


def test_joint_trajectory_offset():
    """joint_trajectory 只是把位移平移到 q0。"""
    t, q, v, a = joint_trajectory(0.5, 1.5, 1.0, 2.0, 0.01)

    assert abs(q[0] - 0.5) < 1e-12
    assert abs(q[-1] - 1.5) < 1e-9
    assert abs(v[0]) < 1e-12
    assert abs(v[-1]) < 1e-12
