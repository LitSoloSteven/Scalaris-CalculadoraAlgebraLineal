"""Resolución real y muestreo orientativo separados del sobre matemático."""
from src.frontend.controladores.biseccion.muestreo import muestrear_funcion
from .controlador import resolver_captura


def calcular_presentacion(captura: dict) -> dict:
    """Devuelve resultado y curva orientativa sin alterar el contrato ni los estados del motor."""
    respuesta = resolver_captura(captura)
    muestra, aviso = None, ""
    if respuesta["estado"] == "ERROR":
        aviso = "No se muestrea la función tras un error. Solo se muestran las evaluaciones válidas registradas."
    else:
        try:
            muestra = muestrear_funcion(respuesta["entrada"])
            if muestra["huecos"]:
                aviso = "El muestreo contiene huecos por evaluaciones inválidas o saltos pronunciados."
        except (ValueError, TypeError, OverflowError, ZeroDivisionError, RecursionError):
            aviso = "No se pudo muestrear la curva. Se conservan el resultado y las evaluaciones del motor."
    return {"resultado": respuesta, "muestra": muestra, "aviso_grafica": aviso}
