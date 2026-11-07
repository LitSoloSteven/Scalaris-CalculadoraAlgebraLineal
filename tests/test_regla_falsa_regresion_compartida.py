"""Regresión compartida de bisección tras extraer validadores comunes."""
import math

import pytest

from src.backend.resolutores.raices.contrato_biseccion import (
    D_MAXIMO,
    LIMITE_ITERACIONES_MAXIMO,
    EntradaBiseccion,
    validar_entrada,
    validar_precision,
)
from src.backend.resolutores.raices.limites_biseccion import (
    D_MAXIMO as D_MAXIMO_FACHADA,
    LIMITE_ITERACIONES_DEFECTO,
    LIMITE_ITERACIONES_MAXIMO as LIMITE_MAX_FACHADA,
    LONGITUD_MAXIMA_EXPRESION,
)
from src.backend.resolutores.raices.limites_raices import (
    D_MAXIMO as D_MAXIMO_RAICES,
    LIMITE_ITERACIONES_DEFECTO as LIMITE_DEFECTO_RAICES,
    LIMITE_ITERACIONES_MAXIMO as LIMITE_MAX_RAICES,
    LONGITUD_MAXIMA_EXPRESION as LONGITUD_MAX_RAICES,
)
from src.backend.resolutores.raices.validacion_raices import (
    validar_expresion,
    validar_extremo,
    validar_limite_iteraciones,
)


def test_constantes_reexportadas_coinciden_con_limites_raices():
    """Los dos nombres publicos de constantes apuntan al mismo valor."""
    assert LIMITE_MAX_FACHADA == LIMITE_MAX_RAICES == LIMITE_ITERACIONES_MAXIMO
    assert D_MAXIMO_FACHADA == D_MAXIMO_RAICES == D_MAXIMO
    assert LIMITE_ITERACIONES_DEFECTO == LIMITE_DEFECTO_RAICES
    assert LONGITUD_MAXIMA_EXPRESION == LONGITUD_MAX_RAICES


@pytest.mark.parametrize("valor", [None, "", "   ", 1, 1.5, True, []])
def test_validar_expresion_rechaza_vacias_y_tipos_ajenos(valor):
    """Las expresiones requieren texto con contenido no vacio."""
    with pytest.raises(ValueError):
        validar_expresion(valor)


def test_validar_expresion_recorta_espacios_y_rechaza_longitud_excesiva():
    """Conserva el comportamiento previo con recorte y limite."""
    assert validar_expresion("  x^2-2  ") == "x^2-2"
    with pytest.raises(ValueError, match=str(LONGITUD_MAX_RAICES)):
        validar_expresion("x" * (LONGITUD_MAX_RAICES + 1))


@pytest.mark.parametrize("valor", [True, False])
def test_validar_extremo_rechaza_booleanos(valor):
    """Los booleanos no son numeros validos para extremos."""
    with pytest.raises(ValueError, match="booleano"):
        validar_extremo(valor, "inferior")


@pytest.mark.parametrize("valor", ["1", [], {}, None])
def test_validar_extremo_rechaza_tipos_no_numericos(valor):
    """Solo int o float se aceptan como extremos."""
    with pytest.raises(ValueError, match="num"):
        validar_extremo(valor, "superior")


@pytest.mark.parametrize("valor", [math.nan, math.inf, -math.inf])
def test_validar_extremo_rechaza_no_finitos(valor):
    """NaN e infinitos no son extremos validos."""
    with pytest.raises(ValueError, match="finito"):
        validar_extremo(valor, "inferior")


def test_validar_extremo_acepta_enteros_y_flotantes_finitos():
    """La conversion a float mantiene el valor del extremo."""
    assert validar_extremo(2, "inferior") == 2.0
    assert validar_extremo(2.5, "superior") == 2.5


def test_validar_extremo_detecta_overflow():
    """Un entero gigante no es convertible y produce un error controlado."""
    with pytest.raises(ValueError, match="capacidad"):
        validar_extremo(10**400, "superior")


def test_validar_limite_acepta_ausencia_como_predeterminado():
    """None sigue siendo equivalente a no especificar limite en biseccion."""
    assert validar_limite_iteraciones(None) == LIMITE_DEFECTO_RAICES


@pytest.mark.parametrize("valor", [True, False, 0, -1, 501, 1.5, "10"])
def test_validar_limite_rechaza_invalidos(valor):
    """Solo enteros del rango admitido son validos."""
    with pytest.raises(ValueError, match="entero"):
        validar_limite_iteraciones(valor)


def test_validar_limite_acepta_limites_validos():
    """1 y el maximo son aceptados sin cambios."""
    assert validar_limite_iteraciones(1) == 1
    assert validar_limite_iteraciones(LIMITE_MAX_RAICES) == LIMITE_MAX_RAICES


def test_validar_entrada_conserva_comportamiento_previo_de_biseccion():
    """La delegacion mantiene normalizacion, defaults y aviso de biseccion."""
    entrada = validar_entrada({
        "expresion": "x**2-2",
        "extremo_izquierdo": 2,
        "extremo_derecho": 1,
        "decimales": 4,
    })
    assert isinstance(entrada, EntradaBiseccion)
    assert entrada.intervalo_invertido
    assert entrada.limite_iteraciones == LIMITE_ITERACIONES_DEFECTO
    assert entrada.unidad_angular == "radianes"


def test_validar_precision_conserva_limites_de_biseccion():
    """Los limites D_MAXIMO siguen siendo los mismos tras la extraccion."""
    assert validar_precision(0) == 0
    assert validar_precision(D_MAXIMO) == D_MAXIMO
    with pytest.raises(ValueError):
        validar_precision(D_MAXIMO + 1)