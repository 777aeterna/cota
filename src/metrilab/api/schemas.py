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
