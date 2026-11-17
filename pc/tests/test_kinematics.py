import math

import numpy as np

from arm.kinematics import fk_dh, ik_analytic, tool_axis


def test_fk_checkpoints():
    """4 个手算检查点，误差应在浮点级别。"""
    cases = [
        ([0, 0, 0, 0, 0], (198.0, 0.0, 158.0), (0.0, 0.0, 1.0)),
        ([0, 0, 0, math.pi / 2, 0], (333.0, 0.0, 23.0), (1.0, 0.0, 0.0)),
        ([0, 0, 0, -math.pi / 2, 0], (63.0, 0.0, 23.0), (-1.0, 0.0, 0.0)),
        ([0, math.pi / 2, 0, 0, 0], (135.0, 0.0, -175.0), (1.0, 0.0, 0.0)),
    ]
    for q, p_exp, z_exp in cases:
        T = fk_dh(q)
        assert np.allclose(T[:3, 3], p_exp, atol=1e-9)
        assert np.allclose(T[:3, 2], z_exp, atol=1e-9)


def test_ik_round_trip_tool_down():
    """alpha=-90：每个可达点 2 解，FK 回代 < 1e-9 mm。"""
    for target in [(150.0, 0.0, 0.0), (100.0, 0.0, 0.0), (120.0, 50.0, 20.0)]:
        sols = ik_analytic(*target, alpha=-math.pi / 2)
        assert len(sols) == 2
        for s in sols:
            T = fk_dh(s["q"])
            assert np.allclose(T[:3, 3], target, atol=1e-9)
            assert np.allclose(T[:3, 2], (0.0, 0.0, -1.0), atol=1e-9)


def test_ik_round_trip_tilted():
    """alpha=-45：同一个 target 斜着抓，FK 回代仍然 < 1e-9 mm。"""
    target = (150.0, 0.0, 100.0)
    sols = ik_analytic(*target, alpha=-math.pi / 4)
    assert len(sols) == 2
    for s in sols:
        T = fk_dh(s["q"])
        assert np.allclose(T[:3, 3], target, atol=1e-9)
        assert np.allclose(T[:3, 2], tool_axis(-math.pi / 4, 0.0), atol=1e-9)


def test_alpha_zero_side_approach():
    """alpha=0：水平朝外，tool z 应该是 (1,0,0)。"""
    target = (150.0, 0.0, 0.0)
    sols = ik_analytic(*target, alpha=0.0)
    assert len(sols) == 2
    for s in sols:
        T = fk_dh(s["q"])
        assert np.allclose(T[:3, 3], target, atol=1e-9)
        assert np.allclose(T[:3, 2], (1.0, 0.0, 0.0), atol=1e-9)


def test_tool_down_rejects_high_target():
    """alpha=-90 够不到 z=100；换成 alpha=-45 就能到。"""
    assert ik_analytic(150.0, 0.0, 100.0, alpha=-math.pi / 2) == []
    assert len(ik_analytic(150.0, 0.0, 100.0, alpha=-math.pi / 4)) == 2
