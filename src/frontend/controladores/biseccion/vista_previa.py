"""Preparación acotada de una gráfica sin resolver ni validar criterios de parada."""
from src.backend.resolutores.raices.limites_biseccion import LONGITUD_MAXIMA_EXPRESION
from src.backend.resolutores.raices.normalizacion_funcion import normalizar_expresion
from src.backend.resolutores.raices.unidades_angulares import opciones_unidad
from src.frontend.controladores.rango_exploracion_raices import (
    LONGITUD_CAMPO_GRAFICA, RANGO_GRAFICA_DEFECTO, rango_grafica,
)
from .muestreo import muestrear_funcion


def preparar_vista_previa(captura: dict) -> dict:
    """Devuelve entrada y muestras finitas, o un error orientativo de función/rango."""
    try:
        if not isinstance(captura, dict):
            raise ValueError("Revisa la función y el rango de la gráfica.")
        expresion = captura.get("expresion", "")
        if not isinstance(expresion, str) or len(expresion) > LONGITUD_MAXIMA_EXPRESION:
            raise ValueError("Escribe una función dentro de la longitud permitida.")
        inferior, superior = rango_grafica(captura)
        entrada = {"expresion": normalizar_expresion(expresion),
                   "extremo_izquierdo": inferior, "extremo_derecho": superior,
                   **opciones_unidad(captura.get("unidad_angular", "radianes"))}
        muestra = muestrear_funcion(entrada)
        return {"estado": "EXITO", "mensaje": _mensaje_muestra(muestra),
                "entrada": entrada, "muestra": muestra}
    except ValueError as error:
        return {"estado": "ERROR", "mensaje": str(error)}


def _mensaje_muestra(muestra: dict) -> str:
    if all(valor is None for valor in muestra["y"]):
        return "No hay muestras reales representables en este rango. Revisa la función o cambia el rango."
    if muestra["huecos"]:
        return "Gráfica previa con huecos por evaluaciones inválidas o saltos pronunciados. Revisa el dominio."
    return "Gráfica previa disponible. El muestreo no certifica raíces ni continuidad."
