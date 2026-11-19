"""Endpoints de ingesta CSV/TSV y exportación de tablas científicas LaTeX."""

from __future__ import annotations

import csv
import io
import math

from fastapi import APIRouter

from cota.api.schemas import (
    ExportLatexRequest,
    ExportLatexResponse,
    ParseCsvRequest,
    ParseCsvResponse,
)
from cota.core.metrology import format_measurement
from cota.core.units import format_unit_latex

router = APIRouter(prefix="/api/data", tags=["Datos y Exportación"])


def _detect_delimiter(sample_line: str) -> str:
    for delim in ("\t", ";", ","):
        if delim in sample_line:
            return delim
    return ","


def _parse_float(token: str, use_decimal_comma: bool) -> float:
    cleaned = token.strip()
    if use_decimal_comma:
        cleaned = cleaned.replace(",", ".")
    val = float(cleaned)
    if not math.isfinite(val):
        raise ValueError("No se admiten valores NaN o infinitos en la tabla.")
    return val


@router.post("/parse-csv", response_model=ParseCsvResponse)
def api_parse_csv(payload: ParseCsvRequest) -> ParseCsvResponse:
    lines = [line for line in payload.text.strip().splitlines() if line.strip()]
    if not lines:
        raise ValueError("El texto CSV está vacío.")

    delimiter = _detect_delimiter(lines[0])
    reader = csv.reader(io.StringIO("\n".join(lines)), delimiter=delimiter)
    raw_rows = [[cell.strip() for cell in row] for row in reader if any(c.strip() for c in row)]
    if not raw_rows:
        raise ValueError("No se encontraron filas válidas en los datos.")

    use_decimal_comma = (
        payload.decimal_comma
        if payload.decimal_comma is not None
        else delimiter in (";", "\t")
    )

    # Detectar si la primera fila es cabecera o ya son números
    first_is_numeric = True
    for cell in raw_rows[0]:
        try:
            _parse_float(cell, use_decimal_comma)
        except ValueError:
            first_is_numeric = False
            break

    if first_is_numeric:
        n_cols = len(raw_rows[0])
        headers = [f"Col {i + 1}" for i in range(n_cols)]
        data_rows_raw = raw_rows
    else:
        headers = raw_rows[0]
        data_rows_raw = raw_rows[1:]

    if not data_rows_raw:
        raise ValueError("La tabla debe contener al menos una fila de datos numéricos.")

    expected_cols = len(headers)
    parsed_rows: list[list[float]] = []
    for idx, row in enumerate(data_rows_raw, start=1):
        if len(row) != expected_cols:
            raise ValueError(
                f"La fila {idx} tiene {len(row)} columnas, pero se esperaban {expected_cols}."
            )
        try:
            parsed_rows.append([_parse_float(cell, use_decimal_comma) for cell in row])
        except ValueError as exc:
            raise ValueError(f"Valor no numérico en la fila {idx}: {exc}") from exc

    return ParseCsvResponse(headers=headers, rows=parsed_rows, delimiter=delimiter)


@router.post("/export-latex", response_model=ExportLatexResponse)
def api_export_latex(payload: ExportLatexRequest) -> ExportLatexResponse:
    n_rows = len(payload.columns[0].values)
    for col in payload.columns:
        if len(col.values) != n_rows:
            raise ValueError("Todas las columnas deben tener la misma cantidad de filas.")
        if col.uncertainties is not None and len(col.uncertainties) != n_rows:
            raise ValueError(
                f"Las incertidumbres de '{col.name}' deben coincidir en longitud con sus valores."
            )

    col_spec = " ".join(["c"] * len(payload.columns))
    header_cells: list[str] = []
    for col in payload.columns:
        if col.unit and col.unit.strip():
            unit_tex = format_unit_latex(col.unit)
            header_cells.append(rf"{col.name} ($\mathrm{{{unit_tex}}}$)")
        else:
            header_cells.append(col.name)

    body_lines: list[str] = []
    for row_idx in range(n_rows):
        cells: list[str] = []
        for col in payload.columns:
            val = col.values[row_idx]
            if col.uncertainties is not None:
                _, tex_val = format_measurement(val, col.uncertainties[row_idx], sig_figs=payload.sig_figs)
                cells.append(f"${tex_val}$")
            else:
                cells.append(f"${val:.4g}$")
        body_lines.append("    " + " & ".join(cells) + r" \\")

    latex = "\n".join(
        [
            r"\begin{table}[htbp]",
            r"  \centering",
            rf"  \caption{{{payload.caption}}}",
            rf"  \label{{{payload.label}}}",
            rf"  \begin{{tabular}}{{{col_spec}}}",
            r"    \toprule",
            "    " + " & ".join(header_cells) + r" \\",
            r"    \midrule",
            *body_lines,
            r"    \bottomrule",
            r"  \end{tabular}",
            r"\end{table}",
        ]
    )
    return ExportLatexResponse(latex=latex)
