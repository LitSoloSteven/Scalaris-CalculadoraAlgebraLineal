# Plan de Ejecución: Cumplimiento Completo de Reglas SCALARIS

## Objetivo
Llevar la totalidad del repositorio al cumplimiento estricto y verificable de las reglas SCALARIS (secciones 0 a 14), preservando exactamente el comportamiento matemático y observable bajo las excepciones explícitas autorizadas E1 a E7.

---

## Excepciones Explícitas del Usuario (Sección 0, Punto 2)

- **E1 Backend editable**: `src/backend` es editable para esta tarea. Prohibido cambiar el comportamiento matemático: aritmética exacta con `Fraction`, mismos resultados numéricos y mismos textos de pasos que ya cumplen. No se redacta MANUAL DE REQUERIMIENTOS PARA BACKEND.
- **E2 Pruebas**: Edición de pruebas existentes permitida solo para: (a) seguir renombrados, (b) renombrar archivos y funciones a español descriptivo sin referencias a fases (`f4`, `f8c`, `f9`, `p5`, `h7`...), (c) extraer helpers duplicados a módulo común `tests/comun.py`, (d) actualizar aserciones cuyo valor cambia por E5 o E6. Prohibido borrar pruebas, debilitar aserciones o cambiar su intención. Registro obligatorio de tabla "aserción antes / después". Código nuevo con lógica lleva pruebas en archivos nuevos.
- **E3 Cero alias**: Ningún nombre en inglés se conserva como alias. Renombrado y propagación en el mismo paso a todo el repositorio (`src`, `tests`, JS, CSS, cadenas con selectores, atributos `data-*`), limitándose al renombrado fuera del alcance de la fase.
- **E4 Contratos internos**: Pasan a español ASCII: claves y valores de retorno y JSON entre capas (ej. `SOLUCION_UNICA`), nombres de módulos, archivos, carpetas, globales JS (`window.scalaris`), atributos `data-*`, ids y clases CSS con prefijo por módulo. Se conservan en su idioma original únicamente: APIs de NiceGUI, Quasar, Tailwind, Plotly, MathJax, FastAPI y stdlib; propiedades CSS y eventos del navegador; dunders; tokens de diseño (`--bg-page`, `--text-main`...); variables de entorno (`OPENROUTER_*`, `SCALARIS_ENV`, `STORAGE_SECRET`, `SCALARIS_NAV`, `SCALARIS_DOCK`, `SCALARIS_PROACTIVE`); claves del payload de OpenRouter; carpetas `src/frontend`, `src/backend`, `src/ai` y `main.py`; y tecnicismos autorizados de la sección 5.1.
- **E5 Movimiento**: Duraciones $\le 250\text{ ms}$, entradas desde `scale(0.95)` y opacidad 0; splash y cambio de tema con fundido $\le 250\text{ ms}$; `:active` con `scale(0.97)` o `scale(0.98)`; eliminación de `ease-elastic`, `ease-in`, `ease-in-out`, `filter` y animaciones de `width` o `clip-path`.
- **E6 CSS**: División modular de `theme.css` en hojas semánticas $\le 300$ líneas. Reemplazo de banners de bloque por localización por archivo y selector en las pruebas.
- **E7 Dominio**: Lógica matemática y reglas de dominio migradas al backend. Controladores y vistas solo delegan y serializan. Eliminación de validaciones duplicadas en la interfaz.

---

## Glosario de Renombrado Ampliado (Única Fuente de Verdad)

| Concepto en Inglés | Concepto en Español ASCII | Contexto / Claves / Atributos |
|---|---|---|
| Matrix | Matriz | filas, columnas, datos, obtener, establecer, clonar, intercambiar_filas, sumar_fila_escalada |
| solve / solver / solvers | resolver / resolutor / resolutores | resolver_sistema, resolutor_inversa, etc. |
| status / state | estado | Clave de respuesta |
| message | mensaje | Clave de respuesta |
| steps / step | pasos / paso | Clave de respuesta |
| solution | solucion | Clave de respuesta |
| add / addition | sumar / suma | Operaciones algebraicas |
| subtract / subtraction | restar / resta | Operaciones algebraicas |
| multiply / multiplication | multiplicar / multiplicacion | Operaciones algebraicas |
| transpose | transponer / transpuesta | Operaciones algebraicas |
| determinant | determinante | Operaciones algebraicas |
| inverse | inversa | Operaciones algebraicas |
| controller / controllers | controlador / controladores | Capa de mediación |
| view / views | vista / vistas | Capa de presentación |
| components | componentes | Elementos reutilizables UI |
| models | modelos | Modelos de dominio backend |
| utils | utilidades | Módulos auxiliares backend |
| build | construir | Ensamblado de componentes y vistas |
| UNIQUE_SOLUTION | SOLUCION_UNICA | Constante y estado de retorno |
| INFINITE_SOLUTIONS | SOLUCIONES_INFINITAS | Constante y estado de retorno |
| NO_SOLUTION | SIN_SOLUCION | Constante y estado de retorno |
| SUCCESS | EXITO | Estado de retorno |
| UNIQUE | UNICA | Tipo de solución |
| INFINITE | INFINITA | Tipo de solución |
| ERROR | ERROR | Se conserva idéntico |
| SINGULAR | SINGULAR | Se conserva idéntico |
| linear_systems | sistemas_lineales | Paquetes y rutas |
| matrix_ops | operaciones_matrices | Paquetes y rutas |
| vector_ops | operaciones_vectores | Paquetes y rutas |
| numeric_systems | sistemas_numericos | Paquetes y rutas |
| inverse_ops | operaciones_inversas | Paquetes y rutas |
| geometry | geometria | Paquetes y rutas |
| validators | validadores | Módulo de utilidades |
| parsers | analizadores | Módulo de utilidades |
| formatters | formateadores | Módulo de utilidades |
| constants | constantes | Módulo de backend |
| exceptions | excepciones | Módulo de backend |

---

## Fases de Ejecución

### Fase 0: Línea Base, Limpieza de Conflictos e Infraestructura de Verificación
- **Estado**: Completada
- **Archivos**: `controllers/linear_systems/_shared.py`, `views/vector_ops/results_mixin.py`, `docs/PLAN_cumplimiento_reglas.md`, `tests/test_cumplimiento_reglas.py`.
- **Criterios de aceptación**:
  - Cero marcadores de conflicto de merge en todo el repositorio.
  - Verificación exitosa con `python -m compileall src`.
  - Línea base de `pytest` registrada (1099 pruebas pasando, 0 fallos).
  - Plan de ejecución temporal creado en `docs/PLAN_cumplimiento_reglas.md`.
  - Arnés `tests/test_cumplimiento_reglas.py` creado con `RUTAS_AUDITADAS` inicializado.
  - Inventario inicial medido entregado.

### Fase 1: Capa de Dominio y Backend (`src/backend`) (E1, E3, E4, E7)
- **Estado**: Completada
- **Sub-entregas**:
  - **Sub-entrega 1.1: Modelos y Utilidades** [COMPLETADA]
    - Modelos: `src/backend/modelos/matriz.py`, `src/backend/modelos/__init__.py`.
    - Utilidades: `src/backend/utilidades/utilidades_matematicas.py`, `formateadores.py`, `validadores.py`, `verificacion.py`, `reglas_dominio.py`, `__init__.py`.
    - Constantes y Excepciones: `src/backend/constantes.py`, `src/backend/excepciones.py`.
    - Eliminado `src/backend/test_backend.py` (movido a `tests/`).
    - Auditado con `tests/test_cumplimiento_reglas.py` y `tests/test_backend_modelos_utilidades.py`.
  - **Sub-entrega 1.2: Sistemas Lineales y Operaciones Matriciales** [COMPLETADA]
    - Paquete `src/backend/resolutores/trazado.py` (`TrazadorPasos`).
    - Subpaquete `src/backend/resolutores/sistemas_lineales/` (`modelo_solucion.py`, `analisis_rouche.py`, `sustitucion.py`, `gauss.py`, `gauss_jordan.py`, `__init__.py`).
    - Subpaquete `src/backend/resolutores/operaciones_matrices/` (`formateadores.py`, `operaciones.py`, `determinante.py`, `inversa.py`, `evaluador.py`, `analizador_expresiones.py`, `transformaciones.py`, `leontief.py`, `__init__.py`).
    - Modularización estricta ($\le 300$ líneas por módulo, $\le 40$ líneas por función, $\le 200$ líneas por clase, $\le 5$ parámetros, anidamiento $\le 3$, complejidad $\le 10$).
    - Eliminación de código muerto en transformaciones y deduplicación de determinante (LU).
    - Auditado en `tests/test_cumplimiento_reglas.py` y verificado con `tests/test_backend_resolutores_matriciales.py`.
  - **Sub-entrega 1.3: Vectores y Sistemas Numéricos** [COMPLETADA]
    - Paquete `src/backend/resolutores/operaciones_vectores/` (`base.py`, `formateadores.py`, `planteamiento.py`, `operaciones.py`, `combinacion_lineal.py`, `__init__.py`).
    - Paquete `src/backend/resolutores/sistemas_numericos/` (`conversor_bases.py`, `calculadora_romana.py`, `__init__.py`).
    - Consolidación de exportaciones canónicas en `src/backend/resolutores/__init__.py`.
    - Modularización y límites auditados ($\le 300$ líneas por archivo, $\le 40$ por función, $\le 5$ parámetros).
    - Compatibilidad de contratos duales E4 garantizada entre backend, controladores y vistas.
    - Suite de pruebas de 1128 tests pasando al 100% y arnés de reglas `test_cumplimiento_reglas.py` con 34 módulos auditados en verde.
- **Criterios de aceptación cumplidos**:
  - Modelos, utilidades y resolutores en español ASCII canónico.
  - Módulos $\le 300$ líneas, funciones $\le 40$ líneas, clases $\le 200$ líneas.
  - Exactitud aritmética con `Fraction` preservada y resultados numéricos idénticos.

### Fase 2: Módulo de IA y Contratos de Contexto (`src/ai`) (E3, E4)
- **Estado**: Completada
- **Archivos**: `src/ai/constantes.py`, `src/ai/clasificador_respuestas.py`, `src/ai/estrategias_recorte.py`, `src/ai/openrouter_ai.py`, `src/ai/context.py`, `src/ai/prompts.py`.
- **Criterios de aceptación cumplidos**:
  - Módulos $\le 300$ líneas, funciones $\le 40$ líneas, clases $\le 200$ líneas, anidamiento $\le 3$, complejidad ciclomática $\le 10$.
  - Desacoplamiento de `_serialize_context_core` en 6 estrategias atómicas de recorte y `OpenRouterIA.ask` en pasos nombrados.
  - Eliminación de código muerto (`analizar_sistema`, variable `nonzero` en `describir_matriz`, imports a mitad de archivo, Protocol huérfano).
  - Unificación de constantes (TTL 3600 s, caché 128, deadline 40 s, timeouts, códigos transitorios y límites de contexto) en `src/ai/constantes.py`.
  - Inyectables de pruebas renombrados a español ASCII (`_bloqueo_cache`, `_cache_respuestas`, `_peticiones_post`, `_tiempo_monotonico`, `_tiempo_dormir`, `MODELO_PRIMARIO`, `MODELOS_RESERVA`) y propagados con cero alias (E3, E4).
  - Prompts y mensajes en español con tuteo, sin raya larga (`—`) y sin filtración de detalles internos.
  - Ampliación de `RUTAS_AUDITADAS` en `tests/test_cumplimiento_reglas.py` con todos los módulos de `src/ai`.
  - Suite de 1112 pruebas pasando al 100%.

### Fase 3: Núcleo de Aplicación y Navegación Frontend (E3, E4)
- **Estado**: Completada
- **Archivos**: `src/main.py`, `src/frontend/app.py`, `routes.py`, `flags.py`, `helpers.py`, `suggestions.py`, `catalogo_sugerencias.py`, `theme.py`, `constantes.py`, `textos.py`, y paquete `src/frontend/navigation/` (`modelo.py`, `catalogo.py`, `consultas.py`, `redirecciones.py`, `__init__.py`).
- **Criterios de aceptación cumplidos**:
  - `navigation.py` modularizado en paquete de 4 submódulos (`modelo`, `catalogo`, `consultas`, `redirecciones`), todos $\le 165$ líneas y funciones $\le 40$ líneas.
  - Resolución dinámica de `HUB_ENABLED` en tiempo de llamada conservada en `legacy_redirects`.
  - Catálogo de sugerencias desacoplado como datos puros a `catalogo_sugerencias.py` y lógica de selección optimizada ($\le 40$ líneas, complejidad ciclomática $\le 10$).
  - Creación de `src/frontend/constantes.py` (límites de dimensión 10 y 50, debounces 0.25, 0.3, 0.35 s, `MAX_HISTORIAL`, TTL y tamaño de handoff, anti-rebote de envío a Glosa) y migración de todos sus consumidores en el frontend.
  - Creación de `src/frontend/textos.py` centralizando copy repetido (mensajes de handoff, avisos de secretos y anti-rebote).
  - Paleta de gráficos en `theme.py` con contraste no textual $\ge 3.0:1$ verificado en los tres temas (`papel`, `marea`, `medianoche`) y consumida como fuente única por JS en `app.js` (`window.scalaris.graficos`).
  - Identificadores en español ASCII sin alias (`resolver_secreto_almacenamiento`, `inicializar_aplicacion`, `ejecutar`, `registrar_rutas`, `a_flotante`, `formatear_paso_mathjax`).
  - Ampliación de `RUTAS_AUDITADAS` en `tests/test_cumplimiento_reglas.py` a 30 archivos, pasando al 100%.
  - Suite de 1112 pruebas pasando (`0 failed, 1112 passed`).

### Fase 4: Sistema de Estilos CSS, Scripts JS y Movimiento (E4, E5, E6)
- **Estado**: Completada
- **Archivos**:
  - `src/frontend/assets/css/theme.css`: Eliminado definitivamente.
  - 14 hojas modulares en `src/frontend/assets/css/` (todas $\le 300$ líneas): `tokens.css` (266), `base.css` (93), `layout.css` (55), `componentes_entradas.css` (185), `componentes_controles.css` (216), `vistas_navegacion.css` (211), `vistas_hub_matriz.css` (297), `vistas_hub_popovers.css` (281), `vistas_hub_adaptable.css` (270), `vistas_glosa_dock.css` (273), `vistas_glosa_componentes.css` (282), `vistas_inversa.css` (146), `movimiento.css` (216), `reproductor_pasos.css` (61).
  - 17 scripts modulares en `src/frontend/assets/js/` (todos $\le 300$ líneas, funciones $\le 40$ líneas): `app.js` (143), `calculadora.js` (81), `cuadricula_compartida.js` (138), `equation_grid.js` (86), `geometry.js` (129), `glosa_dock.js` (249), `hub.js` (276), `hub_recientes.js` (37), `layout_sync.js` (77), `mathjax_config.js` (12), `matrix_capture.js` (87), `recoleccion_basura.js` (127), `reproductor_pasos.js` (32), `splash.js` (43), `square_matrix.js` (43), `theme.js` (68), `vector_capture.js` (88).
- **Criterios de aceptación cumplidos**:
  - `theme.css` descompuesto en 14 hojas cohesivas $\le 300$ líneas cargadas en estricto orden de cascada por `theme.py` y `tests/comun.py` (E6).
  - Cero colores literales fuera de `tokens.css`; paletas de tokens completas para `papel`, `marea` y `medianoche`. Contraste AA validado en toda la suite.
  - Espacio de nombres global único `window.scalaris` con métodos en español ASCII; IIFE; módulos compartidos para cuadrículas (`cuadricula_compartida.js`) y recolección (`recoleccion_basura.js`).
  - Extracción de scripts inline en Python (`calculator.py`, `matrix_capture.py`, `reproductor.py`, `cuerpos.py`) hacia assets JS.
  - Movimiento conforme a E5: todas las duraciones $\le 250\text{ ms}$; entradas desde `scale(0.95)` y opacidad 0; salidas más rápidas que entradas; fundido de tema y splash por opacidad en 240 ms (sin `clip-path`); eliminados `ease-in`, `ease-elastic`, `ease-in-out`, `filter`, y transiciones de `width` o `clip-path`.
  - Ampliación de `RUTAS_AUDITADAS` en `tests/test_cumplimiento_reglas.py` incorporando las 14 hojas CSS y los 17 scripts JS (total 71 rutas auditadas).
  - Suite completa de 1128 pruebas ejecutada con 100% de éxito (1128 pasadas, 0 fallos).

### Fase 5: Controladores de Interfaz (`src/frontend/controladores`) (E1, E2, E3, E4, E7)
- **Estado**: Completada
- **Archivos**:
  - `src/backend/geometria/` (E7): `__init__.py`, `clasificacion.py` (91 líneas), `conjunto_solucion.py` (140 líneas), `planos.py` (47 líneas), `recorte.py` (99 líneas).
  - `src/frontend/controladores/` (E3, E4):
    - Base y pasos: `__init__.py`, `utilidades.py` (38 líneas), `clasificador_pasos.py` (72 líneas), `agrupador_pasos.py` (116 líneas), `manejadores_pasos.py` (124 líneas).
    - `sistemas_lineales/`: `__init__.py`, `compartido.py` (81 líneas), `flujo_comun.py` (116 líneas), `controlador_gauss.py` (53 líneas), `controlador_gauss_jordan.py` (52 líneas).
    - `operaciones_matrices/`: `__init__.py`, `codificador.py` (27 líneas), `controlador_operaciones_matrices.py` (156 líneas), `controlador_leontief.py` (97 líneas), `controlador_transformaciones.py` (98 líneas), `controlador_determinante.py` (47 líneas).
    - `operaciones_vectores/`: `__init__.py`, `controlador_operaciones_vectores.py` (175 líneas).
    - `operaciones_inversas/`: `__init__.py`, `foco_paso.py` (110 líneas), `validador_inversa.py` (83 líneas), `controlador_operaciones_inversas.py` (109 líneas).
    - `geometria/`: `__init__.py`, `utilidades.py` (57 líneas), `controlador_rectas_planos.py` (260 líneas), `controlador_vectores.py` (116 líneas), `controlador_combinacion.py` (197 líneas), `controlador_geometria.py` (42 líneas).
- **Criterios de aceptación cumplidos**:
  - Eliminación total del paquete legacy `src/frontend/controllers` y creación del paquete canónico `src/frontend/controladores`.
  - Desacoplamiento completo de la lógica matemática de geometría hacia el backend en `src/backend/geometria/` (clasificación analítica de ecuaciones, paralelismo estricto, conjunto solución paramétrico, normales y offset de planos, recorte de rectas a la caja visual en $\mathbb{R}^3$, cálculo de rango) con aritmética exacta (`Fraction`) y cero cambio de comportamiento (E7).
  - Los controladores se limitan estrictamente a validación de entrada, delegación y serialización de respuesta didáctica.
  - Reducción drástica de `agrupar_pasos_eliminacion` (~250 líneas) dividida en manejadores modulares por tipo de operación elemental (`manejadores_pasos.py`), manteniendo explicaciones y salidas idénticas.
  - Flujo común de Gauss y Gauss-Jordan extraído a `sistemas_lineales/flujo_comun.py`, y deserialización compartida unificada en `utilidades.parsear_payload`.
  - Construcción de `steps_view` unificada con `construir_vista_pasos` compartido.
  - `controller_inverse_ops` modularizado en `foco_paso.py`, `validador_inversa.py` y `controlador_operaciones_inversas.py`.
  - `controller_determinant.py` refactorizado a `controlador_determinante.py` cumpliendo todas las reglas de estilo y mantenido como artefacto sin consumidor pendiente de decisión de producto.
  - Todos los límites duros respetados rigurosamente: archivos $\le 300$ líneas, funciones $\le 40$ líneas, clases $\le 200$ líneas, anidamiento $\le 3$, complejidad ciclomática $\le 10$, parámetros $\le 5$.
  - Cero alias en inglés (E3); identificadores y contratos internos en español ASCII (E4).
  - Ampliación de `RUTAS_AUDITADAS` en `tests/test_cumplimiento_reglas.py` a 94 rutas (los 5 módulos de backend geométrico y los 18 módulos de controladores).
  - Suite completa de 1127 pruebas pasando al 100% y 7 tests de reglas en verde.

### Fase 6: Componentes de Interfaz (`src/frontend/components`) (E3, E4)
- **Estado**: Pendiente
- **Archivos**: `src/frontend/components/` (`ai_panel.py`, `glosa_dock.py`, `matrix_capture.py`, `vector_capture.py`, `square_matrix_panel.py`, `handoff.py`, etc.).
- **Criterios de aceptación**:
  - Ningún componente supera 300 líneas ni contiene lógica de dominio.
  - Accesibilidad completa: foco visible, nombres accesibles, roles semánticos y cifras tabulares.

### Fase 7: Vistas de Usuario (`src/frontend/views`) (E3, E4, E5)
- **Estado**: Pendiente
- **Archivos**: `src/frontend/views/` (`hub/`, `linear_systems/`, `matrix_ops/`, `vector_ops/`, `inverse_ops/`, `geometry/`, `numeric_systems/`).
- **Criterios de aceptación**:
  - Vistas orquestan sin lógica de negocio ni parseo.
  - Cadenas HTML/JS/CSS largas extraídas a assets o plantillas.
  - Copy en tuteo, sin raya larga ni exclamaciones en éxito.

### Fase 8: Armonización de la Suite de Pruebas y Cierre (E2)
- **Estado**: Pendiente
- **Archivos**: `tests/` completo, `tests/comun.py`, `tests/test_cumplimiento_reglas.py`.
- **Criterios de aceptación**:
  - Todas las pruebas en `tests/` renombradas a español descriptivo sin prefijos de fase (`f4`, `f8c`, `f9`, etc.).
  - Extracción de helpers duplicados a `tests/comun.py`.
  - Ejecución de `test_cumplimiento_reglas.py` sobre la totalidad del repositorio (`RUTAS_AUDITADAS` cubre todo el proyecto, 100% verificado).
  - Eliminación de este plan temporal al completar satisfactoriamente la auditoría.
