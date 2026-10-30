"""Tiempo de lectura proporcional y límites de cada velocidad."""
import pytest

from src.frontend.componentes.reproductor_pasos.catalogo import intervalo_lectura


@pytest.mark.parametrize("velocidad,multiplicador", [("Lenta", 1.6), ("Normal", 1), ("Rápida", 0.6)])
@pytest.mark.parametrize("texto,base", [("", 4), ("a", 4), ("a" * 100, 9), ("a" * 10000, 15)])
def test_intervalo_acota_antes_de_aplicar_velocidad(texto, base, velocidad, multiplicador):
    """Comprueba mínimo, lectura proporcional y máximo para las tres velocidades."""
    assert intervalo_lectura(texto, velocidad) == pytest.approx(base * multiplicador)


def test_velocidad_desconocida_usa_normal():
    """Una preferencia no reconocida conserva el ritmo normal."""
    assert intervalo_lectura("a" * 100, "desconocida") == 9
