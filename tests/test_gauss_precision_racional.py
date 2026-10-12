"""Precisión de soluciones únicas y paramétricas obtenidas por Gauss."""
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver


def test_sustitucion_regresiva_conserva_fracciones_exactas():
    """Los denominadores de las dos soluciones permanecen intactos."""
    matriz = Matrix(2, 3, [[7, 0, 1], [0, 13, 1]])
    resultado = GaussSolver(matriz).solve()
    assert resultado["solution"][0] == "1/7", f"Esperado 1/7, obtenido {resultado['solution'][0]}"
    assert resultado["solution"][1] == "1/13", f"Esperado 1/13, obtenido {resultado['solution'][1]}"


def test_soluciones_infinitas_conservan_parametrizacion():
    """El sistema dependiente conserva sus variables libres."""
    matriz = Matrix(2, 4, [[1, 1, 1, 3], [2, 2, 2, 6]])
    resultado = GaussSolver(matriz).solve()
    assert resultado["status"] == "INFINITE_SOLUTIONS"
    assert resultado["solution"] is not None
    assert any("t" in solucion for solucion in resultado["solution"])
