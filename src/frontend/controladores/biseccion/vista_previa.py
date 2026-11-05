"""Preparación acotada de una gráfica sin resolver ni validar criterios de parada."""
import math

from src.backend.resolutores.raices.limites_biseccion import LONGITUD_MAXIMA_EXPRESION
from .captura_criterio import real_capturado
from .muestreo import muestrear_funcion

RANGO_GRAFICA_DEFECTO = (-10, 10)
LONGITUD_CAMPO_GRAFICA = 64


def preparar_vista_previa(captura: dict) -> dict:
    """Devuelve entrada y muestras finitas, o un error orientativo de función/rango."""
    try:
        if not isinstance(captura, dict):
            raise ValueError("Revisa la función y el rango de la gráfica.")
        expresion = captura.get("expresion", "")
        if not isinstance(expresion, str) or len(expresion) > LONGITUD_MAXIMA_EXPRESION:
            raise ValueError("Escribe una función dentro de la longitud permitida.")
        inferior = _extremo(captura.get("x_min"), "El mínimo de la gráfica")
        superior = _extremo(captura.get("x_max"), "El máximo de la gráfica")
        if inferior >= superior:
            raise ValueError("El rango de la gráfica requiere mínimo < máximo.")
        entrada = {"expresion": expresion.replace("^", "**"),
                   "extremo_izquierdo": inferior, "extremo_derecho": superior}
        muestra = muestrear_funcion(entrada)
        return {"estado": "EXITO", "mensaje": _mensaje_muestra(muestra),
                "entrada": entrada, "muestra": muestra}
    except ValueError as error:
        return {"estado": "ERROR", "mensaje": str(error)}


def _extremo(valor, etiqueta: str) -> float:
    if isinstance(valor, str) and len(valor) > LONGITUD_CAMPO_GRAFICA:
        raise ValueError("Un extremo de la gráfica es demasiado largo; usa notación científica.")
    numero = real_capturado(valor, etiqueta)
    if not math.isfinite(numero):
        raise ValueError(f"{etiqueta} debe ser finito.")
    return numero


def _mensaje_muestra(muestra: dict) -> str:
    if all(valor is None for valor in muestra["y"]):
        return "No hay muestras reales representables en este rango. Revisa la función o cambia el rango."
    if muestra["huecos"]:
        return "Gráfica previa con huecos por evaluaciones inválidas o saltos pronunciados. Revisa el dominio."
    return "Gráfica previa disponible. El muestreo no certifica raíces ni continuidad."
