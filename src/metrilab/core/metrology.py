"""Motor de metrología conforme a la guía GUM (JCGM 100:2008)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy import stats

from metrilab.core.validation import validate_finite_array

DistributionType = Literal["rectangular", "triangular", "normal"]


@dataclass(frozen=True)
class TypeAResult:
    """Resultado del análisis estadístico Tipo A."""

    mean: float
    std_dev: float
    std_uncertainty: float
    dof: int
    n: int
    median: float
    shapiro_p_value: float | None


@dataclass(frozen=True)
class TypeBComponent:
    """Componente de incertidumbre estándar Tipo B."""

    value: float
    distribution: DistributionType
    std_uncertainty: float
    dof: float


@dataclass(frozen=True)
class CombinedUncertaintyResult:
    """Resultado de combinación GUM (Welch-Satterthwaite) e incertidumbre expandida."""

    value: float
    combined_uncertainty: float
    effective_dof: float
    coverage_factor: float
    expanded_uncertainty: float
    confidence_level: float
    formatted_text: str
    formatted_latex: str


def calculate_type_a(values: Sequence[float] | np.ndarray) -> TypeAResult:
    """Calcula estadísticos descriptivos e incertidumbre estándar Tipo A (s / sqrt(n))."""
    arr = validate_finite_array(values, name="muestra", min_length=2)
    n = int(len(arr))
    mean = float(np.mean(arr))
    std_dev = float(np.std(arr, ddof=1))
    std_uncertainty = std_dev / math.sqrt(n)
    median = float(np.median(arr))

    shapiro_p: float | None = None
    if n >= 3 and (float(np.max(arr)) - float(np.min(arr))) > 0.0:
        _, p_val = stats.shapiro(arr)
        shapiro_p = float(p_val)

    return TypeAResult(
        mean=mean,
        std_dev=std_dev,
        std_uncertainty=std_uncertainty,
        dof=n - 1,
        n=n,
        median=median,
        shapiro_p_value=shapiro_p,
    )


def calculate_type_b(
    half_width: float,
    distribution: DistributionType = "rectangular",
    divisor: float | None = None,
    dof: float = float("inf"),
) -> TypeBComponent:
    """Calcula incertidumbre estándar Tipo B a partir de la semiamplitud y distribución."""
    if not math.isfinite(half_width):
        raise ValueError("La semiamplitud debe ser un número finito.")
    if half_width < 0:
        raise ValueError("La semiamplitud de incertidumbre Tipo B no puede ser negativa.")
    if dof <= 0:
        raise ValueError("Los grados de libertad deben ser mayores a 0.")

    if distribution == "rectangular":
        u_std = half_width / math.sqrt(3.0)
    elif distribution == "triangular":
        u_std = half_width / math.sqrt(6.0)
    elif distribution == "normal":
        div = 2.0 if divisor is None else divisor
        if not math.isfinite(div) or div <= 0:
            raise ValueError("El divisor para distribución normal debe ser positivo y finito.")
        u_std = half_width / div
    else:
        raise ValueError(
            f"Distribución '{distribution}' no soportada. Use 'rectangular', 'triangular' o 'normal'."
        )

    return TypeBComponent(
        value=float(half_width),
        distribution=distribution,
        std_uncertainty=float(u_std),
        dof=float(dof),
    )


def format_measurement(
    value: float,
    uncertainty: float,
    sig_figs: int | None = None,
) -> tuple[str, str]:
    """Formatea una medición (valor ± incertidumbre) siguiendo reglas metrológicas GUM.

    Si `sig_figs` es None, usa la regla estándar: 2 cifras significativas cuando el primer
    dígito significativo de la incertidumbre es 1 o 2, y 1 cifra si es >= 3.
    """
    if not math.isfinite(value) or not math.isfinite(uncertainty):
        raise ValueError("El valor y la incertidumbre deben ser finitos.")
    if uncertainty < 0:
        raise ValueError("La incertidumbre no puede ser negativa.")
    if sig_figs is not None and sig_figs < 1:
        raise ValueError("El número de cifras significativas debe ser al menos 1.")

    if uncertainty == 0.0:
        text = f"{value} ± 0"
        latex = rf"{value} \pm 0"
        return text, latex

    exponent = math.floor(math.log10(abs(uncertainty)))
    if sig_figs is None:
        first_digit = int(math.floor(abs(uncertainty) / (10.0**exponent) + 1e-12))
        eff_sig_figs = 2 if first_digit in (1, 2) else 1
    else:
        eff_sig_figs = sig_figs

    decimals = -exponent + (eff_sig_figs - 1)
    rounded_u = round(uncertainty, decimals)

    # Reevaluar por si el redondeo cambió el orden de magnitud (ej. 0.099 -> 0.10)
    new_exp = math.floor(math.log10(abs(rounded_u)))
    if new_exp != exponent:
        decimals = -new_exp + (eff_sig_figs - 1)
        rounded_u = round(uncertainty, decimals)

    rounded_v = round(value, decimals)

    if decimals > 0:
        v_str = f"{rounded_v:.{decimals}f}"
        u_str = f"{rounded_u:.{decimals}f}"
    else:
        v_str = f"{int(round(rounded_v))}"
        u_str = f"{int(round(rounded_u))}"

    return f"{v_str} ± {u_str}", rf"{v_str} \pm {u_str}"


def combine_uncertainties(
    value: float,
    components: Sequence[tuple[float, float]],
    confidence_level: float = 0.95,
    sig_figs: int | None = None,
) -> CombinedUncertaintyResult:
    """Combina componentes de incertidumbre (u_i, dof_i) mediante suma en cuadratura
    y fórmula de Welch-Satterthwaite para grados efectivos de libertad."""
    if not math.isfinite(value):
        raise ValueError("El valor central debe ser finito.")
    if not components:
        raise ValueError("Debe proporcionar al menos una componente de incertidumbre.")
    if not (0.0 < confidence_level < 1.0):
        raise ValueError("El nivel de confianza debe estar entre 0 y 1 (ej. 0.95).")

    u_sq_sum = 0.0
    ws_denom = 0.0
    for idx, (u_i, dof_i) in enumerate(components):
        if not math.isfinite(u_i) or u_i < 0:
            raise ValueError(f"La incertidumbre de la componente {idx} debe ser finita y >= 0.")
        if dof_i <= 0 or math.isnan(dof_i):
            raise ValueError(f"Los grados de libertad de la componente {idx} deben ser > 0.")
        u_sq_sum += u_i**2
        if math.isfinite(dof_i) and u_i > 0:
            ws_denom += (u_i**4) / dof_i

    u_c = math.sqrt(u_sq_sum)
    if u_c == 0.0 or ws_denom == 0.0:
        eff_dof = float("inf")
        k = float(stats.norm.ppf((1.0 + confidence_level) / 2.0))
    else:
        eff_dof = (u_c**4) / ws_denom
        k = float(stats.t.ppf((1.0 + confidence_level) / 2.0, df=eff_dof))

    u_exp = k * u_c
    fmt_text, fmt_latex = format_measurement(value, u_exp, sig_figs=sig_figs)

    return CombinedUncertaintyResult(
        value=float(value),
        combined_uncertainty=float(u_c),
        effective_dof=float(eff_dof),
        coverage_factor=float(k),
        expanded_uncertainty=float(u_exp),
        confidence_level=float(confidence_level),
        formatted_text=fmt_text,
        formatted_latex=fmt_latex,
    )
