"""Clasificación de productos y conservación de otras trazas algebraicas."""
import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.comprobacion_productos import comprobar_producto
from src.frontend.componentes.datos_desarrollo import es_traza_producto, agrupar_filas_producto


def test_producto_real_conserva_filas_y_celdas():
    """Agrupa la traza real sin modificar sus fórmulas ni sus cálculos."""
    identidad = Matriz(2, 2, [[1, 0], [0, 1]])
    traza = comprobar_producto(identidad, identidad, identidad, "AA^{-1}=I")["traza"]
    assert es_traza_producto(traza)
    filas = agrupar_filas_producto(traza)
    assert list(filas) == [1, 2]
    assert [len(detalles) for detalles in filas.values()] == [2, 2]
    assert filas[1][0] == traza[1]["detalle_latex"]


@pytest.mark.parametrize("traza", [[], [{}], [
    {"descripcion": "Propiedad por comprobar: A"},
    {"detalle_latex": "x=1"},
    {"descripcion": "Comprobacion exacta de A: coincide"},
], [
    {"descripcion": "Sistema homogéneo"}, {"detalle_latex": "C_{1,1}=0"},
    {"descripcion": "Comprobacion exacta de A: coincide"},
]])
def test_otras_formas_conservan_modo_plano(traza):
    """Las trazas vacías, incompletas y de otro tipo no se agrupan como productos."""
    assert not es_traza_producto(traza)
    assert agrupar_filas_producto(traza) == {}
