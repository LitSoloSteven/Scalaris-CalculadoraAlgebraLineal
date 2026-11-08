"""Aritmetica de la secante y el punto de cruce, sin tocar el motor."""
import math
import pytest

from src.backend.resolutores.raices.aritmetica_regla_falsa import (
    peso_escalado,
    punto_cruce,
)
from src.backend.resolutores.raices.errores_numericos import ErrorCapacidadNumerica


def test_peso_escalado_lineal():
    """Con f(a) = -1 y f(b) = 1 el peso es la mitad."""
    assert peso_escalado(-1.0, 1.0) == 0.5


def test_peso_escalado_rechaza_denominador_nulo():
    """f(a) = f(b) no permite secante."""
    with pytest.raises(ErrorCapacidadNumerica):
        peso_escalado(2.0, 2.0)


def test_peso_escalado_rechaza_no_finito():
    """Un cociente no finito se reporta como capacidad."""
    with pytest.raises(ErrorCapacidadNumerica):
        peso_escalado(float("inf"), float("inf"))


def test_punto_cruce_en_el_interior():
    """x^2 - 2 en [1, 2] produce c = 1 + 1/3."""
    cruce = punto_cruce(1.0, 2.0, -1.0, 2.0)
    assert math.isclose(cruce, 1.0 + 1.0 / 3.0, rel_tol=1e-12)


def test_punto_cruce_denominador_nulo():
    """f(a) = f(b) se reporta como capacidad, sin evaluar nada mas."""
    with pytest.raises(ErrorCapacidadNumerica):
        punto_cruce(0.0, 1.0, 3.0, 3.0)


def test_punto_cruce_coincide_con_extremo_por_redondeo():
    """Con pendiente extrema, la aproximacion se redondea al extremo inferior."""
    cruce = punto_cruce(1.0, 1e15, -1e-20, 1e15 - 1)
    assert cruce == 1.0