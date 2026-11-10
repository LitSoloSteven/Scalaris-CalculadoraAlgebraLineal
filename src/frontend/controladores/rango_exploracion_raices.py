"""Conversión del rango visual compartido por herramientas de raíces."""
import math

from src.frontend.controladores.captura_real import real_capturado

RANGO_GRAFICA_DEFECTO = (-10, 10)
LONGITUD_CAMPO_GRAFICA = 64


def rango_grafica(captura: dict) -> tuple[float, float]:
    """Devuelve extremos finitos ascendentes; propaga ValueError orientativo."""
    inferior = _extremo(captura.get("x_min"), "El mínimo de la gráfica")
    superior = _extremo(captura.get("x_max"), "El máximo de la gráfica")
    if inferior >= superior:
        raise ValueError("El rango de la gráfica requiere mínimo < máximo.")
    return inferior, superior


def _extremo(valor, etiqueta: str) -> float:
    if isinstance(valor, str) and len(valor) > LONGITUD_CAMPO_GRAFICA:
        raise ValueError("Un extremo de la gráfica es demasiado largo; usa notación científica.")
    numero = real_capturado(valor, etiqueta)
    if not math.isfinite(numero):
        raise ValueError(f"{etiqueta} debe ser finito.")
    return numero


def rango_evento(datos: object) -> tuple[float, float] | None:
    """Valida un encuadre nativo de Plotly y descarta eventos ajenos a límites finitos."""
    if not isinstance(datos, dict):
        return None
    if datos.get("xaxis.autorange") is True:
        return RANGO_GRAFICA_DEFECTO
    par = datos.get("xaxis.range") or (datos.get("xaxis.range[0]"), datos.get("xaxis.range[1]"))
    if not isinstance(par, (tuple, list)) or len(par) != 2:
        return None
    try:
        return rango_grafica({"x_min": par[0], "x_max": par[1]})
    except ValueError:
        return None
