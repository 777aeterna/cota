// Utilidades de interfaz: toasts, KaTeX, modales, tema y portapapeles.

export function toast(mensaje, tipo = "info", duracionMs = 4200) {
  const cont = document.getElementById("toasts");
  if (!cont) return;
  const el = document.createElement("div");
  el.className = `toast ${tipo}`;
  el.textContent = mensaje;
  cont.appendChild(el);
  setTimeout(() => {
    el.style.opacity = "0";
    el.style.transition = "opacity 0.2s";
    setTimeout(() => el.remove(), 220);
  }, duracionMs);
}

export function renderKatex(el, tex, displayMode = true) {
  if (!el) return;
  if (!tex) {
    el.innerHTML = `<span class="faint">—</span>`;
    return;
  }
  if (window.katex) {
    try {
      window.katex.render(tex, el, { displayMode, throwOnError: false });
      return;
    } catch {
      // fallback a texto
    }
  }
  el.textContent = tex;
}

export function formatPmHtml(formattedText) {
  if (!formattedText) return "—";
  const parts = String(formattedText).split("±");
  if (parts.length !== 2) return escapeHtml(formattedText);
  return `${escapeHtml(parts[0].trim())}<span class="pm">±</span>${escapeHtml(parts[1].trim())}`;
}

export function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export async function copyText(text, label = "Copiado al portapapeles") {
  try {
    await navigator.clipboard.writeText(text);
    toast(label, "ok", 2200);
  } catch {
    toast("No se pudo copiar automáticamente; seleccionalo manualmente.", "error");
  }
}

export function showCodeModal(titulo, codigo) {
  const back = document.createElement("div");
  back.className = "modal-back";
  back.innerHTML = `
    <div class="modal" role="dialog" aria-modal="true">
      <div class="modal-head">
        <h3>${escapeHtml(titulo)}</h3>
        <div class="row tight">
          <button class="btn btn-sm btn-primary" data-copiar>Copiar</button>
          <button class="btn btn-sm btn-ghost" data-cerrar>Cerrar</button>
        </div>
      </div>
      <div class="modal-body"><pre class="code">${escapeHtml(codigo)}</pre></div>
    </div>
  `;
  const cerrar = () => back.remove();
  back.addEventListener("click", (e) => {
    if (e.target === back || e.target.closest("[data-cerrar]")) cerrar();
  });
  back.querySelector("[data-copiar]").addEventListener("click", () => {
    copyText(codigo, "Código LaTeX copiado");
  });
  document.addEventListener("keydown", function onEsc(ev) {
    if (ev.key === "Escape") {
      cerrar();
      document.removeEventListener("keydown", onEsc);
    }
  });
  document.body.appendChild(back);
}

export function setLoading(btn, loading) {
  if (!btn) return;
  if (loading) {
    btn.dataset.prevHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spin"></span> Calculando…`;
  } else {
    btn.disabled = false;
    if (btn.dataset.prevHtml) btn.innerHTML = btn.dataset.prevHtml;
  }
}

export function currentTheme() {
  return document.documentElement.dataset.tema === "claro" ? "claro" : "oscuro";
}

export function toggleTheme() {
  const next = currentTheme() === "oscuro" ? "claro" : "oscuro";
  document.documentElement.dataset.tema = next;
  try {
    localStorage.setItem("cota-tema", next);
  } catch {
    // ignorar si storage está bloqueado
  }
  window.dispatchEvent(new CustomEvent("cota:tema", { detail: { tema: next } }));
}
