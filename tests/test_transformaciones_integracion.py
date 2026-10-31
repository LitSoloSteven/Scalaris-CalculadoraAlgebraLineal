"""Pruebas de integración entre la aplicación T(v)=Av y el análisis de núcleo e imagen."""
import pytest
from fractions import Fraction

from src.backend.excepciones import ErrorDiscrepanciaDimension
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.transformaciones import ResolutorTransformacionesLineales


@pytest.fixture
def resolutor():
    """Devuelve una instancia limpia del resolutor de transformaciones."""
    return ResolutorTransformacionesLineales()


def test_aplicacion_en_nucleo_resulta_en_vector_cero(resolutor):
    """Verifica que cualquier vector de la base del núcleo se anule al aplicarle T."""
    # Matriz con columnas linealmente dependientes (rango 1, nulidad 1)
    matriz = Matriz(2, 2, [[1, 2], [2, 4]])
    analisis = resolutor.resolver(matriz)
    
    # Extraemos el vector del núcleo (ej. [-2, 1])
    vector_nulo = analisis["base_nucleo"][0]["vector"]
    v = Matriz(2, 1, [[Fraction(x)] for x in vector_nulo])
    
    resultado = resolutor.aplicar(matriz, v)
    
    assert resultado["estado"] == "EXITO"
    assert resultado["vector_transformado"]["exacta"] == ["0", "0"]


def test_aplicacion_genera_vector_en_imagen(resolutor):
    """Verifica que el resultado de T(v) sea una combinación lineal de las columnas pivote."""
    matriz = Matriz(2, 2, [[1, 0], [0, 1]])  # Identidad (núcleo trivial, imagen R2 completo)
    analisis = resolutor.resolver(matriz)
    
    v = Matriz(2, 1, [[Fraction(3)], [Fraction(4)]])
    resultado = resolutor.aplicar(matriz, v)
    
    # La imagen es generada por las columnas pivote
    assert resultado["vector_transformado"]["exacta"] == ["3", "4"]
    assert len(analisis["base_imagen"]) == 2  # Dos vectores en la base de la imagen


def test_dimensiones_incompatibles_en_resolutor(resolutor):
    """Verifica que el método aplicar del resolutor también valide las dimensiones."""
    matriz = Matriz(3, 2, [[1, 0], [0, 1], [0, 0]])
    vector = Matriz(3, 1, [[1], [2], [3]])
    
    with pytest.raises(ErrorDiscrepanciaDimension):
        resolutor.aplicar(matriz, vector)


def test_verificacion_matematica_exacta(resolutor):
    """Verifica que el resultado de aplicar T(v) sea idéntico al cálculo manual exacto."""
    matriz = Matriz(2, 2, [[2, 1], [1, 3]])
    v = Matriz(2, 1, [[Fraction(1, 2)], [Fraction(1, 3)]])
    
    resultado = resolutor.aplicar(matriz, v)
    
    # Cálculo manual:
    # Fila 1: 2*(1/2) + 1*(1/3) = 1 + 1/3 = 4/3
    # Fila 2: 1*(1/2) + 3*(1/3) = 1/2 + 1 = 3/2
    assert resultado["vector_transformado"]["exacta"] == ["4/3", "3/2"]