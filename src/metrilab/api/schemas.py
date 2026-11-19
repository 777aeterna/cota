"""Contratos Pydantic v2 para la API REST de MetriLab."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


# --- Metrología ---


class TypeARequest(BaseModel):
    values: list[float] = Field(..., min_length=2)


class TypeAResponse(BaseModel):
    mean: float
    std_dev: float
    std_uncertainty: float
    dof: int
    n: int
    median: float
    shapiro_p_value: float | None


class TypeBRequest(BaseModel):
    half_width: float = Field(..., ge=0.0)
    distribution: Literal["rectangular", "triangular", "normal"] = "rectangular"
    divisor: float | None = Field(default=None, gt=0.0)
    dof: float | None = Field(default=None, gt=0.0)


class TypeBResponse(BaseModel):
    value: float
    distribution: Literal["rectangular", "triangular", "normal"]
    std_uncertainty: float
    dof: float | None


class UncertaintyComponentIn(BaseModel):
    uncertainty: float = Field(..., ge=0.0)
    dof: float | None = Field(default=None, gt=0.0)


class CombineUncertaintiesRequest(BaseModel):
    value: float
    components: list[UncertaintyComponentIn] = Field(..., min_length=1)
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)
    sig_figs: int | None = Field(default=None, ge=1, le=6)


class CombineUncertaintiesResponse(BaseModel):
    value: float
    combined_uncertainty: float
    effective_dof: float | None
    coverage_factor: float
    expanded_uncertainty: float
    confidence_level: float
    formatted_text: str
    formatted_latex: str


class FormatMeasurementRequest(BaseModel):
    value: float
    uncertainty: float = Field(..., ge=0.0)
    sig_figs: int | None = Field(default=None, ge=1, le=6)


class FormatMeasurementResponse(BaseModel):
    formatted_text: str
    formatted_latex: str


# --- Unidades ---


class UnitCompatibilityRequest(BaseModel):
    unit_from: str = Field(..., min_length=1)
    unit_to: str = Field(..., min_length=1)


class UnitCompatibilityResponse(BaseModel):
    compatible: bool
    unit_from_latex: str
    unit_to_latex: str


class UnitConvertRequest(BaseModel):
    values: list[float] = Field(..., min_length=1)
    unit_from: str = Field(..., min_length=1)
    unit_to: str = Field(..., min_length=1)
    uncertainties: list[float] | None = None


class UnitConvertResponse(BaseModel):
    values: list[float]
    uncertainties: list[float] | None
    unit_to_latex: str


# --- Propagación ---


class VariableSpecIn(BaseModel):
    value: float
    uncertainty: float = Field(..., ge=0.0)
    distribution: Literal["normal", "uniform", "triangular"] = "normal"


class CovarianceEntryIn(BaseModel):
    var1: str
    var2: str
    covariance: float


class AnalyticalPropagationRequest(BaseModel):
    expression: str = Field(..., min_length=1)
    variables: dict[str, VariableSpecIn] = Field(..., min_length=1)
    covariances: list[CovarianceEntryIn] | None = None


class AnalyticalPropagationResponse(BaseModel):
    value: float
    uncertainty: float
    partial_derivatives: dict[str, float]
    variance_contributions: dict[str, float]
    formula_latex: str
    formatted_text: str
    formatted_latex: str


class MonteCarloPropagationRequest(BaseModel):
    expression: str = Field(..., min_length=1)
    variables: dict[str, VariableSpecIn] = Field(..., min_length=1)
    n_samples: int = Field(default=100_000, ge=100, le=500_000)
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)
    seed: int | None = None
    bins: int = Field(default=50, ge=5, le=200)


class MonteCarloPropagationResponse(BaseModel):
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


# --- Ajuste de Curvas ---


class FitModelInfo(BaseModel):
    id: str
    name: str
    formula_latex: str
    parameters: list[str]


class FitModelsCatalogResponse(BaseModel):
    models: list[FitModelInfo]


class FitParameterOut(BaseModel):
    name: str
    value: float
    uncertainty: float


class LinearFitRequest(BaseModel):
    x: list[float] = Field(..., min_length=3)
    y: list[float] = Field(..., min_length=3)
    dy: list[float] = Field(..., min_length=3)
    dx: list[float] | None = None
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)
    grid_points: int = Field(default=100, ge=20, le=500)


class NonlinearFitRequest(BaseModel):
    x: list[float] = Field(..., min_length=3)
    y: list[float] = Field(..., min_length=3)
    model: str = Field(..., min_length=1)
    dy: list[float] | None = None
    p0: dict[str, float] | None = None
    custom_expression: str | None = None
    param_names: list[str] | None = None
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)
    grid_points: int = Field(default=100, ge=20, le=500)


class FitResponse(BaseModel):
    model_name: str
    parameters: dict[str, FitParameterOut]
    covariance_matrix: list[list[float]]
    chi_squared: float
    reduced_chi_squared: float
    dof: int
    p_value: float
    r_squared: float
    residuals: list[float]
    normalized_residuals: list[float]
    curve_x: list[float]
    curve_y: list[float]
    band_low: list[float]
    band_high: list[float]


# --- Datos (CSV / LaTeX) ---


class ParseCsvRequest(BaseModel):
    text: str = Field(..., min_length=1)
    decimal_comma: bool | None = None


class ParseCsvResponse(BaseModel):
    headers: list[str]
    rows: list[list[float]]
    delimiter: str


class LatexColumnIn(BaseModel):
    name: str = Field(..., min_length=1)
    unit: str | None = None
    values: list[float] = Field(..., min_length=1)
    uncertainties: list[float] | None = None


class ExportLatexRequest(BaseModel):
    caption: str = "Resultados experimentales"
    label: str = "tab:resultados"
    columns: list[LatexColumnIn] = Field(..., min_length=1)
    sig_figs: int | None = Field(default=None, ge=1, le=6)


class ExportLatexResponse(BaseModel):
    latex: str
