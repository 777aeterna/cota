# Contribuir a Cota

¡Gracias por tu interés en mejorar **Cota**! Este proyecto nació para ayudar a estudiantes y docentes de ciencias exactas, naturales e ingeniería en sus prácticas de laboratorio.

## Entorno de desarrollo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

Si modificás lógica en `src/cota/web/static/js/lib/`, corré también los tests de JS:

```bash
node --test tests/js/expr.test.mjs
```

## Convenciones

1. **Rigor científico primero:** cualquier cambio en fórmulas de `src/cota/core/` debe incluir un test unitario contrastado contra un resultado analítico o referencia bibliográfica (GUM, York, etc.).
2. **Interfaz en castellano:** todos los textos visibles, etiquetas y mensajes de error de la API deben redactarse en castellano claro.
3. **Sin dependencias de build en producción:** mantené el frontend sin paso de compilación obligatorio para que `python run.py` siga funcionando solo con Python.
4. **Transparencia:** este repositorio fue inicialmente vibecodeado con asistencia de IA bajo flujo TDD; los PRs asistidos por IA son bienvenidos siempre que incluyan pruebas reales y hayan sido verificados.

## Flujo de Pull Request

1. Creá una rama desde `main` (`git checkout -b feat/mi-mejora`).
2. Escribí tests para tu cambio y verificá que `pytest` pase sin errores.
3. Abrí el Pull Request explicando qué problema resuelve y cómo se probó.
