// Vista 1: Ajuste de curvas (lineal WLS/York, modelos físicos no lineales y personalizados).

import { api } from "../api.js";
import { createDataGrid } from "../grid.js";
import { cleanRows, parseCell } from "../lib/expr.js";
import { downloadPlotImage, renderFitPlot, renderResidualsPlot } from "../plots.js";
import {
  escapeHtml,
  formatPmHtml,
  renderKatex,
  setLoading,
  showCodeModal,
  toast,
} from "../ui.js";

const EXAMPLES = {
  hooke: {
    model: "linear",
    xlabel: "Estiramiento Δx (m)",
    ylabel: "Fuerza F (N)",
    rows: [
      [0.02, 0.51, 0.03, null],
      [0.04, 0.98, 0.03, null],
      [0.06, 1.52, 0.04, null],
      [0.08, 1.97, 0.04, null],
      [0.10, 2.53, 0.05, null],
      [0.12, 2.98, 0.05, null],
      [0.14, 3.51, 0.05, null],
      [0.16, 4.02, 0.06, null],
    ],
  },
  york: {
    model: "linear",
    xlabel: "X (u.a.)",
    ylabel: "Y (u.a.)",
    rows: [
      [0.0, 5.9, 1.0, 0.0316],
      [0.9, 5.4, 0.745, 0.0316],
      [1.8, 4.4, 0.5, 0.0447],
      [2.6, 4.6, 0.354, 0.0354],
      [3.3, 3.5, 0.224, 0.0707],
      [4.4, 3.7, 0.224, 0.1118],
      [5.2, 2.8, 0.120, 0.1291],
      [6.1, 2.8, 0.120, 0.2236],
      [6.5, 2.4, 0.1, 0.7454],
      [7.4, 1.5, 0.0447, 1.0],
    ],
  },
  rc: {
    model: "exponential_decay",
    xlabel: "Tiempo t (s)",
    ylabel: "Voltaje V (V)",
    rows: [
      [0.0, 9.95, 0.12, null],
      [0.5, 7.82, 0.12, null],
      [1.0, 6.18, 0.10, null],
      [1.5, 4.86, 0.10, null],
      [2.0, 3.91, 0.09, null],
      [3.0, 2.54, 0.08, null],
      [4.0, 1.72, 0.08, null],
      [5.0, 1.24, 0.07, null],
      [6.0, 0.95, 0.07, null],
    ],
  },
  gauss: {
    model: "gaussian",
    xlabel: "Longitud de onda λ (nm)",
    ylabel: "Intensidad I (u.a.)",
    rows: [
      [584, 0.14, 0.03, null],
      [586, 0.28, 0.03, null],
      [587, 0.56, 0.04, null],
      [588, 1.12, 0.05, null],
      [589, 1.85, 0.06, null],
      [590, 2.15, 0.06, null],
      [591, 1.78, 0.06, null],
      [592, 1.04, 0.05, null],
      [593, 0.49, 0.04, null],
      [595, 0.18, 0.03, null],
    ],
  },
  osc: {
    model: "damped_oscillator",
    xlabel: "Tiempo t (s)",
    ylabel: "Desplazamiento x (cm)",
    rows: [
      [0.0, 4.95, 0.15, null],
      [0.4, 2.12, 0.15, null],
      [0.8, -2.55, 0.15, null],
      [1.2, -3.72, 0.15, null],
      [1.6, -0.78, 0.15, null],
      [2.0, 2.48, 0.15, null],
      [2.4, 2.38, 0.15, null],
      [2.8, -0.15, 0.15, null],
      [3.2, -1.96, 0.15, null],
      [3.6, -1.42, 0.15, null],
      [4.0, 0.52, 0.15, null],
      [4.4, 1.48, 0.15, null],
    ],
  },
};

export async function initAjusteView() {
  const gridEl = document.getElementById("aj-grilla");
  const modelSel = document.getElementById("aj-modelo");
  const formulaEl = document.getElementById("aj-formula");
  const customBox = document.getElementById("aj-custom");
  const xlabelEl = document.getElementById("aj-xlabel");
  const ylabelEl = document.getElementById("aj-ylabel");
  const confEl = document.getElementById("aj-conf");
  const plotEl = document.getElementById("aj-plot");
  const resEl = document.getElementById("aj-res");
  const resultadosEl = document.getElementById("aj-resultados");
  const metodoEl = document.getElementById("aj-metodo");
  const btnAjustar = document.getElementById("aj-ajustar");

  let catalog = [];
  let lastState = null;

  const grid = createDataGrid(gridEl);

  try {
    const resp = await api.fittingModels();
    catalog = resp.models || [];
  } catch (err) {
    toast(`No se pudo cargar el catálogo de modelos: ${err.message}`, "error");
  }

  modelSel.innerHTML = [
    ...catalog.map((m) => `<option value="${m.id}">${escapeHtml(m.name)}</option>`),
    `<option value="custom">Personalizado f(x)</option>`,
  ].join("");

  function updateFormulaPreview() {
    const id = modelSel.value;
    customBox.classList.toggle("hidden", id !== "custom");
    if (id === "custom") {
      const expr = document.getElementById("aj-expr").value.trim();
      renderKatex(formulaEl, expr ? `f(x) = ${expr}` : "");
      return;
    }
    const found = catalog.find((m) => m.id === id);
    renderKatex(formulaEl, found ? found.formula_latex : "");
  }

  modelSel.addEventListener("change", updateFormulaPreview);
  document.getElementById("aj-expr").addEventListener("input", updateFormulaPreview);

  function extractColumns() {
    const raw = grid.getRows();
    const xy = cleanRows(
      raw.map((r) => [r[0], r[1]]),
      3,
    );
    const validIdx = [];
    raw.forEach((r, idx) => {
      if (typeof r[0] === "number" && Number.isFinite(r[0]) && typeof r[1] === "number" && Number.isFinite(r[1])) {
        validIdx.push(idx);
      }
    });
    const x = xy.map((r) => r[0]);
    const y = xy.map((r) => r[1]);
    const dyRaw = validIdx.map((i) => raw[i][2]);
    const dxRaw = validIdx.map((i) => raw[i][3]);
    const hasDy = dyRaw.every((v) => typeof v === "number" && Number.isFinite(v));
    const hasDx = dxRaw.every((v) => typeof v === "number" && Number.isFinite(v));
    return {
      x,
      y,
      dy: hasDy ? dyRaw : null,
      dx: hasDx ? dxRaw : null,
    };
  }

  function redrawPlots() {
    if (!lastState) return;
    renderFitPlot(plotEl, {
      x: lastState.x,
      y: lastState.y,
      dy: lastState.dy,
      dx: lastState.dx,
      fit: lastState.fit,
      xlabel: xlabelEl.value,
      ylabel: ylabelEl.value,
    });
    renderResidualsPlot(resEl, {
      x: lastState.x,
      normalizedResiduals: lastState.fit.normalized_residuals,
      xlabel: xlabelEl.value,
    });
  }

  async function runFit() {
    setLoading(btnAjustar, true);
    try {
      const { x, y, dy, dx } = extractColumns();
      const model = modelSel.value;
      const confidence_level = Number(confEl.value);

      let fit;
      if (model === "linear" && dy) {
        fit = await api.fitLinear({ x, y, dy, dx, confidence_level });
      } else if (model === "custom") {
        const custom_expression = document.getElementById("aj-expr").value.trim();
        const param_names = document
          .getElementById("aj-params")
          .value.split(",")
          .map((s) => s.trim())
          .filter(Boolean);
        const p0Raw = document.getElementById("aj-p0").value.trim();
        let p0 = null;
        if (p0Raw) {
          const nums = p0Raw.split(",").map(parseCell);
          p0 = {};
          param_names.forEach((name, idx) => {
            if (nums[idx] !== null) p0[name] = nums[idx];
          });
        }
        fit = await api.fitNonlinear({
          x,
          y,
          dy,
          model: "custom",
          custom_expression,
          param_names,
          p0,
          confidence_level,
        });
      } else {
        fit = await api.fitNonlinear({ x, y, dy, model, confidence_level });
      }

      // Formatear todos los parámetros con reglas GUM vía API
      const formattedParams = await Promise.all(
        Object.values(fit.parameters).map(async (p) => {
          const fmt = await api.format({ value: p.value, uncertainty: p.uncertainty });
          return { ...p, ...fmt };
        }),
      );

      lastState = { x, y, dy, dx, fit, formattedParams };
      redrawPlots();
      renderResults(fit, formattedParams);
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setLoading(btnAjustar, false);
    }
  }

  function renderResults(fit, formattedParams) {
    const methodLabel =
      fit.model_name === "linear_york"
        ? "York (δx y δy)"
        : fit.model_name === "linear_wls"
          ? "WLS (δy)"
          : "Levenberg–Marquardt";
    metodoEl.innerHTML = `<span class="badge info">${escapeHtml(methodLabel)}</span>`;

    const chiStatus =
      fit.reduced_chi_squared >= 0.5 && fit.reduced_chi_squared <= 2.0
        ? "ok"
        : fit.reduced_chi_squared <= 5.0
          ? "warn"
          : "err";

    const paramsHtml = formattedParams
      .map(
        (p) => `
      <div class="param">
        <span class="param-name">${escapeHtml(p.name)}</span>
        <span class="param-val">${formatPmHtml(p.formatted_text)}</span>
      </div>`,
      )
      .join("");

    resultadosEl.innerHTML = `
      <div class="params">${paramsHtml}</div>
      <div class="stats" style="margin-top:12px">
        <div class="stat"><div class="stat-k">χ² reducido (ν = ${fit.dof})</div><div class="stat-v"><span class="badge ${chiStatus}">${fit.reduced_chi_squared.toFixed(3)}</span></div></div>
        <div class="stat"><div class="stat-k">R²</div><div class="stat-v">${fit.r_squared.toFixed(5)}</div></div>
        <div class="stat"><div class="stat-k">χ² total</div><div class="stat-v">${fit.chi_squared.toFixed(3)}</div></div>
        <div class="stat"><div class="stat-k">p-valor</div><div class="stat-v">${fit.p_value.toFixed(4)}</div></div>
      </div>
    `;
  }

  // Botones de grilla y ejemplos
  document.getElementById("aj-fila").addEventListener("click", () => grid.addRow());
  document.getElementById("aj-limpiar").addEventListener("click", () => grid.clear());
  document.getElementById("aj-pegar").addEventListener("click", async () => {
    try {
      const txt = await navigator.clipboard.readText();
      if (!txt.trim()) return toast("El portapapeles está vacío.", "error");
      await grid.pasteTabular(txt);
    } catch {
      toast("Usá Ctrl+V directamente dentro de cualquier celda de la grilla.", "info");
    }
  });

  document.getElementById("aj-ejemplo").addEventListener("change", (ev) => {
    const key = ev.target.value;
    if (!key || !EXAMPLES[key]) return;
    const ex = EXAMPLES[key];
    modelSel.value = ex.model;
    xlabelEl.value = ex.xlabel;
    ylabelEl.value = ex.ylabel;
    updateFormulaPreview();
    grid.setRows(ex.rows);
    runFit();
    ev.target.value = "";
  });

  btnAjustar.addEventListener("click", runFit);
  document.getElementById("aj-png").addEventListener("click", () => downloadPlotImage(plotEl, "png", "cota-ajuste"));
  document.getElementById("aj-svg").addEventListener("click", () => downloadPlotImage(plotEl, "svg", "cota-ajuste"));

  document.getElementById("aj-latex").addEventListener("click", async () => {
    try {
      const { x, y, dy, dx } = extractColumns();
      const columns = [
        { name: xlabelEl.value || "x", values: x, uncertainties: dx },
        { name: ylabelEl.value || "y", values: y, uncertainties: dy },
      ];
      const resp = await api.exportLatex({ caption: "Datos experimentales", label: "tab:datos", columns });
      showCodeModal("Tabla de datos en LaTeX (booktabs)", resp.latex);
    } catch (err) {
      toast(err.message, "error");
    }
  });

  document.getElementById("aj-latex-params").addEventListener("click", () => {
    if (!lastState) return toast("Primero ejecutá un ajuste.", "info");
    const lines = lastState.formattedParams.map((p) => `${p.name} &= ${p.formatted_latex} \\\\`);
    const tex = `\\begin{align}\n  ${lines.join("\n  ")}\n\\end{align}\n% \\chi^2_\\nu = ${lastState.fit.reduced_chi_squared.toFixed(3)}, R^2 = ${lastState.fit.r_squared.toFixed(5)}`;
    showCodeModal("Parámetros ajustados en LaTeX", tex);
  });

  window.addEventListener("cota:tema", redrawPlots);

  // Cargar ejemplo inicial (Ley de Hooke) para que la app luzca viva al abrirse
  const initial = EXAMPLES.hooke;
  modelSel.value = initial.model;
  xlabelEl.value = initial.xlabel;
  ylabelEl.value = initial.ylabel;
  updateFormulaPreview();
  grid.setRows(initial.rows);
  await runFit();

  return { runPrimary: runFit };
}
