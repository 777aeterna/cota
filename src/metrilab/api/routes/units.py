"""Endpoints de validación y conversión dimensional de unidades."""

from __future__ import annotations

from fastapi import APIRouter

from metrilab.api.schemas import (
    UnitCompatibilityRequest,
    UnitCompatibilityResponse,
    UnitConvertRequest,
    UnitConvertResponse,
)
from metrilab.core.units import are_compatible, convert_values, format_unit_latex

router = APIRouter(prefix="/api/units", tags=["Unidades"])


@router.post("/compatible", response_model=UnitCompatibilityResponse)
def api_compatible(payload: UnitCompatibilityRequest) -> UnitCompatibilityResponse:
    compatible = are_compatible(payload.unit_from, payload.unit_to)
    return UnitCompatibilityResponse(
        compatible=compatible,
        unit_from_latex=format_unit_latex(payload.unit_from),
        unit_to_latex=format_unit_latex(payload.unit_to),
    )


@router.post("/convert", response_model=UnitConvertResponse)
def api_convert(payload: UnitConvertRequest) -> UnitConvertResponse:
    vals, uncs = convert_values(
        values=payload.values,
        unit_from=payload.unit_from,
        unit_to=payload.unit_to,
        uncertainties=payload.uncertainties,
    )
    return UnitConvertResponse(
        values=[float(v) for v in vals],
        uncertainties=[float(u) for u in uncs] if uncs is not None else None,
        unit_to_latex=format_unit_latex(payload.unit_to),
    )
