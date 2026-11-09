"""Salida copiable de los resultados y diagnósticos de regla falsa."""
from .diagnostico import detalles_diagnostico
from .presentacion import (
    aproximacion_presentada, avisos_resumen, etiqueta_aproximacion,
    metricas_resumen, titulo_estado,
)


def texto_copia_regla_falsa(respuesta: dict, decimales: int) -> str:
    """Compone la salida desde el sobre; propaga ValueError por precisión visual inválida."""
    aproximacion = aproximacion_presentada(respuesta, decimales)
    lineas = ["Regla falsa", titulo_estado(respuesta), etiqueta_aproximacion(respuesta)]
    if respuesta.get("aproximacion") is not None:
        lineas.append(aproximacion)
    lineas.append(respuesta["mensaje"])
    detalles = metricas_resumen(respuesta) + detalles_diagnostico(respuesta)
    lineas.extend(f"{etiqueta}: {valor}" for etiqueta, valor in detalles)
    lineas.extend(avisos_resumen(respuesta))
    return "\n".join(lineas)


def datos_copia_regla_falsa(respuesta: dict, decimales: int) -> dict[str, str]:
    """Entrega el campo de copia existente; los estados sin éxito se publican como resultado."""
    campo = "solucion" if respuesta["estado"] == "EXITO" else "matriz_resultado"
    return {campo: texto_copia_regla_falsa(respuesta, decimales)}
