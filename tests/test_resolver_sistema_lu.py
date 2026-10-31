"""Contratos de resolucion exacta y validacion de sistemas por LU."""
from fractions import Fraction

import pytest

from src.backend.constantes import DIMENSION_MAXIMA_MATRICES
from src.backend.modelos.calculo_matricial import multiplicar_matrices
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.factorizacion_lu import resolver_sistema_lu


def _verificar_resultados_lu(resultado, terminos, esperada, datos, matriz):
    """Helper para agrupar las aserciones del test y reducir su complejidad."""
    assert set(resultado) == {"estado", "convencion", "permutacion", "inferior", "superior", "intermedio", "solucion", "traza"}
    assert resultado["estado"] == "EXITO" and resultado["convencion"] == "PA=LU"
    assert all(isinstance(valor, Fraction) for clave in ("intermedio", "solucion") for valor in resultado[clave])
    
    if esperada is not None:
        assert resultado["solucion"] == esperada
        
    if datos == [[1, 0], [0, 1]]:
        assert resultado["intermedio"] == [2, 3]
        
    vector = lambda valores: Matriz(len(valores), 1, [[valor] for valor in valores])
    permutacion, inferior, superior = (resultado[clave] for clave in ("permutacion", "inferior", "superior"))
    
    assert multiplicar_matrices(matriz, vector(resultado["solucion"])) == vector(terminos)
    assert multiplicar_matrices(permutacion, matriz) == multiplicar_matrices(inferior, superior)
    assert multiplicar_matrices(inferior, vector(resultado["intermedio"])) == multiplicar_matrices(permutacion, vector(terminos))
    
    pasos = resultado["traza"]
    assert [paso["tipo"] for paso in pasos] == ["planteamiento", "operacion"] + ["sustitucion"] * (2 * matriz.filas) + ["resultado"]
    assert all(set(paso) == {"tipo", "descripcion", "detalle_latex", "explicacion"} for paso in pasos)


@pytest.mark.parametrize("datos,terminos,esperada", [
    ([[1, 0], [0, 1]], [2, 3], [2, 3]),
    ([[0, 1], [1, 0]], [1, 2], [2, 1]),
    ([[2, 1], [1, 3]], [3, 5], [Fraction(4, 5), Fraction(7, 5)]),
    ([[4, 1, 0], [2, 0, 1], [1, 2, 2]], [1, 2, 3], None),
])
def test_resolucion_y_productos_exactos(datos, terminos, esperada):
    """Verifica la resolución exacta, los productos y la estructura de la traza."""
    matriz = Matriz(len(datos), len(datos), datos)
    original = [fila[:] for fila in matriz.datos]
    copia_terminos = terminos[:]
    
    resultado = resolver_sistema_lu(matriz, terminos)
    
    _verificar_resultados_lu(resultado, terminos, esperada, datos, matriz)
    
    # Mutación comprobada aquí, liberando al helper de 2 parámetros extra
    assert matriz.datos == original
    assert terminos == copia_terminos