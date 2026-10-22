"""Preparacion del contexto y senales de la captura de matriz inversa."""
from copy import deepcopy
from src.ai.contexto import (
    ContextoIA, EstadoContexto, describir_matriz, generar_nota_ventana,
)
from .captura_contexto import describir_captura, localizar_invalida
from src.backend.constantes import DIMENSION_MAXIMA_CONTEXTO_INVERSA
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from src.frontend.sugerencias import Senales


def preparar_resultado_contexto(resultado: dict | None, dimension: int) -> dict | None:
    """Serializa el resultado vigente sin incluir matrices fuera de la ventana de IA."""
    if not resultado:
        return None
    estado = resultado.get('estado')
    if estado == 'SINGULAR':
        return {'estado': 'SINGULAR', 'mensaje': 'Matriz singular (det = 0).'}
    if estado != 'EXITO':
        return {'estado': 'ERROR'}
    datos = {'estado': 'EXITO', 'determinante': resultado.get('determinante_texto'),
             'pasos_totales': resultado.get('estadisticas', {}).get('total', 0)}
    inversa = resultado.get('inversa')
    if dimension <= DIMENSION_MAXIMA_CONTEXTO_INVERSA and inversa:
        datos['inversa'] = describir_matriz([[formatear_fraccion_texto(valor) for valor in fila] for fila in inversa.datos])
    else:
        datos['inversa_omitida'] = True
    return datos


def obtener_contexto_inversa(vista) -> ContextoIA:
    """Construye el contexto de Glosa omitiendo cualquier resultado desactualizado."""
    panel = vista.panel_matriz_cuadrada
    if panel.esta_vacio():
        return ContextoIA(herramienta='inversa', vista='Matriz inversa', etiqueta='Matriz A', entrada={}, estado=EstadoContexto(vacio=True))
    descripcion, huella = describir_captura(vista)
    descripcion = deepcopy(descripcion)
    contexto = ContextoIA(herramienta='inversa', vista='Matriz inversa', etiqueta=f'A ({panel.dimension}×{panel.dimension})', entrada={'A': descripcion})
    contexto.nota_ventana = generar_nota_ventana(descripcion)
    huella_resultado = getattr(vista, '_huella_resultado', None)
    contexto.desactualizado = huella_resultado is not None and huella != huella_resultado
    if not contexto.desactualizado:
        contexto.resultado = preparar_resultado_contexto(vista.ultimo_resultado, panel.dimension)
    return contexto


def obtener_senales_inversa(vista) -> Senales:
    """Devuelve coordenadas invalidas y el estado del resultado que sigue vigente."""
    invalida = deepcopy(localizar_invalida(vista))
    resultado = getattr(vista, 'ultimo_resultado', None)
    estado = 'sin_resultado'
    if resultado and not obtener_contexto_inversa(vista).desactualizado:
        estado = {'EXITO': 'exito', 'SINGULAR': 'singular'}.get(resultado.get('estado'), estado)
    return Senales(herramienta='inversa', estado=estado, invalida=invalida)
