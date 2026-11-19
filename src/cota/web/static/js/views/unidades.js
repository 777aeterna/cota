// Vista 4: Conversión dimensional de columnas e incertidumbres con Pint.

import { api } from "../api.js";
import { parseCell } from "../lib/expr.js";
import { copyText, escapeHtml, setLoading, toast } from "../ui.js";

const PRESETS = [
  ["cm", "m"],
  ["mm", "m"],
  ["degC", "kelvin"],
  ["km/h", "m/s"],
  ["mV", "V"],
  ["atm", "Pa"],
  ["eV", "J"],
];

export async function initUnidadesView() {
  const fromEl = document.getElementById("u-from");
  const toEl = document.getElementById("u-to");
  const compatEl = document.getElementById("u-compat");
  const chipsEl = document.getElementById("u-chips");
  const valsEl = document.getElementById("u-vals");
  const uncsEl = document.getElementById("u-uncs");
  const resEl = document.getElementById("u-res");
  const btnConv = document.getElementById("u-convertir");

  let lastCopyText = "";

  chipsEl.innerHTML = PRESETS.map(
    ([a, b]) => `<button type="button" class="chip" data-a="${a}" data-b="${b}">${a} → ${b}</button>`,
  ).join("");

  chipsEl.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      fromEl.value = chip.dataset.a;
      toEl.value = chip.dataset.b;
      checkCompatibility();
      runConvert();
    });
  });

  async function checkCompatibility() {
    const u1 = fromEl.value.trim();
    const u2 = toEl.value.trim();
    if (!u1 || !u2) {
      compatEl.innerHTML = "";
      return;
    }
    try {
      const r = await api.unitsCompatible({ unit_from: u1, unit_to: u2 });
      compatEl.innerHTML = r.compatible
        ? `<span class="badge ok">Compatibles</span>`
        : `<span class="badge err">Incompatibles</span>`;
    } catch {
      compatEl.innerHTML = `<span class="badge warn">Unidad desconocida</span>`;
    }
  }

  async function runConvert() {
    setLoading(btnConv, true);
    try {
      const values = valsEl.value
        .split(/[\s;]+/)
        .map(parseCell)
        .filter((v) => v !== null);
      const uncsRaw = uncsEl.value
        .split(/[\s;]+/)
        .map(parseCell)
        .filter((v) => v !== null);
      const uncertainties = uncsRaw.length > 0 ? uncsRaw : null;

      const resp = await api.unitsConvert({
        values,
        unit_from: fromEl.value.trim(),
        unit_to: toEl.value.trim(),
        uncertainties,
      });

      const rows = resp.values.map((v, i) => {
        const u = resp.uncertainties ? resp.uncertainties[i] : null;
        return `<tr><td class="num">${i + 1}</td><td class="num">${values[i]}</td><td class="num" style="color:var(--accent-2)">${v.toPrecision(6)}</td><td class="num">${u !== null ? u.toPrecision(4) : "—"}</td></tr>`;
      });

      resEl.innerHTML = `
        <table class="tabla">
          <thead><tr><th>#</th><th style="text-align:right">Original (${escapeHtml(fromEl.value)})</th><th style="text-align:right">Convertido (${escapeHtml(toEl.value)})</th><th style="text-align:right">δ (${escapeHtml(toEl.value)})</th></tr></thead>
          <tbody>${rows.join("")}</tbody>
        </table>
      `;

      lastCopyText = resp.values
        .map((v, i) => (resp.uncertainties ? `${v}\t${resp.uncertainties[i]}` : `${v}`))
        .join("\n");
      checkCompatibility();
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setLoading(btnConv, false);
    }
  }

  fromEl.addEventListener("change", checkCompatibility);
  toEl.addEventListener("change", checkCompatibility);
  btnConv.addEventListener("click", runConvert);
  document.getElementById("u-copiar").addEventListener("click", () => {
    if (!lastCopyText) return toast("Primero realizá una conversión.", "info");
    copyText(lastCopyText, "Columna convertida copiada");
  });

  checkCompatibility();
  return { runPrimary: runConvert };
}
