"""Motor de ajuste de curvas: regresión lineal ponderada (WLS / York 2004) y modelos no lineales."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
import sympy
from scipy import optimize, stats

from metrilab.core.validation import (
    parse_safe_expression,
    validate_finite_array,
    validate_positive_uncertainties,
)


@dataclass(frozen=True)
class FitParameter:
    """Parámetro ajustado con su valor óptimo e incertidumbre estándar."""

    name: str
    value: float
    uncertainty: float


@dataclass(frozen=True)
class FitResult:
    """Resultado completo de un ajuste de curva con estadísticos y bandas de confianza."""

    model_name: str
    parameters: dict[str, FitParameter]
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


def _model_linear(x: np.ndarray, m: float, b: float) -> np.ndarray:
    return m * x + b


def _model_quadratic(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    return a * x**2 + b * x + c


def _model_exponential_decay(x: np.ndarray, y0: float, A: float, tau: float) -> np.ndarray:
    return y0 + A * np.exp(-x / tau)


def _model_damped_oscillator(
    x: np.ndarray, A: float, gamma: float, omega: float, phi: float, y0: float
) -> np.ndarray:
    return A * np.exp(-gamma * x) * np.cos(omega * x + phi) + y0


def _model_gaussian(
    x: np.ndarray, y0: float, A: float, mu: float, sigma: float
) -> np.ndarray:
    return y0 + A * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def _model_power_law(x: np.ndarray, A: float, b: float, y0: float) -> np.ndarray:
    return A * np.power(x, b) + y0


BUILTIN_MODELS: dict[str, tuple[Callable[..., np.ndarray], list[str]]] = {
    "linear": (_model_linear, ["m", "b"]),
    "quadratic": (_model_quadratic, ["a", "b", "c"]),
    "exponential_decay": (_model_exponential_decay, ["y0", "A", "tau"]),
    "damped_oscillator": (_model_damped_oscillator, ["A", "gamma", "omega", "phi", "y0"]),
    "gaussian": (_model_gaussian, ["y0", "A", "mu", "sigma"]),
    "power_law": (_model_power_law, ["A", "b", "y0"]),
}


def _estimate_initial_params(model: str, x: np.ndarray, y: np.ndarray) -> list[float]:
    y_min, y_max = float(np.min(y)), float(np.max(y))
    x_min, x_max = float(np.min(x)), float(np.max(x))
    x_span = max(x_max - x_min, 1e-6)
    y_span = max(y_max - y_min, 1e-6)

    if model == "linear":
        slope = (y[-1] - y[0]) / (x[-1] - x[0]) if x[-1] != x[0] else 1.0
        intercept = float(np.mean(y) - slope * np.mean(x))
        return [float(slope), intercept]
    if model == "quadratic":
        coeffs = np.polyfit(x, y, 2)
        return [float(coeffs[0]), float(coeffs[1]), float(coeffs[2])]
    if model == "exponential_decay":
        y0_est = float(y[-1])
        a_est = float(y[0] - y[-1]) if y[0] != y[-1] else y_span
        tau_est = x_span / 3.0
        return [y0_est, a_est, tau_est]
    if model == "damped_oscillator":
        y0_est = float(np.mean(y))
        a_est = 0.5 * y_span
        gamma_est = 1.0 / x_span
        omega_est = 2.0 * math.pi / (x_span / 2.0)
        return [a_est, gamma_est, omega_est, 0.0, y0_est]
    if model == "gaussian":
        y0_est = y_min
        idx_max = int(np.argmax(y))
        a_est = float(y[idx_max] - y0_est)
        mu_est = float(x[idx_max])
        sigma_est = x_span / 6.0
        return [y0_est, a_est, mu_est, sigma_est]
    if model == "power_law":
        return [1.0, 1.0, y_min]
    return [1.0]


def _compute_confidence_band(
    func: Callable[..., np.ndarray],
    x_grid: np.ndarray,
    popt: np.ndarray,
    pcov: np.ndarray,
    dof: int,
    confidence_level: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Propaga la matriz de covarianza pcov por diferencias finitas del Jacobiano."""
    y_grid = np.asarray(func(x_grid, *popt), dtype=np.float64)
    n_params = len(popt)
    jac = np.zeros((len(x_grid), n_params), dtype=np.float64)

    for j in range(n_params):
        step = max(abs(float(popt[j])) * 1e-6, 1e-8)
        p_plus = popt.copy()
        p_minus = popt.copy()
        p_plus[j] += step
        p_minus[j] -= step
        jac[:, j] = (func(x_grid, *p_plus) - func(x_grid, *p_minus)) / (2.0 * step)

    var_y = np.einsum("ij,jk,ik->i", jac, pcov, jac)
    std_y = np.sqrt(np.maximum(var_y, 0.0))
    t_crit = float(stats.t.ppf((1.0 + confidence_level) / 2.0, df=dof))
    return y_grid, y_grid - t_crit * std_y, y_grid + t_crit * std_y


def _compute_r_squared(y: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    if ss_tot == 0.0:
        return 1.0 if ss_res == 0.0 else 0.0
    return 1.0 - ss_res / ss_tot


def fit_linear_weighted(
    x: Sequence[float] | np.ndarray,
    y: Sequence[float] | np.ndarray,
    dy: Sequence[float] | np.ndarray,
    dx: Sequence[float] | np.ndarray | None = None,
    confidence_level: float = 0.95,
    grid_points: int = 100,
) -> FitResult:
    """Ajuste lineal ponderado: WLS exacto (si dx es None) o algoritmo iterativo de York (2004)."""
    x_arr = validate_finite_array(x, name="x", min_length=3)
    y_arr = validate_finite_array(y, name="y", min_length=3)
    if len(x_arr) != len(y_arr):
        raise ValueError("Los arreglos 'x' e 'y' deben tener la misma longitud.")

    dy_arr = validate_positive_uncertainties(dy, name="dy", expected_length=len(x_arr))
    dx_arr = (
        validate_positive_uncertainties(dx, name="dx", expected_length=len(x_arr))
        if dx is not None
        else None
    )
    if not (0.0 < confidence_level < 1.0):
        raise ValueError("El nivel de confianza debe estar entre 0 y 1.")

    dof = len(x_arr) - 2
    wy = 1.0 / (dy_arr**2)

    if dx_arr is None:
        s = float(np.sum(wy))
        sx = float(np.sum(wy * x_arr))
        sy = float(np.sum(wy * y_arr))
        sxx = float(np.sum(wy * x_arr**2))
        sxy = float(np.sum(wy * x_arr * y_arr))
        delta = s * sxx - sx**2
        if delta <= 0.0:
            raise ValueError("Los valores de 'x' son colineales o idénticos; no se puede ajustar una recta.")
        m = (s * sxy - sx * sy) / delta
        b = (sxx * sy - sx * sxy) / delta
        var_m = s / delta
        var_b = sxx / delta
        cov_mb = -sx / delta
        eff_weights = wy
        model_name = "linear_wls"
    else:
        wx = 1.0 / (dx_arr**2)
        # Estimación inicial OLS
        slope_ols, _ = np.polyfit(x_arr, y_arr, 1)
        m = float(slope_ols)
        eff_weights = wy
        for _ in range(200):
            eff_weights = (wx * wy) / (wx + (m**2) * wy)
            w_sum = float(np.sum(eff_weights))
            x_bar = float(np.sum(eff_weights * x_arr)) / w_sum
            y_bar = float(np.sum(eff_weights * y_arr)) / w_sum
            u_i = x_arr - x_bar
            v_i = y_arr - y_bar
            beta_i = eff_weights * (u_i / wy + (m * v_i) / wx)
            denom = float(np.sum(eff_weights * beta_i * u_i))
            if denom == 0.0:
                raise ValueError("El algoritmo de York no convergió (denominador nulo).")
            m_new = float(np.sum(eff_weights * beta_i * v_i)) / denom
            if abs(m_new - m) < 1e-12:
                m = m_new
                break
            m = m_new

        eff_weights = (wx * wy) / (wx + (m**2) * wy)
        w_sum = float(np.sum(eff_weights))
        x_bar = float(np.sum(eff_weights * x_arr)) / w_sum
        y_bar = float(np.sum(eff_weights * y_arr)) / w_sum
        u_i = x_arr - x_bar
        v_i = y_arr - y_bar
        beta_i = eff_weights * (u_i / wy + (m * v_i) / wx)
        b = y_bar - m * x_bar

        x_adj = x_bar + beta_i
        x_adj_bar = float(np.sum(eff_weights * x_adj)) / w_sum
        u_adj = x_adj - x_adj_bar
        var_m = 1.0 / float(np.sum(eff_weights * (u_adj**2)))
        var_b = (1.0 / w_sum) + (x_adj_bar**2) * var_m
        cov_mb = -x_adj_bar * var_m
        model_name = "linear_york"

    y_pred = m * x_arr + b
    residuals = y_arr - y_pred
    eff_sigma = 1.0 / np.sqrt(eff_weights)
    norm_residuals = residuals / eff_sigma
    chi2 = float(np.sum(eff_weights * (residuals**2)))
    red_chi2 = chi2 / dof
    p_val = float(stats.chi2.sf(chi2, df=dof))
    r2 = _compute_r_squared(y_arr, y_pred)

    popt = np.array([m, b], dtype=np.float64)
    pcov = np.array([[var_m, cov_mb], [cov_mb, var_b]], dtype=np.float64)
    x_grid = np.linspace(float(np.min(x_arr)), float(np.max(x_arr)), grid_points)
    y_grid, band_low, band_high = _compute_confidence_band(
        _model_linear, x_grid, popt, pcov, dof, confidence_level
    )

    return FitResult(
        model_name=model_name,
        parameters={
            "m": FitParameter(name="m", value=float(m), uncertainty=math.sqrt(max(var_m, 0.0))),
            "b": FitParameter(name="b", value=float(b), uncertainty=math.sqrt(max(var_b, 0.0))),
        },
        covariance_matrix=[[float(pcov[0, 0]), float(pcov[0, 1])], [float(pcov[1, 0]), float(pcov[1, 1])]],
        chi_squared=chi2,
        reduced_chi_squared=red_chi2,
        dof=dof,
        p_value=p_val,
        r_squared=r2,
        residuals=[float(r) for r in residuals],
        normalized_residuals=[float(r) for r in norm_residuals],
        curve_x=[float(v) for v in x_grid],
        curve_y=[float(v) for v in y_grid],
        band_low=[float(v) for v in band_low],
        band_high=[float(v) for v in band_high],
    )


def fit_nonlinear(
    x: Sequence[float] | np.ndarray,
    y: Sequence[float] | np.ndarray,
    model: str,
    dy: Sequence[float] | np.ndarray | None = None,
    p0: dict[str, float] | None = None,
    custom_expression: str | None = None,
    param_names: Sequence[str] | None = None,
    confidence_level: float = 0.95,
    grid_points: int = 100,
) -> FitResult:
    """Ajusta un modelo no lineal predefinido o personalizado usando SciPy curve_fit."""
    if model == "custom":
        if not custom_expression or not param_names:
            raise ValueError(
                "Para el modelo 'custom' debe proporcionar 'custom_expression' y 'param_names'."
            )
        p_names = list(param_names)
        expr, syms = parse_safe_expression(custom_expression, ["x", *p_names])
        sym_args = [syms["x"], *[syms[p] for p in p_names]]
        raw_func = sympy.lambdify(sym_args, expr, modules="numpy")

        def model_func(x_val: np.ndarray, *params: float) -> np.ndarray:
            return np.asarray(raw_func(x_val, *params), dtype=np.float64)

        model_label = f"custom: {custom_expression}"
    elif model in BUILTIN_MODELS:
        model_func, p_names = BUILTIN_MODELS[model]
        model_label = model
    else:
        supported = ", ".join(sorted([*BUILTIN_MODELS.keys(), "custom"]))
        raise ValueError(f"Modelo '{model}' no soportado. Modelos válidos: {supported}.")

    n_params = len(p_names)
    min_pts = n_params + 1
    x_arr = validate_finite_array(x, name="x", min_length=min_pts)
    y_arr = validate_finite_array(y, name="y", min_length=min_pts)
    if len(x_arr) != len(y_arr):
        raise ValueError("Los arreglos 'x' e 'y' deben tener la misma longitud.")

    dy_arr = (
        validate_positive_uncertainties(dy, name="dy", expected_length=len(x_arr))
        if dy is not None
        else None
    )
    if not (0.0 < confidence_level < 1.0):
        raise ValueError("El nivel de confianza debe estar entre 0 y 1.")

    if p0 is not None:
        initial_guess = [float(p0.get(name, 1.0)) for name in p_names]
    elif model in BUILTIN_MODELS:
        initial_guess = _estimate_initial_params(model, x_arr, y_arr)
    else:
        initial_guess = [1.0] * n_params

    try:
        popt, pcov = optimize.curve_fit(
            model_func,
            x_arr,
            y_arr,
            p0=initial_guess,
            sigma=dy_arr,
            absolute_sigma=(dy_arr is not None),
            maxfev=20_000,
        )
    except Exception as exc:
        raise ValueError(
            f"El ajuste no lineal para '{model_label}' no convergió. Pruebe con estimaciones iniciales 'p0'. Detalle: {exc}"
        ) from exc

    if not np.all(np.isfinite(popt)) or not np.all(np.isfinite(pcov)):
        raise ValueError("El ajuste produjo parámetros o covarianzas no finitas.")

    dof = len(x_arr) - n_params
    y_pred = np.asarray(model_func(x_arr, *popt), dtype=np.float64)
    residuals = y_arr - y_pred

    if dy_arr is not None:
        norm_residuals = residuals / dy_arr
        chi2 = float(np.sum(norm_residuals**2))
        red_chi2 = chi2 / dof
        p_val = float(stats.chi2.sf(chi2, df=dof))
    else:
        rms = math.sqrt(float(np.sum(residuals**2)) / dof)
        norm_residuals = residuals / rms if rms > 0 else np.zeros_like(residuals)
        chi2 = float(np.sum(residuals**2))
        red_chi2 = chi2 / dof
        p_val = 1.0

    r2 = _compute_r_squared(y_arr, y_pred)
    param_uncertainties = np.sqrt(np.maximum(np.diag(pcov), 0.0))
    params_dict = {
        name: FitParameter(
            name=name,
            value=float(popt[idx]),
            uncertainty=float(param_uncertainties[idx]),
        )
        for idx, name in enumerate(p_names)
    }

    x_grid = np.linspace(float(np.min(x_arr)), float(np.max(x_arr)), grid_points)
    y_grid, band_low, band_high = _compute_confidence_band(
        model_func, x_grid, popt, pcov, dof, confidence_level
    )

    return FitResult(
        model_name=model_label,
        parameters=params_dict,
        covariance_matrix=[[float(val) for val in row] for row in pcov],
        chi_squared=chi2,
        reduced_chi_squared=red_chi2,
        dof=dof,
        p_value=p_val,
        r_squared=r2,
        residuals=[float(r) for r in residuals],
        normalized_residuals=[float(r) for r in norm_residuals],
        curve_x=[float(v) for v in x_grid],
        curve_y=[float(v) for v in y_grid],
        band_low=[float(v) for v in band_low],
        band_high=[float(v) for v in band_high],
    )
