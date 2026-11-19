"""Validadores numéricos y parseo seguro de expresiones simbólicas."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import sympy
from sympy.parsing.sympy_parser import parse_expr

_SAFE_MATH_FUNCTIONS: dict[str, object] = {
    "pi": sympy.pi,
    "E": sympy.E,
    "e": sympy.E,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "tan": sympy.tan,
    "asin": sympy.asin,
    "acos": sympy.acos,
    "atan": sympy.atan,
    "sinh": sympy.sinh,
    "cosh": sympy.cosh,
    "tanh": sympy.tanh,
    "exp": sympy.exp,
    "log": sympy.log,
    "ln": sympy.log,
    "sqrt": sympy.sqrt,
    "abs": sympy.Abs,
    "Abs": sympy.Abs,
}

_SAFE_SYMPY_GLOBALS: dict[str, object] = {
    "__builtins__": {},
    "Integer": sympy.Integer,
    "Float": sympy.Float,
    "Rational": sympy.Rational,
    "Symbol": sympy.Symbol,
    "Function": sympy.Function,
}

_FORBIDDEN_SUBSTRINGS = ("__", "import", "exec", "eval", "open", "lambda", "getattr", "setattr")


def validate_finite_array(
    values: Sequence[float] | np.ndarray,
    name: str,
    min_length: int = 1,
) -> np.ndarray:
    """Convierte una secuencia a ndarray float64 validando longitud mínima y valores finitos."""
    try:
        arr = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Los valores de '{name}' deben ser numéricos.") from exc

    if arr.ndim != 1:
        raise ValueError(f"'{name}' debe ser un arreglo unidimensional.")

    if len(arr) < min_length:
        raise ValueError(f"'{name}' requiere al menos {min_length} valores (se recibieron {len(arr)}).")

    if not np.all(np.isfinite(arr)):
        raise ValueError(f"Todos los valores de '{name}' deben ser finitos (no se admiten NaN ni infinitos).")

    return arr


def validate_positive_uncertainties(
    values: Sequence[float] | np.ndarray,
    name: str,
    expected_length: int,
) -> np.ndarray:
    """Valida que un arreglo de incertidumbres tenga la longitud esperada y todos sus valores > 0."""
    arr = validate_finite_array(values, name=name, min_length=1)
    if len(arr) != expected_length:
        raise ValueError(
            f"'{name}' debe tener exactamente {expected_length} valores (se recibieron {len(arr)})."
        )
    if np.any(arr <= 0):
        raise ValueError(f"Todas las incertidumbres en '{name}' deben ser estrictamente positivas (> 0).")
    return arr


def parse_safe_expression(
    expression: str,
    allowed_symbols: Sequence[str],
) -> tuple[sympy.Expr, dict[str, sympy.Symbol]]:
    """Parsea una expresión matemática de forma segura sin usar eval() arbitrario."""
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("La expresión matemática no puede estar vacía.")

    cleaned = expression.strip()
    lowered = cleaned.lower()
    for token in _FORBIDDEN_SUBSTRINGS:
        if token in lowered:
            raise ValueError(f"Expresión no permitida: contiene el elemento restringido '{token}'.")

    symbols_map: dict[str, sympy.Symbol] = {
        name: sympy.Symbol(name, real=True) for name in allowed_symbols
    }
    local_dict: dict[str, object] = {**_SAFE_MATH_FUNCTIONS, **symbols_map}

    try:
        expr = parse_expr(
            cleaned,
            local_dict=local_dict,
            global_dict=_SAFE_SYMPY_GLOBALS,
            evaluate=True,
        )
    except Exception as exc:
        raise ValueError(f"Expresión matemática inválida: '{cleaned}'. Detalle: {exc}") from exc

    if not isinstance(expr, sympy.Expr):
        raise ValueError(f"Expresión matemática inválida: '{cleaned}' no produce una expresión simbólica.")

    allowed_set = set(symbols_map.values())
    unknown = expr.free_symbols - allowed_set
    if unknown:
        unknown_names = ", ".join(sorted(str(s) for s in unknown))
        raise ValueError(
            f"La expresión contiene símbolos desconocidos no declarados: {unknown_names}."
        )

    return expr, symbols_map
