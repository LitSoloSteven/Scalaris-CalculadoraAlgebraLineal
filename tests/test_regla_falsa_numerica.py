"""Pruebas numericas del motor de regla falsa (regresion de capacidad)."""
import pytest

from src.backend.resolutores.raices.aritmetica_regla_falsa import (
    peso_escalado,
    punto_cruce,
)
from src.backend.resolutores.raices.errores_numericos import ErrorCapacidadNumerica


def test_peso_escalado_normaliza_magnitudes_opuestas():
    """Regresion del bug: -1e308 / 1e308 no desborda; el peso debe ser 0.5."""
    assert peso_escalado(-1e308, 1e308) == 0.5


def test_peso_escalado_magnitudes_grandes_asimetricas():
    """Con magnitudes grandes distintas, t coincide con la formula exacta."""
    esperado = 1.0 / 1.3
    assert abs(peso_escalado(-1e308, 3e307) - esperado) < 1e-15


def test_peso_escalado_rechaza_ambos_cero():
    """Ambos extremos en cero no admiten interpolacion."""
    with pytest.raises(ErrorCapacidadNumerica) as info:
        peso_escalado(0.0, 0.0)
    assert getattr(info.value, "codigo", None) == "INTERPOLACION_NO_REPRESENTABLE"


@pytest.mark.parametrize("valor", [float("inf"), float("-inf"), float("nan")])
def test_peso_escalado_rechaza_escala_no_finita(valor):
    """Una escala NaN o infinita no es representable."""
    with pytest.raises(ErrorCapacidadNumerica) as info:
        peso_escalado(valor, 1.0)
    assert getattr(info.value, "codigo", None) == "INTERPOLACION_NO_REPRESENTABLE"


def test_punto_cruce_magnitudes_grandes_da_cero():
    """Combinacion convexa: c=0 con extremos -1e308 y 1e308."""
    assert punto_cruce(-1.0, 1.0, -1e308, 1e308) == 0.0


def test_punto_cruce_intervalo_asimetrico_mantiene_c_en_rango():
    """Con [0, 2] y magnitudes opuestas, c se mantiene en el intervalo."""
    c = punto_cruce(0.0, 2.0, -1e308, 1e308)
    assert 0.0 <= c <= 2.0
    assert abs(c - 1.0) < 1e-15


def test_punto_cruce_ancho_no_representable():
    """Intervalo -1e308 a 1e308 no tiene ancho representable."""
    with pytest.raises(ErrorCapacidadNumerica) as info:
        punto_cruce(-1e308, 1e308, -1.0, 1.0)
    assert getattr(info.value, "codigo", None) == "ANCHO_NO_REPRESENTABLE"