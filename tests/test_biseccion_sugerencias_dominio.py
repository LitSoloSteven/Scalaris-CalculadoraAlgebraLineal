"""Sugerencias acotadas de dominio comprobadas sin cambiar la ejecución solicitada."""
import json
from dataclasses import asdict
from fractions import Fraction

import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada
from src.backend.resolutores.raices.dominio_intervalo import comprobar_dominio_intervalo
from src.backend.resolutores.raices.evaluador_funcion import compilar, evaluar
from src.backend.resolutores.raices.sugerencias_dominio import sugerir_intervalo_dominio


def test_sqrt_sugiere_intervalo_comprobado_sin_aplicarlo():
    """El fallo original sigue en x=-1 aunque [0,9] sea una alternativa válida."""
    entrada = EntradaBiseccion("sqrt(x)-2", -1, 9, 4)
    resultado = biseccion(entrada)
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DOMINIO_INVALIDO"
    assert resultado.contexto_fallo["x_fallo"] == -1
    assert resultado.aproximacion is None
    assert resultado.iteraciones == ()
    assert resultado.sugerencias[0]["tipo"] == "intervalo_dominio"
    assert resultado.sugerencias[0]["intervalo"] == (0, 9)
    assert (entrada.extremo_izquierdo, entrada.extremo_derecho) == (-1, 9)
    comprobar_dominio_intervalo(entrada.expresion, (0, 9))
    funcion = compilar(entrada.expresion)
    assert (evaluar(funcion, 0), evaluar(funcion, 9)) == (-2, 1)
    json.dumps(asdict(resultado), default=str, allow_nan=False)


@pytest.mark.parametrize("expresion,intervalo,esperado", [
    ("sqrt(2*x-2)-1", (-2, 4), (1, 4)),
    ("sqrt(2-x)-1", (-1, 9), (-1, 2)),
    ("sqrt(x)+sqrt(4-x)-2", (-1, 9), (0, 4)),
    ("sqrt(0*x+1)+sqrt(x)-2", (-1, 9), (0, 9)),
])
def test_interseccion_de_restricciones_afines(expresion, intervalo, esperado):
    """Las pendientes negativas, constantes e intersecciones recortan solo el rango solicitado."""
    assert sugerir_intervalo_dominio(EntradaBiseccion(expresion, *intervalo, 4)) == esperado


@pytest.mark.parametrize("expresion,intervalo", [
    ("sqrt(x*x-1)", (-2, 2)), ("sqrt(sin(x))", (-1, 9)),
    ("sqrt(x)+sqrt(sin(x))", (-1, 9)), ("sqrt(-1)", (-1, 9)),
    ("sqrt(x)+sqrt(-x)", (-1, 9)), ("sqrt(x-10)", (-1, 9)),
    ("sqrt(x)-2", (0, 9)), ("log(x)", (-1, 9)),
    ("sqrt(x)+log(x)", (-1, 9)), ("sqrt(x)+1/(x-1)", (-1, 9)),
    ("sqrt(x)+exp(x)", (-1, 1000)), ("sqrt(x)+exp(-1000)", (-1, 9)),
    ("sqrt(x)+1/x", (-1, 9)), ("sqrt(x", (-1, 9)),
    ("__import__('os')", (-1, 9)),
])
def test_no_inventa_intervalos_no_comprobables(expresion, intervalo):
    """Faltas de afinidad, polos, extremos inválidos y restricciones incompatibles no generan propuesta."""
    assert sugerir_intervalo_dominio(EntradaBiseccion(expresion, *intervalo, 4)) is None


@pytest.mark.parametrize("expresion,comparar", [
    ("sqrt(3*x-1)", "inferior"), ("sqrt(1-3*x)", "superior"),
])
def test_frontera_no_representable_se_redondea_hacia_dominio(expresion, comparar):
    """La conversión de un tercio nunca elige el lado matemáticamente inválido."""
    intervalo = sugerir_intervalo_dominio(EntradaBiseccion(expresion, -1, 1, 4))
    assert intervalo is not None
    if comparar == "inferior":
        assert Fraction(intervalo[0]) >= Fraction(1, 3)
    else:
        assert Fraction(intervalo[1]) <= Fraction(1, 3)
    funcion = compilar(expresion)
    assert evaluar(funcion, intervalo[0]) >= 0
    assert evaluar(funcion, intervalo[1]) >= 0


def test_relativo_cerca_de_cero_ofrece_ancho_sin_cambiar_criterio():
    """Agotar cien filas conserva el relativo solicitado y devuelve solo una acción opcional."""
    resultado = biseccion(EntradaBiseccion("x", -1, 2, 4, criterio=CriterioParada("relativo", 1)))
    assert resultado.estado == "PRECISION_NO_ALCANZADA"
    assert resultado.motivo_parada == "limite_iteraciones"
    assert len(resultado.iteraciones) == 100
    assert resultado.criterio_solicitado == CriterioParada("relativo", 1)
    assert resultado.sugerencias[0]["tipo"] == "criterio_absoluto"
    assert "cero" in resultado.sugerencias[0]["mensaje"]
    assert "parametro" not in resultado.sugerencias[0]


@pytest.mark.parametrize("criterio", [CriterioParada("ancho", .01), CriterioParada("residuo", .01),
                                     CriterioParada("iteraciones", 2), CriterioParada("decimales", 2)])
def test_otro_criterio_no_recibe_cambio_relativo(criterio):
    """La propuesta no reemplaza un criterio absoluto, residual, decimal o de conteo."""
    resultado = biseccion(EntradaBiseccion("x", -1, 2, 4, criterio=criterio))
    assert not resultado.sugerencias


def test_cero_evaluado_no_recibe_sugerencia_de_criterio():
    """Un cero válido tiene salida propia incluso con relativo indefinido."""
    resultado = biseccion(EntradaBiseccion("x", -1, 1, 4, criterio=CriterioParada("relativo", 1)))
    assert resultado.codigo_diagnostico == "CERO_EVALUADO"
    assert not resultado.sugerencias
