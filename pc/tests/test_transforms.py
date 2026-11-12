import numpy as np

from arm.transforms import apply, compose, inv_T, make_T, rot_z


def test_inverse_round_trip():
    """验证逆变换和点变换能往返。"""
    T = make_T(rot_z(30), np.array([1.0, 2.0, 3.0]))
    p = np.array([0.5, -0.2, 0.1])

    assert np.allclose(inv_T(T) @ T, np.eye(4), atol=1e-9)
    assert np.allclose(apply(inv_T(T), apply(T, p)), p, atol=1e-9)


def test_rot_z_90():
    """验证绕 z 轴转 90° 后，x 轴会转到 y 轴。"""
    T = make_T(rot_z(90), np.zeros(3))
    p = apply(T, np.array([1.0, 0.0, 0.0]))

    assert np.allclose(p, [0.0, 1.0, 0.0], atol=1e-9)


def test_compose_matches_step_by_step():
    """验证矩阵复合和逐步 apply 的结果一致。"""
    T01 = make_T(rot_z(90), np.array([1.0, 0.0, 0.0]))
    T12 = make_T(np.eye(3), np.array([0.0, 2.0, 0.0]))
    T02 = compose(T01, T12)

    p = np.array([1.0, 0.0, 0.0])
    assert np.allclose(apply(T02, p), apply(T01, apply(T12, p)), atol=1e-9)
