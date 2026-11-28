"""Conversión del rango visual compartido por herramientas de raíces."""
import math

from src.frontend.controladores.raices.compartido.formato.captura_real import real_capturado

RANGO_GRAFICA_DEFECTO = (-10, 10)
LONGITUD_CAMPO_GRAFICA = 64
_MENSAJE_RANGO_INVALIDO = (
    "El rango visible no se puede representar. Restablece la vista o acerca el encuadre."
)


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


def rango_evento_distinto(datos: object, captura: dict) -> tuple[float, float] | None:
    """Entrega solo encuadres válidos diferentes del rango capturado para evitar realimentación."""
    nuevo = rango_evento(datos)
    if nuevo is None:
        return None
    try:
        return None if nuevo == rango_grafica(captura) else nuevo
    except ValueError:
        return nuevo


def interpretar_relayout_x(
    datos: object,
    rango_base: tuple[float, float] = RANGO_GRAFICA_DEFECTO,
) -> dict | None:
    """Interpreta cambios de encuadre del eje X en plotly_relayout sin alterar la entrada."""
    if not isinstance(datos, dict):
        return None
    if datos.get("xaxis.autorange") is True:
        return {"tipo": "restablecer", "rango": tuple(rango_base)}
    par = _par_relayout_x(datos)
    if par is None:
        return None
    try:
        inferior, superior = rango_grafica({"x_min": par[0], "x_max": par[1]})
    except ValueError:
        return {"tipo": "invalido", "mensaje": _MENSAJE_RANGO_INVALIDO}
    if not math.isfinite(superior - inferior):
        return {"tipo": "invalido", "mensaje": _MENSAJE_RANGO_INVALIDO}
    return {"tipo": "rango", "rango": (inferior, superior)}


def _par_relayout_x(datos: dict) -> tuple | list | None:
    if "xaxis.range" in datos:
        par = datos["xaxis.range"]
        return par if isinstance(par, (tuple, list)) and len(par) == 2 else (None, None)
    if "xaxis.range[0]" in datos and "xaxis.range[1]" in datos:
        return (datos["xaxis.range[0]"], datos["xaxis.range[1]"])
    return None
