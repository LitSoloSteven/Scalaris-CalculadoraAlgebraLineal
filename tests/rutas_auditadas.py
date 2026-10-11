"""Catálogo de rutas incluidas en la auditoría de reglas."""
from pathlib import Path
from tests.comun import RAIZ


def _rutas(prefijo: str, nombres: str) -> list[Path]:
    return [RAIZ / prefijo / f'{nombre}.py' for nombre in nombres.split()]


RUTAS_AUDITADAS = _rutas('src/backend', 'constantes excepciones')
RUTAS_AUDITADAS += _rutas('src/backend/modelos', 'matriz')
RUTAS_AUDITADAS += _rutas('src/backend/utilidades',
    'analizadores formateadores utilidades_matematicas validadores verificacion reglas_dominio')
RUTAS_AUDITADAS += _rutas('src/backend/resolutores', '__init__ trazado')
RUTAS_AUDITADAS += _rutas('src/backend/resolutores/sistemas_lineales',
    '__init__ modelo_solucion analisis_rouche sustitucion gauss gauss_jordan')
RUTAS_AUDITADAS += _rutas('src/backend/resolutores/operaciones_matrices',
    '__init__ formateadores operaciones determinante inversa evaluador analizador_expresiones transformaciones leontief')
RUTAS_AUDITADAS += _rutas('src/backend/resolutores/operaciones_vectores',
    '__init__ base formateadores operaciones planteamiento combinacion_lineal')
RUTAS_AUDITADAS += _rutas('src/backend/resolutores/sistemas_numericos',
    '__init__ conversor_bases calculadora_romana')
RUTAS_AUDITADAS += _rutas('src/ai',
    'constantes context estrategias_recorte clasificador_respuestas openrouter_ai prompts')
RUTAS_AUDITADAS += _rutas('src', 'main')
RUTAS_AUDITADAS += _rutas('src/frontend',
    'app routes flags helpers suggestions catalogo_sugerencias theme constantes textos')
RUTAS_AUDITADAS += _rutas('src/frontend/navigation', '__init__ modelo catalogo consultas redirecciones')

RUTAS_AUDITADAS += [RAIZ / 'src/frontend/assets/css' / f'{nombre}.css' for nombre in (
    'tokens', 'base', 'layout', 'componentes_entradas', 'componentes_controles', 'vistas_navegacion',
    'vistas_hub_matriz', 'vistas_hub_popovers', 'vistas_hub_adaptable', 'vistas_glosa_dock',
    'vistas_glosa_componentes', 'vistas_inversa', 'movimiento', 'reproductor_pasos',
)]
RUTAS_AUDITADAS += [RAIZ / 'src/frontend/assets/js' / f'{nombre}.js' for nombre in (
    'app', 'calculadora', 'cuadricula_compartida', 'equation_grid', 'geometria', 'glosa_dock',
    'hub', 'hub_recientes', 'layout_sync', 'mathjax_config', 'matrix_capture', 'recoleccion_basura',
    'reproductor_pasos', 'splash', 'square_matrix', 'theme', 'vector_capture',
)]
RUTAS_AUDITADAS += _rutas('src/backend/geometria', '__init__ clasificacion recorte planos conjunto_solucion')
RUTAS_AUDITADAS += _rutas('src/frontend/controladores',
    '__init__ utilidades clasificador_pasos agrupador_pasos manejadores_pasos')
RUTAS_AUDITADAS += _rutas('src/frontend/controladores/sistemas_lineales',
    '__init__ compartido flujo_comun controlador_gauss controlador_gauss_jordan')
RUTAS_AUDITADAS += _rutas('src/frontend/controladores/operaciones_matrices',
    '__init__ codificador controlador_operaciones_matrices controlador_leontief controlador_transformaciones controlador_determinante')
RUTAS_AUDITADAS += _rutas('src/frontend/controladores/operaciones_vectores',
    '__init__ controlador_operaciones_vectores')
RUTAS_AUDITADAS += _rutas('src/frontend/controladores/operaciones_inversas',
    '__init__ foco_paso validador_inversa controlador_operaciones_inversas')
RUTAS_AUDITADAS += _rutas('src/frontend/controladores/geometria',
    '__init__ utilidades controlador_rectas_planos controlador_vectores controlador_combinacion controlador_geometria')
RUTAS_AUDITADAS += _rutas('src/frontend/componentes',
    '__init__ ai_panel ai_panel_legacy app_shell calculator cuadricula_base equation_grid exportador_ecuaciones '
    'glosa_bitacora glosa_cabecera glosa_chips glosa_dock glosa_envio glosa_foco glosa_pie glosa_render handoff icons matrix_capture navbar')
RUTAS_AUDITADAS += _rutas('src/frontend/componentes/reproductor_pasos',
    '__init__ catalogo controles cuerpos html_tablas indice modelo reproductor vista')
RUTAS_AUDITADAS += _rutas('src/frontend/componentes', 'square_matrix_panel tareas theme_switcher vector_capture')
RUTAS_AUDITADAS += sorted((RAIZ / 'src/frontend/vistas/geometria').glob('*.py'))
RUTAS_AUDITADAS += _rutas('src/backend/geometria', 'muestreo transferencia')
RUTAS_AUDITADAS += _rutas('src/frontend/controladores/geometria', 'captura')
RUTAS_AUDITADAS += [RAIZ / 'src/frontend/assets/css/vistas_geometria.css']
