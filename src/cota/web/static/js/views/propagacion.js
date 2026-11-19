// Vista 2: Propagación de incertidumbres (Analítica SymPy + Monte Carlo JCGM 101).

import { api } from "../api.js";
import { extractVariables, parseCell } from "../lib/expr.js";
import { renderMonteCarloHist } from "../plots.js";
import { copyText, escapeHtml, formatPmHtml, renderKatex, setLoading, toast } from "../ui.js";

const EXAMPLES = {
  pendulo: {
    expr: "4*pi**2*L/T**2",
    vars: {
      L: { value: 1.000, uncertainty: 0.002, distribution: "normal" },
      T: { value: 2.006, uncertainty: 0.005, distribution: "normal" },
    },
  },
  densidad: {
    expr: "4*m/(pi*d**2*h)",
    vars: {
      m: { value: 125.4, uncertainty: 0.1, distribution: "uniform" },
      d: { value: 2.52, uncertainty: 0.01, distribution: "uniform" },
      h: { value: 8.15, uncertainty: 0.02, distribution: "uniform" },
    },
  },
  ohm: {
    expr: "V**2 / R",
    vars: {
      V: { value: 12.0, uncertainty: 0.08, distribution: "normal" },
      R: { value: 220.0, uncertainty: 2.2, distribution: "triangular" },
    },
  },
  lente: {
    expr: "(s * sp) / (s + sp)",
    vars: {
      s: { value: 30.0, uncertainty: 0.3, distribution: "uniform" },
      sp: { value: 60.5, uncertainty: 0.5, distribution: "uniform" },
    },
  },
};

export async function initPropagacionView() {
  const exprEl = document.getElementById("pr-expr");
  const previewEl = document.getElementById("pr-preview");
  const varsEl = document.getElementById("pr-vars");
  const nEl = document.getElementById("pr-n");
  const confEl = document.getElementById("pr-conf");
  const btnCalc = document.getElementById("pr-calcular");
  const anaEl = document.getElementById("pr-ana");
  const mcEl = document.getElementById("pr-mc");
  const icEl = document.getElementById("pr-ic");
  const histEl = document.getElementById("pr-hist");
  const contribEl = document.getElementById("pr-contrib");
  const formulaEl = document.getElementById("pr-formula");

  const varState = { ...EXAMPLES.pendulo.vars };
  let lastFormulaLatex = "";
  let lastMc = null;

  function renderVarInputs() {
    const names = extractVariables(exprEl.value);
    renderKatex(previewEl, exprEl.value.trim() ? `f = ${exprEl.value.trim().replaceAll("**", "^")}` : "");

    if (names.length === 0) {
      varsEl.innerHTML = `<div class="empty-note">Escribí una expresión con variables (ej. <span class="mono">L</span>, <span class="mono">T</span>).</div>`;
      return;
    }

    varsEl.innerHTML = `
      <table class="tabla">
        <thead><tr><th>Var</th><th>Valor</th><th>Incertidumbre u</th><th>Distribución</th></tr></thead>
        <tbody>
          ${names
            .map((name) => {
              const s = varState[name] || { value: 1.0, uncertainty: 0.05, distribution: "normal" };
              varState[name] = s;
              return `
                <tr data-var="${escapeHtml(name)}">
                  <td class="mono" style="color:var(--accent-2);font-weight:650">${escapeHtml(name)}</td>
                  <td><input class="input mono" data-k="value" value="${s.value}" /></td>
                  <td><input class="input mono" data-k="uncertainty" value="${s.uncertainty}" /></td>
                  <td>
                    <select class="select" data-k="distribution">
                      <option value="normal" ${s.distribution === "normal" ? "selected" : ""}>Normal</option>
                      <option value="uniform" ${s.distribution === "uniform" ? "selected" : ""}>Rectangular</option>
                      <option value="triangular" ${s.distribution === "triangular" ? "selected" : ""}>Triangular</option>
                    </select>
                  </td>
                </tr>`;
            })
            .join("")}
        </tbody>
      </table>
    `;

    varsEl.querySelectorAll("tr[data-var]").forEach((tr) => {
      const name = tr.dataset.var;
      tr.querySelectorAll("[data-k]").forEach((inp) => {
        inp.addEventListener("input", () => {
          const key = inp.dataset.k;
          varState[name][key] = key === "distribution" ? inp.value : parseCell(inp.value) ?? 0;
        });
      });
    });
  }

  async function runPropagation() {
    setLoading(btnCalc, true);
    try {
      const expression = exprEl.value.trim();
      const names = extractVariables(expression);
      if (names.length === 0) throw new Error("La fórmula debe contener al menos una variable.");

      const variables = {};
      for (const name of names) {
        const s = varState[name];
        variables[name] = {
          value: Number(s.value),
          uncertainty: Number(s.uncertainty),
          distribution: s.distribution || "normal",
        };
      }

      const n_samples = Number(nEl.value);
      const confidence_level = Number(confEl.value);

      const [ana, mc] = await Promise.all([
        api.propagateAnalytical({ expression, variables }),
        api.propagateMonteCarlo({ expression, variables, n_samples, confidence_level }),
      ]);

      anaEl.innerHTML = formatPmHtml(ana.formatted_text);
      mcEl.innerHTML = formatPmHtml(mc.formatted_text);
      icEl.textContent = `IC ${(confidence_level * 100).toFixed(0)} %: [${mc.ci_low.toPrecision(5)}, ${mc.ci_high.toPrecision(5)}]  (${mc.n_samples.toLocaleString("es-AR")} muestras)`;

      lastFormulaLatex = ana.formula_latex;
      renderKatex(formulaEl, ana.formula_latex);

      lastMc = mc;
      renderMonteCarloHist(histEl, mc);

      const rows = Object.entries(ana.variance_contributions)
        .sort((a, b) => b[1] - a[1])
        .map(
          ([v, pct]) => `
          <tr>
            <td class="mono" style="color:var(--accent-2);font-weight:650">${escapeHtml(v)}</td>
            <td class="num">${ana.partial_derivatives[v].toPrecision(4)}</td>
            <td style="width:45%"><div class="bar"><span style="width:${Math.min(100, pct).toFixed(1)}%"></span></div></td>
            <td class="num">${pct.toFixed(1)} %</td>
          </tr>`,
        )
        .join("");
      contribEl.innerHTML = `<table class="tabla"><thead><tr><th>Var</th><th style="text-align:right">∂f/∂x</th><th>Aporte</th><th style="text-align:right">%</th></tr></thead><tbody>${rows}</tbody></table>`;
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setLoading(btnCalc, false);
    }
  }

  exprEl.addEventListener("input", renderVarInputs);
  btnCalc.addEventListener("click", runPropagation);
  document.getElementById("pr-copiar").addEventListener("click", () => {
    if (!lastFormulaLatex) return toast("Primero calculá una propagación.", "info");
    copyText(lastFormulaLatex, "Fórmula LaTeX copiada");
  });

  document.getElementById("pr-ejemplo").addEventListener("change", (ev) => {
    const key = ev.target.value;
    if (!key || !EXAMPLES[key]) return;
    exprEl.value = EXAMPLES[key].expr;
    Object.assign(varState, structuredClone(EXAMPLES[key].vars));
    renderVarInputs();
    runPropagation();
    ev.target.value = "";
  });

  window.addEventListener("cota:tema", () => {
    if (lastMc) renderMonteCarloHist(histEl, lastMc);
  });

  renderVarInputs();
  return { runPrimary: runPropagation };
}
