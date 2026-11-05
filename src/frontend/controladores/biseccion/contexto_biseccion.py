"""Resumen acotado de bisección para el contexto pedagógico."""
from .presentacion_criterio import etiqueta_aproximacion, titulo_estado

_CAMPOS_RESULTADO = (
    "estado", "mensaje", "aproximacion", "intervalo_final", "tolerancia", "cota", "motivo_parada", "metricas",
    "criterio_solicitado", "unidad_criterio", "umbral", "metrica_final", "codigo_diagnostico", "advertencias",
    "diagnostico", "aviso_grafica", "contexto_fallo", "sugerencias", "unidad_angular",
)
_CAMPOS_FILA = ("i", "c", "f_c", "signo_producto", "accion", "motivo_parada")


def resumir_contexto_biseccion(respuesta: dict | None) -> dict | None:
    """Conserva el estado, el cierre y solo la última fila válida para Glosa."""
    if respuesta is None:
        return None
    filas = respuesta.get("iteraciones", ())
    resumen = {clave: respuesta.get(clave) for clave in _CAMPOS_RESULTADO}
    resumen["titulo_estado"] = titulo_estado(respuesta)
    resumen["etiqueta_aproximacion"] = etiqueta_aproximacion(respuesta)
    resumen["total_iteraciones"] = len(filas)
    if filas:
        ultima = filas[-1]
        resumen["ultima_fila_valida"] = {**{clave: ultima.get(clave) for clave in _CAMPOS_FILA},
                                        "a": ultima.get("extremo_izquierdo"), "b": ultima.get("extremo_derecho")}
    return resumen
