"""Estimación de filas estrictas en potencias de dos y rangos extremos."""
import math
from dataclasses import asdict

import pytest

from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada
from src.backend.resolutores.raices.estimacion_biseccion import estimar_iteraciones


def _entrada(criterio, intervalo=(0.0, 1.0), limite=100):
    return EntradaBiseccion("x", *intervalo, 4, limite, criterio=CriterioParada(*criterio))


@pytest.mark.parametrize("ancho,filas", [
    (math.nextafter(1.0, 0.0), 4), (1.0, 5), (math.nextafter(1.0, math.inf), 5),
    (.0625, 1), (.125, 2), (.25, 3),
])
def test_comparacion_estricta_en_potencia_de_dos(ancho, filas):
    """No adelanta una fila al igualar el umbral ni al rodear una potencia exacta."""
    estimacion = estimar_iteraciones(_entrada(("ancho", .125), (0, ancho)))
    assert estimacion.filas_previstas == filas
    assert not estimacion.supera_limite
    assert "ceros evaluados" in estimacion.advertencias[0]


@pytest.mark.parametrize("criterio", [("ancho", .01), ("decimales", 2)])
def test_estimacion_decimal_y_absoluta_coinciden(criterio):
    """El intervalo unitario prevé ocho filas para ambas condiciones equivalentes."""
    assert estimar_iteraciones(_entrada(criterio)).filas_previstas == 8


def test_cociente_extremo_no_necesita_logaritmo_flotante():
    """Un cociente ideal de 2 elevado a 2000 no desborda al estimar."""
    entrada = _entrada(("ancho", math.ldexp(1, -1000)), (0, math.ldexp(1, 1000)))
    estimacion = estimar_iteraciones(entrada)
    assert estimacion.filas_previstas == 2002
    assert estimacion.supera_limite
    assert "superan" in estimacion.advertencias[-1]


def test_tolerancia_subnormal_y_ancho_pequeno():
    """El menor umbral representable conserva la igualdad estricta sin redondearse a cero."""
    minimo = math.ulp(0.0)
    estimacion = estimar_iteraciones(_entrada(("ancho", minimo), (0, minimo * 4)))
    assert estimacion.filas_previstas == 4


@pytest.mark.parametrize("tipo", ["relativo", "residuo"])
def test_no_inventa_estimacion_para_criterios_no_geometricos(tipo):
    """El ancho inicial no predice una secuencia general de residuos ni errores relativos."""
    estimacion = estimar_iteraciones(_entrada((tipo, .01)))
    assert asdict(estimacion)["filas_previstas"] is None
    assert not estimacion.supera_limite


def test_conteo_fijo_muestra_n_y_puede_terminar_antes():
    """La predicción fija conserva el aviso sobre salidas excepcionales."""
    estimacion = estimar_iteraciones(_entrada(("iteraciones", 10), limite=10))
    assert estimacion.filas_previstas == 10
    assert not estimacion.supera_limite
    assert estimacion.advertencias


def test_rechaza_ancho_no_representable_como_el_motor():
    """La predicción no promete ejecución de un intervalo que el motor rechaza."""
    with pytest.raises(ValueError, match="ancho"):
        estimar_iteraciones(_entrada(("ancho", .01), (-1e308, 1e308)))


def test_entrada_antigua_y_entrada_directa_invalida():
    """La estimación revalida datos directos y deriva el criterio decimal antiguo."""
    assert estimar_iteraciones(EntradaBiseccion("x", 1, 2, 2)).filas_previstas == 8
    with pytest.raises(ValueError):
        estimar_iteraciones(_entrada(("iteraciones", 101)))
    with pytest.raises(ValueError):
        estimar_iteraciones(None)
