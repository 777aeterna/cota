// Vista 3: Presupuesto de incertidumbre GUM (Tipo A, Tipo B y Welch-Satterthwaite).

import { api } from "../api.js";
import { parseCell } from "../lib/expr.js";
import { escapeHtml, formatPmHtml, setLoading, toast } from "../ui.js";

export async function initGumView() {
  const muestraEl = document.getElementById("g-muestra");
  const resAEl = document.getElementById("g-res-a");
  const compBEl = document.getElementById("g-comp-b");
  const valorEl = document.getElementById("g-valor");
  const confEl = document.getElementById("g-conf");
  const finalEl = document.getElementById("g-final");
  const finalSubEl = document.getElementById("g-final-sub");
  const presupuestoEl = document.getElementById("g-presupuesto");
  const btnCombinar = document.getElementById("g-combinar");

  let lastTypeA = null;
  let sourcesB = [
    { name: "Resolución del cronómetro", half_width: 0.01, distribution: "rectangular" },
    { name: "Calibración del fabricante", half_width: 0.005, distribution: "normal" },
  ];

  function parseSample() {
    return muestraEl.value
      .split(/[\s;]+/)
      .map(parseCell)
      .filter((v) => v !== null);
  }

  function renderTypeBList() {
    compBEl.innerHTML = sourcesB
      .map(
        (s, idx) => `
      <div class="component" data-idx="${idx}">
        <div class="row">
          <input class="input" data-k="name" value="${escapeHtml(s.name)}" placeholder="Fuente (ej. calibre)" />
          <button class="btn btn-sm btn-ghost" data-del="${idx}" title="Quitar">×</button>
        </div>
        <div class="row">
          <input class="input mono" data-k="half_width" value="${s.half_width}" placeholder="semiamplitud a" />
          <select class="select" data-k="distribution">
            <option value="rectangular" ${s.distribution === "rectangular" ? "selected" : ""}>Rectangular (a/√3)</option>
            <option value="triangular" ${s.distribution === "triangular" ? "selected" : ""}>Triangular (a/√6)</option>
            <option value="normal" ${s.distribution === "normal" ? "selected" : ""}>Normal (a/2)</option>
          </select>
        </div>
      </div>`,
      )
      .join("");

    compBEl.querySelectorAll(".component").forEach((el) => {
      const idx = Number(el.dataset.idx);
      el.querySelectorAll("[data-k]").forEach((inp) => {
        inp.addEventListener("input", () => {
          const k = inp.dataset.k;
          sourcesB[idx][k] = k === "half_width" ? parseCell(inp.value) ?? 0 : inp.value;
        });
      });
      el.querySelector("[data-del]").addEventListener("click", () => {
        sourcesB.splice(idx, 1);
        renderTypeBList();
      });
    });
  }

  async function runTypeA() {
    try {
      const values = parseSample();
      const res = await api.typeA({ values });
      lastTypeA = res;
      if (!valorEl.value.trim()) valorEl.placeholder = res.mean.toPrecision(6);
      const shapiro = res.shapiro_p_value !== null ? res.shapiro_p_value.toFixed(3) : "—";
      resAEl.innerHTML = `
        <div class="stats">
          <div class="stat"><div class="stat-k">Media (n = ${res.n})</div><div class="stat-v">${res.mean.toPrecision(6)}</div></div>
          <div class="stat"><div class="stat-k">u_A = s/√n</div><div class="stat-v">${res.std_uncertainty.toPrecision(4)}</div></div>
          <div class="stat"><div class="stat-k">Desvío s (ν = ${res.dof})</div><div class="stat-v">${res.std_dev.toPrecision(4)}</div></div>
          <div class="stat"><div class="stat-k">Shapiro–Wilk p</div><div class="stat-v">${shapiro}</div></div>
        </div>
      `;
    } catch (err) {
      toast(err.message, "error");
    }
  }

  async function runCombine() {
    setLoading(btnCombinar, true);
    try {
      const sample = parseSample();
      if (sample.length >= 2) {
        await runTypeA();
      } else {
        lastTypeA = null;
      }

      const budget = [];
      if (lastTypeA) {
        budget.push({ label: "Tipo A (repeticiones)", u: lastTypeA.std_uncertainty, dof: lastTypeA.dof });
      }
      for (const s of sourcesB) {
        if (s.half_width > 0) {
          const resB = await api.typeB({ half_width: Number(s.half_width), distribution: s.distribution });
          budget.push({ label: s.name || "Tipo B", u: resB.std_uncertainty, dof: null });
        }
      }
      if (budget.length === 0) throw new Error("Ingresá al menos una muestra Tipo A o una fuente Tipo B.");

      const centralVal = parseCell(valorEl.value) ?? lastTypeA?.mean;
      if (centralVal === null || centralVal === undefined) {
        throw new Error("Indicá un valor central o una muestra Tipo A.");
      }

      const comb = await api.combine({
        value: centralVal,
        components: budget.map((b) => ({ uncertainty: b.u, dof: b.dof })),
        confidence_level: Number(confEl.value),
      });

      finalEl.innerHTML = formatPmHtml(comb.formatted_text);
      const dofStr = comb.effective_dof === null ? "∞" : comb.effective_dof.toFixed(1);
      finalSubEl.textContent = `u_c = ${comb.combined_uncertainty.toPrecision(4)} · k = ${comb.coverage_factor.toFixed(3)} · ν_eff = ${dofStr}`;

      const totalVar = budget.reduce((acc, b) => acc + b.u ** 2, 0) || 1;
      const rowsHtml = budget
        .map((b) => {
          const pct = ((b.u ** 2) / totalVar) * 100;
          return `
            <tr>
              <td>${escapeHtml(b.label)}</td>
              <td class="num">${b.u.toPrecision(3)}</td>
              <td style="width:34%"><div class="bar"><span style="width:${pct.toFixed(1)}%"></span></div></td>
              <td class="num">${pct.toFixed(1)} %</td>
            </tr>`;
        })
        .join("");

      presupuestoEl.innerHTML = `<table class="tabla"><thead><tr><th>Fuente</th><th style="text-align:right">uᵢ</th><th>Peso</th><th style="text-align:right">%</th></tr></thead><tbody>${rowsHtml}</tbody></table>`;
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setLoading(btnCombinar, false);
    }
  }

  document.getElementById("g-calc-a").addEventListener("click", runTypeA);
  document.getElementById("g-add-b").addEventListener("click", () => {
    sourcesB.push({ name: "Nueva fuente instrumental", half_width: 0.01, distribution: "rectangular" });
    renderTypeBList();
  });
  btnCombinar.addEventListener("click", runCombine);

  renderTypeBList();
  return { runPrimary: runCombine };
}
