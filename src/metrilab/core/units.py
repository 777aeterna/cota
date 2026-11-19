"""Validación dimensional y conversión de unidades con soporte para incertidumbres (Pint)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pint

from metrilab.core.validation import validate_finite_array

_UREG = pint.UnitRegistry()
_Q = _UREG.Quantity


def _parse_unit(unit: str) -> pint.Unit:
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("La unidad no puede estar vacía.")
    try:
        return _UREG.Unit(unit.strip())
    except Exception as exc:
        raise ValueError(f"Unidad desconocida o inválida: '{unit}'.") from exc


def are_compatible(unit_from: str, unit_to: str) -> bool:
    """Devuelve True si dos unidades son dimensionalmente compatibles."""
    u_from = _parse_unit(unit_from)
    u_to = _parse_unit(unit_to)
    return bool(u_from.is_compatible_with(u_to))


def convert_values(
    values: Sequence[float] | np.ndarray,
    unit_from: str,
    unit_to: str,
    uncertainties: Sequence[float] | np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Convierte un arreglo de valores y opcionalmente sus incertidumbres entre unidades.

    Las incertidumbres se convierten como diferencias (escala lineal sin offset), por lo que
    unidades con desplazamiento como degC -> kelvin preservan correctamente el delta.
    """
    arr = validate_finite_array(values, name="valores", min_length=1)
    u_from = _parse_unit(unit_from)
    u_to = _parse_unit(unit_to)

    try:
        converted = np.asarray(_Q(arr, u_from).to(u_to).magnitude, dtype=np.float64)
    except pint.DimensionalityError as exc:
        raise ValueError(
            f"Unidades dimensionalmente incompatibles: no se puede convertir de '{unit_from}' a '{unit_to}'."
        ) from exc

    if uncertainties is None:
        return converted, None

    unc_arr = validate_finite_array(uncertainties, name="incertidumbres", min_length=1)
    if len(unc_arr) != len(arr):
        raise ValueError(
            f"Las incertidumbres deben tener la misma longitud que los valores ({len(arr)})."
        )
    if np.any(unc_arr < 0):
        raise ValueError("Las incertidumbres no pueden ser negativas.")

    # Factor de escala lineal sin offset (ej. °C -> K tiene escala 1.0, cm -> m tiene 0.01)
    scale = abs(float(_Q(1.0, u_from).to(u_to).magnitude) - float(_Q(0.0, u_from).to(u_to).magnitude))
    converted_unc = unc_arr * scale
    return converted, converted_unc


def format_unit_latex(unit: str) -> str:
    """Devuelve una representación en LaTeX de la unidad especificada."""
    parsed = _parse_unit(unit)
    return f"{parsed:~L}"
