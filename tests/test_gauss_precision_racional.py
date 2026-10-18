"""Precisión de soluciones únicas y paramétricas obtenidas por Gauss."""
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss


def test_sustitucion_regresiva_conserva_fracciones_exactas():
    """Los denominadores de las dos soluciones permanecen intactos."""
    matriz = Matriz(2, 3, [[7, 0, 1], [0, 13, 1]])
    resultado = ResolutorGauss(matriz).resolver()
    assert resultado["solucion"][0] == "1/7", f"Esperado 1/7, obtenido {resultado['solucion'][0]}"
    assert resultado["solucion"][1] == "1/13", f"Esperado 1/13, obtenido {resultado['solucion'][1]}"


def test_soluciones_infinitas_conservan_parametrizacion():
    """El sistema dependiente conserva sus variables libres."""
    matriz = Matriz(2, 4, [[1, 1, 1, 3], [2, 2, 2, 6]])
    resultado = ResolutorGauss(matriz).resolver()
    assert resultado["estado"] == "SOLUCIONES_INFINITAS"
    assert resultado["solucion"] is not None
    assert any("t" in solucion for solucion in resultado["solucion"])
