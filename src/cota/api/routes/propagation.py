"""Endpoints de propagación de incertidumbres (Analítica y Monte Carlo)."""

from __future__ import annotations

from fastapi import APIRouter

from cota.api.schemas import (
    AnalyticalPropagationRequest,
    AnalyticalPropagationResponse,
    MonteCarloPropagationRequest,
    MonteCarloPropagationResponse,
)
from cota.core.propagation import (
    VariableSpec,
    propagate_analytical,
    propagate_monte_carlo,
)

router = APIRouter(prefix="/api/propagation", tags=["Propagación"])


@router.post("/analytical", response_model=AnalyticalPropagationResponse)
def api_propagate_analytical(payload: AnalyticalPropagationRequest) -> AnalyticalPropagationResponse:
    vars_map = {
        name: VariableSpec(
            value=spec.value,
            uncertainty=spec.uncertainty,
            distribution=spec.distribution,
        )
        for name, spec in payload.variables.items()
    }
    cov_map = (
        {(entry.var1, entry.var2): entry.covariance for entry in payload.covariances}
        if payload.covariances
        else None
    )
    res = propagate_analytical(payload.expression, vars_map, covariances=cov_map)
    return AnalyticalPropagationResponse(
        value=res.value,
        uncertainty=res.uncertainty,
        partial_derivatives=res.partial_derivatives,
        variance_contributions=res.variance_contributions,
        formula_latex=res.formula_latex,
        formatted_text=res.formatted_text,
        formatted_latex=res.formatted_latex,
    )


@router.post("/monte-carlo", response_model=MonteCarloPropagationResponse)
def api_propagate_monte_carlo(payload: MonteCarloPropagationRequest) -> MonteCarloPropagationResponse:
    vars_map = {
        name: VariableSpec(
            value=spec.value,
            uncertainty=spec.uncertainty,
            distribution=spec.distribution,
        )
        for name, spec in payload.variables.items()
    }
    res = propagate_monte_carlo(
        expression=payload.expression,
        variables=vars_map,
        n_samples=payload.n_samples,
        confidence_level=payload.confidence_level,
        seed=payload.seed,
        bins=payload.bins,
    )
    return MonteCarloPropagationResponse(
        mean=res.mean,
        std_dev=res.std_dev,
        median=res.median,
        ci_low=res.ci_low,
        ci_high=res.ci_high,
        confidence_level=res.confidence_level,
        n_samples=res.n_samples,
        histogram_counts=res.histogram_counts,
        histogram_edges=res.histogram_edges,
        formatted_text=res.formatted_text,
        formatted_latex=res.formatted_latex,
    )
