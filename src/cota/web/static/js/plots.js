// Gráficos científicos interactivos con Plotly.js adaptados al tema de Cota.

import { currentTheme } from "./ui.js";

function palette() {
  const light = currentTheme() === "claro";
  return {
    bg: "rgba(0,0,0,0)",
    grid: light ? "rgba(15, 23, 42, 0.08)" : "rgba(148, 163, 184, 0.12)",
    zero: light ? "rgba(15, 23, 42, 0.25)" : "rgba(148, 163, 184, 0.30)",
    text: light ? "#0f172a" : "#e6ebf5",
    muted: light ? "#55627a" : "#8b97ad",
    accent: light ? "#2563eb" : "#3b82f6",
    cyan: light ? "#0891b2" : "#22d3ee",
    gold: light ? "#a8843d" : "#c9a45c",
    band: light ? "rgba(37, 99, 235, 0.14)" : "rgba(34, 211, 238, 0.16)",
    hoverBg: light ? "#ffffff" : "#111724",
  };
}

function baseLayout(extra = {}) {
  const p = palette();
  return {
    paper_bgcolor: p.bg,
    plot_bgcolor: p.bg,
    font: { family: "Inter, system-ui, sans-serif", color: p.text, size: 12 },
    margin: { t: 22, r: 22, b: 48, l: 58 },
    hoverlabel: { bgcolor: p.hoverBg, bordercolor: p.accent, font: { family: "JetBrains Mono, monospace", size: 12 } },
    legend: { orientation: "h", y: 1.08, x: 0, bgcolor: "rgba(0,0,0,0)", font: { size: 11.5 } },
    xaxis: {
      gridcolor: p.grid,
      zerolinecolor: p.zero,
      linecolor: p.grid,
      tickfont: { family: "JetBrains Mono, monospace", size: 11, color: p.muted },
      ...(extra.xaxis || {}),
    },
    yaxis: {
      gridcolor: p.grid,
      zerolinecolor: p.zero,
      linecolor: p.grid,
      tickfont: { family: "JetBrains Mono, monospace", size: 11, color: p.muted },
      ...(extra.yaxis || {}),
    },
    ...extra,
  };
}

const PLOT_CONFIG = {
  responsive: true,
  displaylogo: false,
  modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d"],
};

export function renderFitPlot(el, { x, y, dy, dx, fit, xlabel, ylabel }) {
  if (!window.Plotly || !el) return;
  const p = palette();
  const traces = [];

  if (fit) {
    traces.push({
      x: [...fit.curve_x, ...fit.curve_x.slice().reverse()],
      y: [...fit.band_high, ...fit.band_low.slice().reverse()],
      fill: "toself",
      fillcolor: p.band,
      line: { color: "transparent" },
      name: "Banda de confianza",
      hoverinfo: "skip",
      type: "scatter",
    });
    traces.push({
      x: fit.curve_x,
      y: fit.curve_y,
      mode: "lines",
      name: "Modelo ajustado",
      line: { color: p.cyan, width: 2.6 },
      type: "scatter",
    });
  }

  traces.push({
    x,
    y,
    mode: "markers",
    name: "Mediciones",
    type: "scatter",
    marker: { color: p.accent, size: 7.5, line: { color: "#ffffff", width: 1.2 } },
    error_y: dy ? { type: "data", array: dy, visible: true, color: p.accent, thickness: 1.4, width: 4 } : undefined,
    error_x: dx ? { type: "data", array: dx, visible: true, color: p.gold, thickness: 1.4, width: 4 } : undefined,
  });

  window.Plotly.react(
    el,
    traces,
    baseLayout({
      xaxis: { title: { text: xlabel || "x", standoff: 10 } },
      yaxis: { title: { text: ylabel || "y", standoff: 10 } },
    }),
    PLOT_CONFIG,
  );
}

export function renderResidualsPlot(el, { x, normalizedResiduals, xlabel }) {
  if (!window.Plotly || !el) return;
  const p = palette();
  const traces = [
    {
      x,
      y: normalizedResiduals,
      mode: "markers",
      type: "scatter",
      name: "Residuo normalizado",
      marker: { color: p.gold, size: 7, line: { color: p.text, width: 0.7 } },
    },
  ];
  const xMin = Math.min(...x);
  const xMax = Math.max(...x);
  window.Plotly.react(
    el,
    traces,
    baseLayout({
      margin: { t: 10, r: 22, b: 42, l: 58 },
      showlegend: false,
      xaxis: { title: { text: xlabel || "x", standoff: 8 } },
      yaxis: { title: { text: "r / σ", standoff: 8 } },
      shapes: [
        { type: "line", x0: xMin, x1: xMax, y0: 0, y1: 0, line: { color: p.cyan, width: 1.5, dash: "dash" } },
        { type: "line", x0: xMin, x1: xMax, y0: 2, y1: 2, line: { color: p.grid, width: 1, dash: "dot" } },
        { type: "line", x0: xMin, x1: xMax, y0: -2, y1: -2, line: { color: p.grid, width: 1, dash: "dot" } },
      ],
    }),
    PLOT_CONFIG,
  );
}

export function renderMonteCarloHist(el, mc) {
  if (!window.Plotly || !el) return;
  const p = palette();
  const centers = [];
  for (let i = 0; i < mc.histogram_counts.length; i++) {
    centers.push(0.5 * (mc.histogram_edges[i] + mc.histogram_edges[i + 1]));
  }
  const maxY = Math.max(...mc.histogram_counts, 1);

  const traces = [
    {
      x: centers,
      y: mc.histogram_counts,
      type: "bar",
      name: "Muestras",
      marker: { color: p.accent, opacity: 0.78, line: { color: p.cyan, width: 0.6 } },
    },
  ];

  window.Plotly.react(
    el,
    traces,
    baseLayout({
      bargap: 0.04,
      showlegend: false,
      margin: { t: 18, r: 20, b: 46, l: 58 },
      xaxis: { title: { text: "Valor simulado de f", standoff: 8 } },
      yaxis: { title: { text: "Frecuencia", standoff: 8 } },
      shapes: [
        { type: "line", x0: mc.mean, x1: mc.mean, y0: 0, y1: maxY * 1.05, line: { color: p.cyan, width: 2 } },
        { type: "line", x0: mc.ci_low, x1: mc.ci_low, y0: 0, y1: maxY * 1.05, line: { color: p.gold, width: 1.8, dash: "dash" } },
        { type: "line", x0: mc.ci_high, x1: mc.ci_high, y0: 0, y1: maxY * 1.05, line: { color: p.gold, width: 1.8, dash: "dash" } },
      ],
      annotations: [
        { x: mc.mean, y: maxY * 1.03, text: "media", showarrow: false, font: { size: 11, color: p.cyan } },
        { x: mc.ci_low, y: maxY * 0.92, text: "IC inf", showarrow: false, font: { size: 10.5, color: p.gold } },
        { x: mc.ci_high, y: maxY * 0.92, text: "IC sup", showarrow: false, font: { size: 10.5, color: p.gold } },
      ],
    }),
    PLOT_CONFIG,
  );
}

export function downloadPlotImage(el, format = "png", filename = "cota-grafico") {
  if (!window.Plotly || !el) return;
  window.Plotly.downloadImage(el, {
    format,
    filename,
    width: 1200,
    height: 750,
    scale: format === "png" ? 2 : 1,
  });
}
