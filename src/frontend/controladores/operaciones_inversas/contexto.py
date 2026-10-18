"""Preparacion del contexto y senales de la captura de matriz inversa."""
from src.ai.contexto import (
    ContextoIA, EstadoContexto, describir_matriz, generar_nota_ventana, sanear_cadena_usuario,
)
from src.ai.huellas import esta_desactualizado
from src.backend.constantes import DIMENSION_MAXIMA_CONTEXTO_INVERSA
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from src.frontend.sugerencias import Senales, primera_celda_invalida


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
    datos = panel.obtener_datos_matriz()
    descripcion = describir_matriz([[sanear_cadena_usuario(valor or '', 32) for valor in fila] for fila in datos])
    contexto = ContextoIA(herramienta='inversa', vista='Matriz inversa', etiqueta=f'A ({panel.dimension}×{panel.dimension})', entrada={'A': descripcion})
    contexto.nota_ventana = generar_nota_ventana(descripcion)
    contexto.desactualizado = esta_desactualizado({'datos': datos}, getattr(vista, '_huella_resultado', None))
    if not contexto.desactualizado:
        contexto.resultado = preparar_resultado_contexto(vista.ultimo_resultado, panel.dimension)
    return contexto


def obtener_senales_inversa(vista) -> Senales:
    """Devuelve coordenadas invalidas y el estado del resultado que sigue vigente."""
    datos = vista.panel_matriz_cuadrada.obtener_datos_matriz()
    elementos = [(f'A[{fila+1},{columna+1}]', valor, (fila, columna))
                 for fila, valores in enumerate(datos) for columna, valor in enumerate(valores)]
    invalida = primera_celda_invalida(elementos)
    resultado = getattr(vista, 'ultimo_resultado', None)
    estado = 'sin_resultado'
    if resultado and not obtener_contexto_inversa(vista).desactualizado:
        estado = {'EXITO': 'exito', 'SINGULAR': 'singular'}.get(resultado.get('estado'), estado)
    return Senales(herramienta='inversa', estado=estado, invalida=invalida)
