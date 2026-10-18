"""Integración de análisis de ecuaciones, evaluación y errores de controladores."""
import json
from fractions import Fraction
from src.backend.utilidades.analizadores import AnalizadorSistema
from src.backend.resolutores.operaciones_matrices.evaluador import EvaluadorExpresionesMatriciales
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import formatear_fraccion_texto, numero_a_latex
from src.frontend.controladores.sistemas_lineales.controlador_gauss import ControladorGauss
from src.frontend.controladores.sistemas_lineales.controlador_gauss_jordan import ControladorGaussJordan


def test_analizador_distingue_productos_lineales_y_ecuaciones_constantes():
    """Los coeficientes escalares se aceptan y los productos de variables se rechazan."""
    valido, matriz, variables, mensaje = AnalizadorSistema.parsear_sistema("2*x + y = 3\nx - y = 0")
    assert valido is True
    valido, matriz, variables, mensaje = AnalizadorSistema.parsear_sistema("x*y = 3")
    assert valido is False
    valido, matriz, variables, mensaje = AnalizadorSistema.parsear_sistema("2x*y = 3")
    assert valido is False
    valido, matriz, variables, mensaje = AnalizadorSistema.parsear_sistema("x + y = 1\n0 = 5")
    assert valido is True


def test_evaluador_producto_implicito_equivale_a_explicito():
    """El producto conserva el resultado y la suma identifica su variable temporal."""
    evaluador = EvaluadorExpresionesMatriciales()
    matrices = {"A": Matriz(2, 2, [[1, 2], [3, 4]]),
                "B": Matriz(2, 2, [[5, 6], [7, 8]])}
    implicito = evaluador.evaluar("AB", matrices)
    explicito = evaluador.evaluar("A*B", matrices)
    assert implicito["matriz_resultado"].datos == explicito["matriz_resultado"].datos
    suma = evaluador.evaluar("A+B", matrices)
    assert suma["variable_final"] == "T_{1}"


def test_formateadores_conservan_denominador_grande():
    """Texto y LaTeX conservan los denominadores exactos."""
    assert formatear_fraccion_texto(Fraction(1, 1001)) == "1/1001"
    assert numero_a_latex(Fraction(2, 1001)) == r"\frac{2}{1001}"


def test_controladores_error_en_no_numerico():
    """Ambos métodos comunican el error de entrada no numérica."""
    carga = json.dumps({
        "matriz_a": [["1", "no_es_numero"], ["3", "4"]],
        "vector_b": ["1", "2"], "variables": ["x", "y"],
    })
    resultado_gauss = json.loads(ControladorGauss.procesar_sistema(carga))
    assert resultado_gauss["estado"] == "ERROR"
    resultado_jordan = json.loads(ControladorGaussJordan.procesar_sistema(carga))
    assert resultado_jordan["estado"] == "ERROR"
