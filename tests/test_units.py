import numpy as np
import pytest
from metrilab.core.units import are_compatible, convert_values, format_unit_latex


def test_unit_compatibility_and_conversion():
    assert are_compatible("cm", "m") is True
    assert are_compatible("m/s", "km/h") is True
    assert are_compatible("m/s", "kg") is False

    vals, uncs = convert_values([100.0, 250.0], "cm", "m", uncertainties=[0.5, 0.5])
    assert np.allclose(vals, [1.0, 2.5])
    assert uncs is not None and np.allclose(uncs, [0.005, 0.005])


def test_offset_temperature_conversion_scales_uncertainty_as_delta():
    # 0 °C = 273.15 K, pero incertidumbre de 1 °C sigue siendo 1 K (no 274.15 K)
    vals, uncs = convert_values([0.0, 100.0], "degC", "kelvin", uncertainties=[0.5, 0.5])
    assert np.allclose(vals, [273.15, 373.15])
    assert uncs is not None and np.allclose(uncs, [0.5, 0.5])


def test_incompatible_units_raise_spanish_value_error():
    with pytest.raises(ValueError, match="incompatib"):
        convert_values([1.0, 2.0], "m/s", "kg")


def test_format_unit_latex():
    tex = format_unit_latex("m/s**2")
    assert "m" in tex and "s" in tex
