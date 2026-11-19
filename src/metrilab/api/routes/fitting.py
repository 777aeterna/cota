"""Endpoints de ajuste de curvas lineal (WLS / York) y no lineal."""

from __future__ import annotations

from fastapi import APIRouter

from metrilab.api.schemas import (
    FitModelInfo,
    FitModelsCatalogResponse,
    FitParameterOut,
    FitResponse,
    LinearFitRequest,
    NonlinearFitRequest,
)
from metrilab.core.fitting import (
    BUILTIN_MODELS,
    FitResult,
    fit_linear_weighted,
    fit_nonlinear,
)

router = APIRouter(prefix="/api/fitting", tags=["Ajuste de Curvas"])

_MODEL_METADATA: dict[str, tuple[str, str]] = {
    "linear": ("Lineal", r"y = m x + b"),
    "quadratic": ("Cuadrático", r"y = a x^2 + b x + c"),
    "exponential_decay": ("Decaimiento Exponencial", r"y = y_0 + A e^{-x/\tau}"),
    "damped_oscillator": ("Oscilador Amortiguado", r"y = A e^{-\gamma x} \cos(\omega x + \phi) + y_0"),
    "gaussian": ("Gaussiana (Pico Espectral)", r"y = y_0 + A e^{-\frac{(x-\mu)^2}{2\sigma^2}}"),
    "power_law": ("Ley de Potencias", r"y = A x^b + y_0"),
}


def _serialize_fit(res: FitResult) -> FitResponse:
    return FitResponse(
        model_name=res.model_name,
        parameters={
            k: FitParameterOut(name=p.name, value=p.value, uncertainty=p.uncertainty)
            for k, p in res.parameters.items()
        },
        covariance_matrix=res.covariance_matrix,
        chi_squared=res.chi_squared,
        reduced_chi_squared=res.reduced_chi_squared,
        dof=res.dof,
        p_value=res.p_value,
        r_squared=res.r_squared,
        residuals=res.residuals,
        normalized_residuals=res.normalized_residuals,
        curve_x=res.curve_x,
        curve_y=res.curve_y,
        band_low=res.band_low,
        band_high=res.band_high,
    )


@router.get("/models", response_model=FitModelsCatalogResponse)
def api_list_models() -> FitModelsCatalogResponse:
    items = [
        FitModelInfo(
            id=model_id,
            name=_MODEL_METADATA[model_id][0],
            formula_latex=_MODEL_METADATA[model_id][1],
            parameters=list(param_names),
        )
        for model_id, (_, param_names) in BUILTIN_MODELS.items()
    ]
    return FitModelsCatalogResponse(models=items)


@router.post("/linear", response_model=FitResponse)
def api_fit_linear(payload: LinearFitRequest) -> FitResponse:
    res = fit_linear_weighted(
        x=payload.x,
        y=payload.y,
        dy=payload.dy,
        dx=payload.dx,
        confidence_level=payload.confidence_level,
        grid_points=payload.grid_points,
    )
    return _serialize_fit(res)


@router.post("/nonlinear", response_model=FitResponse)
def api_fit_nonlinear(payload: NonlinearFitRequest) -> FitResponse:
    res = fit_nonlinear(
        x=payload.x,
        y=payload.y,
        model=payload.model,
        dy=payload.dy,
        p0=payload.p0,
        custom_expression=payload.custom_expression,
        param_names=payload.param_names,
        confidence_level=payload.confidence_level,
        grid_points=payload.grid_points,
    )
    return _serialize_fit(res)
