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
| 3. Límites completos de pruebas | Completado: Python cumple tamaño, parámetros, anidamiento y complejidad; JavaScript de pruebas cumple los límites medidos con AST. |
| 4. Español completo en nombres, variables, docstrings y comentarios | Parcial: archivos con referencias a fases retirados; quedan archivos y símbolos ingleses heredados. |
| 5. Conservación de intención histórica y tabla acumulada de todas las ediciones E2/E5/E6 | Parcial: comparación estructural contra inicio de fase y familias revisadas; falta conciliación histórica completa. |
| 6. Correcciones de `src` y auditoría global, incluidos límites de JavaScript | Parcial: alcance completo y arnés Python corregido; deuda real aún produce fallos. |
| 7. Suite/análisis/revisión finales completamente satisfactorios | Parcial: suite actual con 1194 pasadas y seis auditorías globales fallidas; revisión realmente delegada. |
| 8. Informe final, contratos externos definitivos y eliminación del plan | Pendiente del cierre real; conservar este plan para continuar. |

**Archivos y responsabilidades.** Nuevos auxiliares: `tests/comun_estilos.py`, `comun_clientes.py`, `comun_openrouter.py`, `comun_auditoria.py`, `comun_vista_previa.py`; `comun.py` incorpora limpieza de handoff. `rutas_auditadas.py` descubre todos los `.py`, `.js`, `.css` y `.html` de ambos árboles, sin exclusiones por carpeta. El controlador geométrico se separó de rangos/recorte. Operaciones vectoriales se separaron en suma/resta y producto escalar; combinación lineal en soluciones, validación y trazabilidad. Vista previa y pasos largos se dividieron conservando casos. OpenRouter se separó en peticiones, caché y seguridad de mensajes. Los renombrados restantes se registran en el diff del árbol de trabajo, sin commit.

**Conservación y línea base.** VERIFICADO: al iniciar esta fase se recogieron 1161 casos. Las 2720 expresiones de aserción de ese estado se conservan como multiconjunto AST, normalizando únicamente nombres locales por expresión y conservando operadores, constantes, atributos y relaciones entre nombres. Esta comparación no demuestra por sí sola equivalencia de preparación o control de flujo. El revisor de regresiones comparó cuerpos completos de operaciones vectoriales (29), combinación (37), controlador/recorte (37) y vista previa (3 funciones, con parametrización): conservados, salvo dos catálogos de claves trasladados con valores idénticos. Se corrigió una diferencia de recorrido en matrices irregulares del auxiliar de vista previa y se añadieron regresiones.

VERIFICADO: se exportó y ejecutó una instantánea histórica del commit `7142090`, primera versión del arnés de cumplimiento en este historial: **1106 pruebas pasaron**, incluidas siete del arnés. El registro del plan dice 1099; la correspondencia 1099 + 7 es INFERIDA y todavía requiere conciliar el momento exacto de la línea base. La instantánea y su ZIP se eliminaron después de guardar inventario/colección en `scratch`. La comparación de intención histórica completa sigue pendiente. Se restauraron en archivo nuevo los contratos de ausencia de scripts residuales y de tres alias prohibidos, que no aparecían en el arnés al inicio de esta fase.

**Verificación del primer tramo.** VERIFICADO: suite completa **1181 pasadas, 5 fallidas**, 1186 casos totales. Los cinco fallos eran de auditoría: complejidad de `context.py:describir_matriz`, docstring y nombre de `models/matrix.py:Matrix`, banners de `constants.py` y estilo embebido de `vistas/hub/view_hub.py`. Cada fallo mostraba solo el primer incumplimiento de su categoría; había deuda adicional. `compileall` de `src` y `tests`, `node --check` de los 18 archivos JS y `git diff --check` pasaron. No se encontró configuración ni instalación de Ruff, mypy, pylint, radon o ESLint; no se instaló nada. Advertencia heredada de Starlette sobre TestClient/httpx: registrada, sin cambiar dependencias. Suite ejecutada con permiso para sockets locales de Windows. El resultado actualizado aparece al final de esta sección.

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

**Punto limpio para continuar:** bloque 4, comenzando por `tests/test_gauss_solution_exact.py` y `tests/test_gauss_solution_param.py`. Quedan nueve archivos con nombres ingleses: esos dos, `test_conversor_ui_logic.py`, `test_nav_items.py`, `test_navigation_registry.py`, `test_number_length_and_sci_notation.py`, `test_reviewer_coverage.py`, `test_roman_calculator.py` y `test_roman_error_structured.py`. También quedan nombres internos, docstrings y comentarios heredados dentro de archivos ya renombrados. Luego conciliar todos los casos históricos y la tabla; corregir `src` desde las firmas/alias de `src/ai/context.py` y los árboles duplicados de backend, propagando cada renombrado sin alias; modularizar los demás JS y extraer los scripts embebidos. Repetir suite/revisiones cuando nuevas correcciones lo justifiquen. Al cumplir los ocho bloques, trasladar el informe completo a la respuesta y eliminar este plan; retirar los datos temporales de `scratch` tras aprovechar su evidencia. No se ha realizado commit ni push por el agente, ni instalación o modificación de archivos de entorno.

#### Continuación: nombres numéricos y auditoría estructural de JavaScript

**Implementación VERIFICADA.** Otros 23 archivos de prueba se renombraron y tradujeron por responsabilidad: validación numérica, normalización matricial, verificación/formato de soluciones, productos implícitos, literales, precisión racional, ecuaciones disjuntas/constantes, opciones de interfaz, utilidades, contenedores, clases CSS, navegación, formateadores, producto escalar/transpuesta, expresiones paramétricas, integración, pregunta de explicación, determinantes, inversa y bloques independientes de Gauss. Todos sus casos y valores de expectativas permanecen. El lector duplicado de clases semánticas se extrajo a `comun_estilos.py` conservando las dos expresiones regulares y los tres prefijos.

`src/ai/ventana_matriz.py` extrae el recorrido de `describir_matriz`: normaliza cada celda, cuenta errores en toda la matriz y formatea únicamente la ventana visible. Cuatro regresiones cubren errores fuera de ventana, ventana cero, fila irregular y ausencia de errores. La complejidad inicial de 13 ya está corregida; ahora la primera infracción de ese archivo es la firma heredada de nueve parámetros.

`tests/comun_auditoria_javascript.js` analiza con Acorn 8.18.0 incluido en Node, sin instalar dependencias ni ejecutar los textos inspeccionados. `test_cumplimiento_javascript.py` mide funciones, callbacks, métodos, clases, parámetros, anidamiento y complejidad de todos los `.js` del manifiesto. Las funciones interiores se miden separadamente, `else if` comparte nivel y se incluyen decisiones en parámetros predeterminados. Seis regresiones Node comprueban esas reglas. El parser se carga mediante `--expose-internals`; es una dependencia del arnés respecto del runtime Node disponible, no de producción. Si cambia esa API interna de Node, la comprobación falla explícitamente y deberá adaptarse. No se considera este mecanismo una garantía de portabilidad a cualquier versión.

**Modularización del cliente VERIFICADA.** `app.js` se retiró y distribuyó en `interacciones_globales.js`, `renderizado_mathjax.js`, `escritura_progresiva.js` y `tema_graficos.js`, conservando las APIs de `window.scalaris`. Producción y pruebas comparten el catálogo de datos puro `assets/catalogo_interacciones.json`, sin lógica, de seis líneas. Las comprobaciones negativas de `key-pulse` y `9999` leen los cuatro sucesores, conservando el alcance original. `theme.py` pasó a `tema.py` y `setup_theme` a `configurar_tema`, con consumidores migrados; se retiró su reexport de compatibilidad muerto en `app.py`.

**Revisión independiente VERIFICADA.** Los tres revisores de solo lectura comprobaron este tramo y sus correcciones. Sin hallazgos críticos/altos nuevos. Se corrigieron: omisión de decisiones en parámetros por defecto, alcance demasiado estrecho de dos comprobaciones negativas tras dividir assets, y un fallo medio heredado de escritura progresiva. El fallo reproducido mostraba `ABCBC` después de pulsar para saltar y ejecutar temporizadores; ahora cancela el temporizador y marca el índice como terminado, conservando `ABC` incluso ante un callback pendiente. Esta corrección de robustez se registra como desviación necesaria de conservación estricta del fallo conforme a 6.3. Seis regresiones del cliente ejecutan los assets reales en una VM de pruebas; no ejecutan texto del usuario. Seguridad confirmó que todo texto variable continúa insertándose con `textContent`.

**Resultado actualizado VERIFICADO.** Suite Python completa: **1188 pasadas, 6 fallidas**, 1194 casos. Los seis fallos son auditorías: IIFE de 78 líneas en `calculadora.js`; firma de nueve parámetros en `context.py`; docstring/nombre de `Matrix`; banners de `constants.py`; y estilo embebido de Hub. Los doce tests Node del auditor y cliente pasan. `compileall`, sintaxis de los **24 archivos JS** y `git diff --check` pasan. El manifiesto cubre **401 rutas**; el diagnóstico Python/archivos registra 159 incumplimientos (49 de complejidad, 19 firmas, cinco archivos, 16 clases, 27 funciones y 43 anidamientos), sin exceso físico de tamaño en pruebas. El análisis JS inspecciona 280 funciones y expone 21 funciones con algún límite excedido; los resultados están en `scratch/medidas_javascript.json`. Estas cifras son métricas parciales de la auditoría pendiente, sin excepciones ocultas.

**Conservación actualizada VERIFICADA.** La referencia de inicio se fija en `e85f186bfa5c653ee9aafc213e9214f5dfd03a7d`, evitando que posteriores cambios de HEAD alteren la comparación. Siguen existiendo 2720 expresiones de aserción de la suite inicial; solo dos predicados difieren por el renombrado literal autorizado indicado debajo. Hay 67 expresiones nuevas/restauradas en Python y doce casos nuevos Node registrados aparte. La revisión de cuerpos, preparación y parametrización de familias traducidas no encontró pérdida sustentada. La conciliación histórica exhaustiva de Fase 0 sigue pendiente.

| Aserción antes | Después | Motivo |
|---|---|---|
| `"scrollWidth > target.clientWidth" in app_js` | `"scrollWidth > objetivo.clientWidth" in app_js` | E2/E3: variable local JS en español; mismo predicado sobre anchura. |
| `"target.title = target.value" in app_js` | `"objetivo.title = objetivo.value" in app_js` | E2/E3: mismo contenido asignado a ayuda de celda. |
| Negativos sobre todo `app.js` | Negativos sobre concatenación de sus cuatro sucesores | E2: conservación completa del alcance tras extracción. |
| Ruta `src/frontend/theme.py` | `src/frontend/tema.py` | E2/E3: consumidor estático del mismo módulo renombrado. |

| Before | After | Why |
|---|---|---|
| Un único cierre JavaScript incluía 149 líneas de varias responsabilidades | Cuatro assets con funciones dentro de los límites | Permitir medir y mantener cada responsabilidad sin cambiar sus APIs. |
| El clic de salto podía duplicar caracteres al ejecutar callbacks pendientes | Estado final y temporizador cancelado | Conservar el texto solicitado tras terminar la escritura. |

**Pendientes y riesgos actualizados.** Medir o extraer JavaScript embebido en Python/HTML: el parser nuevo cubre archivos `.js`, no esos fragmentos. Dividir los demás IIFE y resolver complejidad/firma de sus funciones; no ignorarlos como excepción. `interacciones_globales.js` conserva cuatro unidades de inicialización cuya separación adicional puede completarse junto a la limpieza global. Completar todas las traducciones y contratos internos, incluida la firma de `OpenRouterIA.ask`; los contratos E4 definitivos no se declaran cerrados. Verificación visual de la carga en navegador: NO PROBADA; ejecutar la aplicación, abrir Hub y una vista matricial, comprobar fórmulas, ayuda de celdas, tema de figuras, escritura normal/salto y movimiento reducido. Las verificaciones de 320 px, zoom 200 %, teclado y lectores de pantalla siguen pendientes. Leontief, Transformaciones y controlador de determinante conservan los pendientes de producto ya documentados. No se elimina todavía el plan porque la fase no está cerrada.

#### Continuación: cierre de nombres de archivos y conexión de temas

**Implementación VERIFICADA.** Los nueve archivos ingleses enumerados en el punto anterior se retiraron con todos sus casos trasladados: soluciones exactas/paramétricas de Gauss, elementos/registro de navegación, interfaz del conversor, límites numéricos, conversiones/operaciones romanas y errores romanos. La cobertura de revisión se dividió por responsabilidad en dimensiones/índices matriciales, signos unarios y constantes izquierdas. Los tres dobles NiceGUI del conversor se extrajeron al nivel del módulo; las coordenadas libres de Gauss a un auxiliar que evita anidamiento excesivo. Se tradujeron también las siete funciones de pasos de bases y se corrigió el identificador con tilde de conversión romana. Quedan símbolos, docstrings y comentarios ingleses dentro de otros archivos; el bloque 4 sigue parcial.

`calculadora.js` conserva su API y comportamiento mediante funciones privadas en un bloque léxico estricto: no agrega nombres globales y deja cada función dentro de límites. Ocho pruebas Node ejecutan el asset real y cubren inserción/selección, foco alternativo, signos, limpieza, borrado, entradas ajenas, ausencia de entrada y aislamiento. `comun_cliente_javascript.js` comparte la carga de assets con las pruebas de interacciones. `test_ejecucion_suite_cliente.py` descubre todos los `test_*.js` y ejecuta la suite Node dentro de pytest; su fallo impide que la suite Python pase.

Las cabeceras extensas de `tema.py` pasan a `assets/plantillas/cabecera.html` y `cabecera_glosa.html`. Sus scripts se extraen a `inicializacion_tema.js` e `inicializacion_glosa.js`; `theme.js` se sustituye por `tema.js` y se propaga su referencia. La configuración de figuras se transporta como JSON declarativo, escapando `<`, y se lee con `JSON.parse(textContent)`. La inicialización de tema se comparte y mantiene las dos invocaciones existentes y las equivalencias almacenadas. Cuatro pruebas Python comprueban datos, assets, cascada y orden; trece Node cubren preparación, conmutación, rechazo, ancho de Glosa, teclado/movimiento reducido y carreras.

**Revisión independiente VERIFICADA.** Los tres revisores de solo lectura comprobaron el mismo contexto acotado. Confirmaron 128 funciones y 274 aserciones conservadas en los nueve grupos renombrados, con entradas y parametrizaciones iguales. Los dobles extraídos y el auxiliar de coordenadas libres mantienen preparación y predicados. También verificaron el aislamiento de calculadora y las plantillas. Detectaron tres problemas heredados baratos dentro del alcance: el selector llamaba a un global inexistente; el rechazo/callback de una transición vieja podía restablecer un tema anterior; y el temporizador de Plotly podía actualizar figuras con una selección anterior. Se corrigieron y revisaron: el selector llama a la API real y las tareas de tema comprueban identidad de selección. Las tres regresiones de carrera fallaban antes de corregir y ahora pasan. No quedan hallazgos críticos/altos ni medios abiertos en este tramo revisado. Estas correcciones funcionales se registran conforme a 6.3; no modifican aritmética.

`theme_switcher.py` pasa a `selector_tema.py`, `render_theme_button` a `renderizar_boton_tema`; `navbar.py` y su comprobación negativa migran en el mismo paso sin alias. La prueba nueva del selector crea el menú real, captura sus manejadores y verifica las tres llamadas emitidas. E5 hace instantáneo el cambio de tema por teclado o preferencia de movimiento reducido, reutilizando `window.scalaris.movimiento.permitido`.

**Verificación actual VERIFICADA.** Suite completa: **1194 pasadas, seis fallidas, 1200 recogidas**, una advertencia heredada de Starlette. Los seis fallos son exclusivamente de auditoría: IIFE de 135 líneas en `cuadricula_compartida.js`, firma de nueve parámetros en `context.py`, docstring y nombre de `Matrix`, banners de `constants.py` y estilo embebido de Hub. Son los primeros incumplimientos de cada categoría y no describen toda la deuda. Las **33 pruebas Node pasan** y ahora las ejecuta la suite Python. `compileall`, `node --check` de los **30 archivos JS** y `git diff --check` pasan. Ruff, mypy, pylint, radon, flake8 y pyright no están instalados; no hay configuración ESLint ni se instalaron herramientas. La ejecución completa usa permiso para sockets locales de Windows.

El manifiesto cubre **414 rutas**, sin exclusiones por carpeta. El diagnóstico exhaustivo actualizado registra **158 infracciones Python/archivos**: 19 firmas, 49 complejidades, cinco archivos, 16 clases, 27 funciones y 42 anidamientos. No hay exceso físico de tamaño en pruebas, pero **13 infracciones de complejidad/anidamiento sí afectan a pruebas**, en seis archivos. El análisis JS mide 339 funciones y **19 funciones incumplidoras**, todas de producción. Las dos funciones envolventes retiradas de calculadora y tema dejaron de ser infracciones sin excepciones del arnés. Las métricas/datos están en `scratch` para la continuación y no constituyen código de parcheo.

**Conservación actual VERIFICADA.** Contra `e85f186bfa5c653ee9aafc213e9214f5dfd03a7d` se conservan las **2720 aserciones iniciales**, más **85 nuevas/restauradas** en Python. El multiconjunto AST conserva constantes, operadores y relaciones entre nombres; sus siete diferencias se explican por dos literales JS ya registrados, cuatro accesos del doble `styles` a `estilos` y el nombre literal del selector. Tras esas equivalencias explícitas E2/E3 no falta ningún predicado. Los revisores comprobaron también cuerpos, preparación y parametrización del tramo; esta evidencia no sustituye la conciliación completa contra Fase 0, que sigue pendiente. Los 33 casos Node se registran por separado y no se suman como casos individuales al conteo pytest.

| Aserción antes | Después | Excepción e intención conservada |
|---|---|---|
| `opacity: 0.45; in dummy_card.styles` | Mismo literal en `tarjeta.estilos` | E2/E3: nombre español del registro del mismo doble. |
| `opacity: 0.45; in ui_inst.bits_container.styles` | Mismo literal en `interfaz.bits_container.estilos` | E2/E3: mismo registro y control. |
| `opacity: 0; transform: translateY(16px); in dummy_card.styles` | Mismo literal en `tarjeta.estilos` | E2/E3: mismo estado de limpieza. |
| `opacity: 0; in ui_inst.bits_container.styles` | Mismo literal en `interfaz.bits_container.estilos` | E2/E3: mismo ocultamiento. |
| `render_theme_button not in view` | `renderizar_boton_tema not in view` | E2/E3: mismo control ausente de la vista del Hub. |
| Carga anterior de `/assets/js/theme.js` antes del catálogo | Carga de `/assets/js/tema.js` antes del catálogo | E2/E3: misma restricción de orden con el archivo renombrado. |
| Enlaces de reproductor leídos desde `tema.py` | Mismos enlaces/predicados leídos desde `assets/plantillas/cabecera.html` | E2: seguir la extracción; archivo ausente falla por lectura. |
| Nueve archivos con nombres ingleses y funciones numeradas de Gauss | Once archivos por responsabilidad, funciones españolas | E2: 128 funciones y parametrizaciones conservadas, sin cambios de expectativas. |

| Before | After | Why |
|---|---|---|
| El menú invocaba `setTheme`, un global inexistente | Invoca `window.scalaris.tema.establecer` | Recuperar la conexión con la API real. |
| Una transición antigua podía restablecer el tema anterior | Sus callbacks se descartan si cambió la selección | Mantener la última elección. |
| Un timer de figuras podía aplicar el tema anterior | Comprueba la identidad antes de actualizar Plotly | Mantener figuras y documento en el mismo tema. |
| Teclado y movimiento reducido iniciaban una transición de tema | Cambio inmediato sin transición | E5: respetar la modalidad y la preferencia. |
| Cabeceras y scripts extensos estaban embebidos en Python | Plantillas y assets auditados | Medir los scripts reales y separar responsabilidades. |

**Excepciones y riesgos.** E1 y autorización posterior siguen vigentes para corregir `src` sin cambios matemáticos. E2/E3 sustentan los renombrados, extracciones y tabla; E5 el cambio instantáneo por teclado/movimiento reducido. E6 conserva su aplicación histórica a la cascada CSS; este tramo no cambia sus valores. E7 y la consolidación de dominio siguen pendientes. E4 mantiene en los archivos nuevos únicamente APIs de navegador, NiceGUI, stdlib, pytest y Node; `style`, `classes`, `clear`, `text`, `value`, `set_value`, eventos y prefijos `test_`/`Test` son contratos reales. Las claves `theme`, los atributos `data-theme`/`data-input` y estados `open`/`closed` siguen siendo contratos internos pendientes de migración, no se declaran excepciones. La lista definitiva E4 se entregará en el cierre real.

**NO PROBADO:** inspección visual y disponibilidad del despliegue/empaquetado de las nuevas plantillas. Para verificar manualmente, inicia la aplicación con su comando habitual, abre Hub y una herramienta matricial; selecciona los tres temas por ratón y teclado, recarga cada selección, activa movimiento reducido y abre/cierra Glosa a ambos lados de 1024 px. Comprueba colores de Plotly, carga CSS/MathJax, logotipos y consola sin errores. Después comprueba 320 px, zoom 200 % y navegación por teclado. Las pruebas automáticas sí verifican assets y contenido local; no sustituyen estas comprobaciones visuales. Leontief/Transformaciones siguen fuera de navegación y Hub; el controlador de determinante permanece sin consumidor.

**Punto de continuación de ese tramo:** los trece límites de pruebas indicados aquí se resolvieron en la continuación siguiente. El estado y punto vigente están al final del documento; no usar este registro histórico como lista actual.

#### Continuación: límites de pruebas, huellas y animación de cuadrículas

**Implementación VERIFICADA.** Los seis archivos de auditoría/pasos se apoyan ahora en `tests/comun_recorrido_codigo.py` y `comun_textos.py`. Se comparten recorrido de archivos/líneas, relaciones padre-hijo AST, nombres de asignación y cadenas estáticas. Se conservan los filtros, ventanas de líneas, condiciones sobre argumentos de botones, tratamiento histórico de docstrings y excepciones de saludo existentes. Los tres revisores confirmaron equivalencia del detector sobre 223 módulos y 44 escenarios sintéticos. Ya no quedan infracciones numéricas en pruebas Python; los ayudantes JavaScript también cumplen.

La comprobación idéntica de textos de pasos y grupos se extrae a `comprobar_textos_sobrios`. Sus seis expresiones sintácticas anteriores pasan a tres compartidas, invocadas para las mismas dos familias. Los tres revisores comprobaron **400 controles efectivos antes y después**. Esta deduplicación E2 reduce tres nodos `assert`; no elimina casos ni controles.

`src/ai/huellas.py` extrae normalización, `calcular_huella` y `esta_desactualizado`, propagados a trece consumidores y dos familias de pruebas, sin alias. Conserva SHA1, serialización ordenada, representación de Fraction y comportamiento de huella ausente. Ocho casos nuevos incluyen seis valores históricos y ausencia de mutación; revisión independiente de cuarenta entradas confirma equivalencia.

`cuadricula_compartida.js` elimina su cierre extenso y comparte animación de celdas; utiliza la política existente de teclado/movimiento reducido. Conserva fotogramas, duraciones y espera de promesas. El contorno de error pasa a `.cuadricula-error`; una identidad por control evita que un temporizador antiguo retire una marca reciente. Nueve pruebas Node ejecutan los assets reales.

`cuadricula_base.py` comparte `_animar_cuadricula` entre entrada y salida y usa `json.dumps` para los argumentos. Los dos consumidores se migran. Se corrigen llamadas heredadas a globales inexistentes y el escape de selectores/nombres; doce casos parametrizados capturan el JavaScript emitido por Python y lo ejecutan contra los assets reales en una VM de pruebas. El documento simulado registra selectores; esto no prueba la validez CSS de los selectores deliberadamente malformados del ensayo de inyección. Se conservan la espera inicial de entrada y la gestión existente de errores de ejecución. Los tres revisores aprobaron las correcciones del tramo; el hallazgo bajo de duplicación se resolvió con el auxiliar compartido. Estas correcciones de robustez se registran conforme a 6.3; no alteran aritmética.

| Aserción antes | Después | Excepción e intención conservada |
|---|---|---|
| Tres controles de sobriedad repetidos para pasos y grupos | Los mismos tres controles comunes invocados para ambas familias | E2: 400 comprobaciones efectivas conservadas; tres nodos AST menos por deduplicación. |
| `fingerprint` e `is_stale` importados desde `context.py` | `calcular_huella` y `esta_desactualizado` desde `huellas.py` | E2/E3: mismos valores y clasificación de datos anteriores, sin alias. |
| Llamadas emitidas a globales de animación sin definición | Invocaciones a `window.scalaris.cuadricula` con argumentos JSON | Corrección 6.3: las pruebas nuevas verifican ejecución, duraciones y datos sin inyección. |

| Before | After | Why |
|---|---|---|
| Un aviso antiguo podía borrar una marca de error reciente | Cada temporizador comprueba la identidad de su aviso | Conservar la señal de la última validación. |
| Selectores y nombres con comillas podían producir JavaScript inválido | Argumentos transportados como literales JSON | Ejecutar la animación con los datos completos. |
| La ruta de ecuaciones llamaba funciones globales inexistentes | Delega a la API compartida de celdas | Conectar el consumidor con su implementación activa. |

#### Continuación: contrato español del cliente OpenRouter y conciliación de conteos

**Implementación VERIFICADA.** `openrouter_ai.py` se sustituye por `cliente_openrouter.py`; la clase es `ClienteOpenRouter`, su operación `preguntar`. Las cinco entradas son pregunta, historial, contexto, cancelación y `OpcionesConsulta`, que agrupa caché y respuesta simple. No queda alias de la API anterior en `src` o `tests`. `respuestas.py` define `ResultadoIA`, `TipoErrorIA` y opciones inmutables; `cache_respuestas.py` conserva la caché aislada y `textos.py` comparte los mensajes repetidos. Clasificador, panel, puente de envío, fixture de limpieza y seis archivos de pruebas migran conjuntamente.

La caché conserva exactamente el hash SHA256 de cliente/modelos/mensajes, la validez a 3600 segundos y caducidad estricta después, capacidad y desalojo por fecha de guardado más antigua. Leer no refresca la fecha: no se denomina LRU. Se conservan límite total, tiempos de red, modelos de reserva, reintentos, cancelación y textos de respuesta. El valor interno `fallback` pasa a `reserva`; el control de flujo es equivalente. Claves HTTP, payload y variables de entorno se mantienen por E4.

**Revisión independiente VERIFICADA.** Tres revisores de solo lectura revisaron el mismo contexto acotado y confirmaron **17 funciones y 68 predicados de aserción** conservados en las seis familias existentes. El revisor de regresiones contrastó **108 combinaciones** de clasificación HTTP/transporte contra HEAD. Los módulos nuevos cumplen límites: máximo 157 líneas por archivo, 29 por función y 130 por clase. No quedan hallazgos nuevos pendientes en este tramo; no implica aceptación de la auditoría global.

Doce casos nuevos en `test_ia_contrato_consulta.py` cubren cuatro combinaciones de opciones, cuatro transmisiones del puente, inmutabilidad/ausencia de alias, cancelación durante HTTP, privacidad del fallo imprevisto y resultado ausente por cancelación/apagado. Se reprodujo la copia de detalles privados al registro por `logger.exception`; ahora el puente registra solo el mensaje genérico. El revisor encontró que la versión instalada de `nicegui.run` permite `None` por cancelación/apagado: se reprodujo y se convierte a `ResultadoIA` cancelado, evitando el acceso a atributos de `None`. Ambas regresiones fallaron antes de corregir y pasan después. Son correcciones necesarias de robustez/privacidad conforme a 6.3; no afectan resultados matemáticos.

| Aserción antes | Después | Excepción e intención conservada |
|---|---|---|
| `res.ok`, `res.text`, `res.kind`, `res.model`, `res.cached` | `resultado.exito`, `.texto`, `.tipo_error`, `.modelo`, `.desde_cache` | E2/E3/E4: mismos predicados y expectativas, con campos internos españoles. |
| `NO_KEY`, `AUTH`, `TIMEOUT`, `RATE_LIMIT`, `EMPTY`, `NETWORK`, `SERVICE`, `CANCELLED` | `SIN_CLAVE`, `AUTENTICACION`, `TIEMPO_AGOTADO`, `LIMITE_PETICIONES`, `VACIO`, `RED`, `SERVICIO`, `CANCELADO` | E2/E4: mismas ocho causas granulares; no son valores externos del proveedor. |
| `ask(..., cacheable=..., simpler=...)` | `preguntar(..., opciones=OpcionesConsulta(...))` | E2/E3: mismas combinaciones, valores por defecto y contenido efectivo enviado. |
| Fixture limpia caché del módulo monolítico | Fixture limpia el módulo `cache_respuestas` con el mismo bloqueo | E2: mismo aislamiento antes y después de cada caso. |

| Before | After | Why |
|---|---|---|
| Una excepción imprevista del puente incorporaba detalles privados al registro | Diagnóstico genérico sin cuerpo ni traceback | Conservar el fallo comunicado evitando divulgar datos. |
| Cancelación/apagado de NiceGUI podía devolver `None` al consumidor | Resultado tipado de cancelación | Evitar un `AttributeError` durante la finalización. |

**Línea base VERIFICADA.** La instantánea limpia `71420904a7bf8ea0e50ed2b88727eb2552f20bc9` ejecutada con su `pytest.ini` original recoge y pasa **1099 casos**, de los cuales siete son el arnés añadido. Sin ese archivo pasan 1092. Entre su padre `94eea757c7d11376b531da57e553f4cdba824705` y ese commit, el único cambio en pruebas es añadir el arnés. El padre conserva conflictos y falla colección; no se alteró. El anterior conteo de **1106** incluía además seis pruebas de backend y una de controlador ubicadas en `src`, fuera de `testpaths=tests`. Se registran por separado en `scratch/conciliacion_linea_base.json` y `recoleccion_fase0_testpaths.txt`; las instantáneas y ZIP se eliminaron con rutas verificadas. Queda pendiente la conciliación exhaustiva de intención histórica, incluida la conservación/migración de esos siete casos adicionales. Se corrige aquí la inferencia anterior de 1099 más siete auditorías: los siete añadidos al conteo ampliado eran casos de `src`.

**Conservación actual VERIFICADA.** Contra el inicio fijo `e85f186bfa5c653ee9aafc213e9214f5dfd03a7d`, 2720 nodos `assert` originales pasan a **2834** actuales: **117 nuevos/restaurados**, y **tres instancias duplicadas extraídas** al auxiliar común. No se afirma que existan 2720 instancias sintácticas originales separadas. Tras las equivalencias de renombrado enumeradas, las únicas diferencias son esos tres predicados de sobriedad revisados. Esta evidencia, las 68 aserciones del cliente y las comparaciones independientes de preparación/parametrización no sustituyen la conciliación histórica completa de todas las familias.

**Verificación actual VERIFICADA.** Suite completa: **1226 pasadas, seis auditorías fallidas, 1232 recogidas**, una advertencia heredada de Starlette. Las **42 pruebas Node** pasan dentro de pytest. Fallos iniciales: cierre de 83 líneas en `equation_grid.js`; firma de nueve parámetros en `context.py`; docstring/nombre de `Matrix`; banners de `constants.py`; estilo embebido de Hub. El manifiesto descubre **426 rutas**, sin exclusiones por carpeta. Diagnóstico completo Python/archivos: **144 infracciones**, con 18 firmas, 46 complejidades, cinco archivos, 16 clases, 27 funciones y 32 anidamientos; **cero infracciones numéricas en pruebas**. JavaScript conserva 18 funciones incumplidoras de producción. Compilación Python, sintaxis de los 33 archivos JavaScript y comprobación de diff se actualizan en el cierre de este tramo. Ruff, mypy, pylint, radon, flake8 y pyright no están instalados; no se instalan herramientas ni dependencias.

**Excepciones y contratos.** E1 sigue vigente para el backend; este tramo no cambia aritmética. E2 permite las extracciones y migraciones de pruebas; E3/E4 sustentan las APIs españolas sin alias. E5 sigue aplicado a teclado/movimiento reducido en cuadrículas; E6 mantiene la cascada modular; E7 y las reglas de dominio aún pendientes no se declaran completadas. En los módulos IA tocados se mantienen APIs de stdlib/requests/dotenv/pytest/NiceGUI, `status_code`, `json`, `headers`, `timeout`, `Authorization`, cabeceras HTTP, payload OpenRouter (`model`, `messages`, `choices`, `message`, `content`, `role`) y variables `OPENROUTER_*`. Las claves heredadas de historial/panel aún no se presentan como excepciones. La lista E4 global definitiva sigue pendiente.

**Riesgos y producto.** NO PROBADO: navegador, empaquetado de plantillas, inspección visual, 320 px, zoom 200 %, teclado y lector de pantalla; siguen los pasos manuales anteriores. La documentación permanente no se editó: README conserva referencias históricas a `openrouter_ai.py`/`OpenRouterIA`, que ahora están desactualizadas; se declara esta deuda sin restaurar alias. Leontief y Transformaciones siguen fuera de navegación contextual y Hub; `controlador_determinante.py` continúa sin consumidor. No se hace commit/push, instalación ni cambio de entorno.

**Punto limpio vigente:** tres de ocho bloques completos. Continuar contratos/firmas de `src/ai/context.py` y modularización de `equation_grid.js`, `matrix_capture.js` y `vector_capture.js`, con consumidores y casos reales de teclado/pegado/foco. Resolver los árboles activos duplicados de backend, demás infracciones e idioma; conciliar todas las intenciones históricas y completar la tabla acumulada E2/E5/E6. El plan se conserva hasta el cierre real de la fase conforme a la regla 11; solo entonces se elimina y declara. La fase no está terminada.

#### Continuación: mensajes pedagógicos y filtrado de historial

**Implementación VERIFICADA.** `prompts.py` pasa a `mensajes.py`: `build_messages` a `construir_mensajes`, `trim_history` a `recortar_historial` y `SYSTEM_PROMPT` a `INSTRUCCIONES_SISTEMA`. Se traducen parámetros y variables de las tres funciones públicas. Cliente, puente de Glosa y cuatro archivos de pruebas se migran conjuntamente; no quedan alias ni referencias a la API retirada en `src/tests`. Textos del sistema, instrucciones de pasos, sufijos, orden de mensajes y payload se conservan exactamente. Las claves internas de historial/contexto continúan pendientes de E4; no se añaden excepciones.

Los tres revisores confirmaron los mismos **41 predicados de aserción existentes** y cuerpos equivalentes antes de la extracción. Detectaron complejidad 11 heredada en el filtrado. Se corrigió separando `_mensaje_historial_valido` y `_normalizar_mensaje_historial`: primero se filtra, después se aplica exactamente `[-maximo_mensajes:]` y finalmente se normaliza. Complejidades finales **5, 4 y 4**; ninguna infracción numérica en el módulo. Se conservan las prioridades `text/content`, `role/sent`, límites cero/negativos y las excepciones originales para contenido no textual. No se transforma esa entrada en cadena ni se cambia su contrato silenciosamente.

**Revisión independiente VERIFICADA.** Los tres revisores revisaron también la extracción final. Seguridad contrastó **486 combinaciones** con salida o excepción exacta, regresiones **99 escenarios** y mantenibilidad ejecutó **22 casos relacionados**, todos pasados. No quedan hallazgos nuevos pendientes en el tramo. Trece casos nuevos en `test_ia_historial_filtrado.py` cubren estos límites y prioridades. Esta aprobación no cierra la auditoría global.

| Aserción antes | Después | Excepción e intención conservada |
|---|---|---|
| Llamadas/imports `build_messages` y `trim_history` desde `prompts` | `construir_mensajes` y `recortar_historial` desde `mensajes` | E2/E3: mismas entradas, salidas, orden, textos y cuarenta y un predicados existentes. |
| `history`, `question`, `context_block`, `simpler`, `max_messages` | `historial`, `pregunta`, `contexto`, `respuesta_simple`, `maximo_mensajes` | E3/E4: productores y consumidores migrados en el mismo paso. |
| Filtrado, recorte y normalización dentro de una función compleja | Auxiliares privados y la misma secuencia | Extracción por límite duro: conserva incluso slice cero/negativo y excepciones originales. |

**Estado final de este tramo VERIFICADO.** Suite completa **1239 pasadas, seis auditorías fallidas, 1245 casos**, una advertencia heredada de Starlette; las **42 pruebas Node** se ejecutan y pasan dentro de pytest. Compilación Python, sintaxis de los **33 archivos JS** y `git diff --check` con configuración normal pasan. La prueba hecha con `core.autocrlf=false` interpretó los CRLF del árbol Windows como espacios finales; no se usa ese resultado como defecto del código ni se modifica la configuración Git. No se instala ninguna herramienta. Manifiesto **427 rutas**; diagnóstico actualizado **143 infracciones Python/archivos**: 18 firmas, 45 complejidades, cinco archivos, 16 clases, 27 funciones y 32 anidamientos. **Cero límites numéricos incumplidos en pruebas**; JavaScript conserva 18 funciones incumplidoras de producción entre 380 medidas.

Conservación sintáctica actual: **2837 aserciones**, equivalentes a 2720 iniciales, **120 nuevas/restauradas** y tres instancias duplicadas extraídas. Las tablas previas siguen acumuladas; el nuevo recuento sustituye 2834/117. La lectura de los siete casos históricos situados fuera de `testpaths` confirma sus sucesores de dominio/combinación/controlador; queda pendiente conciliar todas sus aserciones específicas contra esos sucesores y las otras familias, sin dar por suficiente el incremento de conteo.

**Punto limpio vigente de continuación:** `src/ai/context.py` (firmas, constructores y contratos duales), con migración simultánea de sus consumidores; después cuadrículas JS y consolidación de backend. Tres de ocho bloques completos, seis auditorías fallan. Las claves internas pendientes, E7 y la intención histórica exhaustiva continúan abiertas. Se conserva el plan temporal hasta el cierre real; documentación permanente y decisiones de producto permanecen sin cambios. No hay commit/push, instalaciones ni modificaciones de entorno.

#### Continuación: datos agrupados y esquema español del contexto de IA

**Implementación VERIFICADA.** `context.py` se retiró. `contexto.py` expone la interfaz canónica y delega en `datos_contexto.py`, `texto_contexto.py` y `matrices_contexto.py`. Las cuatro estructuras son `ContextoIA`, `EstadoContexto`, `ReferenciaPaso` y `CapturaPaso`; sus constructores admiten hasta cinco parámetros. Estado y captura agrupan las opciones que provocaban las firmas de diez y nueve parámetros. Las propiedades españolas del contexto acceden al estado agrupado; no se mantienen atributos, constructores ni alias ingleses. Se conservan los valores por defecto independientes y la entrada canónica ausente se normaliza a diccionario vacío.

Se migraron las seis familias de vistas, el contexto geométrico, panel y pie de Glosa, mensajes pedagógicos e imports de tres controladores. El esquema JSON principal y los descriptores matriciales usan claves españolas. Las instrucciones del sistema apuntan a los metadatos nuevos. La captura inmutable se sustituye mediante `dataclasses.replace` y la cascada sigue trabajando sobre copia profunda. Fracciones, aproximación de presentación, ventanas, recuento de errores, `IndexError` de filas irregulares y textos del ejercicio permanecen. La representación histórica de `Matriz` española como texto y de `Matrix` heredada como dimensiones sigue diferenciada; su consolidación queda pendiente con el backend.

**Corrección de robustez VERIFICADA.** Las pruebas nuevas reprodujeron que el contexto mínimo excedía su presupuesto al sumar delimitadores y escapar comillas/barras. Ahora se mide el bloque completo y se recortan los nombres, conservando JSON válido. Si el presupuesto no admite ni el esquema mínimo, lanza `ValueError` explícito. Se registra conforme a 6.3; no se debilita la aserción histórica `len(...) <= 400 + 24`, mientras pruebas nuevas exigen el límite total estricto. Al traducir claves aumenta la longitud del JSON: la cascada puede alcanzar un recorte anterior con el mismo presupuesto; se conserva el orden de estrategias y el aviso de truncamiento.

**Revisión independiente VERIFICADA.** Los tres revisores confirmaron **133 predicados de aserción existentes conservados** en seis archivos seguidos, tras el mapa nominal explícito. `test_ia_ventana_matriz.py` ya era nuevo en el árbol de esta tarea y se revisó como tal, sin inventar una comparación contra HEAD. Regresiones contrastó **78 casos** de texto/descriptores y **603 presupuestos** de contexto mínimo; seguridad comprobó **660 combinaciones** adicionales y las pruebas del contrato. Mantenibilidad ejecutó 51 casos focalizados y 28 después de la corrección de aislamiento. Máximos de los módulos: 264 líneas por archivo, 29 por función y 62 por clase; constructores dentro del límite. Sin hallazgos nuevos pendientes en el tramo.

`test_ia_contrato_contexto.py` añade **22 casos** de firmas, ausencia de alias, independencia, inmutabilidad, serialización, copia, presupuestos escapados/imposibles y cuatro estados de la píldora real NiceGUI. Se inspeccionan etiquetas de la API real; esto no acredita apariencia en navegador. Se corrigió un hallazgo bajo introducido en la prueba: el `finally` cubre ahora también un renderizado fallido y elimina su contenedor. Los revisores confirmaron la limpieza mediante una reproducción independiente. Las pruebas de contexto tocadas recibieron nombres locales y docstrings españoles sin cambios de predicados.

| Aserción antes | Después | Excepción e intención conservada |
|---|---|---|
| `AIContext` y `StepRef` con opciones planas y alias ingleses | `ContextoIA`/`ReferenciaPaso` con `EstadoContexto`/`CapturaPaso` | E2/E3/E4: mismo ejercicio y captura, firmas de hasta cinco parámetros, sin alias. |
| `rows`, `cols`, `data`, `window`, `invalid` en descriptores | `filas`, `columnas`, `datos`, `ventana`, `invalidos` | E2/E4: dimensiones, celdas, ventana y recuento exactos conservados. |
| `v`, `tool`, `view`, `input`, `result`, `focus`, `meta` | `version`, `herramienta`, `vista`, `entrada`, `resultado`, `foco`, `metadatos` | E3/E4: productor, instrucciones y consumidores migrados conjuntamente. |
| `index`, `kind`, `op`, `rows_before`, `rows_after`, `cols`, `detail` en el foco serializado | `indice`, `tipo`, `operacion`, `filas_antes`, `filas_despues`, `columnas`, `detalle` | E2/E4: misma referencia y datos opcionales; no cambia el formato del reproductor todavía pendiente. |
| Metadatos `window`, `stale`, `truncated` | `ventana`, `desactualizado`, `truncado` | E2/E4: mismas notas y señales, sin reinterpretar contratos internos como externos. |
| `ctx.input`, `ctx.empty`, `ctx.window_note` | `.entrada`, `.vacio`, `.nota_ventana` | E2/E3: mismos controles del ejercicio, vacío y ventana. |

| Before | After | Why |
|---|---|---|
| El contexto mínimo medía JSON sin todos sus delimitadores/escapes | Mide y acota el bloque completo | Cumplir el presupuesto real de serialización. |
| Un presupuesto imposible producía un bloque mayor que el límite | Produce un error explícito | Evitar una garantía de tamaño falsa. |
| La prueba podía conservar un contenedor si fallaba el render | El `finally` también protege el renderizado | Mantener aislamiento entre casos de NiceGUI. |

**Contratos y pendientes.** E2/E3/E4 sustentan esta migración. E1 conserva la aritmética; E5/E6 mantienen las aplicaciones históricas y este tramo no cambia movimiento ni estilos. E7 continúa pendiente. El JSON propio nuevo no es una excepción externa. Las claves heredadas de resultados del backend y metadatos del reproductor siguen en inglés y requieren migración conjunta posterior; tampoco son excepciones E4. La lectura de `rows/cols` del modelo heredado en el serializador se conserva hasta consolidar ese modelo activo, sin declararla contrato externo. APIs de Python/dataclasses/json, NiceGUI, pytest y marcadores españoles de contexto permanecen. La documentación permanente no se editó, aunque sus referencias históricas puedan quedar desactualizadas.

#### Continuación: complejidad de validación de parámetros geométricos

**Implementación y revisión VERIFICADAS.** `obtener_parametros_solucion` en `src/backend/geometria/conjunto_solucion.py` pasa de complejidad 12 a **6**, con auxiliares de dimensiones y coeficientes de complejidad **3 y 6**. Se conservan las cinco lecturas únicas en orden, cortocircuito de longitudes, comprobación de Fraction, prioridad de claves, excepciones y retorno por identidad. E1: no hay cambios matemáticos ni de textos. Los alias, valores de enums y claves inglesas preexistentes del módulo siguen como deuda E3/E4; este refactor no los convierte en excepciones.

Dieciséis casos nuevos en `test_geometria_parametros_exactos.py` cubren identidad/exactitud, siete datos inválidos, cinco campos ausentes, prioridad/vacíos y diccionario instrumentado. **29 pruebas pasan: 16 nuevas y 13 existentes**. Los tres revisores aprobaron únicamente este refactor, sin hallazgos nuevos. Regresiones contrastó **256 combinaciones** con HEAD y mantenibilidad **720**, preservando aceptación, rechazo, identidad o excepción; seguridad ejecutó los 16 casos nuevos. Funciones de 17, 7 y 7 líneas. No se editó el archivo de pruebas histórico del conjunto solución.

**Verificación vigente VERIFICADA, 2026-10-12.** Suite completa: **1277 pasadas, seis auditorías fallidas, 1283 casos**, una advertencia heredada de Starlette. Las **42 pruebas Node** pasan dentro de pytest. El intento anterior de la suite no se ejecutó al agotarse la revisión automática de permisos; el reintento posterior fue autorizado y completó la ejecución, sin eludir permisos. Compilación Python y `git diff --check` pasan; sintaxis de 33 archivos JS y ausencia de Ruff/mypy/pylint/radon/flake8/pyright comprobadas en este tramo, sin instalaciones.

Manifiesto **432 rutas**. Diagnóstico Python/archivos: **140 infracciones**: 16 firmas, 44 complejidades, cinco archivos, 16 clases, 27 funciones y 32 anidamientos. No quedan límites numéricos incumplidos en pruebas. JavaScript mantiene 18 funciones incumplidoras entre 380 medidas. Los seis fallos muestran ahora primero: cierre de 83 líneas de ecuaciones; constructor `Matriz` de complejidad 13; docstring/nombre de `Matrix`; banners de constantes; y estilo embebido de Hub. No equivalen a toda la deuda.

Conservación actual: **2869 aserciones**, 2720 iniciales más **152 nuevas/restauradas** y tres instancias duplicadas extraídas al auxiliar revisado. Se mantiene la evidencia de 400 comprobaciones efectivas de esas dos familias. La conciliación histórica exhaustiva de Fase 0 y sus siete casos adicionales sigue pendiente; no se sustituye por crecimiento de conteos.

**Punto limpio vigente:** tres de ocho bloques completos. Continuar `src/backend/modelos/matriz.py` (complejidad de constructor y consolidación del modelo activo heredado), y cuadrículas JS. Propagar cada contrato sin alias y conservar Fraction/errores; después resolver resto de límites, idioma y conciliación histórica. Plan temporal conservado hasta completar la fase, sin commit/push ni cambios de entorno. Leontief/Transformaciones siguen fuera de navegación contextual y Hub; el controlador de determinante sigue sin consumidor. Navegador, empaquetado, 320 px, zoom 200 %, teclado y lector de pantalla continúan NO PROBADOS con los pasos manuales anteriores.

#### Continuación: construcción matricial y normalización compartida

**Implementación VERIFICADA.** El constructor canónico de `Matriz` delega la validación de dimensiones y forma en dos auxiliares privados. Su complejidad pasa de 13 a 6; los auxiliares tienen 5 y 4. Se conservan tipo y positividad, aceptación de booleanos, orden de comprobaciones, mensajes exactos, llamadas a `len` y despacho del normalizador en subclases. Once casos nuevos cubren errores dimensionales y de forma, prioridad de forma sobre parseo, filas independientes, orden de normalización y booleanos. Los tres revisores aprobaron el tramo; regresiones comparó 240 escenarios con HEAD y mantenibilidad 640. Veintitrés casos focalizados pasan.

La clase heredada `Matrix` hereda ahora el mismo normalizador canónico: se elimina su implementación duplicada y el alias `_normalize_val`, sin consumidores ejecutables. Las constantes y clases de excepción eran idénticas. Diecisiete casos nuevos verifican identidad de implementación, valores/tipos, errores exactos y los tres flotantes no finitos. E1 conserva su aceptación heredada; no se presenta como validación segura de no finitos. No cambian otros métodos, límites, comparación ni aritmética. Los alias y contratos ingleses restantes del modelo siguen pendientes, sin excepción E4.

**Revisión independiente VERIFICADA.** Seguridad aprobó los 17 casos; regresiones contrastó 137 valores con HEAD; mantenibilidad contrastó 27 entradas y ejecutó 40 pruebas relacionadas. Se conservan tipos, identidad y errores. Los comentarios de Gauss y el docstring de operaciones vectoriales se traducen sin cambiar el AST ejecutable. Se corrigió el hallazgo bajo introducido que confundía magnitud y denominador; el revisor confirmó la corrección. Sin hallazgos nuevos pendientes en estos dos tramos; no es aprobación global.

| Aserción antes | Después | Excepción e intención conservada |
|---|---|---|
| Pruebas existentes de normalización y modelos | Mismos predicados y entradas, sin edición | E1/E2: ambas extracciones conservan el contrato; las 28 parametrizaciones nuevas se añaden en archivos independientes. |
| Normalización duplicada en `Matrix` | Método heredado de `Matriz` por identidad | Misma validación de cadenas, reconstrucción flotante, tipos, excepciones y mensajes. |

**Verificación vigente VERIFICADA.** Suite completa: **1305 pasadas, seis auditorías fallidas, 1311 casos**, una advertencia heredada de Starlette. Manifiesto de **434 rutas**; **138 infracciones Python/archivos**: 42 complejidades, cinco archivos, 16 clases, 27 funciones, 32 anidamientos y 16 firmas. Cero límites numéricos incumplidos en pruebas. El primer límite Python pendiente es ahora `_verificar_producto` de la inversa. Hay **2885 aserciones**: 2720 iniciales, 168 nuevas/restauradas y tres instancias duplicadas extraídas. No se acredita todavía conciliación exhaustiva de Fase 0.

Compilación Python pasa. `git diff --check` estándar señala CRLF de los comentarios/docstring recién traducidos en dos archivos heredados; se comprobará por separado con reconocimiento explícito de CR al final de línea, sin modificar configuración Git. No se oculta este resultado ni se declara superado el análisis estándar.

**Plan de cambios inmediato:** extraer navegación/pegado y foco de cuadrículas en assets compartidos; sustituir los tres cierres extensos por adaptadores españoles; migrar cargadores y comprobaciones nominales en el mismo paso; añadir pruebas de teclado, selección, pegado, alcance de panel y limpieza. Conservar diferencias de recorte y orientación. Renombrar selectores propios con todos sus productores/consumidores en un paso coherente posterior. Revisar los tres agentes y ejecutar mediciones/suite al terminar. Tres de ocho bloques completos; fase abierta.

#### Continuación: eventos de captura, aislamiento y contratos de celda

**Implementación VERIFICADA.** Se retiran `equation_grid.js`, `matrix_capture.js` y `vector_capture.js`. Los tres adaptadores españoles son `captura_ecuaciones.js`, `captura_matrices.js` y `captura_vectores.js`; delegan en cinco assets por responsabilidad: coordenadas/selectores, teclado, pegado, foco y registro de eventos. El catálogo JSON puro `catalogo_captura.json` comparte su orden entre cabecera y auxiliares de pruebas. Todos los cargadores de los cuatro componentes migran simultáneamente. Los ocho assets nuevos cumplen límites; se conserva la diferencia entre recorte final de ecuaciones, `trim` matricial y separadores vectoriales, incluidos eje perpendicular y Enter.

El registro usa exclusivamente `window.scalaris`, sustituye cada adaptador sin duplicar manejadores, cancela su selección diferida y retira el resaltado. `pagehide` limpia recursos y `pageshow` restaura las configuraciones una sola vez. La selección conserva diez milisegundos y requiere entrada conectada y con foco; una navegación posterior cancela la anterior. Los identificadores de grupo se pasan por la API nativa `CSS.escape`.

**Contratos E3/E4 VERIFICADOS.** `data-row/col` pasa a `data-ecuaciones-fila/columna`; `data-matrix-id/row/col` a `data-matriz-identificador/fila/columna`; `cross-hl` a `cuadricula-resaltado-cruzado`. Se migran propiedades NiceGUI, animaciones, selector de errores geométricos, adaptadores, CSS y expectativas. Ya no aparecen los nombres retirados en producción; las muestras negativas nuevas los conservan solo como datos de prueba. Las propiedades comunes emiten una sola familia de coordenadas. `matrix-input`, el asset cuadrado y nombres Python heredados continúan pendientes, sin considerarlos contratos externos.

**Correcciones de robustez VERIFICADAS.** Dos pruebas nuevas fallaron con los assets originales: Enter en una matriz saltaba dos filas y pegado emitía dos eventos. Cada objetivo tiene ahora un adaptador responsable, evitando que el siguiente listener procese una entrada recién enfocada. La revisión encontró un fallo medio heredado adicional: el panel general de vectores emitía únicamente atributos matriciales y su adaptador lo ignoraba. Dos pruebas con propiedades NiceGUI reales reprodujeron `KeyError` por los atributos ausentes. `props_vector_accesible` conserva aria, nombre y coordenadas matriciales y añade grupo panel/nombre, índice y orientación. Los atributos geométricos específicos se siguen sobrescribiendo por posición de error. Las propiedades reales pasan por JSON al adaptador JavaScript y verifican Enter/pegado en ambos ejes, sin reinterpretar HTML. No se cambia aritmética.

**Revisión independiente VERIFICADA.** Los tres revisores aprobaron el refactor y la corrección vectorial de forma acotada. Regresiones comparó **435 escenarios** aislados contra HEAD; mantenibilidad verificó **130 predicados existentes** de estilos/controlador geométrico tras el mapa nominal. Se corrigieron dos bajos introducidos: propiedad interna inglesa del doble de pruebas, renombrada a `manejadoresPorEvento` sin alias, y lectura duplicada de catálogos, extraída a `_leer_scripts_catalogo`. Confirmados resueltos. Sin hallazgos nuevos pendientes del tramo. Se ejecutaron **42 casos nuevos Node**; junto a los 42 anteriores son **84**. Once casos Python nuevos cubren inyección, orden, atributos reales y el puente NiceGUI/JS. Las pruebas focalizadas de consumidores también pasan.

| Aserción antes | Después | Excepción e intención conservada |
|---|---|---|
| `.cross-hl {` y `cross-hl` en los tres assets | `.cuadricula-resaltado-cruzado {` y nombre español en adaptador más auxiliares | E2/E3/E4: mismas señales y predicados, con toda la lógica extraída incluida. |
| Ausencia de `filter: blur` y `style.background =` por archivo monolítico | Mismos predicados sobre catálogo completo y adaptador | E2: el auxiliar amplía la lectura al código extraído; no se restringe la aserción a una fachada vacía. |
| Selectores `data-row/col`, `data-matrix-id/row/col` | Coordenadas `data-ecuaciones-*` y `data-matriz-*` | E2/E3/E4: mismas coordenadas, selección de error y eventos, con productores migrados. |
| Fotogramas, duraciones 180/140, curva y pruebas de teclado/reducción | Mismas expectativas; solo nombre de atributos cambia | E2/E5: movimiento y espera conservados, sin animar la navegación. |

| Before | After | Why |
|---|---|---|
| Manejadores de ecuaciones y matrices procesaban el mismo Enter | Un adaptador procesa el objetivo original | Evitar saltos dobles de fila. |
| Dos manejadores pegaban el mismo texto y notificaban dos veces | Un evento `input` por celda existente | Evitar cambios repetidos y efectos duplicados. |
| Selecciones diferidas podían actuar después de perder foco/desmontar | Cancelación y comprobación de foco/conexión | Mantener el cursor del destino actual. |
| El panel general de vectores no emitía los atributos exigidos por su script | Productor y adaptador comparten las propiedades vectoriales | Activar teclado/pegado en las celdas reales. |

**Verificación vigente VERIFICADA.** Suite completa: **1316 pasadas, seis auditorías fallidas, 1322 recogidas**, una advertencia heredada de Starlette; las 84 pruebas Node pasan dentro de pytest. Sintaxis de **44 archivos JavaScript**, compilación Python y diff con reconocimiento explícito `cr-at-eol` pasan. El diff estándar sigue señalando CRLF en comentarios/docstring de dos archivos heredados; no se cambió la configuración Git. Ruff/mypy/pylint/radon/flake8/pyright no están instalados. Manifiesto **447 rutas**, **138 infracciones Python/archivos**; cero límites numéricos incumplidos en pruebas. JavaScript baja de 18 a **12 funciones incumplidoras**, entre 463 medidas; primer cierre pendiente: `geometria.js`.

Conservación sintáctica: **2908 aserciones**, 2720 iniciales, **191 nuevas/restauradas** y las mismas tres instancias duplicadas extraídas. La comparación por multiconjunto nominal antes de añadir los 23 predicados nuevos confirma que no apareció ninguna pérdida adicional; siguen los tres predicados comunes revisados. No acredita la conciliación histórica exhaustiva de Fase 0, todavía pendiente.

**Riesgos y pendientes.** El espía verifica que se invoca `CSS.escape` y se usa su retorno; ejecutar ese escape nativo en navegador queda NO PROBADO. No se acredita apariencia, zoom, móvil ni lector de pantalla. Se detectaron dos deudas funcionales heredadas del consumidor vectorial: tres llamadas a `build_container` inexistente (el componente actual expone `build(container)`) y el global inexistente `animateVectorDimensionRemoval`, cuyo fallo queda atrapado. Deben corregirse con pruebas del consumidor; no se declara operativa toda esa vista. Continúan seis auditorías y deuda de idioma/contratos/límites en todo `src`, sin excepciones añadidas. Tres de ocho bloques completos; plan temporal conservado hasta el cierre real, documentación permanente sin edición, sin commit/push/instalaciones. Pendientes de producto originales intactos.

#### Continuación: identidad compartida de inversas y consumidor vectorial

**Inversa VERIFICADA.** Las dos construcciones idénticas de identidad se extraen literalmente a `_construir_identidad(dimension)` en `inversa.py`. `_verificar_producto` pasa de complejidad 13 a **10**, con 32 líneas; el auxiliar tiene cuatro líneas y complejidad cuatro. Archivo y clase cumplen tamaños. Catorce casos nuevos fijan ambos órdenes por identidad de operandos, producto correcto/incorrecto, cinco productos falsos y los nueve campos completos de salida. Estos casos y trece existentes pasan antes y después: **27**. Los tres revisores aprueban la extracción; expandiendo ambas llamadas, el AST coincide con HEAD. Mantenibilidad confirma **49 aserciones existentes intactas**. E1 conserva comparación aproximada, matemática, mensajes y orden; contratos duales permanecen pendientes y no se declaran E4.

**Consumidor vectorial VERIFICADO.** Se sustituyen las tres llamadas a `build_container` inexistente por `build` con contenedor NiceGUI real. Dos pruebas nuevas reprodujeron `AttributeError` en suma/resta y escalar y verifican después inputs reales dentro del contenedor. No se añade código a la clase extensa: se reemplazan esas llamadas; modularización e idioma siguen pendientes. La tercera llamada usa el mismo método vigente en combinación lineal, pero no se acredita el montaje completo de la vista.

La reducción de dimensión deja de llamar al global inexistente y espera la API real de salida de celdas antes de purgar el caché y renderizar. `comun_animaciones_cliente.py` extrae íntegro el ejecutor compartido; las doce parametrizaciones originales y sus predicados se conservan. El caso nuevo verifica el estado antes de la salida, caché posterior, callbacks y ejecución del JavaScript emitido contra el asset real, con duración 140 ms.

**Hallazgo introducido corregido y VERIFICADO.** Los tres revisores reprodujeron que el primer selector por índice era global: podía dejar invisible la última celda de otro panel mediante `fill: forwards`. Se corrige al contenedor concreto usando `container.html_id`, API verificada en NiceGUI instalado que devuelve `c` más su ID numérico. No se interpolan etiquetas arbitrarias; la subclase geométrica conserva aislamiento pese a sobrescribir grupos. Dos regresiones nuevas montan dos paneles reales, para componente base y subclase geométrica, y llevan sus ubicaciones al asset. Antes daban animaciones **[0,0,1,0,0,1]** y después **[0,0,1,0,0,0]**. Se mantienen la dimensión ajena y limpieza mediante `finally`. El método queda en 30 líneas y complejidad 10.

**Revisión independiente VERIFICADA.** Los tres revisores confirmaron resuelto el hallazgo medio y aprobaron únicamente este tramo. Regresiones y seguridad no pudieron completar sus ejecuciones Python independientes y las detuvieron; no se cuentan como pases. Mantenibilidad reprodujo el aislamiento en VM. La ejecución principal completó **19 casos focalizados** y la suite completa posterior. Sin hallazgos nuevos pendientes en el tramo; no se declara operativa toda la vista ni concluida la auditoría.

| Aserción antes | Después | Excepción e intención conservada |
|---|---|---|
| Ejecutor local de doce casos de animaciones con validación de Node | Mismo ejecutor extraído a `comun_animaciones_cliente.py` | E2: mismo código, predicados, número de casos y resultado, reutilizado por el consumidor vectorial. |
| Verificaciones matriciales y clasificación de pasos existentes | Sin edición de pruebas existentes | E1/E2: 49 aserciones revisadas intactas; catorce casos nuevos caracterizan el diccionario completo. |

| Before | After | Why |
|---|---|---|
| Dos bloques vectoriales abortaban con `build_container` ausente | Montan celdas reales usando `build(container)` | Conectar el consumidor con la API existente, sin alias. |
| La reducción ejecutaba un global de animación inexistente | Espera la salida de la API compartida | Conservar orden de reducción y usar la política real de movimiento. |
| El selector introducido animaba también otros paneles | Selector limitado al contenedor numérico de NiceGUI | Evitar ocultar celdas ajenas conservadas en el DOM. |

**Estado vigente VERIFICADO.** Suite completa: **1335 pasadas, seis auditorías fallidas, 1341 recogidas**, una advertencia heredada de Starlette; 84 pruebas Node pasan dentro de pytest. Colección guardada. Compilación Python, sintaxis de los 44 archivos JS —incluida la nueva versión del ejecutor— y diff con reconocimiento explícito de CR al final de línea pasan. El resultado del diff estándar y las herramientas ausentes siguen declarados arriba; sin instalaciones ni cambios de configuración.

Manifiesto **451 rutas**; **137 infracciones Python/archivos**: cinco archivos, 16 clases, 27 funciones, 41 complejidades, 32 anidamientos y 16 firmas. **Cero límites numéricos incumplidos en pruebas**. JavaScript conserva 12 funciones incumplidoras, entre 469 medidas. Primer límite Python pendiente: `backend/solvers/linear_systems/gauss.py`, 445 líneas; primer cierre JS: `geometria.js`, 138. Los demás fallos siguen documentación/nombres de `Matrix`, banners de constantes y estilo embebido de Hub; no se excluyen rutas ni se añaden dispensas para ocultarlos.

Conservación sintáctica: **2929 aserciones**, 2720 iniciales, **212 nuevas/restauradas**, y tres instancias extraídas por la deduplicación histórica revisada de 400 controles efectivos. La comparación nominal ejecutada tras extraer el runner mantiene únicamente esos tres predicados menos. La conciliación exhaustiva de intención histórica de Fase 0 sigue pendiente, junto a la lista global de contratos externos y el informe final E1–E7.

**Continuación pendiente:** modularizar y traducir el consumidor vectorial, resolver callbacks `on_tab_change`/`clear_all` ausentes y revisar su inicialización mínima, sin inventar un pase del flujo completo; resolver Gauss heredado y los cierres JavaScript restantes. Consolidar los árboles de backend y sus contratos internos, terminar idioma/DRY/global, conciliar todas las intenciones de Fase 0 y completar verificación/revisión global. Tres de ocho bloques completos. El plan temporal se conserva hasta el cierre real; no se toca documentación permanente. Navegador y verificaciones visuales/accesibles siguen NO PROBADOS con sus pasos anteriores. Leontief y Transformaciones siguen fuera de navegación contextual y Hub; controlador de determinante sin consumidor. No commit/push, cambios de entorno ni dependencias.
