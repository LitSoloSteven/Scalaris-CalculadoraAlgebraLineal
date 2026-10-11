"""Contrato, pasos, verificación y mensajes de combinación lineal."""
import re
from fractions import Fraction
from src.backend.models.matrix import Matrix
from src.backend.solvers.vector_ops.linear_combination import LinearCombinationSolver

_CLAVES_RESPUESTA = {
    "status", "es_combinacion_lineal", "coeficientes", "coeficientes_str",
    "solucion_parametrica", "parametros_libres", "message", "steps",
    "back_substitution_steps", "verification_step",
}


def test_combinacion_unica_devuelve_pasos_gauss():
    """Los pasos conservan la matriz del planteamiento."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    objetivo = Matrix(2, 1, [[3], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1, v2])
    assert len(resultado["steps"]) > 0
    assert resultado["steps"][0]["matrix"] is not None


def test_combinacion_unica_incluye_sustitucion_regresiva():
    """La solución única conserva los pasos de sustitución."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    objetivo = Matrix(2, 1, [[3], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1, v2])
    assert len(resultado["back_substitution_steps"]) > 0


def test_verificacion_unica_incluye_comprobacion_y_coeficientes():
    """La comprobación identifica el coeficiente y confirma coincidencia."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    objetivo = Matrix(2, 1, [[3], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1, v2])
    assert resultado["verification_step"] is not None
    assert resultado["verification_step"]["coincide"] is True
    assert "Comprobación" in resultado["verification_step"]["description"]
    assert "c_1" in resultado["verification_step"]["detail_latex"]


def test_verificacion_unica_muestra_marca_de_coincidencia():
    """El detalle LaTeX muestra la marca cuando coincide el objetivo."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    objetivo = Matrix(2, 1, [[3], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1, v2])
    assert "\\checkmark" in resultado["verification_step"]["detail_latex"]
    assert resultado["verification_step"]["coincide"] is True


def test_contrato_completo_en_combinacion_exitosa():
    """La respuesta exitosa contiene todas las claves contratadas."""
    v1 = Matrix(2, 1, [[1], [0]])
    objetivo = Matrix(2, 1, [[3], [0]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1])
    assert _CLAVES_RESPUESTA.issubset(resultado.keys())


def test_contrato_completo_en_combinacion_erronea():
    """El error conserva la misma estructura del contrato."""
    objetivo = Matrix(2, 1, [[1], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, [])
    assert _CLAVES_RESPUESTA.issubset(resultado.keys())


def test_sustitucion_regresiva_utiliza_nombres_personalizados():
    """Los pasos de sustitución incorporan los nombres recibidos."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    objetivo = Matrix(2, 1, [[3], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1, v2], variable_names=["alpha", "beta"])
    texto = " ".join(resultado["back_substitution_steps"])
    assert "alpha" in texto or "beta" in texto


def test_combinacion_delega_pasos_matriciales_en_gauss():
    """Los pasos delegados incluyen matriz y descripción de operación."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    objetivo = Matrix(2, 1, [[3], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1, v2])
    assert len(resultado["gauss_steps"]) > 0
    for paso in resultado["gauss_steps"]:
        assert paso.get("matrix") is not None
        assert paso.get("description")


def test_verificacion_latex_separa_filas_sin_comas():
    """Las matrices de comprobación usan separadores de fila válidos."""
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    objetivo = Matrix(2, 1, [[3], [2]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1, v2])
    detalle = resultado["verification_step"]["detail_latex"]
    assert "\\\\" in detalle
    matrices = re.findall(r"\\begin\{pmatrix\}(.*?)\\end\{pmatrix\}", detalle)
    assert len(matrices) >= 2
    for contenido in matrices:
        assert "," not in contenido


def test_mensaje_singular_para_combinacion_unica():
    """Una combinación de un solo vector utiliza el singular."""
    v1 = Matrix(3, 1, [[2], [4], [6]])
    objetivo = Matrix(3, 1, [[6], [12], [18]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1])
    assert resultado["status"] == "UNIQUE"
    assert "del vector" in resultado["message"]
    assert "de los 1 vectores" not in resultado["message"]


def test_mensaje_singular_para_combinacion_sin_solucion():
    """La incompatibilidad de un solo vector utiliza el singular."""
    v1 = Matrix(3, 1, [[2], [4], [6]])
    objetivo = Matrix(3, 1, [[1], [0], [0]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1])
    assert resultado["status"] == "NO_SOLUTION"
    assert "del vector" in resultado["message"]
    assert "de los 1 vectores" not in resultado["message"]


def test_mensaje_singular_para_combinacion_infinita():
    """La familia generada por un solo vector utiliza el singular."""
    v1 = Matrix(3, 1, [[0], [0], [0]])
    objetivo = Matrix(3, 1, [[0], [0], [0]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1])
    assert resultado["status"] == "INFINITE"
    assert "del vector" in resultado["message"]
    assert "de los 1 vectores" not in resultado["message"]


def test_combinacion_resuelve_sin_dependencia_de_operaciones_vectoriales():
    """El resolutor de combinación obtiene por sí mismo los coeficientes."""
    from src.backend.solvers.vector_ops.operations import VectorOpsSolver
    v1 = Matrix(2, 1, [[1], [0]])
    v2 = Matrix(2, 1, [[0], [1]])
    objetivo = Matrix(2, 1, [[3], [4]])
    resultado = LinearCombinationSolver().solve(objetivo, [v1, v2])
    assert resultado["status"] == "UNIQUE"
    assert resultado["coeficientes"] == [Fraction(3), Fraction(4)]
