# MetriLab — Plataforma Web de Análisis Experimental, Metrología y Reportes Científicos

> **Nombre del proyecto:** **MetriLab** (*Laboratorio Metrológico Digital*)  
> **Definición:** Plataforma web fullstack open-source en Python diseñada para transformar datos experimentales en resultados científicos rigurosos, visualizaciones de calidad editorial e informes académicos automáticos para estudiantes y docentes de ciencias exactas, naturales e ingeniería.

---

## 1. Visión del Producto y Filosofía de Diseño

### 1.1 El Problema Actual
En las materias de ciencias e ingeniería (Física I-IV, Química General/Física, Mediciones, Termodinámica), los estudiantes pierden hasta el 70% del tiempo de laboratorio en:
1. Calcular a mano derivadas parciales engorrosas para propagar errores.
2. Usar software privativo complejo o anticuado (OriginLab, SciDAVis, LoggerPro).
3. Formatear gráficos mediocres en hojas de cálculo estándar que no respetan convenciones metrológicas ni cifras significativas.
4. Luchar para pasar tablas y ecuaciones a LaTeX para el informe final.

### 1.2 La Propuesta de MetriLab
* **Rigor Metrológico Automático:** Implementa el estándar internacional **GUM (Guide to the Expression of Uncertainty in Measurement / JCGM 100:2008)**.
* **Experiencia de Usuario Premium:** Interfaz oscura/clara moderna inspirada en herramientas contemporáneas de alto nivel (Linear, Raycast, Vercel), con gráficos vectoriales interactivos, microinteracciones y atajos de teclado.
* **Arranque en un Solo Comando:** El backend en Python sirve la aplicación web moderna empaquetada. El estudiante clona el repositorio, ejecuta `python run.py` y se abre automáticamente en el navegador sin configuraciones complejas de Node ni servidores múltiples.

---

## 2. Arquitectura del Sistema y Módulos Técnicos

```
┌─────────────────────────────────────────────────────────────────┐
│                    METRILAB - ARQUITECTURA                      │
└─────────────────────────────────────────────────────────────────┘

     [ Interfaz Web Premium (SPA) ]  <─── WebSocket / REST API
         ├─ Rejilla de Datos tipo Spreadsheet (Handsontable / TanStack)
         ├─ Lienzo Científico Interactivo (Plotly.js / WebGL)
         └─ Asistente de Exportación LaTeX / PDF
                        │
                        ▼
     [ Backend Python Fullstack (FastAPI) ]
         ├─ Módulo Metrológico (GUM + Monte Carlo + SymPy)
         ├─ Motor de Ajuste de Curvas (SciPy Optimize + LMFIT)
         ├─ Validador Dimensional y Unidades (Pint)
         └─ Generador de Reportes (Jinja2 + LaTeX / Typst)
```

### Módulo A: Rejilla de Datos Inteligente (*DataGrid*)
* Soporte para copiar y pegar directo desde Excel, Google Sheets o archivos `.csv` / `.tsv`.
* Asociación inteligente de columnas: Variable Independiente ($X$), Variable Dependiente ($Y$) y sus respectivas incertidumbres ($\Delta X$, $\Delta Y$).
* Conversión de unidades integrada mediante la librería `Pint` (ej. si una columna está en $\text{cm}$ y otra en $\text{m}$, unifica automáticamente).
* Estadísticos descriptivos instantáneos por columna: media muestral ($\bar{x}$), desviación estándar muestral ($s$), mediana, curtosis y test de normalidad.

### Módulo B: Motor de Metrología y Propagación de Incertidumbres
* **Incertidumbre Tipo A:** Basada en repeticiones estadísticas, grados de libertad y factor de cobertura $t$ de Student.
* **Incertidumbre Tipo B:** Estimación instrumental (resolución del calibre, tester digital, tolerancia del fabricante, distribuciones rectangular o triangular).
* **Propagación Analítica (Simbólica):** Utiliza `SymPy` para calcular automáticamente el gradiente $\nabla f$ y aplicar la fórmula de propagación de Gauss:
  $$u_c^2(y) = \sum_{i=1}^n \left(\frac{\partial f}{\partial x_i}\right)^2 u^2(x_i) + 2 \sum_{i=1}^{n-1} \sum_{j=i+1}^n \frac{\partial f}{\partial x_i} \frac{\partial f}{\partial x_j} u(x_i, x_j)$$
* **Propagación por Monte Carlo:** Genera $10^5$ iteraciones para modelos altamente no lineales o distribuciones no gaussianas (siguiendo JCGM 101).
* **Redondeo Científico y Cifras Significativas:** Reglas metrológicas automáticas (incertidumbres reportadas a 1 o 2 cifras significativas y valor central acotado al mismo orden decimal).

### Módulo C: Motor de Ajuste de Curvas y Modelado Físico
* **Regresión Lineal Ponderada en Ambos Ejes:** Algoritmo de York / Chi-cuadrado ($\chi^2$), calculando pendiente, ordenada al origen, sus incertidumbres correlacionadas y el valor de $\chi^2_{\text{reducido}}$.
* **Biblioteca de Modelos Físicos Estándar:**
  - Decaimiento exponencial y carga/descarga de capacitores: $y(t) = y_0 + A e^{-t/\tau}$.
  - Movimiento oscilatorio amortiguado: $y(t) = A e^{-\gamma t} \cos(\omega t + \phi)$.
  - Distribuciones Gaussianas / Picos espectrales: $y(x) = y_0 + \frac{A}{w \sqrt{\pi/2}} e^{-2 \frac{(x-x_c)^2}{w^2}}$.
  - Ley de enfriamiento de Newton, Ley de Beer-Lambert, Ley de Ohm, Ley de Hooke.
* **Ajuste Personalizado:** El usuario escribe su propia función matemática (ej. `A * sin(w*x + p) / x`) y el motor ajusta los parámetros con estimaciones iniciales automáticas.
* **Gráfico de Residuos:** Visualización simultánea de $y_i - f(x_i)$ para evaluar la validez del modelo físico.

### Módulo D: Visualizador Científico Gráfico
* Gráficos interactivos con zoom, pan, tooltip dinámico que muestra $(x \pm \Delta x, y \pm \Delta y)$.
* Bandas de confianza del 95% y bandas de predicción alrededor del ajuste.
* Exportación vectorial en SVG, PDF y PNG a 300/600 DPI con tipografías tipográficas estándar (Computer Modern / TeX Gyre Termes) para incluir directamente en informes o tesis.

### Módulo E: Exportador de Informes y LaTeX
* Generación de tablas formateadas con sintaxis de LaTeX (`tabular`, `booktabs`).
* Exportación del procedimiento completo a formato Markdown o documento PDF listo para imprimir.

---

## 3. Esquema de Fases de Desarrollo

Para garantizar modularidad, trazabilidad metrológica y cobertura de pruebas, la arquitectura se estructura en **5 fases**:

| Fase | Objetivo Principal | Entregables Clave |
| :--- | :--- | :--- |
| **Fase 1: Núcleo Matemático y Metrología (TDD)** | Construir y verificar el motor de cálculo en Python con pruebas unitarias estrictas. | Módulos `metrology.py`, `propagation.py`, `fitting.py` y `units.py` con cobertura de tests basados en casos reales de laboratorio. |
| **Fase 2: API REST y Contratos de Datos (FastAPI)** | Exponer el motor matemático mediante endpoints REST estructurados y validados con Pydantic. | Servidor FastAPI, esquemas Pydantic para matrices de datos, validación de unidades y tests de integración de API. |
| **Fase 3: Interfaz Web Premium (Frontend SPA)** | Crear la interfaz visual (Dark/Light), tabla interactiva de datos y visualización con Plotly.js. | Componentes interactivos, DataGrid con pegado directo y lienzo de gráficos responsivo. |
| **Fase 4: Integración, Exportador LaTeX/PDF y Empaquetado** | Conectar frontend y backend; habilitar exportaciones y ejecución con un solo comando. | Script de inicio `run.py`, integración estática en FastAPI y generador de código LaTeX (`booktabs`). |
| **Fase 5: Documentación y Lanzamiento** | Documentar instalación, arquitectura y ejemplos de uso. | `README.md`, guías de contribución y flujo de integración continua (CI). |
---

## 4. Requisitos para una "Interfaz Excelente y Premium"

Para que el proyecto se destaque inmediatamente al abrirse:
1. **Tema "Dark Mode First":** Paleta moderna oscura (grises profundos `#0B0F17`, acentos en azul eléctrico `#3B82F6` o cian esmeralda `#10B981`), acompañada de tipografía limpia (`Inter` para UI, `JetBrains Mono` para datos numéricos y fórmulas).
2. **Tablero tipo Estudio:**
   - **Panel Izquierdo:** Entrada de datos (DataGrid con pegado veloz y selector de columnas).
   - **Panel Central Superior:** Gráfico interactivo con barra de herramientas flotante.
   - **Panel Central Inferior:** Parámetros del ajuste, $\chi^2$, $R^2$, matriz de covarianza y gráfico de residuos.
   - **Panel Derecho Desplegable:** Generador de reportes, código LaTeX instantáneo y opciones de exportación.
3. **Respuesta Inmediata:** Cálculos en segundo plano con Web Workers o endpoints asíncronos ultrarrápidos (<50 ms de latencia) para que el ajuste de curva se sienta en tiempo real mientras se modifican los datos.

