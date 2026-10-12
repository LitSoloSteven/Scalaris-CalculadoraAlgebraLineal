"""Estructura, precisión exacta y prioridad de parámetros del conjunto solución."""
from fractions import Fraction
import pytest

from src.backend.geometria.conjunto_solucion import obtener_parametros_solucion


def _crear_parametros_validos():
    return {
        "num_vars": 2, "particular": [Fraction(1, 3), Fraction(0)],
        "directions": [[Fraction(-2, 5), Fraction(1)]],
        "free_cols": [1], "param_names": ["t"],
    }


@pytest.mark.parametrize("clave", ["solution_param", "parametros_solucion"])
def test_parametros_validos_conservan_objeto_y_fracciones(clave):
    """La validación no transforma el diccionario ni sus coeficientes exactos."""
    parametros = _crear_parametros_validos()
    assert obtener_parametros_solucion({clave: parametros}) is parametros
    assert parametros["particular"] == [Fraction(1, 3), Fraction(0)]


@pytest.mark.parametrize("campo,valor", [
    ("num_vars", 3), ("particular", [Fraction(1)]), ("free_cols", []),
    ("param_names", []), ("particular", [0.5, Fraction(0)]),
    ("directions", [[Fraction(1), 1.0]]), ("directions", [None]),
])
def test_parametros_malformados_o_aproximados_se_rechazan(campo, valor):
    """Un desajuste estructural o coeficiente aproximado conserva el rechazo histórico."""
    parametros = _crear_parametros_validos()
    parametros[campo] = valor
    assert obtener_parametros_solucion({"solution_param": parametros}) is None


@pytest.mark.parametrize("campo", ["num_vars", "particular", "directions", "free_cols", "param_names"])
def test_campos_ausentes_conservan_resultado_nulo(campo):
    """Los cinco campos obligatorios se validan antes de aceptar la solución."""
    parametros = _crear_parametros_validos()
    del parametros[campo]
    assert obtener_parametros_solucion({"solution_param": parametros}) is None


def test_prioridad_y_alternativa_vacia_se_conservan():
    """La primera estructura no vacía conserva su prioridad frente a la alternativa."""
    primero, segundo = _crear_parametros_validos(), _crear_parametros_validos()
    assert obtener_parametros_solucion({"solution_param": primero, "parametros_solucion": segundo}) is primero
    assert obtener_parametros_solucion({"solution_param": {}, "parametros_solucion": segundo}) is segundo
    assert obtener_parametros_solucion({}) is None


def test_campos_se_leen_una_vez_y_en_orden_original():
    """La extracción conserva el orden de acceso incluso en un diccionario instrumentado."""
    class DiccionarioInstrumentado(dict):
        """Registra las lecturas sin alterar los valores del diccionario."""

        def __getitem__(self, clave):
            lecturas.append(clave)
            return super().__getitem__(clave)

    lecturas = []
    parametros = DiccionarioInstrumentado(_crear_parametros_validos())
    assert obtener_parametros_solucion({"solution_param": parametros}) is parametros
    assert lecturas == ["num_vars", "particular", "directions", "free_cols", "param_names"]
