# Plan de Ejecución: Cumplimiento Completo de Reglas SCALARIS

## Objetivo
Llevar la totalidad del repositorio al cumplimiento estricto y verificable de las reglas SCALARIS (secciones 0 a 14), preservando exactamente el comportamiento matemático y observable bajo las excepciones explícitas autorizadas E1 a E7.

**Estado verificado de cierre global (2026-10-11): pendiente.** Las declaraciones históricas de fases completadas no acreditan cumplimiento de todo el árbol. La ampliación de la auditoría encuentra implementaciones activas duplicadas en `backend/solvers` y `backend/resolutores`, contratos internos duales, identificadores heredados y límites incumplidos. El usuario autorizó expresamente corregir `src` conservando el comportamiento. La fase 8 continúa hasta resolver esa deuda; no se interpreta ningún nombre interno inglés como excepción E4.

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
| GeometryUI | VistaGeometria | Orquestación de las tres escenas geométricas |
| view_geometry / controls_mixin / scenes_mixin / _scenes | vista_geometria / mixin_controles / mixin_escenas / _escenas | Módulos de vistas/geometria; sin alias |
| GeometryControlsMixin / GeometryScenesMixin | MixinControlesGeometria / MixinEscenasGeometria | Clases de composición |
| VALID_SCENES / normalize_scene | ESCENAS_VALIDAS / normalizar_escena | Catálogo y normalización |
| build_lines_planes_figure / build_vectors_figure / build_combination_figure | construir_figura_rectas_planos / construir_figura_vectores / construir_figura_combinacion | Constructores de figuras |
| get_ai_context / get_ai_signals | obtener_contexto_ia / obtener_senales_ia | Vistas, paneles, protocolos y dobles de pruebas |
| schedule_context_refresh / render_inline_chips | programar_actualizacion_contexto / renderizar_sugerencias_en_linea | Paneles y todos sus consumidores |
| geometry.js / window.scalaris.geometry | geometria.js / window.scalaris.geometria | Asset y espacio de nombres del cliente |
| data-vec-id / data-vec-idx / data-vec-orientation | data-geometria-vector / data-geometria-indice / data-geometria-orientacion | Selectores, cliente y controles geométricos |
| geo_vec / geo_comb / geo-cell-error | geometria_vectores / geometria_combinacion / geometria-celda-error | Identificadores de panel y marcado de error |
| scene / grid_n / theme | escena / n_cuadricula / tema | Parámetros del selector y constructores de figuras; no claves JSON heredadas |
| frame_index / handoff_token | indice_cuadro / token_handoff | Parámetros de figura vectorial y construcción de geometría |

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

### Fase 6: Componentes de Interfaz (`src/frontend/componentes`) (E3, E4, E7)
- **Estado**: Completada
- **Archivos creados y auditados (33 módulos en `src/frontend/componentes/`)**:
  - Base y utilidades: `__init__.py`, `cuadricula_base.py` (91 líneas), `tareas.py` (22 líneas), `icons.py` (31 líneas), `theme_switcher.py` (52 líneas), `app_shell.py` (26 líneas), `navbar.py` (140 líneas).
  - Captura y calculadoras: `calculator.py` (97 líneas), `matrix_capture.py` (119 líneas), `vector_capture.py` (114 líneas), `square_matrix_panel.py` (104 líneas), `equation_grid.py` (91 líneas), `exportador_ecuaciones.py` (55 líneas).
  - Transferencia segura: `handoff.py` (261 líneas).
  - Paneles de IA: `ai_panel.py` (124 líneas), `ai_panel_legacy.py` (80 líneas).
  - Asistente Glosa Dock modularizado: `glosa_dock.py` (117 líneas), `glosa_cabecera.py` (42 líneas), `glosa_bitacora.py` (69 líneas), `glosa_pie.py` (80 líneas), `glosa_chips.py` (38 líneas), `glosa_envio.py` (107 líneas), `glosa_foco.py` (54 líneas), `glosa_render.py` (28 líneas).
  - Reproductor de pasos desacoplado: `reproductor_pasos/__init__.py`, `reproductor_pasos/modelo.py` (23 líneas), `reproductor_pasos/catalogo.py` (33 líneas), `reproductor_pasos/controles.py` (148 líneas), `reproductor_pasos/indice.py` (77 líneas), `reproductor_pasos/cuerpos.py` (42 líneas), `reproductor_pasos/html_tablas.py` (54 líneas), `reproductor_pasos/vista.py` (76 líneas), `reproductor_pasos/reproductor.py` (115 líneas).
- **Criterios de aceptación cumplidos**:
  - Eliminación completa del paquete legado `src/frontend/components` y reemplazo formal por `src/frontend/componentes`.
  - Descomposición de `glosa_dock.py` (~330 líneas originales) en 8 submódulos altamente cohesivos (cabecera, bitácora, pie, chips, envío, foco, render, dock orquestador).
  - Unificación de ejecución asíncrona segura (`_spawn`) en `tareas.py: lanzar_tarea`, eliminando duplicaciones entre el dock y la geometría.
  - Separación de `ai_panel.py` en ruta nativa dock y ruta legacy aislada (`ai_panel_legacy.py`), migrando estilos de escritura a clases CSS.
  - Extracción de la lógica duplicada de cuadrículas (límites, celdas, adición/remoción, focus traversal y sanitización) a `cuadricula_base.py`.
  - JS embebido eliminado; solo llamadas breves a scripts precompilados de assets.
  - Delegación estricta de validación y límites de celdas al backend (`ValidadorMatriz.validar_celda` y `LONGITUD_MAXIMA_CELDA = 64`) conforme a E7.
  - Handoff parametrizado con `_consumir_transferencia` y mensajes centralizados en `textos.py`.
  - Escape HTML riguroso en `render_glosa_text` contra XSS; clases CSS en lugar de estilos en línea.
  - Cumplimiento estricto de todos los límites duros: 33 archivos $\le 300$ líneas, funciones $\le 40$, clases $\le 200$, parámetros $\le 5$, anidamiento $\le 3$, complejidad $\le 10$.
  - `RUTAS_AUDITADAS` en `tests/test_cumplimiento_reglas.py` ampliado con los 33 módulos de componentes.
  - 1115 pruebas pasando al 100% (incluyendo auditoría de accesibilidad, contratos de dock y pruebas de límites).

### Fase 7: Vistas de Usuario (`src/frontend/vistas`) (E1 a E7)
- **Estado**: En curso. Se retoma primero la subentrega de geometría; operaciones matriciales y resto siguen pendientes.
- **Plan de cambios de geometría**:
  1. Medir los límites y ejecutar la suite inicial con `venv/Scripts/python.exe`.
  2. Renombrar `views` a `vistas`, y geometría a nombres canónicos; propagar consumidores sin alias.
  3. Completar la extracción de actualización, controles, resúmenes, estados y contexto de IA.
  4. Llevar armado de cargas a controladores y reglas de transferencia y cálculo gráfico al backend.
  5. Reutilizar la paleta central y retirar estilos en línea; asegurar scroll y estados accesibles.
  6. Añadir pruebas nuevas de datos límite, cancelación y escape; ampliar las rutas auditadas.
  7. Ejecutar suite, auditoría y tres revisores independientes; registrar informe y detenerse.
- **Archivos**: `src/frontend/vistas/` (`hub/`, `linear_systems/`, `matrix_ops/`, `vector_ops/`, `inverse_ops/`, `geometria/`, `numeric_systems/`). Los subpaquetes restantes aún requieren sus nombres canónicos.
- **Criterios de aceptación**:
  - Vistas orquestan sin lógica de negocio ni parseo.
  - Cadenas HTML/JS/CSS largas extraídas a assets o plantillas.
  - Copy en tuteo, sin raya larga ni exclamaciones en éxito.

#### Informe 12.4: avance de geometría, 11 de octubre de 2026

**Estado: punto de continuación, sin cierre de la subentrega ni de la fase.** La implementación estructural y las regresiones descritas están verificadas; siguen pendientes contratos internos E4, dominio heredado E7 y comprobación visual. Las afirmaciones históricas de las fases 1 a 6 sobre cero alias y cumplimiento total no constituyen evidencia de esos requisitos en el árbol actual.

**a. Archivos y alcance (VERIFICADO).** Se preservó el trabajo previo sin commit, push, instalación ni edición de `.env`. El estado inicial ya incluía la migración incompleta de componentes y extracciones parciales de geometría; el diff contra HEAD incorpora ese trabajo anterior.

- Renombrado del paquete completo `src/frontend/views` a `src/frontend/vistas`. En los otros seis subpaquetes solo se propagaron rutas y los cuatro métodos compartidos de IA.
- Renombrados geométricos: `geometry` a `geometria`, `view_geometry.py` a `vista_geometria.py`, `controls_mixin.py` a `mixin_controles.py`, `scenes_mixin.py` a `mixin_escenas.py`, `_scenes.py` a `_escenas.py`, y `assets/js/geometry.js` a `assets/js/geometria.js`. Las rutas anteriores se retiraron sin alias.
- Geometría reorganizada en 15 módulos: `__init__.py`, `vista_geometria.py`, `mixin_controles.py`, `mixin_escenas.py`, `_actualizacion_geometria.py`, `_contexto_ia_geometria.py`, `_escenas.py`, `_estados_geometria.py`, `_figuras_comunes.py`, `_figura_combinacion.py`, `_figura_rectas_planos.py`, `_figura_vectores.py`, `_handoff_geometria.py`, `_panel_vectores.py`, `_resumen_geometria.py`. Se completaron extracciones previas y se añadieron estados, resumen y adaptación del panel.
- Creados `src/backend/geometria/muestreo.py`, `transferencia.py`, `src/frontend/controladores/geometria/captura.py` y `src/frontend/assets/css/vistas_geometria.css`. Retirado el intermediario `_payload_geometria.py`, sustituyéndolo por captura del controlador.
- Modificados consumidores: `routes.py`, `suggestions.py`, `theme.py`; métodos de IA en `componentes/ai_panel.py`, `glosa_dock.py`, `glosa_pie.py`; `controladores/geometria/utilidades.py`, `controlador_vectores.py`, `controlador_combinacion.py`; `assets/js/vector_capture.js`, `cuadricula_compartida.js`; clase de error en `assets/css/componentes_entradas.css`.
- Pruebas renombradas: `test_f8d_geometry_view_flow.py` a `test_flujo_vista_geometria.py`, `test_f8e_slot_context.py` a `test_contexto_cliente_asincrono.py`, `test_geometry_figures.py` a `test_figuras_geometria.py`, `test_geometry_scene_param.py` a `test_parametro_escena_geometria.py`. Sus aserciones e intención se conservaron.
- Creados `tests/test_geometria_datos_extremos.py`, `test_geometria_actualizacion_cancelable.py`, `test_geometria_regresiones_revision.py`, `test_geometria_script_cliente.py`, `geometria_cliente_simulado.js` y `rutas_auditadas.py`. Modificados `tests/comun.py`, `test_cumplimiento_reglas.py` y consumidores de nombres, rutas y selectores. Restauradas las 12 pruebas de los tres archivos encontrados vacíos: `test_css_class_coverage.py`, `test_f8c_styles_motion.py`, `test_f9_static_audit.py`.

**b. Criterios y evidencia.**

| Criterio | Estado | Evidencia y límite |
|---|---|---|
| Modularización geométrica | VERIFICADO | 15 módulos; máximo 147 líneas por archivo, 29 por función y 124 por clase, medidos con AST. La vista inicial tenía 358 líneas y su clase 324; el mixin de escenas tenía una clase de 237 líneas. |
| Auditoría del alcance | VERIFICADO | 172 rutas existentes, incluidas todas las vistas geométricas; siete comprobaciones pasan. El arnés no analiza límites de funciones JS ni todos los parámetros exclusivos por palabra clave. No demuestra cumplimiento global de E4. |
| Regresiones y exactitud cubierta | VERIFICADO | Suite completa: 1161 pruebas pasadas. Casos nuevos de vacío, una y diez ecuaciones, fracciones, enteros de 80 cifras, rechazo por límite real del parser, cardinalidades y planos degenerados. Los resultados comprobados conservan Fraction; no se afirma equivalencia matemática exhaustiva. |
| Cancelación y confirmación | VERIFICADO | Pruebas de cancelación normal y absorbida por io_bound, deduplicación de carga confirmada, cancelación del debounce y retiro del marcado inválido. |
| Cliente y seguridad de presentación | VERIFICADO | DOM simulado ejecuta JS con Node: cuadros 2D/3D, aria-valuetext, foco, limpieza de recursos, espera del montaje, reemplazo con cuadro pendiente y fallo/reintento. Escape HTML de fórmulas, selectores serializados y textContent. |
| Dominio extraído en esta entrega | VERIFICADO | Muestreo de rectas/planos al backend; cantidades de vectores compartidas por transferencia, controles y validadores; carga capturada por controladores. |
| Separación completa del dominio | NO PROBADO | Quedan cálculos heredados en los controladores: cuadros de ku + v, suma estática y cadena acumulada. Requieren traslado E7 y regresiones. |
| Idioma y cero alias de todo el repositorio | NO PROBADO | Los nombres migrados se propagaron; siguen contratos y APIs internas heredados en inglés. El catálogo del arnés no detecta todos estos casos. |
| 320 px, zoom 200 %, temas y lector de pantalla | NO PROBADO | CSS dispone scroll propio, min-width:0, foco y cifras tabulares. Su resultado visual, táctil y con lector necesita los pasos manuales siguientes. |
| Compatibilidad visual de las figuras | INFERIDO | Las trazas conservan los contratos comprobados y se restauró grosor 3D. No se compararon capturas de pantalla. |

Comandos finales: `venv/Scripts/python.exe -m pytest -q`, `venv/Scripts/python.exe -m pytest tests/test_cumplimiento_reglas.py -q`, `venv/Scripts/python.exe -m compileall -q src tests`, `node --check` sobre geometría, captura vectorial, cuadrícula compartida y arnés del cliente. El pytest asíncrono se ejecutó con aprobación automática fuera del sandbox por bloqueo de sockets locales de asyncio en Windows. Se conserva una advertencia de deprecación Starlette/httpx; no se instalaron dependencias.

**c. Revisión independiente (DELEGACIÓN REAL).** Seguridad, bugs y mantenibilidad se ejecutaron en paralelo, en dos pasadas de solo lectura, con igual contexto. No hubo hallazgos críticos ni altos. Seguridad no encontró vulnerabilidades nuevas sustentadas. Se deduplicaron y corrigieron los medios siguientes:

| Hallazgo | Resolución y evidencia |
|---|---|
| io_bound absorbe CancelledError y devuelve None, causando falso error | Guardia de cancelación tras el trabajador; regresión que simula el contrato instalado. |
| Celda corregida sigue aria-invalid | Limpieza al confirmar éxito y al vaciar; regresiones de transición. |
| Selector incorrecto tras eliminar un vector intermedio | Identificador de celda basado en la posición enviada al controlador; prueba con eliminación de v_1 y error en v_2. |
| Transferencia 2D conserva etiqueta 3D | Sincronización de etiqueta y botones; prueba con componentes reales. |
| Grosor de columnas 3D cambia de 3 a 2 | Restaurado a 3; nueva aserción de figura. |
| Cantidades de vectores duplicadas | Catálogo backend consumido por controles y ambos validadores, preservando mensajes. |
| Registro JS reemplazado deja cuadro anterior pendiente | Cancelación del requestAnimationFrame anterior y guardia de identidad; regresión del cliente que invoca incluso el callback antiguo. |

La segunda pasada confirmó las primeras correcciones y descubrió el último problema de cuadros pendientes, corregido y probado por el agente principal después de esa revisión. No se atribuye una tercera aprobación a los revisores. Pendientes sustentados: E4/E7 heredados y cobertura incompleta del arnés.

**d. Desviaciones y excepciones.** Se eligió el avance de geometría permitido por el usuario; no se abordaron las otras subentregas. La API real del panel era `build`, y se corrigió la llamada inexistente `build_container`. Se restituyeron pruebas vacías antes de aceptar el resultado de la suite. Las correcciones baratas señaladas por revisión permanecen en el alcance geométrico.

- E1: backend editable, sin manual de requerimientos; muestreo gráfico trasladado conservando orden de operaciones y tolerancia.
- E2: pruebas existentes siguen renombrados y se restituyen sin retirar aserciones; lógica nueva lleva archivos nuevos.
- E3: propagación de los nombres efectivamente migrados a todos sus consumidores, sin alias añadidos.
- E4: conservación de APIs NiceGUI, Quasar, Tailwind, Plotly, MathJax, FastAPI y stdlib; propiedades CSS, eventos y APIs del navegador; dunders; tokens existentes; variables de entorno; payload externo de OpenRouter; carpetas frontend/backend/ai y main.py; tecnicismos token, hash, cache y mixin. Los nombres internos heredados NO se consideran excepciones autorizadas: quedan pendientes.
- E5: geometría evita animación al actualizar cuadros; teclado y reduced-motion sin escala; no se cambiaron valores de aserciones de movimiento en esta subentrega.
- E6: hoja geométrica añadida al orden de carga de producción y de tests; uso del conjunto CSS existente.
- E7: captura al controlador, muestreo y restricciones al backend; cálculos restantes de controladores se enumeran como deuda.

**e. Pruebas existentes y aserciones antes/después.** Los cambios masivos son renombrados de rutas, clases, métodos y dobles. No se cambiaron valores numéricos, estados matemáticos ni expectativas funcionales de pruebas existentes por otro motivo. Los auxiliares duplicados de tareas y trabajadores se centralizaron en `tests/comun.py`; el manifiesto de auditoría se extrajo a `tests/rutas_auditadas.py` conservando comprobaciones y ampliando cobertura.

Las funciones de las pruebas de figuras y escenas renombradas tienen nombres españoles descriptivos, y se filtraron comentarios redundantes y docstrings en inglés conforme a las instrucciones de comentarios del usuario. Ninguna de esas ediciones cambia sus aserciones.

| Aserción o referencia antes | Después | Motivo |
|---|---|---|
| src.frontend.views / src/frontend/views | src.frontend.vistas / src/frontend/vistas | E3, renombrado del paquete en imports y comprobaciones estáticas. |
| src/frontend/components | src/frontend/componentes | E3, consumidores de la migración previa, incluidas las pruebas restauradas. |
| GeometryUI, GeometryControlsMixin, GeometryScenesMixin | VistaGeometria, MixinControlesGeometria, MixinEscenasGeometria | E3/E4, clases canónicas. |
| VALID_SCENES, normalize_scene | ESCENAS_VALIDAS, normalizar_escena | E3/E4, catálogo y método. |
| get_ai_context, get_ai_signals | obtener_contexto_ia, obtener_senales_ia | E3/E4, métodos y dobles de toda la suite. |
| schedule_context_refresh, render_inline_chips | programar_actualizacion_contexto, renderizar_sugerencias_en_linea | E3/E4, método observado por mocks y comprobaciones de fuente. |
| _client, _js, _spawn, _debounced_update, _render_error de geometría | _cliente, _ejecutar_js, _lanzar_tarea, _actualizar_con_debounce, _renderizar_error | E3/E4, flujo y aislamiento del cliente; contexto del dock conservado. |
| Constructores build_*_figure y argumento theme | construir_figura_* y argumento tema | E3/E4; aserciones de trazas y layout conservadas. |
| input[data-vec-id="geo_vec_v_1"][data-vec-idx="0"] | input[data-geometria-vector="geometria_vectores_v_1"][data-geometria-indice="0"] | E3/E4, selector exacto en test_controlador_geometria. |
| input[data-vec-id="geo_comb_b"][data-vec-idx="1"] | input[data-geometria-vector="geometria_combinacion_b"][data-geometria-indice="1"] | E3/E4, selector exacto en test_controlador_geometria. |
| kwargs scene y grid_n del selector | escena y n_cuadricula | E3/E4, misma selección de celda. |
| Ausencia de contenido en tres archivos de pruebas | 12 pruebas originales restauradas desde HEAD | Restitución E2; mismas aserciones, solo rutas de paquetes renombradas. |

**Revisión de interfaz.** Esta tabla registra implementación; no sustituye inspección visual.

| Before | After | Why |
|---|---|---|
| Fórmulas y estados mezclados en la vista | Funciones de resumen y estados con escape y scroll propio | Reducir tamaño y contener valores anchos. |
| Error podía dejar una celda marcada tras corregirla | Éxito y vacío retiran clase y aria-invalid | El estado accesible debe corresponder a la entrada actual. |
| Error de un cuadro JS podía quedar silencioso | Aviso role=alert y reintento al mover el control | Explicar el fallo del parámetro y permitir recuperación. |
| Listener y cuadros podían sobrevivir a reemplazos | Limpieza del observador, listener y requestAnimationFrame | Evitar actualizaciones obsoletas y recursos huérfanos. |
| Dimensión recibida y cabecera podían discrepar | Dimensión, etiqueta, botones y componentes sincronizados | Representar correctamente la transferencia. |

**f. Pendientes, riesgos y punto exacto de continuación.**

1. E4: migrar conjuntamente productores y consumidores de `status`, `message`, `matrix_A`, `vector_b`, `vectors`, `data`, `orientation`, `frames`, `set`, `chain`, estados ingleses y contratos de IA. Retirar alias heredados y renombrar módulos/APIs internas pendientes. Esta entrega no declara que esos nombres estén autorizados por E4.
2. E7: mover cuadros de vectores, suma y cadena acumulada desde controladores al backend, preservando Fraction, mensajes y resultados. Revisar otros cálculos heredados de los controladores geométricos.
3. Auditoría: completar análisis JS y parámetros exclusivos por palabra clave con pruebas nuevas; no debilitar el arnés existente. La armonización global de nombres/comentarios/tamaños de tests sigue en fase 8.
4. Comprobación manual NO PROBADA: desde la raíz ejecutar `.\venv\Scripts\python.exe src/main.py`; usar la dirección anunciada por NiceGUI. Abrir `/visualizador?escena=rectas-planos`, `?escena=vectores` y `?escena=combinacion`. Repetir en papel, marea y medianoche, con viewport de 320 px y luego zoom de navegador al 200 %. Confirmar ausencia de scroll horizontal de toda la página y acceso al scroll propio de fórmulas/figuras y a todas las acciones.
5. En rectas/planos comprobar vacío, una ecuación, diez ecuaciones, fracciones 1/3 y coeficientes de 80 cifras. Introducir abc, usar «Ir a la celda», corregirlo y verificar que desaparecen marca y anuncio de error. En vectores probar 2D/3D y deslizador con ratón, táctil y flechas de teclado, con reduced-motion activado; contrastar etiqueta k y figura. En combinación eliminar v_1 después de añadir v_2 y repetir error/foco en la celda restante. Transferir dos vectores 2D y confirmar cabecera 2. Comprobar anuncios de carga/error/vacío con lector de pantalla y foco visible.
6. Después del cierre real de geometría, continuar operaciones matriciales (inversa, Leontief y transformaciones) y luego las vistas restantes. No empezar fase 8 en este punto.

**g. Backend:** no aplica MANUAL DE REQUERIMIENTOS PARA BACKEND por E1.

**h. Plan:** actualizado y conservado. Fase 7 continúa en curso; ninguna de sus tres subentregas se declara cerrada con cumplimiento total.

### Fase 8: Armonización de la Suite de Pruebas y Cierre (E2)
- **Estado**: En curso; entrega intermedia, sin cierre de auditoría global.
- **Archivos**: `tests/` completo, `tests/comun.py`, `tests/test_cumplimiento_reglas.py`.
- **Criterios de aceptación**:
  - Todas las pruebas en `tests/` renombradas a español descriptivo sin prefijos de fase (`f4`, `f8c`, `f9`, etc.).
  - Extracción de helpers duplicados a `tests/comun.py`.
  - Ejecución de `test_cumplimiento_reglas.py` sobre la totalidad del repositorio (`RUTAS_AUDITADAS` cubre todo el proyecto, 100% verificado).
  - Eliminación de este plan temporal al completar satisfactoriamente la auditoría.

#### Avance verificable y continuación

Los ocho bloques de esta fase se mantienen separados para no confundir verificaciones parciales con aceptación global:

| Bloque | Estado |
|---|---|
| 1. Inventario inicial, colección y descubrimiento completo de rutas | Completado: datos en `scratch`, manifiesto dinámico de `src` y `tests`. |
| 2. Auxiliares solicitados de tokens/contraste, clientes, OpenRouter y limpieza de handoff | Completado para las duplicaciones identificadas; consumidores migrados. |
| 3. Tamaño físico de pruebas Python | Completado: ningún archivo supera 300 líneas, función 40 o clase 200, medido con AST. |
| 4. Español completo en nombres, variables, docstrings y comentarios | Parcial: archivos con referencias a fases retirados; quedan archivos y símbolos ingleses heredados. |
| 5. Conservación de intención histórica y tabla acumulada de todas las ediciones E2/E5/E6 | Parcial: comparación estructural contra inicio de fase y familias revisadas; falta conciliación histórica completa. |
| 6. Correcciones de `src` y auditoría global, incluidos límites de JavaScript | Parcial: alcance completo y arnés Python corregido; deuda real aún produce fallos. |
| 7. Suite/análisis/revisión finales completamente satisfactorios | Parcial: se ejecutaron, pero cinco auditorías globales fallan; revisiones realmente delegadas. |
| 8. Informe final, contratos externos definitivos y eliminación del plan | Pendiente del cierre real; conservar este plan para continuar. |

**Archivos y responsabilidades.** Nuevos auxiliares: `tests/comun_estilos.py`, `comun_clientes.py`, `comun_openrouter.py`, `comun_auditoria.py`, `comun_vista_previa.py`; `comun.py` incorpora limpieza de handoff. `rutas_auditadas.py` descubre todos los `.py`, `.js`, `.css` y `.html` de ambos árboles, sin exclusiones por carpeta. El controlador geométrico se separó de rangos/recorte. Operaciones vectoriales se separaron en suma/resta y producto escalar; combinación lineal en soluciones, validación y trazabilidad. Vista previa y pasos largos se dividieron conservando casos. OpenRouter se separó en peticiones, caché y seguridad de mensajes. Los renombrados restantes se registran en el diff del árbol de trabajo, sin commit.

**Conservación y línea base.** VERIFICADO: al iniciar esta fase se recogieron 1161 casos. Las 2720 expresiones de aserción de ese estado se conservan como multiconjunto AST, normalizando únicamente nombres locales por expresión y conservando operadores, constantes, atributos y relaciones entre nombres. Esta comparación no demuestra por sí sola equivalencia de preparación o control de flujo. El revisor de regresiones comparó cuerpos completos de operaciones vectoriales (29), combinación (37), controlador/recorte (37) y vista previa (3 funciones, con parametrización): conservados, salvo dos catálogos de claves trasladados con valores idénticos. Se corrigió una diferencia de recorrido en matrices irregulares del auxiliar de vista previa y se añadieron regresiones.

VERIFICADO: se exportó y ejecutó una instantánea histórica del commit `7142090`, primera versión del arnés de cumplimiento en este historial: **1106 pruebas pasaron**, incluidas siete del arnés. El registro del plan dice 1099; la correspondencia 1099 + 7 es INFERIDA y todavía requiere conciliar el momento exacto de la línea base. La instantánea y su ZIP se eliminaron después de guardar inventario/colección en `scratch`. La comparación de intención histórica completa sigue pendiente. Se restauraron en archivo nuevo los contratos de ausencia de scripts residuales y de tres alias prohibidos, que no aparecían en el arnés al inicio de esta fase.

**Verificación más reciente.** VERIFICADO: suite completa **1181 pasadas, 5 fallidas**, 1186 casos totales. Los cinco fallos son de auditoría: complejidad de `context.py:describir_matriz`, docstring y nombre de `models/matrix.py:Matrix`, banners de `constants.py` y estilo embebido de `vistas/hub/view_hub.py`. Cada fallo muestra solo el primer incumplimiento de su categoría; hay deuda adicional. `compileall` de `src` y `tests`, `node --check` de los 18 archivos JS y `git diff --check` pasan. No se encontró configuración ni instalación de Ruff, mypy, pylint, radon o ESLint; no se instaló nada. Advertencia heredada de Starlette sobre TestClient/httpx: registrada, sin cambiar dependencias. Suite ejecutada con permiso para sockets locales de Windows.

VERIFICADO: el manifiesto contiene **390 rutas**. El diagnóstico exhaustivo de límites disponible en `scratch/limites_pendientes.json` registra 162 incumplimientos: cinco archivos, 16 clases, 27 funciones, 19 firmas, 44 casos de anidamiento y 51 de complejidad. No implica 162 archivos distintos; una función puede infringir varios límites. El contraste contra inicio de fase registra 2720 aserciones existentes conservadas y 49 expresiones nuevas o restauradas. Los datos temporales se conservan exclusivamente para la continuación.

**Revisión coordinada real.** Seguridad, regresiones y mantenibilidad se delegaron a tres agentes de solo lectura con el mismo contexto acotado. Seguridad verificó el cierre de un hallazgo alto heredado: la caché global de Glosa omitía historial y cliente. Ahora la clave incluye mensajes efectivos, modelos y UUID de la instancia; cada panel crea su propio cliente. También se eliminaron cuerpos HTTP y textos de excepciones de los registros cambiados. Regresiones nuevas cubren clientes/historiales y secretos ficticios en registros. El cambio de privacidad es una desviación necesaria conforme a 6.3, sin modificación matemática. No quedaron hallazgos críticos o altos abiertos en las correcciones revisadas.

Los revisores detectaron y se corrigieron falsos positivos al analizar patrones/muestras de prueba como comentarios o estilos renderizados. El arnés cuenta ahora parámetros exclusivos y variádicos, métodos públicos asíncronos, decisiones de comprensiones y alternativas condicionales. `elif` comparte nivel, mientras `else: if` conserva anidamiento real. Las funciones auxiliares introducidas con complejidad excesiva se dividieron. Pendiente: análisis estructural JS, idioma completo y firmas heredadas como `OpenRouterIA.ask` con seis parámetros.

#### Tabla acumulada de aserciones antes / después comprobadas hasta aquí

Las filas históricas siguientes están verificadas mediante `git diff 7142090 HEAD`; no se cambiaron otra vez los valores de movimiento en esta subentrega. La conciliación exhaustiva del resto del historial queda en el bloque 5.

| Aserción antes | Después | Excepción y propósito conservado |
|---|---|---|
| Transición de recolección `transform 240ms ... opacity 240ms ...` en `app.js` | `transform 160ms ... opacity 160ms ...` en `recoleccion_basura.js` | E5/E6: misma verificación de transición, módulo propio y duración permitida. |
| Cierre de diálogo por `setTimeout(..., 340)` | `setTimeout(..., 220)` | E5: mismo cierre de respaldo dentro del límite. |
| Opacidad de salida de popover `220ms` | `180ms` | E5: salida más rápida que entrada. |
| Tarjeta: opacidad/transformación `220ms` con curva estándar | Opacidad `180ms linear`, transformación `200ms` con curva estándar | E5: propiedades permitidas y duración acotada. |
| Entrada general de popover `320ms` | `250ms` | E5: mismo estado de entrada. |
| Salida móvil `240ms` | `200ms` | E5: mismo estado de salida. |
| Máximo de duraciones del Hub `<=340` | `<=250` | E5: umbral más estricto. |
| Duración de tarjeta de escritorio: salida `220`, entrada `320` | Salida `180`, entrada `250` | E5: se mantiene además la aserción entrada > salida. |
| Duración móvil: salida `240`, entrada `340` | Salida `200`, entrada `250` | E5: se mantiene además entrada > salida. |
| Entrada de fondo modal `320` | `250` | E5: mismo fondo y estado. |
| Entrada de herramienta `280` | `220` | E5: mismo escalonamiento y estado. |
| Respaldo de cierre identificado por `setTimeout` y duración `>240` | Identificado por `closeTimer = setTimeout` y duración `<=250` | E5: adaptación histórica deliberada de temporización; todavía se comprueban listener y cancelación. |
| Existencia/lectura de `theme.css` | Lectura del conjunto ordenado de hojas; falta de cualquier archivo provoca error | E6: cobertura de carga modular. |
| Contraste, muestras y tokens leídos de `theme.css` | Leídos de `tokens.css` | E6: mismos pares, parámetros y umbrales numéricos. |
| Bloque Hub localizado por banners dentro de `theme.css` | Tres hojas `vistas_hub_*` en orden de producción | E6: mismas comprobaciones por selector. |
| Bloque de accesibilidad localizado por banners | Lectura de `movimiento.css` | E6: mismas comprobaciones de reduced-motion. |
| Navegación delimitada por expresión regular entre bloques y `assert match` | Lectura directa de `vistas_navegacion.css` | E6: archivo faltante falla por lectura; mismas comprobaciones de reglas. |
| Bloques de muestras anteriores al banner BASE | Bloques raíz que contienen `--swatch-papel` en `tokens.css` | E6: se conserva el conteo exacto de cuatro y todas las muestras esperadas. |
| Imports/rutas `components`, `views`, `controllers` | `componentes`, `vistas`, `controladores` | E2/E3: referencias a los mismos consumidores migrados. |
| Archivos `test_f4`, `test_f8*`, `test_f9*`, `test_p6_*`, `test_hub_motion_h10` | Nombres por responsabilidad en español, sin referencias a fases | E2: casos y parametrización conservados. |
| Auxiliares CSS y dobles repetidos en módulos | Funciones y clases de módulos comunes; una/seis pasadas de tokens preservadas | E2: mismos valores y comportamiento de preparación. |
| Dos conjuntos idénticos de claves de combinación lineal | `_CLAVES_RESPUESTA`, con todas las mismas claves | E2: predicado `issubset` intacto en ambos casos. |
| Muestras de cadenas del propio auditor consideradas infracciones | Comentarios/docstrings reales y cadenas de presentación diferenciados por AST/tokenización | Corrección del arnés ampliado; ninguna ruta se excluye, regresiones positivas y negativas añadidas. |

**Excepciones y contratos.** E1 y autorización posterior permiten corregir backend sin cambiar matemáticas. E2 ampara movimientos, renombrados y extracciones; E3/E4 siguen incompletas y no permiten los alias duales encontrados. E5/E6 sustentan la tabla histórica; E7 sigue pendiente en cálculos de controladores. E4 conserva únicamente las APIs ajenas enumeradas arriba: entre las tocadas, `run_javascript`, `is_deleted`, `status_code`, `text`, `json`, argumentos de requests y fixtures de pytest. `_storage`, `ai_ctx_enabled`, `ask`, `AIResult`, `AIContext` y claves internas inglesas no se declaran contratos externos. El inventario final de nombres conservados se entregará al terminar la migración.

**Producto y riesgos.** VERIFICADO por lectura: Leontief y Transformaciones están habilitados en el catálogo/rutas, pero `_crear_items_algebra` no los incluye; `hub_pillars` usa esos items, de modo que continúan fuera de navegación contextual y Hub. `controller_determinant` ya se llama `controlador_determinante.py`; `ControladorDeterminante` solo se define y reexporta, sin consumidor de funcionalidad en `src` o `tests`. No cambiar decisiones de producto en esta fase. Interfaz visual/teclado/320 px/zoom 200 %: NO PROBADO en esta subentrega, sin cambios visuales implementados. Los pasos manuales anteriores siguen disponibles.

**Punto limpio para continuar:** bloque 4, comenzando por `tests/test_validators_parse_number.py`, archivos restantes en inglés y variables/comentarios heredados. Luego conciliar todos los casos históricos y la tabla; corregir `src` desde `src/ai/context.py` y los árboles duplicados de backend, propagando cada renombrado sin alias; completar el análisis JS y cerrar auditoría. Repetir suite/revisiones cuando nuevas correcciones lo justifiquen. Al cumplir los ocho bloques, trasladar el informe completo a la respuesta y eliminar este plan; retirar los datos temporales de `scratch` tras aprovechar su evidencia. No hay commit, push, instalación ni archivos de entorno modificados.
