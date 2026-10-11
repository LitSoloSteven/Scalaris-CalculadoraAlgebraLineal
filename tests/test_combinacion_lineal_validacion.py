"""Validación de entradas para representar un vector como combinación."""
from src.backend.models.matrix import Matrix
from src.backend.solvers.vector_ops.linear_combination import LinearCombinationSolver
from src.backend.solvers.vector_ops.operations import VectorOpsSolver


def test_combinacion_rechaza_lista_vacia():
    """La combinación requiere al menos un vector generador."""
    objetivo = Matrix(2, 1, [[1], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, [])
    assert resultado["status"] == "ERROR"
    assert "al menos un vector" in resultado["message"]


def test_combinacion_rechaza_coleccion_no_lista():
    """Una cadena no se interpreta como lista de vectores."""
    objetivo = Matrix(2, 1, [[1], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, "no soy lista")
    assert resultado["status"] == "ERROR"


def test_combinacion_rechaza_objetivo_fila():
    """El objetivo debe ser columna y no se transpone automáticamente."""
    v1 = Matrix(2, 1, [[1], [0]])
    objetivo_fila = Matrix(1, 2, [[3, 2]])
    resultado = LinearCombinationSolver().solve(objetivo_fila, [v1])
    assert resultado["status"] == "ERROR"
    assert "b" in resultado["message"]
    assert "se esperaba vector columna" in resultado["message"]


def test_combinacion_rechaza_generador_fila():
    """El error identifica el generador con orientación incompatible."""
    primera_columna = Matrix(2, 1, [[1], [0]])
    segunda_fila = Matrix(1, 2, [[0, 1]])
    objetivo = Matrix(2, 1, [[3], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, [primera_columna, segunda_fila])
    assert resultado["status"] == "ERROR"
    assert "v_2" in resultado["message"]


def test_combinacion_rechaza_objetivo_matricial():
    """Una matriz rectangular no es un objetivo vectorial."""
    v1 = Matrix(2, 1, [[1], [0]])
    objetivo = Matrix(2, 3, [[1, 2, 3], [4, 5, 6]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1])
    assert resultado["status"] == "ERROR"
    assert "2×3" in resultado["message"]


def test_combinacion_rechaza_dimension_objetivo_incompatible():
    """El mensaje detalla las dimensiones del objetivo y del generador."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    objetivo = Matrix(3, 1, [[1], [2], [3]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1, v2])
    assert resultado["status"] == "ERROR"
    assert "Dimensiones incompatibles" in resultado["message"]
    assert "b tiene dim 3" in resultado["message"]
    assert "v_1 tiene dim 2" in resultado["message"]


def test_combinacion_rechaza_dimensiones_distintas_entre_generadores():
    """El mensaje señala el generador cuya dimensión difiere."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(3, 1, [[0], [1], [2]])
    objetivo = Matrix(2, 1, [[1], [1]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1, v2])
    assert resultado["status"] == "ERROR"
    assert "v_2" in resultado["message"]


def test_combinacion_rechaza_objetivo_sin_modelo_matriz():
    """Un objetivo nulo devuelve error en lugar de una excepción de atributo."""
    v1 = Matrix(2, 1, [[1], [0]])
    resultado = LinearCombinationSolver().solve(None, [v1])
    assert resultado["status"] == "ERROR"
    assert "Matrix" in resultado["message"]


def test_combinacion_rechaza_generador_sin_modelo_matriz():
    """Un generador textual devuelve un error de tipo claro."""
    objetivo = Matrix(2, 1, [[1], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, ["no soy matriz"])
    assert resultado["status"] == "ERROR"
    assert "Matrix" in resultado["message"]


def test_suma_rechaza_operando_sin_modelo_matriz():
    """La operación vectorial también valida el tipo del operando."""
    v1 = Matrix(2, 1, [[1], [0]])
    resultado = VectorOpsSolver().add(v1, "no soy vector")
    assert resultado["status"] == "ERROR"
    assert "Matrix" in resultado["message"]


def test_combinacion_rechaza_cantidad_incorrecta_de_nombres():
    """Cada generador requiere un nombre cuando se personalizan variables."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    v3 = Matrix(2, 1, [[1], [1]])
    objetivo = Matrix(2, 1, [[2], [3]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1, v2, v3], variable_names=["alpha"])
    assert resultado["status"] == "ERROR"
    assert "variable_names tiene 1" in resultado["message"]


def test_combinacion_rechaza_nombres_fuera_de_lista():
    """Los nombres personalizados deben recibirse como lista."""
    v1 = Matrix(2, 1, [[1], [0]])
    objetivo = Matrix(2, 1, [[3], [0]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1], variable_names="alpha")
    assert resultado["status"] == "ERROR"
    assert "lista" in resultado["message"]
