"""Completitud de pasos al incluir u omitir el detalle LaTeX de la inversa."""
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa


def test_inversa_con_y_sin_latex_conserva_pasos():
    """La opción de formato conserva los pasos y controla todos sus detalles."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    resolutor = ResolutorInversa()
    resultado = resolutor.resolver(matriz)
    assert all(paso['detalle_latex'] is not None for paso in resultado['pasos'])
    sin_latex = resolutor.resolver(matriz, construir_detalle_latex=False)
    assert len(sin_latex['pasos']) > 0
