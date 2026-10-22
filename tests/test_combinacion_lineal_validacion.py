"""Validación de entradas para representar un vector como combinación."""
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import ResolutorCombinacionLineal
from src.backend.resolutores.operaciones_vectores.operaciones import ResolutorOperacionesVectores


def test_combinacion_rechaza_lista_vacia():
    """La combinación requiere al menos un vector generador."""
    objetivo = Matriz(2, 1, [[1], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [])
    assert resultado["estado"] == "ERROR"
    assert "al menos un vector" in resultado["mensaje"]


def test_combinacion_rechaza_coleccion_no_lista():
    """Una cadena no se interpreta como lista de vectores."""
    objetivo = Matriz(2, 1, [[1], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, "no soy lista")
    assert resultado["estado"] == "ERROR"


def test_combinacion_rechaza_objetivo_fila():
    """El objetivo debe ser columna y no se transpone automáticamente."""
    v1 = Matriz(2, 1, [[1], [0]])
    objetivo_fila = Matriz(1, 2, [[3, 2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo_fila, [v1])
    assert resultado["estado"] == "ERROR"
    assert "b" in resultado["mensaje"]
    assert "se esperaba vector columna" in resultado["mensaje"]


def test_combinacion_rechaza_generador_fila():
    """El error identifica el generador con orientación incompatible."""
    primera_columna = Matriz(2, 1, [[1], [0]])
    segunda_fila = Matriz(1, 2, [[0, 1]])
    objetivo = Matriz(2, 1, [[3], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [primera_columna, segunda_fila])
    assert resultado["estado"] == "ERROR"
    assert "v_2" in resultado["mensaje"]


def test_combinacion_rechaza_objetivo_matricial():
    """Una matriz rectangular no es un objetivo vectorial."""
    v1 = Matriz(2, 1, [[1], [0]])
    objetivo = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1])
    assert resultado["estado"] == "ERROR"
    assert "2×3" in resultado["mensaje"]


def test_combinacion_rechaza_dimension_objetivo_incompatible():
    """El mensaje detalla las dimensiones del objetivo y del generador."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(3, 1, [[1], [2], [3]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["estado"] == "ERROR"
    assert "Dimensiones incompatibles" in resultado["mensaje"]
    assert "b tiene dim 3" in resultado["mensaje"]
    assert "v_1 tiene dim 2" in resultado["mensaje"]


def test_combinacion_rechaza_dimensiones_distintas_entre_generadores():
    """El mensaje señala el generador cuya dimensión difiere."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(3, 1, [[0], [1], [2]])
    objetivo = Matriz(2, 1, [[1], [1]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["estado"] == "ERROR"
    assert "v_2" in resultado["mensaje"]


def test_combinacion_rechaza_objetivo_sin_modelo_matriz():
    """Un objetivo nulo devuelve error en lugar de una excepción de atributo."""
    v1 = Matriz(2, 1, [[1], [0]])
    resultado = ResolutorCombinacionLineal().resolver(None, [v1])
    assert resultado["estado"] == "ERROR"
    assert "Matriz" in resultado["mensaje"]


def test_combinacion_rechaza_generador_sin_modelo_matriz():
    """Un generador textual devuelve un error de tipo claro."""
    objetivo = Matriz(2, 1, [[1], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, ["no soy matriz"])
    assert resultado["estado"] == "ERROR"
    assert "Matriz" in resultado["mensaje"]


def test_suma_rechaza_operando_sin_modelo_matriz():
    """La operación vectorial también valida el tipo del operando."""
    v1 = Matriz(2, 1, [[1], [0]])
    resultado = ResolutorOperacionesVectores().sumar(v1, "no soy vector")
    assert resultado["estado"] == "ERROR"
    assert "Matriz" in resultado["mensaje"]


def test_combinacion_rechaza_cantidad_incorrecta_de_nombres():
    """Cada generador requiere un nombre cuando se personalizan variables."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    v3 = Matriz(2, 1, [[1], [1]])
    objetivo = Matriz(2, 1, [[2], [3]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2, v3], nombres_variables=["alpha"])
    assert resultado["estado"] == "ERROR"
    assert "nombres_variables tiene 1" in resultado["mensaje"]


def test_combinacion_rechaza_nombres_fuera_de_lista():
    """Los nombres personalizados deben recibirse como lista."""
    v1 = Matriz(2, 1, [[1], [0]])
    objetivo = Matriz(2, 1, [[3], [0]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1], nombres_variables="alpha")
    assert resultado["estado"] == "ERROR"
    assert "lista" in resultado["mensaje"]
