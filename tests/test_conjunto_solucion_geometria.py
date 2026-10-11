"""Pruebas del módulo de conjunto solución para geometría analítica."""
from fractions import Fraction
import pytest

from src.backend.geometria.conjunto_solucion import (
    ConjuntoSolucion,
    TipoSolucionGeometria,
    clasificar_conjunto_solucion,
    construir_conjunto_desde_gauss,
    obtener_parametros_solucion,
    tiene_parametros_solucion,
)
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss


def test_clasificar_vacio():
    assert clasificar_conjunto_solucion(None, ()) == TipoSolucionGeometria.VACIO


def test_clasificar_punto():
    assert (
        clasificar_conjunto_solucion((Fraction(1), Fraction(2)), ())
        == TipoSolucionGeometria.PUNTO
    )


def test_clasificar_recta():
    direcciones = ((Fraction(1), Fraction(0)),)
    assert (
        clasificar_conjunto_solucion((Fraction(0), Fraction(0)), direcciones)
        == TipoSolucionGeometria.RECTA
    )


def test_clasificar_plano():
    direcciones = (
        (Fraction(1), Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(1), Fraction(0)),
    )
    assert (
        clasificar_conjunto_solucion((Fraction(0), Fraction(0), Fraction(0)), direcciones)
        == TipoSolucionGeometria.PLANO
    )


def test_clasificar_subespacio_afin():
    direcciones = tuple((Fraction(i), Fraction(0), Fraction(0)) for i in range(3))
    assert (
        clasificar_conjunto_solucion((Fraction(0),) * 3, direcciones)
        == TipoSolucionGeometria.SUBESPACIO_AFIN
    )


def test_construir_desde_gauss_solucion_unica():
    datos = [
        [Fraction(1), Fraction(1), Fraction(3)],
        [Fraction(1), Fraction(-1), Fraction(1)],
    ]
    matriz = Matriz(2, 3, datos)
    resultado = ResolutorGauss(matriz).resolver()
    conjunto = construir_conjunto_desde_gauss(resultado)
    assert conjunto is not None
    assert conjunto.tipo == TipoSolucionGeometria.PUNTO
    assert conjunto.punto == (Fraction(2), Fraction(1))


def test_construir_desde_gauss_sin_solucion():
    datos = [
        [Fraction(1), Fraction(1), Fraction(1)],
        [Fraction(1), Fraction(1), Fraction(2)],
    ]
    matriz = Matriz(2, 3, datos)
    resultado = ResolutorGauss(matriz).resolver()
    conjunto = construir_conjunto_desde_gauss(resultado)
    assert conjunto is not None
    assert conjunto.tipo == TipoSolucionGeometria.VACIO


def test_construir_desde_gauss_soluciones_infinitas():
    datos = [[Fraction(1), Fraction(1), Fraction(1)]]
    matriz = Matriz(1, 3, datos)
    resultado = ResolutorGauss(matriz).resolver()
    conjunto = construir_conjunto_desde_gauss(resultado)

    assert conjunto is not None
    assert conjunto.tipo == TipoSolucionGeometria.RECTA
    assert conjunto.dimension == 1
    assert conjunto.punto == (Fraction(1), Fraction(0))
    assert conjunto.direcciones == ((-Fraction(1), Fraction(1)),)


def test_tiene_parametros_solucion_verdadero():
    assert tiene_parametros_solucion({"solution_param": "algo"})


def test_tiene_parametros_solucion_falso():
    assert not tiene_parametros_solucion({"status": "OK"})


def test_tiene_parametros_solucion_clave_presente_invalida():
    resultado = {
        "status": "INFINITE_SOLUTIONS",
        "solution_param": "x = 1 + t",
        "solution": ["1 + t"],
        "solution_exact": None,
        "free_cols": [1],
    }
    conjunto = construir_conjunto_desde_gauss(resultado)
    assert conjunto is None
    assert tiene_parametros_solucion(resultado)


def test_obtener_parametros_solucion_valido():
    resultado = {
        "solution_param": {
            "num_vars": 2,
            "particular": [Fraction(1), Fraction(0)],
            "directions": [[Fraction(-1), Fraction(1)]],
            "free_cols": [1],
            "param_names": ["t"],
        }
    }
    sp = obtener_parametros_solucion(resultado)
    assert sp is not None


def test_obtener_parametros_solucion_invalido():
    resultado = {
        "solution_param": {
            "num_vars": 2,
            "particular": [1, 0],
            "directions": [[-1, 1]],
            "free_cols": [1],
            "param_names": ["t"],
        }
    }
    assert obtener_parametros_solucion(resultado) is None
