import math
import pytest
from metrilab.core.metrology import (
    calculate_type_a,
    calculate_type_b,
    combine_uncertainties,
    format_measurement,
)


def test_type_a_standard_sample():
    # Muestra de 5 mediciones de tiempo de caída
    data = [2.01, 2.03, 1.99, 2.02, 2.00]
    res = calculate_type_a(data)
    assert res.n == 5
    assert res.dof == 4
    assert res.mean == pytest.approx(2.01, abs=1e-9)
    assert res.std_dev == pytest.approx(0.0158113883, rel=1e-6)
    assert res.std_uncertainty == pytest.approx(0.0158113883 / math.sqrt(5), rel=1e-6)
    assert res.shapiro_p_value is not None and 0.0 <= res.shapiro_p_value <= 1.0


def test_type_a_identical_values_and_min_length():
    res = calculate_type_a([5.0, 5.0, 5.0])
    assert res.mean == 5.0
    assert res.std_dev == 0.0
    assert res.std_uncertainty == 0.0

    with pytest.raises(ValueError, match="al menos 2"):
        calculate_type_a([5.0])


def test_type_b_distributions():
    rect = calculate_type_b(0.5, distribution="rectangular")
    assert rect.std_uncertainty == pytest.approx(0.5 / math.sqrt(3), rel=1e-9)

    tri = calculate_type_b(0.6, distribution="triangular")
    assert tri.std_uncertainty == pytest.approx(0.6 / math.sqrt(6), rel=1e-9)

    norm = calculate_type_b(0.4, distribution="normal", divisor=2.0)
    assert norm.std_uncertainty == pytest.approx(0.2, rel=1e-9)

    with pytest.raises(ValueError, match="negativ"):
        calculate_type_b(-0.1, distribution="rectangular")


def test_combine_uncertainties_welch_satterthwaite():
    # u_A = 0.03 (dof=9), u_B = 0.04 (dof=inf) -> u_c = 0.05
    res = combine_uncertainties(
        value=9.8123,
        components=[(0.03, 9), (0.04, float("inf"))],
        confidence_level=0.95,
    )
    assert res.combined_uncertainty == pytest.approx(0.05, rel=1e-9)
    # nu_eff = 0.05^4 / (0.03^4 / 9) = 69.444...
    assert res.effective_dof == pytest.approx(69.444444, rel=1e-4)
    assert res.coverage_factor == pytest.approx(1.9947, rel=1e-3)
    assert res.expanded_uncertainty == pytest.approx(0.05 * res.coverage_factor, rel=1e-6)


def test_format_measurement_gum_rounding():
    # Regla GUM: primer dígito 1 o 2 -> 2 cifras significativas por defecto; >= 3 -> 1 cifra
    txt1, tex1 = format_measurement(9.8123, 0.0432)
    assert txt1 == "9.81 ± 0.04"
    assert tex1 == r"9.81 \pm 0.04"

    txt2, tex2 = format_measurement(9.8123, 0.0148)
    assert txt2 == "9.812 ± 0.015"
    assert tex2 == r"9.812 \pm 0.015"

    # Incertidumbre nula no debe lanzar error
    txt0, tex0 = format_measurement(5.0, 0.0)
    assert txt0 == "5.0 ± 0"
    assert tex0 == r"5.0 \pm 0"
