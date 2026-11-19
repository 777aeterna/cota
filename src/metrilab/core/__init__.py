"""Núcleo matemático y metrológico de MetriLab."""

from metrilab.core.fitting import (
    BUILTIN_MODELS,
    FitParameter,
    FitResult,
    fit_linear_weighted,
    fit_nonlinear,
)
from metrilab.core.metrology import (
    CombinedUncertaintyResult,
    TypeAResult,
    TypeBComponent,
    calculate_type_a,
    calculate_type_b,
    combine_uncertainties,
    format_measurement,
)
from metrilab.core.propagation import (
    AnalyticalPropagationResult,
    MonteCarloResult,
    VariableSpec,
    propagate_analytical,
    propagate_monte_carlo,
)
from metrilab.core.units import are_compatible, convert_values, format_unit_latex

__all__ = [
    "AnalyticalPropagationResult",
    "BUILTIN_MODELS",
    "CombinedUncertaintyResult",
    "FitParameter",
    "FitResult",
    "MonteCarloResult",
    "TypeAResult",
    "TypeBComponent",
    "VariableSpec",
    "are_compatible",
    "calculate_type_a",
    "calculate_type_b",
    "combine_uncertainties",
    "convert_values",
    "fit_linear_weighted",
    "fit_nonlinear",
    "format_measurement",
    "format_unit_latex",
    "propagate_analytical",
    "propagate_monte_carlo",
]
