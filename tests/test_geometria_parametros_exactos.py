"""Estructura, precisión exacta y prioridad de parámetros del conjunto solución."""
from fractions import Fraction
import pytest

from src.backend.geometria.conjunto_solucion import obtener_parametros_solucion


def _crear_parametros_validos():
    return {
        "numero_variables": 2, "particular": [Fraction(1, 3), Fraction(0)],
        "direcciones": [[Fraction(-2, 5), Fraction(1)]],
        "columnas_libres": [1], "nombres_parametros": ["t"],
    }


@pytest.mark.parametrize("clave", ["parametros_solucion", "parametros_solucion"])
def test_parametros_validos_conservan_objeto_y_fracciones(clave):
    """La validación no transforma el diccionario ni sus coeficientes exactos."""
    parametros = _crear_parametros_validos()
    assert obtener_parametros_solucion({clave: parametros}) is parametros
    assert parametros["particular"] == [Fraction(1, 3), Fraction(0)]


@pytest.mark.parametrize("campo,valor", [
    ("numero_variables", 3), ("particular", [Fraction(1)]), ("columnas_libres", []),
    ("nombres_parametros", []), ("particular", [0.5, Fraction(0)]),
    ("direcciones", [[Fraction(1), 1.0]]), ("direcciones", [None]),
])
def test_parametros_malformados_o_aproximados_se_rechazan(campo, valor):
    """Un desajuste estructural o coeficiente aproximado conserva el rechazo histórico."""
    parametros = _crear_parametros_validos()
    parametros[campo] = valor
    assert obtener_parametros_solucion({"parametros_solucion": parametros}) is None


@pytest.mark.parametrize("campo", ["numero_variables", "particular", "direcciones", "columnas_libres", "nombres_parametros"])
def test_campos_ausentes_conservan_resultado_nulo(campo):
    """Los cinco campos obligatorios se validan antes de aceptar la solución."""
    parametros = _crear_parametros_validos()
    del parametros[campo]
    assert obtener_parametros_solucion({"parametros_solucion": parametros}) is None


def test_prioridad_y_alternativa_vacia_se_conservan():
    """La primera estructura no vacía conserva su prioridad frente a la alternativa."""
    primero, segundo = _crear_parametros_validos(), _crear_parametros_validos()
    assert obtener_parametros_solucion({"parametros_solucion": primero, "solution_param": segundo}) is primero
    assert obtener_parametros_solucion({"parametros_solucion": segundo, "solution_param": {}}) is segundo
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
    assert obtener_parametros_solucion({"parametros_solucion": parametros}) is parametros
    assert lecturas == ["numero_variables", "particular", "direcciones", "columnas_libres", "nombres_parametros"]
