"""Resolución real y muestreo orientativo separados del sobre matemático."""
from src.frontend.controladores.muestreo_raices import muestrear_funcion
from .controlador import resolver_captura
from .ejecucion_ampliada import resolver_presentacion


def calcular_presentacion(captura: dict) -> dict:
    """Devuelve resultado y curva orientativa sin alterar el contrato ni los estados del motor."""
    datos = resolver_presentacion(captura)
    respuesta = datos["resultado"]
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
    return {**datos, "muestra": muestra, "aviso_grafica": aviso}
