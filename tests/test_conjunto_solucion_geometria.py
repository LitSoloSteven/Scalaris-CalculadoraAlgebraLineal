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
    """Verifica clasificar vacio."""
    assert clasificar_conjunto_solucion(None, ()) == TipoSolucionGeometria.VACIA


def test_clasificar_punto():
    """Verifica clasificar punto."""
    assert (
        clasificar_conjunto_solucion((Fraction(1), Fraction(2)), ())
        == TipoSolucionGeometria.PUNTO
    )


def test_clasificar_recta():
    """Verifica clasificar recta."""
    direcciones = ((Fraction(1), Fraction(0)),)
    assert (
        clasificar_conjunto_solucion((Fraction(0), Fraction(0)), direcciones)
        == TipoSolucionGeometria.RECTA
    )


def test_clasificar_plano():
    """Verifica clasificar plano."""
    direcciones = (
        (Fraction(1), Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(1), Fraction(0)),
    )
    assert (
        clasificar_conjunto_solucion((Fraction(0), Fraction(0), Fraction(0)), direcciones)
        == TipoSolucionGeometria.PLANO
    )


def test_clasificar_subespacio_afin():
    """Verifica clasificar subespacio afin."""
    direcciones = tuple((Fraction(i), Fraction(0), Fraction(0)) for i in range(3))
    assert (
        clasificar_conjunto_solucion((Fraction(0),) * 3, direcciones)
        == TipoSolucionGeometria.ESPACIO_AFIN
    )


def test_construir_desde_gauss_solucion_unica():
    """Verifica construir desde gauss solucion unica."""
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
    """Verifica construir desde gauss sin solucion."""
    datos = [
        [Fraction(1), Fraction(1), Fraction(1)],
        [Fraction(1), Fraction(1), Fraction(2)],
    ]
    matriz = Matriz(2, 3, datos)
    resultado = ResolutorGauss(matriz).resolver()
    conjunto = construir_conjunto_desde_gauss(resultado)
    assert conjunto is not None
    assert conjunto.tipo == TipoSolucionGeometria.VACIA


def test_construir_desde_gauss_soluciones_infinitas():
    """Verifica construir desde gauss soluciones infinitas."""
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
    """Verifica tiene parametros solucion verdadero."""
    assert tiene_parametros_solucion({"parametros_solucion": "algo"})


def test_tiene_parametros_solucion_falso():
    """Verifica tiene parametros solucion falso."""
    assert not tiene_parametros_solucion({"estado": "EXITO"})


def test_tiene_parametros_solucion_clave_presente_invalida():
    """Verifica tiene parametros solucion clave presente invalida."""
    resultado = {
        "estado": "SOLUCIONES_INFINITAS",
        "parametros_solucion": "x = 1 + t",
        "solucion": ["1 + t"],
        "solucion_exacta": None,
        "columnas_libres": [1],
    }
    conjunto = construir_conjunto_desde_gauss(resultado)
    assert conjunto is None
    assert tiene_parametros_solucion(resultado)


def test_obtener_parametros_solucion_valido():
    """Verifica obtener parametros solucion valido."""
    resultado = {
        "parametros_solucion": {
            "numero_variables": 2,
            "particular": [Fraction(1), Fraction(0)],
            "direcciones": [[Fraction(-1), Fraction(1)]],
            "columnas_libres": [1],
            "nombres_parametros": ["t"],
        }
    }
    sp = obtener_parametros_solucion(resultado)
    assert sp is not None


def test_obtener_parametros_solucion_invalido():
    """Verifica obtener parametros solucion invalido."""
    resultado = {
        "parametros_solucion": {
            "numero_variables": 2,
            "particular": [1, 0],
            "direcciones": [[-1, 1]],
            "columnas_libres": [1],
            "nombres_parametros": ["t"],
        }
    }
    assert obtener_parametros_solucion(resultado) is None
