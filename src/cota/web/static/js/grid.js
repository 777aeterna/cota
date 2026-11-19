// Grilla editable de datos experimentales con soporte de pegado desde Excel / Sheets.

import { api } from "./api.js";
import { parseCell } from "./lib/expr.js";
import { toast } from "./ui.js";

const COLUMNS = [
  { key: "x", label: "x", role: "indep." },
  { key: "y", label: "y", role: "dep." },
  { key: "dy", label: "δy", role: "error y" },
  { key: "dx", label: "δx", role: "opcional" },
];

export function createDataGrid(container, { onChange } = {}) {
  let rows = [];

  function notify() {
    if (onChange) onChange(getRows());
  }

  function render() {
    const wrap = document.createElement("div");
    wrap.className = "grid-wrap";
    const table = document.createElement("table");
    table.className = "grid";

    const thead = document.createElement("thead");
    thead.innerHTML = `<tr><th>#</th>${COLUMNS.map(
      (c) => `<th>${c.label}<span class="role">${c.role}</span></th>`,
    ).join("")}<th></th></tr>`;
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    rows.forEach((row, rIdx) => {
      const tr = document.createElement("tr");
      const tdIdx = document.createElement("td");
      tdIdx.className = "idx";
      tdIdx.textContent = String(rIdx + 1);
      tr.appendChild(tdIdx);

      COLUMNS.forEach((col, cIdx) => {
        const td = document.createElement("td");
        const inp = document.createElement("input");
        inp.type = "text";
        inp.inputMode = "decimal";
        inp.value = row[cIdx] ?? "";
        inp.dataset.r = String(rIdx);
        inp.dataset.c = String(cIdx);

        inp.addEventListener("input", () => {
          rows[rIdx][cIdx] = inp.value;
          notify();
        });

        inp.addEventListener("keydown", (ev) => {
          if (ev.key === "Enter" && !ev.ctrlKey && !ev.metaKey) {
            ev.preventDefault();
            if (rIdx === rows.length - 1) {
              rows.push(["", "", "", ""]);
              render();
            }
            focusCell(rIdx + 1, cIdx);
          } else if (ev.key === "ArrowDown") {
            focusCell(Math.min(rows.length - 1, rIdx + 1), cIdx);
          } else if (ev.key === "ArrowUp") {
            focusCell(Math.max(0, rIdx - 1), cIdx);
          }
        });

        inp.addEventListener("paste", async (ev) => {
          const text = ev.clipboardData?.getData("text");
          if (text && (text.includes("\n") || text.includes("\t") || text.includes(";"))) {
            ev.preventDefault();
            await pasteTabular(text);
          }
        });

        td.appendChild(inp);
        tr.appendChild(td);
      });

      const tdDel = document.createElement("td");
      tdDel.className = "del";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.title = "Eliminar fila";
      btn.textContent = "×";
      btn.addEventListener("click", () => {
        rows.splice(rIdx, 1);
        if (rows.length === 0) rows.push(["", "", "", ""]);
        render();
        notify();
      });
      tdDel.appendChild(btn);
      tr.appendChild(tdDel);
      tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    wrap.appendChild(table);
    container.innerHTML = "";
    container.appendChild(wrap);
  }

  function focusCell(r, c) {
    const inp = container.querySelector(`input[data-r="${r}"][data-c="${c}"]`);
    if (inp) inp.focus();
  }

  async function pasteTabular(text) {
    try {
      const parsed = await api.parseCsv({ text });
      rows = parsed.rows.map((r) => [
        r[0] !== undefined ? String(r[0]) : "",
        r[1] !== undefined ? String(r[1]) : "",
        r[2] !== undefined ? String(r[2]) : "",
        r[3] !== undefined ? String(r[3]) : "",
      ]);
      render();
      notify();
      toast(`Se importaron ${rows.length} filas (${parsed.headers.length} columnas).`, "ok", 2500);
    } catch (err) {
      toast(err.message, "error");
    }
  }

  function setRows(newRows) {
    rows = newRows.map((r) => [
      r[0] !== undefined && r[0] !== null ? String(r[0]) : "",
      r[1] !== undefined && r[1] !== null ? String(r[1]) : "",
      r[2] !== undefined && r[2] !== null ? String(r[2]) : "",
      r[3] !== undefined && r[3] !== null ? String(r[3]) : "",
    ]);
    if (rows.length === 0) rows.push(["", "", "", ""]);
    render();
    notify();
  }

  function getRows() {
    return rows.map((r) => r.map(parseCell));
  }

  function addRow() {
    rows.push(["", "", "", ""]);
    render();
    focusCell(rows.length - 1, 0);
  }

  function clear() {
    setRows([["", "", "", ""], ["", "", "", ""], ["", "", "", ""]]);
  }

  setRows([["", "", "", ""]]);

  return { setRows, getRows, addRow, clear, pasteTabular };
}
