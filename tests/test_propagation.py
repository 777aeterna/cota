import math
import pytest
from metrilab.core.propagation import (
    VariableSpec,
    propagate_analytical,
    propagate_monte_carlo,
)


def test_analytical_propagation_pendulum_gravity():
    # g = 4 * pi^2 * L / T^2
    # L = 1.000 ± 0.002 m, T = 2.006 ± 0.005 s
    vars_spec = {
        "L": VariableSpec(value=1.000, uncertainty=0.002),
        "T": VariableSpec(value=2.006, uncertainty=0.005),
    }
    res = propagate_analytical("4 * pi**2 * L / T**2", vars_spec)
    expected_g = 4 * math.pi**2 * 1.000 / (2.006**2)
    # dg/g = sqrt((dL/L)^2 + (2 dT/T)^2)
    expected_ug = expected_g * math.sqrt((0.002 / 1.000) ** 2 + (2 * 0.005 / 2.006) ** 2)

    assert res.value == pytest.approx(expected_g, rel=1e-6)
    assert res.uncertainty == pytest.approx(expected_ug, rel=1e-6)
    assert sum(res.variance_contributions.values()) == pytest.approx(100.0, abs=1e-6)
    assert r"\partial" in res.formula_latex or "u_" in res.formula_latex


def test_analytical_propagation_with_covariance():
    # f = x - y, u(x)=1, u(y)=1, cov(x,y)=0.5 -> u_f^2 = 1 + 1 - 2*0.5 = 1
    vars_spec = {
        "x": VariableSpec(value=10.0, uncertainty=1.0),
        "y": VariableSpec(value=5.0, uncertainty=1.0),
    }
    res = propagate_analytical("x - y", vars_spec, covariances={("x", "y"): 0.5})
    assert res.value == pytest.approx(5.0)
    assert res.uncertainty == pytest.approx(1.0, rel=1e-6)


def test_monte_carlo_matches_analytical_for_linear_and_handles_distributions():
    vars_spec = {
        "L": VariableSpec(value=1.000, uncertainty=0.002, distribution="normal"),
        "T": VariableSpec(value=2.006, uncertainty=0.005, distribution="normal"),
    }
    ana = propagate_analytical("4 * pi**2 * L / T**2", vars_spec)
    mc = propagate_monte_carlo("4 * pi**2 * L / T**2", vars_spec, n_samples=50_000, seed=42)

    assert mc.mean == pytest.approx(ana.value, rel=1e-3)
    assert mc.std_dev == pytest.approx(ana.uncertainty, rel=2e-2)
    assert mc.ci_low < mc.median < mc.ci_high
    assert len(mc.histogram_counts) == 50
    assert len(mc.histogram_edges) == 51


def test_propagation_rejects_malicious_or_invalid_expression():
    vars_spec = {"x": VariableSpec(value=1.0, uncertainty=0.1)}
    with pytest.raises(ValueError):
        propagate_analytical("__import__('os').system('echo hi')", vars_spec)
