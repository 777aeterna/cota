// Punto de entrada de la SPA de Cota: router de pestañas, estado de API y atajos.

import { api } from "./api.js";
import { toggleTheme } from "./ui.js";
import { initAjusteView } from "./views/ajuste.js";
import { initGumView } from "./views/gum.js";
import { initPropagacionView } from "./views/propagacion.js";
import { initUnidadesView } from "./views/unidades.js";

const views = {};
let activeView = "ajuste";

function switchView(name) {
  if (!document.getElementById(`vista-${name}`)) return;
  activeView = name;
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.setAttribute("aria-selected", btn.dataset.vista === name ? "true" : "false");
  });
  document.querySelectorAll(".view").forEach((sec) => {
    sec.classList.toggle("active", sec.id === `vista-${name}`);
  });
  // Forzar recalculo de tamaño de Plotly al mostrar una pestaña que estaba oculta
  window.dispatchEvent(new Event("resize"));
}

async function checkHealth() {
  const pill = document.getElementById("estado-api");
  const text = pill?.querySelector(".status-text");
  try {
    const h = await api.health();
    pill.className = "status-pill ok";
    text.textContent = `Motor v${h.version}`;
  } catch {
    pill.className = "status-pill err";
    text.textContent = "Sin conexión";
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.vista));
  });

  document.getElementById("btn-tema")?.addEventListener("click", toggleTheme);

  document.addEventListener("keydown", (ev) => {
    if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter") {
      ev.preventDefault();
      views[activeView]?.runPrimary?.();
    }
  });

  await checkHealth();
  views.ajuste = await initAjusteView();
  views.propagacion = await initPropagacionView();
  views.gum = await initGumView();
  views.unidades = await initUnidadesView();
});
