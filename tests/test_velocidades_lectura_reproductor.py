"""Intervalos y preferencias de velocidad del reproductor didáctico."""
import pytest

from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.catalogo import (
    MULTIPLICADORES_LECTURA,
    intervalo_lectura,
)


@pytest.mark.parametrize("velocidad,esperados", [
    ("Lenta", (4.0, 9.0, 15.0)),
    ("Normal", (2.4, 5.4, 9.0)),
    ("Rápida", (1.4, 3.15, 5.25)),
])
@pytest.mark.parametrize("longitud,indice", [(0, 0), (100, 1), (10000, 2)])
def test_intervalos_por_velocidad_y_limites(velocidad, esperados, longitud, indice):
    """Comprueba cada velocidad con base mínima, proporcional y máxima."""
    assert intervalo_lectura("a" * longitud, velocidad) == pytest.approx(esperados[indice])


@pytest.mark.parametrize("longitud,esperado", [
    (9, 1.4), (10, 1.4175), (209, 5.24825), (210, 5.25),
])
def test_rapida_en_las_fronteras_del_acotado(longitud, esperado):
    """El mínimo y el máximo se aplican a la base antes del multiplicador rápido."""
    assert intervalo_lectura("a" * longitud, "Rápida") == pytest.approx(esperado)


@pytest.mark.parametrize("longitud,esperado", [(0, 2.4), (100, 5.4), (10000, 9.0)])
def test_velocidad_desconocida_tiene_los_intervalos_normales(longitud, esperado):
    """Una etiqueta desconocida usa Normal incluso cuando la base llega a sus límites."""
    assert intervalo_lectura("a" * longitud, "desconocida") == pytest.approx(esperado)


def test_orden_del_selector_y_velocidad_predeterminada():
    """El catálogo conserva el orden del selector y las instancias comienzan en Normal."""
    reproductor = ReproductorPasos((), (), lambda paso, destino: None, "velocidades")
    assert list(MULTIPLICADORES_LECTURA) == ["Lenta", "Normal", "Rápida"]
    assert reproductor.velocidad == "Normal"
