"""Preparacion del intervalo de regla falsa y prioridad de diagnosticos."""
import pytest

from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.preparacion_regla_falsa import (
    preparar_intervalo_regla_falsa,
)


def _entrada(expresion="x**2-2", a=1.0, b=2.0, unidad="radianes"):
    return EntradaReglaFalsa(
        expresion=expresion,
        extremo_izquierdo=a,
        extremo_derecho=b,
        tolerancia=1e-6,
        unidad_angular=unidad,
    )


def test_preparado_valido_pol_confirmado_por_cobertura():
    """Un polinomio de cobertura polinomica confirma continuidad por estructura."""
    preparado = preparar_intervalo_regla_falsa(_entrada())
    assert preparado.fallo is None
    assert preparado.restriccion is None
    assert preparado.admite_cero is False
    assert preparado.informe["estado"] == "CONFIRMADA"
    assert preparado.informe["politica"] == "PERMITIR"
    assert all(evaluacion["codigo"] == "" for evaluacion in preparado.evaluaciones)


def test_preparado_detecta_cero_en_extremo():
    """La raiz en un extremo se reconoce en el preparado sin iterar."""
    preparado = preparar_intervalo_regla_falsa(_entrada("x-1", 1.0, 2.0))
    assert preparado.fallo is None
    assert preparado.admite_cero is True


def test_preparado_detecta_ambos_extremos_en_cero():
    """f(a) = f(b) = 0 se conserva como dos ceros evaluados."""
    preparado = preparar_intervalo_regla_falsa(_entrada("x*(x-1)", 0.0, 1.0))
    assert preparado.admite_cero is True


def test_preparado_dominio_invalido_reporte_extremos():
    """Una raiz cuadrada negativa produce fallo con contexto y evaluaciones."""
    preparado = preparar_intervalo_regla_falsa(_entrada("sqrt(x)", -1.0, 1.0))
    assert preparado.fallo is not None
    assert preparado.fallo.estado == "ERROR"
    assert preparado.fallo.codigo_diagnostico == "DOMINIO_INVALIDO"
    assert preparado.fallo.contexto_fallo["etapa"] == "extremos"
    assert preparado.fallo.contexto_fallo["x_fallo"] == -1.0
    codigos = [evaluacion["codigo"] for evaluacion in preparado.fallo.contexto_fallo["extremos"]]
    assert "DOMINIO_INVALIDO" in codigos


def test_preparado_sintaxis_invalida_contexto_sin_abscisa():
    """La sintaxis invalida no atribuye abscisa ni intervalo valido."""
    preparado = preparar_intervalo_regla_falsa(_entrada("sin()"))
    assert preparado.fallo is not None
    assert preparado.fallo.codigo_diagnostico == "EXPRESION_INVALIDA"
    assert preparado.fallo.contexto_fallo["etapa"] == "sintaxis"
    assert preparado.fallo.contexto_fallo["x_fallo"] is None
    assert preparado.fallo.contexto_fallo["intervalo_valido"] is None


def test_preparado_restriccion_estructural_sin_fallo():
    """Un polo afín se anota como restriccion, no como fallo, si los extremos evaluan."""
    preparado = preparar_intervalo_regla_falsa(_entrada("1/(x-0.125)", 0.0, 1.0))
    assert preparado.fallo is None
    assert preparado.restriccion is not None
    assert preparado.restriccion["codigo"] == "SINGULARIDAD_DETECTADA"
    assert preparado.informe["estado"] == "RESTRICCION_DETECTADA"


def test_preparado_sin_cambio_de_signo_no_falla_en_preparacion():
    """El preparado no decide sin cambio de signo: lo hara el motor al primer calculo."""
    preparado = preparar_intervalo_regla_falsa(_entrada("x**2+1", -1.0, 1.0))
    assert preparado.fallo is None
    assert preparado.restriccion is None
    assert preparado.informe["estado"] == "CONFIRMADA"


def test_preparado_expresion_no_polinomica_advierte():
    """cos(x)-x: cobertura insuficiente implica ADVERTIR, no rechazo."""
    preparado = preparar_intervalo_regla_falsa(_entrada("cos(x)-x", 0.0, 1.0))
    assert preparado.fallo is None
    assert preparado.informe["estado"] == "NO_VERIFICADA"
    assert preparado.informe["politica"] == "ADVERTIR"


def test_preparado_revalida_entrada_construida_directamente():
    """Una EntradaReglaFalsa con tolerancia invalida se rechaza antes de compilar."""
    entrada = EntradaReglaFalsa(
    expresion="x-1",
    extremo_izquierdo=0.0,
    extremo_derecho=2.0,
    tolerancia=0.0,
    )
    with pytest.raises(ValueError, match="tolerancia"):
        preparar_intervalo_regla_falsa(entrada)


def test_preparado_normaliza_intervalo_invertido():
    """La entrada normalizada ordena los extremos antes de evaluar."""
    preparado = preparar_intervalo_regla_falsa(_entrada(a=2.0, b=1.0))
    assert preparado.intervalo == (1.0, 2.0)
    assert preparado.entrada.intervalo_invertido is True
    assert preparado.entrada.advertencias


def test_preparado_rechaza_objeto_ajeno():
    """No admite diccionarios ni None como sustituto de la entrada."""
    with pytest.raises(ValueError, match="contrato de regla falsa"):
        preparar_intervalo_regla_falsa({"expresion": "x"})
    with pytest.raises(ValueError, match="contrato de regla falsa"):
        preparar_intervalo_regla_falsa(None)


def test_preparado_en_grados_conserva_unidad():
    """sin(x)-0.5 en grados se evalua con la unidad declarada."""
    preparado = preparar_intervalo_regla_falsa(
        _entrada("sin(x)-0.5", 0.0, 90.0, unidad="grados")
    )
    assert preparado.entrada.unidad_angular == "grados"
    assert preparado.informe["unidad_angular"] == "grados"
    assert preparado.fallo is None