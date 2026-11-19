"""Propagación de incertidumbres: analítica (SymPy/GUM) y Monte Carlo (JCGM 101)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
import sympy

from cota.core.metrology import format_measurement
from cota.core.validation import parse_safe_expression

MCDistribution = Literal["normal", "uniform", "triangular"]


@dataclass(frozen=True)
class VariableSpec:
    """Definición de una variable de entrada con su valor, incertidumbre y distribución."""

    value: float
    uncertainty: float
    distribution: MCDistribution = "normal"


@dataclass(frozen=True)
class AnalyticalPropagationResult:
    """Resultado de propagación analítica por serie de Taylor de primer orden."""

    value: float
    uncertainty: float
    partial_derivatives: dict[str, float]
    variance_contributions: dict[str, float]
    formula_latex: str
    formatted_text: str
    formatted_latex: str


@dataclass(frozen=True)
class MonteCarloResult:
    """Resultado de propagación por simulación de Monte Carlo (JCGM 101)."""

    mean: float
    std_dev: float
    median: float
    ci_low: float
    ci_high: float
    confidence_level: float
    n_samples: int
    histogram_counts: list[int]
    histogram_edges: list[float]
    formatted_text: str
    formatted_latex: str


def _validate_variables(variables: dict[str, VariableSpec]) -> None:
    if not variables:
        raise ValueError("Debe declarar al menos una variable de entrada.")
    for name, spec in variables.items():
        if not math.isfinite(spec.value) or not math.isfinite(spec.uncertainty):
            raise ValueError(f"La variable '{name}' debe tener valor e incertidumbre finitos.")
        if spec.uncertainty < 0:
            raise ValueError(f"La incertidumbre de '{name}' no puede ser negativa.")


def propagate_analytical(
    expression: str,
    variables: dict[str, VariableSpec],
    covariances: dict[tuple[str, str], float] | None = None,
) -> AnalyticalPropagationResult:
    """Propaga incertidumbres simbólicamente con SymPy aplicando la fórmula GUM."""
    _validate_variables(variables)
    var_names = list(variables.keys())
    expr, syms = parse_safe_expression(expression, var_names)

    subs_map = {syms[name]: float(variables[name].value) for name in var_names}
    central_val = float(expr.subs(subs_map).evalf())
    if not math.isfinite(central_val):
        raise ValueError("La evaluación de la expresión en los valores centrales no es finita.")

    partials: dict[str, float] = {}
    raw_terms: dict[str, float] = {}
    latex_terms: list[str] = []

    for name in var_names:
        deriv_expr = sympy.diff(expr, syms[name])
        deriv_val = float(deriv_expr.subs(subs_map).evalf())
        if not math.isfinite(deriv_val):
            raise ValueError(f"La derivada parcial respecto a '{name}' no es finita en el punto evaluado.")
        partials[name] = deriv_val
        u_i = float(variables[name].uncertainty)
        raw_terms[name] = (deriv_val * u_i) ** 2
        if deriv_expr != 0:
            latex_terms.append(rf"\left({sympy.latex(deriv_expr)}\right)^2 u_{{{name}}}^2")

    variance = sum(raw_terms.values())
    if covariances:
        for (v1, v2), cov_val in covariances.items():
            if v1 not in variables or v2 not in variables:
                raise ValueError(f"Covarianza declarada para variables desconocidas: ({v1}, {v2}).")
            if not math.isfinite(cov_val):
                raise ValueError(f"La covarianza entre '{v1}' y '{v2}' debe ser finita.")
            if v1 != v2:
                variance += 2.0 * partials[v1] * partials[v2] * cov_val

    if variance < -1e-15:
        raise ValueError("La varianza combinada resultó negativa; verifique las covarianzas ingresadas.")
    variance = max(0.0, variance)
    uncertainty = math.sqrt(variance)

    diag_sum = sum(raw_terms.values())
    if diag_sum > 0:
        contributions = {name: (term / diag_sum) * 100.0 for name, term in raw_terms.items()}
    else:
        contributions = {name: 0.0 for name in var_names}

    formula_latex = (
        r"u_c = \sqrt{" + " + ".join(latex_terms) + "}" if latex_terms else r"u_c = 0"
    )
    fmt_text, fmt_latex = format_measurement(central_val, uncertainty)

    return AnalyticalPropagationResult(
        value=central_val,
        uncertainty=uncertainty,
        partial_derivatives=partials,
        variance_contributions=contributions,
        formula_latex=formula_latex,
        formatted_text=fmt_text,
        formatted_latex=fmt_latex,
    )


def propagate_monte_carlo(
    expression: str,
    variables: dict[str, VariableSpec],
    n_samples: int = 100_000,
    confidence_level: float = 0.95,
    seed: int | None = None,
    bins: int = 50,
) -> MonteCarloResult:
    """Propaga incertidumbres mediante simulación de Monte Carlo (JCGM 101)."""
    _validate_variables(variables)
    if n_samples < 100:
        raise ValueError("Se requieren al menos 100 muestras para la simulación de Monte Carlo.")
    if not (0.0 < confidence_level < 1.0):
        raise ValueError("El nivel de confianza debe estar entre 0 y 1 (ej. 0.95).")
    if bins < 5:
        raise ValueError("El número de intervalos (bins) del histograma debe ser al menos 5.")

    var_names = list(variables.keys())
    expr, syms = parse_safe_expression(expression, var_names)
    sym_list = [syms[name] for name in var_names]
    func = sympy.lambdify(sym_list, expr, modules="numpy")

    rng = np.random.default_rng(seed)
    sampled_args: list[np.ndarray] = []

    for name in var_names:
        spec = variables[name]
        if spec.uncertainty == 0.0:
            sampled_args.append(np.full(n_samples, spec.value, dtype=np.float64))
        elif spec.distribution == "normal":
            sampled_args.append(rng.normal(spec.value, spec.uncertainty, size=n_samples))
        elif spec.distribution == "uniform":
            half_w = spec.uncertainty * math.sqrt(3.0)
            sampled_args.append(rng.uniform(spec.value - half_w, spec.value + half_w, size=n_samples))
        elif spec.distribution == "triangular":
            half_w = spec.uncertainty * math.sqrt(6.0)
            sampled_args.append(
                rng.triangular(spec.value - half_w, spec.value, spec.value + half_w, size=n_samples)
            )
        else:
            raise ValueError(f"Distribución '{spec.distribution}' no soportada para Monte Carlo.")

    with np.errstate(all="ignore"):
        y_samples = np.asarray(func(*sampled_args), dtype=np.float64)

    if y_samples.ndim == 0:
        y_samples = np.full(n_samples, float(y_samples), dtype=np.float64)

    finite_mask = np.isfinite(y_samples)
    valid = y_samples[finite_mask]
    if len(valid) < max(10, int(0.5 * n_samples)):
        raise ValueError(
            "Demasiadas evaluaciones no finitas en Monte Carlo; verifique el dominio de la expresión."
        )

    mean_val = float(np.mean(valid))
    std_val = float(np.std(valid, ddof=1))
    median_val = float(np.median(valid))
    alpha = 1.0 - confidence_level
    ci_low = float(np.quantile(valid, alpha / 2.0))
    ci_high = float(np.quantile(valid, 1.0 - alpha / 2.0))

    counts, edges = np.histogram(valid, bins=bins)
    fmt_text, fmt_latex = format_measurement(mean_val, std_val)

    return MonteCarloResult(
        mean=mean_val,
        std_dev=std_val,
        median=median_val,
        ci_low=ci_low,
        ci_high=ci_high,
        confidence_level=float(confidence_level),
        n_samples=int(len(valid)),
        histogram_counts=[int(c) for c in counts],
        histogram_edges=[float(e) for e in edges],
        formatted_text=fmt_text,
        formatted_latex=fmt_latex,
    )
