// Lógica pura (sin DOM) reutilizada por las vistas y testeada con `node --test`.

const RESERVED = new Set([
  "pi", "e", "E",
  "sin", "cos", "tan", "asin", "acos", "atan",
  "sinh", "cosh", "tanh",
  "exp", "log", "ln", "sqrt", "abs", "Abs",
]);

/**
 * Devuelve los nombres de variables de una expresión matemática, en orden de
 * aparición y sin duplicados, excluyendo funciones y constantes conocidas.
 * @param {string} expr
 * @returns {string[]}
 */
export function extractVariables(expr) {
  if (!expr) return [];
  // Quitar literales numéricos (incluida notación científica) para no confundir "e3" con una variable.
  const sinNumeros = expr.replace(/\b\d+(\.\d*)?([eE][+-]?\d+)?|\.\d+([eE][+-]?\d+)?/g, " ");
  const vistos = [];
  for (const [nombre] of sinNumeros.matchAll(/[A-Za-z_][A-Za-z0-9_]*/g)) {
    if (!RESERVED.has(nombre) && !vistos.includes(nombre)) vistos.push(nombre);
  }
  return vistos;
}

/**
 * Descarta filas con celdas vacías o no finitas.
 * @param {(number|null|undefined)[][]} rows
 * @param {number} minPoints
 * @returns {number[][]}
 */
export function cleanRows(rows, minPoints = 3) {
  const validas = rows.filter(
    (fila) => fila.length > 0 && fila.every((v) => typeof v === "number" && Number.isFinite(v)),
  );
  if (validas.length < minPoints) {
    throw new Error(
      `Se necesitan al menos ${minPoints} filas completas para continuar (hay ${validas.length}).`,
    );
  }
  return validas;
}

/** Convierte el texto de una celda en número aceptando coma decimal. */
export function parseCell(texto) {
  if (texto === null || texto === undefined) return null;
  const t = String(texto).trim().replace(",", ".");
  if (t === "") return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}
