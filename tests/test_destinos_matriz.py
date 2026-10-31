"""Límites de destino y exclusiones de las transferencias matriciales."""
import pytest
from src.frontend.controladores.destinos_matriz import destinos_compatibles


@pytest.mark.parametrize("dimension,esperados", [
    (1, {"inversa", "determinantes", "factorizacion_lu", "sistemas", "matrices", "transformaciones"}),
    (2, {"inversa", "determinantes", "factorizacion_lu", "sistemas", "matrices", "transformaciones", "leontief"}),
    (8, {"inversa", "determinantes", "factorizacion_lu", "sistemas", "matrices", "transformaciones", "leontief"}),
    (9, {"inversa", "determinantes", "factorizacion_lu", "sistemas", "matrices"}),
    (10, {"inversa", "determinantes", "factorizacion_lu", "sistemas", "matrices"}),
    (11, {"inversa", "determinantes"}), (50, {"inversa", "determinantes"}), (51, set()),
])
def test_limites_exactos_de_cada_destino(dimension, esperados):
    """Cada frontera conserva todos los destinos y solo los que admiten ese orden."""
    assert set(destinos_compatibles(dimension, dimension, "")) == esperados


@pytest.mark.parametrize("origen", ["inversa", "determinantes", "factorizacion_lu", "sistemas",
                                     "matrices", "transformaciones", "leontief"])
def test_origen_excluido_sin_perder_los_otros_destinos(origen):
    """El emisor no se ofrece a sí mismo ni oculta herramientas compatibles."""
    todos = set(destinos_compatibles(2, 2, ""))
    assert set(destinos_compatibles(2, 2, origen)) == todos - {origen}


@pytest.mark.parametrize("filas,columnas", [(0, 0), (-1, -1), (2, 3), (3, 2), (1, 50),
                                           (True, True), (2.0, 2), ("2", 2), (None, None)])
def test_formas_no_admitidas_no_ofrecen_transferencia(filas, columnas):
    """Vacíos, rectángulos y dimensiones ajenas al contrato no producen botones."""
    assert destinos_compatibles(filas, columnas, "determinantes") == ()


def test_vectores_conserva_su_flujo_geometrico():
    """La herramienta vectorial no incorpora transferencias de matrices."""
    assert destinos_compatibles(2, 2, "vectores") == ()
