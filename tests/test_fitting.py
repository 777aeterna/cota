import numpy as np
import pytest
from cota.core.fitting import fit_linear_weighted, fit_nonlinear


def test_linear_weighted_wls_exact_line():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = 2.5 * x + 1.0
    dy = np.array([0.1, 0.1, 0.1, 0.1, 0.1])

    res = fit_linear_weighted(x, y, dy)
    assert res.parameters["m"].value == pytest.approx(2.5, rel=1e-6)
    assert res.parameters["b"].value == pytest.approx(1.0, rel=1e-6)
    assert res.chi_squared == pytest.approx(0.0, abs=1e-10)
    assert res.dof == 3
    assert res.r_squared == pytest.approx(1.0, rel=1e-6)
    assert len(res.curve_x) == 100


def test_linear_weighted_york_with_dx_and_dy():
    # Dataset clásico de York (1966) / Pearson
    x = np.array([0.0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4])
    y = np.array([5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5])
    wx = np.array([1000.0, 1000.0, 500.0, 800.0, 200.0, 80.0, 60.0, 20.0, 1.8, 1.0])
    wy = np.array([1.0, 1.8, 4.0, 8.0, 20.0, 20.0, 70.0, 70.0, 100.0, 500.0])
    dx = 1.0 / np.sqrt(wx)
    dy = 1.0 / np.sqrt(wy)

    res = fit_linear_weighted(x, y, dy=dy, dx=dx)
    # Valores de referencia publicados en York et al. (2004)
    assert res.parameters["m"].value == pytest.approx(-0.48053, abs=1e-4)
    assert res.parameters["b"].value == pytest.approx(5.47991, abs=1e-4)
    assert res.parameters["m"].uncertainty == pytest.approx(0.0576, abs=2e-3)


def test_nonlinear_exponential_decay_and_custom_expression():
    x = np.linspace(0, 5, 30)
    y = 1.5 + 10.0 * np.exp(-x / 2.0)
    dy = np.full_like(x, 0.05)

    res = fit_nonlinear(x, y, model="exponential_decay", dy=dy)
    assert res.parameters["y0"].value == pytest.approx(1.5, rel=1e-3)
    assert res.parameters["A"].value == pytest.approx(10.0, rel=1e-3)
    assert res.parameters["tau"].value == pytest.approx(2.0, rel=1e-3)

    custom = fit_nonlinear(
        x,
        y,
        model="custom",
        dy=dy,
        custom_expression="c + a * exp(-x / t)",
        param_names=["c", "a", "t"],
        p0={"c": 1.0, "a": 8.0, "t": 1.5},
    )
    assert custom.parameters["a"].value == pytest.approx(10.0, rel=1e-3)
    assert custom.parameters["t"].value == pytest.approx(2.0, rel=1e-3)


def test_fitting_validation_edge_cases():
    # Grados de libertad insuficientes (3 puntos para cuadrática de 3 params -> dof=0)
    with pytest.raises(ValueError, match="al menos"):
        fit_nonlinear([1, 2, 3], [1, 4, 9], model="quadratic")

    # Incertidumbre nula en ajuste ponderado
    with pytest.raises(ValueError, match="positivas"):
        fit_linear_weighted([1, 2, 3, 4], [2, 4, 6, 8], dy=[0.1, 0.0, 0.1, 0.1])
