"""Integración de análisis de ecuaciones, evaluación y errores de controladores."""
import json
from fractions import Fraction
from src.backend.utils.parsers import SystemParser
from src.backend.solvers.matrix_ops.evaluator import MatrixExpressionEvaluator
from src.backend.models.matrix import Matrix
from src.backend.utils.formatters import format_fraction_str, number_to_latex
from src.frontend.controladores.sistemas_lineales.controlador_gauss import ControladorGauss
from src.frontend.controladores.sistemas_lineales.controlador_gauss_jordan import ControladorGaussJordan


def test_analizador_distingue_productos_lineales_y_ecuaciones_constantes():
    """Los coeficientes escalares se aceptan y los productos de variables se rechazan."""
    valido, matriz, variables, mensaje = SystemParser.parse_system("2*x + y = 3\nx - y = 0")
    assert valido is True
    valido, matriz, variables, mensaje = SystemParser.parse_system("x*y = 3")
    assert valido is False
    valido, matriz, variables, mensaje = SystemParser.parse_system("2x*y = 3")
    assert valido is False
    valido, matriz, variables, mensaje = SystemParser.parse_system("x + y = 1\n0 = 5")
    assert valido is True


def test_evaluador_producto_implicito_equivale_a_explicito():
    """El producto conserva el resultado y la suma identifica su variable temporal."""
    evaluador = MatrixExpressionEvaluator()
    matrices = {"A": Matrix(2, 2, [[1, 2], [3, 4]]),
                "B": Matrix(2, 2, [[5, 6], [7, 8]])}
    implicito = evaluador.evaluate("AB", matrices)
    explicito = evaluador.evaluate("A*B", matrices)
    assert implicito["result_matrix"].data == explicito["result_matrix"].data
    suma = evaluador.evaluate("A+B", matrices)
    assert suma["final_variable"] == "T_{1}"


def test_formateadores_conservan_denominador_grande():
    """Texto y LaTeX conservan los denominadores exactos."""
    assert format_fraction_str(Fraction(1, 1001)) == "1/1001"
    assert number_to_latex(Fraction(2, 1001)) == r"\frac{2}{1001}"


def test_controladores_error_en_no_numerico():
    """Ambos métodos comunican el error de entrada no numérica."""
    carga = json.dumps({
        "matrix_A": [["1", "no_es_numero"], ["3", "4"]],
        "vector_b": ["1", "2"], "variables": ["x", "y"],
    })
    resultado_gauss = json.loads(ControladorGauss.procesar_sistema(carga))
    assert resultado_gauss["status"] == "ERROR"
    resultado_jordan = json.loads(ControladorGaussJordan.procesar_sistema(carga))
    assert resultado_jordan["status"] == "ERROR"
