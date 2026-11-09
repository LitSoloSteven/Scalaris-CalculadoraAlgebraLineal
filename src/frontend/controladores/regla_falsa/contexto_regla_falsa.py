"""Resumen independiente del resultado para el contexto pedagógico."""
from copy import deepcopy

from .presentacion import etiqueta_aproximacion, titulo_estado


def resumir_contexto_regla_falsa(respuesta: dict | None) -> dict | None:
    """Copia el sobre sin el historial completo y conserva solo la última fila válida para Glosa."""
    if respuesta is None:
        return None
    resumen = deepcopy({campo: valor for campo, valor in respuesta.items() if campo != "iteraciones"})
    resumen.update(titulo_estado=titulo_estado(respuesta),
                   etiqueta_aproximacion=etiqueta_aproximacion(respuesta),
                   total_iteraciones=respuesta["iteraciones_totales"])
    filas = respuesta["iteraciones"]
    if filas:
        resumen["ultima_fila_valida"] = deepcopy(filas[-1])
    return resumen
