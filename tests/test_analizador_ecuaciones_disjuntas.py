"""Validación permisiva y estricta de ecuaciones con variables disjuntas."""
from fractions import Fraction
from src.backend.utilidades.analizadores import AnalizadorSistema
from tests.comun_analizador import comprobar_sistema_dos_variables


def test_ecuaciones_disjuntas_se_aceptan_por_defecto():
    """Dos ecuaciones independientes conservan variables y matriz aumentada."""
    texto = "x1 = 1\nx2 = 2"
    valido, matriz, variables, mensaje = AnalizadorSistema.parsear_sistema(texto)
    assert valido, mensaje
    assert variables == ["x1", "x2"]
    assert matriz.filas == 2
    assert matriz.columnas == 3
    assert matriz.obtener(0, 0) == Fraction(1)
    assert matriz.obtener(0, 1) == Fraction(0)
    assert matriz.obtener(0, 2) == Fraction(1)
    assert matriz.obtener(1, 0) == Fraction(0)
    assert matriz.obtener(1, 1) == Fraction(1)
    assert matriz.obtener(1, 2) == Fraction(2)


def test_modo_estricto_rechaza_ecuaciones_disjuntas():
    """La validación estricta exige relación entre las variables."""
    texto = "x1 = 1\nx2 = 2"
    valido, _, _, mensaje = AnalizadorSistema.parsear_sistema(texto, variables_estrictas=True)
    assert not valido
    assert "no tienen relación" in mensaje


def test_sistema_acoplado_se_acepta():
    """El sistema relacionado conserva variables y dimensiones."""
    texto = "2x + y = 5\nx - y = 1"
    matriz = comprobar_sistema_dos_variables(texto)


def test_sistema_parcialmente_acoplado_se_acepta():
    """Una variable aislada puede coexistir con ecuaciones relacionadas."""
    texto = "x + y = 3\nx - y = 1\nz = 7"
    valido, _, variables, mensaje = AnalizadorSistema.parsear_sistema(texto)
    assert valido, mensaje
    assert set(variables) == {"x", "y", "z"}
