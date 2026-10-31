"""Pruebas de la aplicación lineal exacta T(v) = A·v."""
import pytest
from fractions import Fraction

from src.backend.excepciones import ErrorDiscrepanciaDimension
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.aplicacion_transformacion import aplicar_vector
from src.backend.resolutores.operaciones_matrices.transformaciones import ResolutorTransformacionesLineales

@pytest.mark.parametrize("datos_a,datos_v,esperada", [
    ([[1, 0], [0, 1]], [[5], [3]], [[5], [3]]),
    ([[2, 0], [0, 2]], [[1], [2]], [[2], [4]]),
    ([[1, 1], [0, 1]], [["1/3"], ["2/3"]], [["1"], ["2/3"]]),
])
def test_aplicacion_exitosa_conserva_valores_exactos(datos_a, datos_v, esperada):
    """Verifica la identidad, la escala y la aritmética fraccionaria exacta."""
    matriz = Matriz(len(datos_a), len(datos_a[0]), datos_a)
    vector = Matriz(len(datos_v), 1, datos_v)
    
    resultado = aplicar_vector(matriz, vector)
    
    assert resultado["estado"] == "EXITO"
    assert resultado["aproximacion"] is False
    assert resultado["vector_transformado"]["exacta"] == [str(val[0]) for val in esperada]
    assert len(resultado["pasos"]) == matriz.filas


def test_aplicacion_devuelve_contrato_completo():
    """Verifica que el diccionario de retorno tenga las claves canónicas."""
    matriz = Matriz(2, 2, [[1, 0], [0, 1]])
    vector = Matriz(2, 1, [[1], [1]])
    
    resultado = aplicar_vector(matriz, vector)
    
    assert set(resultado.keys()) == {
        "estado", "mensaje", "matriz_a", "vector_original",
        "vector_transformado", "aproximacion", "pasos"
    }
    assert "aproximado" in resultado["vector_transformado"]
    assert "exacta" in resultado["vector_transformado"]
    assert "detalle_latex" in resultado["pasos"][0]


def test_dimensiones_incompatibles_lanzan_excepcion():
    """Verifica que A(m×n) y v(k×1) fallen si n != k."""
    matriz = Matriz(2, 3, [[1, 0, 0], [0, 1, 0]])
    vector = Matriz(2, 1, [[1], [1]])
    
    with pytest.raises(ErrorDiscrepanciaDimension):
        aplicar_vector(matriz, vector)


def test_vector_debe_ser_columna():
    """Verifica que un vector fila (1×n) sea rechazado."""
    matriz = Matriz(2, 2, [[1, 0], [0, 1]])
    vector = Matriz(1, 2, [[1, 1]])
    
    with pytest.raises(ValueError, match="columna"):
        aplicar_vector(matriz, vector)


def test_metodo_aplicar_en_resolutor():
    """Verifica que el resolutor de transformaciones delegue en aplicar_vector."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    vector = Matriz(2, 1, [[1], [0]])
    
    resolutor = ResolutorTransformacionesLineales()
    resultado = resolutor.aplicar(matriz, vector)
    
    assert resultado["vector_transformado"]["exacta"] == ["1", "3"]