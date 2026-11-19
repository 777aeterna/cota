"""Endpoints de metrología GUM."""

from __future__ import annotations

import math

from fastapi import APIRouter

from metrilab.api.schemas import (
    CombineUncertaintiesRequest,
    CombineUncertaintiesResponse,
    FormatMeasurementRequest,
    FormatMeasurementResponse,
    TypeARequest,
    TypeAResponse,
    TypeBRequest,
    TypeBResponse,
)
from metrilab.core.metrology import (
    calculate_type_a,
    calculate_type_b,
    combine_uncertainties,
    format_measurement,
)

router = APIRouter(prefix="/api/metrology", tags=["Metrología"])


@router.post("/type-a", response_model=TypeAResponse)
def api_type_a(payload: TypeARequest) -> TypeAResponse:
    res = calculate_type_a(payload.values)
    return TypeAResponse(
        mean=res.mean,
        std_dev=res.std_dev,
        std_uncertainty=res.std_uncertainty,
        dof=res.dof,
        n=res.n,
        median=res.median,
        shapiro_p_value=res.shapiro_p_value,
    )


@router.post("/type-b", response_model=TypeBResponse)
def api_type_b(payload: TypeBRequest) -> TypeBResponse:
    dof_in = float("inf") if payload.dof is None else payload.dof
    res = calculate_type_b(
        half_width=payload.half_width,
        distribution=payload.distribution,
        divisor=payload.divisor,
        dof=dof_in,
    )
    return TypeBResponse(
        value=res.value,
        distribution=res.distribution,
        std_uncertainty=res.std_uncertainty,
        dof=None if math.isinf(res.dof) else res.dof,
    )


@router.post("/combine", response_model=CombineUncertaintiesResponse)
def api_combine(payload: CombineUncertaintiesRequest) -> CombineUncertaintiesResponse:
    comps = [
        (c.uncertainty, float("inf") if c.dof is None else c.dof)
        for c in payload.components
    ]
    res = combine_uncertainties(
        value=payload.value,
        components=comps,
        confidence_level=payload.confidence_level,
        sig_figs=payload.sig_figs,
    )
    return CombineUncertaintiesResponse(
        value=res.value,
        combined_uncertainty=res.combined_uncertainty,
        effective_dof=None if math.isinf(res.effective_dof) else res.effective_dof,
        coverage_factor=res.coverage_factor,
        expanded_uncertainty=res.expanded_uncertainty,
        confidence_level=res.confidence_level,
        formatted_text=res.formatted_text,
        formatted_latex=res.formatted_latex,
    )


@router.post("/format", response_model=FormatMeasurementResponse)
def api_format(payload: FormatMeasurementRequest) -> FormatMeasurementResponse:
    text, latex = format_measurement(
        value=payload.value,
        uncertainty=payload.uncertainty,
        sig_figs=payload.sig_figs,
    )
    return FormatMeasurementResponse(formatted_text=text, formatted_latex=latex)
