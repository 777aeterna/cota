import numpy as np
import pytest
from cota.core.validation import (
    parse_safe_expression,
    validate_finite_array,
    validate_positive_uncertainties,
)


def test_validate_finite_array_rejects_nan_and_inf():
    with pytest.raises(ValueError, match="finitos"):
        validate_finite_array([1.0, float("nan"), 3.0], name="x")
    with pytest.raises(ValueError, match="finitos"):
        validate_finite_array([1.0, float("inf")], name="x")


def test_validate_finite_array_enforces_min_length():
    with pytest.raises(ValueError, match="al menos 2"):
        validate_finite_array([1.0], name="x", min_length=2)


def test_validate_positive_uncertainties_rejects_zero_or_negative():
    with pytest.raises(ValueError, match="positivas"):
        validate_positive_uncertainties([0.1, 0.0, 0.2], name="dy", expected_length=3)
    with pytest.raises(ValueError, match="positivas"):
        validate_positive_uncertainties([0.1, -0.5], name="dy", expected_length=2)


def test_parse_safe_expression_allows_math_and_blocks_malicious_code():
    expr, syms = parse_safe_expression("4 * pi**2 * L / T**2", ["L", "T"])
    assert set(syms.keys()) == {"L", "T"}
    assert float(expr.subs({syms["L"]: 1.0, syms["T"]: 2.0}).evalf()) == pytest.approx(
        np.pi**2, rel=1e-6
    )

    with pytest.raises(ValueError, match="inválida|no permitid"):
        parse_safe_expression("__import__('os').system('ls')", ["x"])

    with pytest.raises(ValueError, match="inválida"):
        parse_safe_expression("x + (y", ["x", "y"])

    with pytest.raises(ValueError, match="desconocid"):
        parse_safe_expression("x + z", ["x"])
