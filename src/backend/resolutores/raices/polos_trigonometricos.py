"""Detección acotada de polos de tangente sin enumerar períodos ni evaluar funciones."""
import math
from fractions import Fraction

from .errores_numericos import ErrorSingularidad
from .unidades_angulares import validar_unidad_angular

_PERIODO_GRADOS = (Fraction(180), Fraction(180))
_PERIODO_RADIANES = (Fraction(math.pi), Fraction(math.nextafter(math.pi, math.inf)))
_MEDIO = Fraction(1, 2)


def comprobar_polos_tangente(rango: tuple[Fraction, Fraction], unidad: str) -> None:
    """Rechaza polos seguros con ErrorSingularidad; unidad inválida lanza ValueError."""
    validar_unidad_angular(unidad)
    periodos = _PERIODO_GRADOS if unidad == "grados" else _PERIODO_RADIANES
    inferior, superior = rango
    contiene_periodo = superior - inferior >= periodos[1]
    limite_inferior = max(inferior / periodo for periodo in periodos)
    limite_superior = min(superior / periodo for periodo in periodos)
    contiene_polo = math.ceil(limite_inferior - _MEDIO) <= math.floor(limite_superior - _MEDIO)
    if contiene_periodo or contiene_polo:
        raise ErrorSingularidad(
            "La tangente tiene un polo en el rango de su argumento afín dentro del intervalo. "
            "Elige un intervalo que no atraviese esa singularidad.")
