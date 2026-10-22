"""Compatibilidad de las huellas históricas para entradas estructuradas y exactas."""
from fractions import Fraction

import pytest

from src.ai.huellas import calcular_huella, esta_desactualizado


@pytest.mark.parametrize("entrada, esperada", [
    (None, "2be88ca4242c76e8253ac62474851065032d6833"),
    (0, "b6589fc6ab0dc82cf12099d1c2d40ab994e8410c"),
    ({"A": Fraction(1, 1001)}, "03f8127cccc4601f51e8c39fa64834bf31ac3c87"),
    ({(0, 1): "1/1001"}, "45395f4881be8559c48106d10add27d18ef41745"),
    ({"a": [1, 2, 3], "b": {"x": "a"}}, "585cf88dad58ab3c502b015a9eb20c617fda7908"),
    (["á", True, None], "421b418d2d97d35c4ecfd42a02b58996ea7c8c24"),
])
def test_huella_conserva_valor_historico(entrada, esperada):
    """La entrada produce exactamente la huella registrada antes de la extracción."""
    assert calcular_huella(entrada) == esperada


def test_huella_normaliza_tuplas_sin_mutar_entrada():
    """Las tuplas y listas equivalentes comparten huella y mantienen sus datos originales."""
    entrada = {"A": {(0, 1): (Fraction(1, 1001), 2)}}
    equivalente = {"A": {"(0, 1)": [Fraction(1, 1001), 2]}}
    assert calcular_huella(entrada) == calcular_huella(equivalente)
    assert entrada == {"A": {(0, 1): (Fraction(1, 1001), 2)}}


def test_ausencia_de_huella_no_normaliza_entrada():
    """Sin un resultado previo no se necesita serializar la entrada."""
    class EntradaSinRepresentacion:
        """Entrada cuya conversión textual permite detectar una serialización indebida."""

        def __str__(self):
            raise AssertionError("No se debe serializar una entrada sin huella previa")

    assert esta_desactualizado(EntradaSinRepresentacion(), None) is False
