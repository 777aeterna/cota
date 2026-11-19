<p align="center">
  <img src="src/cota/web/static/img/logo-cota.png" alt="Logo de Cota" width="180" />
</p>

<h1 align="center">Cota</h1>

<p align="center">
  <strong>Plataforma web de análisis experimental, metrología GUM y ajuste de curvas para estudiantes de ciencias exactas, naturales e ingeniería.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Licencia-MIT-3B82F6?style=flat-square" alt="Licencia MIT" />
  <img src="https://img.shields.io/badge/Modo-100%25%20Offline-22D3EE?style=flat-square" alt="100% Offline" />
  <img src="https://img.shields.io/badge/Vibecodeado-con%20IA%20%2B%20TDD-C9A45C?style=flat-square" alt="Vibecodeado con IA y TDD" />
</p>

---

## ¿Qué es Cota?

**Cota** (*alusión directa a la cota de error de toda medición experimental*) es una alternativa moderna, abierta y gratuita a herramientas privativas como *OriginLab* o *SciDAVis*, pensada específicamente para las materias de laboratorio de Física, Química e Ingeniería.

Funciona **100 % en local y sin conexión a internet** (tanto Plotly.js como KaTeX vienen empaquetados localmente) y se levanta con **un solo comando en Python**.

> **Nota de transparencia:** Este proyecto fue **vibecodeado** (diseñado y programado de forma asistida por agentes de IA bajo flujo TDD estricto, validación numérica contra datasets publicados como York 2004 y normas GUM/JCGM).

---

## Capacidades Principales

### 1. Ajuste de Curvas y Residuos
* **Grilla editable con pegado directo desde Excel / Google Sheets** (detección automática de `;`, `\t`, `,` y soporte de coma decimal en español).
* **Regresión lineal ponderada:** mínimos cuadrados ponderados (**WLS**) si solo hay error en $Y$, y **algoritmo iterativo de York (2004)** cuando hay errores en ambos ejes ($\delta x$ y $\delta y$).
* **Modelos físicos no lineales:** Lineal, Cuadrático, Decaimiento exponencial ($RC$), Oscilador amortiguado, Gaussiana (picos espectrales), Ley de potencias y **expresiones personalizadas** evaluadas de forma segura con `SymPy` (sin `eval()`).
* Gráficos interactivos con **barras de error**, **banda de confianza al 95 %**, **residuos normalizados**, $\chi^2_\nu$, $R^2$, $p$-valor y exportación en **PNG / SVG** y **tablas/parámetros en LaTeX (`booktabs`)**.

### 2. Propagación de Incertidumbres
* **Analítica simbólica (GUM):** calcula derivadas parciales con `SymPy`, aportes porcentuales a la varianza y genera la fórmula simbólica en LaTeX lista para copiar a Overleaf.
* **Simulación Monte Carlo (JCGM 101):** hasta 300 000 muestras con distribuciones Normal, Rectangular o Triangular, histograma interactivo e intervalos de cobertura.

### 3. Presupuesto de Incertidumbre (GUM — JCGM 100:2008)
* **Tipo A:** media, desvío estándar muestral, $u_A = s/\sqrt{n}$ y test de normalidad de Shapiro–Wilk.
* **Tipo B:** fuentes instrumentales con distribución rectangular ($a/\sqrt{3}$), triangular ($a/\sqrt{6}$) o normal ($a/k$).
* **Combinación:** suma en cuadratura, grados efectivos de libertad (**Welch–Satterthwaite**), factor de cobertura $t$ de Student y **redondeo científico automático** de cifras significativas.

### 4. Conversor Dimensional de Unidades
* Conversión de columnas completas con sus incertidumbres mediante `Pint`.
* Manejo correcto de escalas con desplazamiento (por ejemplo `°C → K`, donde la temperatura suma `273.15` pero la incertidumbre se conserva como delta).

---

## Instalación y Uso Rápido

Solo necesitás **Python 3.12+** (no hace falta instalar Node.js para correr la aplicación).

```bash
# 1. Clonar el repositorio
git clone https://github.com/<tu-usuario>/cota.git
cd cota

# 2. Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -e .

# 4. Iniciar Cota (abre automáticamente tu navegador)
python run.py
```

Opciones útiles del lanzador:
```bash
python run.py --port 8080        # Elegir puerto preferido (si está ocupado busca el siguiente libre)
python run.py --no-browser       # Iniciar solo el servidor sin abrir el navegador
```

También podés explorar la documentación interactiva OpenAPI en `http://127.0.0.1:8000/docs`.

---

## Tests y Verificación

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Correr la suite de tests en Python (núcleo matemático, API, estáticos y lanzador)
pytest -v

# (Opcional) Correr los tests unitarios de lógica JS pura con Node 22+
node --test tests/js/expr.test.mjs
```

---

## Estructura del Proyecto

```text
.
├── run.py                          # Lanzador en un solo comando
├── pyproject.toml                  # Configuración del paquete y dependencias
├── src/cota/
│   ├── core/                       # Núcleo científico puro (sin dependencias web)
│   │   ├── validation.py           # Validadores numéricos y parseo seguro SymPy
│   │   ├── metrology.py            # GUM Tipo A, Tipo B, Welch-Satterthwaite y redondeo
│   │   ├── propagation.py          # Propagación analítica y Monte Carlo (JCGM 101)
│   │   ├── fitting.py              # WLS, York (2004), modelos no lineales y bandas
│   │   └── units.py                # Conversión dimensional con Pint
│   ├── api/                        # Capa REST con FastAPI + Pydantic v2
│   └── web/static/                 # Interfaz SPA sin build (CSS, ES Modules, Plotly y KaTeX locales)
└── tests/                          # Suite de pruebas unitarias e integración
```

---

## Contribuir

Las contribuciones, reportes de bugs y nuevos ejemplos de prácticas de laboratorio son bienvenidos. Revisá [CONTRIBUTING.md](CONTRIBUTING.md) para ver cómo enviar un Pull Request.

## Licencia

Distribuido bajo la licencia **MIT**. Consultá el archivo [LICENSE](LICENSE) para más detalles.
