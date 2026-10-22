"""Preparación y controles comunes de matrices extraídas de ecuaciones textuales."""
from src.backend.utilidades.analizadores import AnalizadorSistema


def comprobar_sistema_dos_variables(texto):
    """Exige análisis válido, variables x/y y una matriz aumentada de dos por tres."""
    valido, matriz, variables, mensaje = AnalizadorSistema.parsear_sistema(texto)
    assert valido, mensaje
    assert variables == ['x', 'y']
    assert matriz.filas == 2
    assert matriz.columnas == 3
    return matriz
