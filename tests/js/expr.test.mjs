import { test } from "node:test";
import assert from "node:assert/strict";
import { extractVariables, cleanRows } from "../../src/cota/web/static/js/lib/expr.js";

test("extractVariables detecta solo variables, no funciones ni constantes", () => {
  assert.deepEqual(extractVariables("4*pi**2*L/T**2"), ["L", "T"]);
  assert.deepEqual(extractVariables("A*exp(-t/tau) + sin(w*t)"), ["A", "t", "tau", "w"]);
  assert.deepEqual(extractVariables("x_1 + 2.5e3*x_2"), ["x_1", "x_2"]);
  assert.deepEqual(extractVariables("sqrt(a**2 + b**2) + E"), ["a", "b"]);
  assert.deepEqual(extractVariables(""), []);
});

test("cleanRows descarta filas incompletas o no finitas", () => {
  assert.deepEqual(
    cleanRows([[1, 2], [null, 3], [4, NaN], [5, 6], [7, 8]]),
    [[1, 2], [5, 6], [7, 8]],
  );
});

test("cleanRows exige un mínimo de puntos válidos", () => {
  assert.throws(() => cleanRows([[1, 2], [3, 4]]), /al menos 3/);
});
