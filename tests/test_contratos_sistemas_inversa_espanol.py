"""Caracterización literal y contratos canónicos de sistemas e inversa."""
import json
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.backend.resolutores.sistemas_lineales.gauss_jordan import ResolutorGaussJordan
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa
from src.frontend.controladores.sistemas_lineales import ControladorGauss, ControladorGaussJordan
from src.frontend.controladores.operaciones_inversas import ControladorOperacionesInversas


CLAVES_SISTEMA = {
    "estado", "mensaje", "clasificacion", "matriz_escalonada", "solucion",
    "solucion_exacta", "columnas_libres", "parametros_solucion", "analisis_sistema",
    "pasos", "pasos_sustitucion_regresiva",
}
CLAVES_CONTROLADOR = {
    "estado", "mensaje", "clasificacion", "solucion", "parametros_solucion",
    "analisis_sistema", "pasos_intermedios_latex", "metadatos_pasos",
    "pasos_sustitucion_regresiva", "pasos_verificacion_latex", "variables",
    "numero_variables", "vista_pasos", "grupos", "estadisticas",
}
PASOS_GAUSS = [
    "Matriz inicial aumentada [A|b]:",
    "Pivote seleccionado en Fila 1, Columna 1 (valor = 2)",
    "Fila 2 = Fila 2 − (1/2) · Fila 1",
    "Pivote seleccionado en Fila 2, Columna 2 (valor = -3/2)",
    "Normalizar pivote: Fila 1 = Fila 1 / 2",
    "Normalizar pivote: Fila 2 = Fila 2 / -3/2",
]
PASOS_JORDAN = [
    "Matriz inicial aumentada [A|b]:",
    "Pivote seleccionado en Fila 1, Columna 1",
    "Fila 2 = Fila 2 − (1/2) · Fila 1",
    "Pivote seleccionado en Fila 2, Columna 2",
    "Fila 1 = Fila 1 − (-2/3) · Fila 2",
    "Normalizar pivote a 1: Fila 1 = Fila 1 / 2",
    "Normalizar pivote a 1: Fila 2 = Fila 2 / -3/2",
]


@pytest.mark.parametrize("resolutor,pasos", [(ResolutorGauss, PASOS_GAUSS), (ResolutorGaussJordan, PASOS_JORDAN)])
def test_pasos_y_solucion_exacta_son_literales(resolutor, pasos):
    """Conserva clasificación, fracciones y textos completos de ambos métodos."""
    resultado = resolutor(Matriz(2, 3, [[2, 1, 5], [1, -1, 1]])).resolver()
    assert set(resultado) == CLAVES_SISTEMA
    assert resultado["clasificacion"] == "Sistema Consistente Determinado: Presenta Solución Única."
    assert resultado["solucion_exacta"] == [Fraction(2), Fraction(1)]
    assert all(type(valor) is Fraction for valor in resultado["solucion_exacta"])
    assert resultado["solucion"] == ["2", "1"]
    assert resultado["pasos_sustitucion_regresiva"] == ["x_{2} = 1", "x_{1} = 2"]
    assert [paso["descripcion"] for paso in resultado["pasos"]] == pasos


@pytest.mark.parametrize("resolutor", [ResolutorGauss, ResolutorGaussJordan])
def test_parametros_libres_y_sin_solucion_conservan_contrato(resolutor):
    """Comprueba las tres clasificaciones con una única estructura de claves."""
    infinito = resolutor(Matriz(2, 4, [[1, 2, 3, 3], [2, 4, 6, 6]])).resolver()
    assert set(infinito) == CLAVES_SISTEMA
    assert infinito["solucion"] == ["3 - 2t - 3s", "t", "s"]
    assert infinito["solucion_exacta"] is None
    assert infinito["parametros_solucion"] == {
        "numero_variables": 3, "columnas_libres": [1, 2], "nombres_parametros": ["t", "s"],
        "particular": [Fraction(3), Fraction(0), Fraction(0)],
        "direcciones": [[Fraction(-2), Fraction(1), Fraction(0)], [Fraction(-3), Fraction(0), Fraction(1)]],
    }
    inconsistente = resolutor(Matriz(2, 3, [[1, 1, 2], [1, 1, 3]])).resolver()
    assert set(inconsistente) == CLAVES_SISTEMA
    assert inconsistente["estado"] == "SIN_SOLUCION"
    assert inconsistente["parametros_solucion"] is None
    assert inconsistente["pasos_sustitucion_regresiva"] == []


@pytest.mark.parametrize("controlador", [ControladorGauss, ControladorGaussJordan])
def test_controlador_y_matrices_serializadas_sin_alias(controlador):
    """Exige claves exactas de respuesta y matrices, incluyendo comprobaciones literales."""
    respuesta = json.loads(controlador.procesar_sistema(json.dumps({"matriz_a": [[2, 1], [1, -1]], "vector_b": [5, 1]})))
    assert set(respuesta) == CLAVES_CONTROLADOR
    assert respuesta["pasos_verificacion_latex"] == [
        r"\text{Ecuación 1: } \left(2\right) \cdot \left(2\right) + \left(1\right) \cdot \left(1\right) = 5 \quad (\text{Correcto}, \; b_{1} = 5)",
        r"\text{Ecuación 2: } \left(1\right) \cdot \left(2\right) + \left(-1\right) \cdot \left(1\right) = 1 \quad (\text{Correcto}, \; b_{2} = 1)",
    ]
    assert all(set(paso["matriz"]) == {"filas", "columnas", "datos"} for paso in respuesta["vista_pasos"])
    antigua = json.loads(controlador.procesar_sistema(json.dumps({"matrix_A": [[1]], "vector_b": [1]})))
    assert antigua["estado"] == "ERROR"


def test_inversa_y_tres_comprobaciones_exactas_literales():
    """Conserva determinante, inversa fraccionaria y ambas multiplicaciones exactas."""
    resultado = ResolutorInversa().resolver(Matriz(2, 2, [[1, 2], [3, 4]]))
    assert set(resultado) == {"estado", "mensaje", "determinante", "matriz_aumentada_inicial_latex", "inversa", "inversa_latex", "pasos", "paso_verificacion", "paso_verificacion_inverso", "paso_propiedad_transpuesta"}
    assert resultado["determinante"] == Fraction(-2)
    assert resultado["inversa"].datos == [[Fraction(-2), Fraction(1)], [Fraction(3, 2), Fraction(-1, 2)]]
    identidad = "\\begin{bmatrix}\n1 & 0 \\\\\n0 & 1\n\\end{bmatrix}"
    for clave, prefijo, estado in [
        ("paso_verificacion", r"A \cdot A^{-1}", "Correcto"),
        ("paso_verificacion_inverso", r"A^{-1} \cdot A", "Correcto"),
        ("paso_propiedad_transpuesta", r"(A^{-1})^T \cdot A^T", "Coinciden"),
    ]:
        assert resultado[clave]["coincide"] is True
        assert resultado[clave]["detalle_latex"] == prefijo + " = " + identidad + rf" \quad (\text{{{estado}}})"


@pytest.mark.parametrize("datos,estado", [([[1]], "EXITO"), ([[0]], "SINGULAR"), ([["1/0"]], "ERROR")])
def test_inversa_salida_homogenea_y_entrada_sin_compatibilidad(datos, estado):
    """La salida completa conserva el esquema en éxito, singularidad y error por celda."""
    resultado = ControladorOperacionesInversas.procesar_inversa(json.dumps({"dimension": 1, "datos": datos}))
    assert resultado["estado"] == estado
    assert set(resultado) == {"estado", "mensaje", "dimension", "tiempo_transcurrido_segundos", "determinante", "determinante_texto", "matriz_a", "matriz_a_latex", "inversa", "inversa_latex", "pasos", "grupos", "estadisticas", "comprobaciones", "celda_error"}
    if estado == "ERROR":
        assert resultado["celda_error"] == [0, 0]
    elif estado == "EXITO":
        assert [comprobacion["clave"] for comprobacion in resultado["comprobaciones"]] == ["derecha", "izquierda", "transpuesta"]
    antigua = ControladorOperacionesInversas.procesar_inversa('{"n":1,"data":[[1]]}')
    assert antigua["estado"] == "ERROR"
