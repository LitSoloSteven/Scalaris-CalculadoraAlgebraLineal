"""Restricciones de dominio para enviar una familia vectorial al visualizador."""
import pytest

from src.backend.geometria.transferencia import preparar_vectores_visualizador


@pytest.mark.parametrize("operacion,cantidad,dimension,escena", [
    ("suma_resta", 2, 2, "vectores"), ("suma_resta", 2, 3, "vectores"),
    ("suma_resta", 1, 3, ""), ("suma_resta", 3, 3, ""), ("suma_resta", 2, 4, ""),
    ("combinacion_lineal", 2, 2, "combinacion"), ("combinacion_lineal", 5, 3, "combinacion"),
    ("combinacion_lineal", 6, 3, ""), ("escalar", 1, 3, ""),
])
def test_transferencia_conserva_limites_y_orden(operacion, cantidad, dimension, escena):
    """Se conserva el orden de captura y el objetivo encabeza la combinación."""
    vectores = {nombre: {"datos": [str(indice)] * dimension}
                for indice, nombre in enumerate(["b", "u", "v", "w", "x", "y"][:cantidad])}
    datos, destino = preparar_vectores_visualizador(operacion, vectores)
    assert destino == escena
    assert datos == [vector["datos"] for vector in vectores.values()] if escena else datos == []


def test_transferencia_rechaza_dimensiones_distintas_y_objetivo_ausente():
    """La familia irregular o sin b no produce una transferencia de combinación."""
    assert preparar_vectores_visualizador("suma_resta", {"u": {"datos": [1, 2]}, "v": {"datos": [1, 2, 3]}}) == ([], "")
    assert preparar_vectores_visualizador("combinacion_lineal", {"u": {"datos": [1, 2]}, "v": {"datos": [1, 2]}}) == ([], "")
