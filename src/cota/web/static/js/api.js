// Cliente HTTP para la API de Cota con manejo limpio de errores en castellano.

async function request(path, options = {}) {
  let resp;
  try {
    resp = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
  } catch {
    throw new Error("No se pudo conectar con el servidor local de Cota.");
  }

  let data = null;
  try {
    data = await resp.json();
  } catch {
    data = null;
  }

  if (!resp.ok) {
    let msg = `Error HTTP ${resp.status}`;
    if (data && typeof data.detail === "string") {
      msg = data.detail;
    } else if (data && Array.isArray(data.detail) && data.detail.length > 0) {
      const first = data.detail[0];
      const loc = Array.isArray(first.loc) ? first.loc.slice(1).join(".") : "";
      msg = loc ? `Campo '${loc}': ${first.msg}` : first.msg;
    }
    throw new Error(msg);
  }
  return data;
}

export const api = {
  health: () => request("/api/health", { method: "GET" }),
  fittingModels: () => request("/api/fitting/models", { method: "GET" }),
  fitLinear: (body) => request("/api/fitting/linear", { method: "POST", body: JSON.stringify(body) }),
  fitNonlinear: (body) => request("/api/fitting/nonlinear", { method: "POST", body: JSON.stringify(body) }),
  propagateAnalytical: (body) =>
    request("/api/propagation/analytical", { method: "POST", body: JSON.stringify(body) }),
  propagateMonteCarlo: (body) =>
    request("/api/propagation/monte-carlo", { method: "POST", body: JSON.stringify(body) }),
  typeA: (body) => request("/api/metrology/type-a", { method: "POST", body: JSON.stringify(body) }),
  typeB: (body) => request("/api/metrology/type-b", { method: "POST", body: JSON.stringify(body) }),
  combine: (body) => request("/api/metrology/combine", { method: "POST", body: JSON.stringify(body) }),
  format: (body) => request("/api/metrology/format", { method: "POST", body: JSON.stringify(body) }),
  unitsCompatible: (body) => request("/api/units/compatible", { method: "POST", body: JSON.stringify(body) }),
  unitsConvert: (body) => request("/api/units/convert", { method: "POST", body: JSON.stringify(body) }),
  parseCsv: (body) => request("/api/data/parse-csv", { method: "POST", body: JSON.stringify(body) }),
  exportLatex: (body) => request("/api/data/export-latex", { method: "POST", body: JSON.stringify(body) }),
};
