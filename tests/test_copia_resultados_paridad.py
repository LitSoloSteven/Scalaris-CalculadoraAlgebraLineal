"""Texto copiador compartido para magnitudes exactas de varios módulos."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.frontend.componentes.copia_resultado import texto_resultado_copiable


def test_copia_valores_exactos_y_no_incluye_la_traza():
    """Conserva fracciones y filas tabuladas sin copiar miles de pasos ni entradas editables."""
    texto = texto_resultado_copiable({"determinante": Fraction(-1, 3),
                                    "inferior": Matriz(2, 2, [[1, 0], [Fraction(1, 3), 1]]),
                                    "traza": ["dato interno"]})
    assert "Determinante:\n-1/3" in texto
    assert "L:\n1\t0\n1/3\t1" in texto
    assert "dato interno" not in texto


def test_copia_bases_vectores_y_resultado_serializado():
    """Reconoce matrices serializadas y bases sin depender de una clase de vista."""
    texto = texto_resultado_copiable({"matriz_resultado": {"datos": [["1/2", "2"]]},
                                    "base_nucleo": [{"vector": ["1", "-1"]}], "rango": 0})
    assert "Resultado:\n1/2\t2" in texto
    assert "Base del núcleo:\n1\n-1" in texto
    assert "Rango:\n0" in texto
