"""Resolución real y muestreo orientativo separados del sobre matemático."""
from src.frontend.controladores.muestreo_raices import muestrear_funcion
from .ejecucion_ampliada import resolver_presentacion


def calcular_presentacion(captura: dict) -> dict:
    """Devuelve resultado y curva orientativa sin alterar el contrato ni los estados del motor."""
    return agregar_grafica(resolver_presentacion(captura))


def agregar_grafica(datos: dict) -> dict:
    """Muestrea un resultado ya calculado sin repetir sus iteraciones ni certificar continuidad."""
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
