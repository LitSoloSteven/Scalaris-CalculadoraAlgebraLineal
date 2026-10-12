"""Traslado de constantes izquierdas y rechazo de variables derechas."""
from fractions import Fraction

from src.backend.utils.parsers import SystemParser


def test_constante_izquierda_se_traslada():
    """La constante izquierda se resta del término independiente derecho."""
    entrada = "2x + 5 = 10"
    valido, matriz, variables, mensaje = SystemParser.parse_system(entrada)
    assert valido, mensaje
    assert variables == ["x"]
    assert matriz.get(0, 0) == Fraction(2)
    assert matriz.get(0, 1) == Fraction(5)


def test_varias_constantes_izquierdas_se_suman():
    """Las constantes izquierdas se acumulan antes de trasladarse."""
    entrada = "x + 1 + 2 = 10"
    valido, matriz, _, mensaje = SystemParser.parse_system(entrada)
    assert valido, mensaje
    assert matriz.get(0, 0) == Fraction(1)
    assert matriz.get(0, 1) == Fraction(7)


def test_constante_negativa_izquierda_se_traslada():
    """Una constante negativa izquierda aumenta el término derecho."""
    entrada = "x - 3 = 5"
    valido, matriz, _, mensaje = SystemParser.parse_system(entrada)
    assert valido, mensaje
    assert matriz.get(0, 0) == Fraction(1)
    assert matriz.get(0, 1) == Fraction(8)


def test_variable_derecha_rechazada():
    """El analizador rechaza las variables a la derecha de la igualdad."""
    entrada = "2x + 3 = x + 5"
    valido, _, _, mensaje = SystemParser.parse_system(entrada)
    assert not valido
