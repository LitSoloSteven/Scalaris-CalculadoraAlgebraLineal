"""Prioridades de validación y conservación del contexto numérico del motor."""
import json
from dataclasses import asdict

import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion
from src.backend.resolutores.raices.dominio_intervalo import comprobar_dominio_intervalo
from src.frontend.controladores.biseccion.controlador import resolver_captura


def _resolver(expresion, intervalo):
    return biseccion(EntradaBiseccion(expresion, *intervalo, 4))


@pytest.mark.parametrize("expresion,intervalo,fallo", [
    ("(x-1)*exp(x)", (1, 1000), 1000),
    ("(x-1)*sqrt(x)", (-1, 1), -1),
    ("(x-1)/x", (0, 1), 0),
    ("(x-1)*exp(-x)", (1, 1000), 1000),
])
def test_extremo_invalido_impide_devolver_cero_del_otro(expresion, intervalo, fallo):
    """Dominio, división, overflow y underflow extremos tienen prioridad sobre un cero."""
    resultado = _resolver(expresion, intervalo)
    assert resultado.estado == "ERROR"
    assert resultado.aproximacion is None
    assert resultado.iteraciones == ()
    contexto = resultado.contexto_fallo
    assert contexto["etapa"] == "extremos"
    assert contexto["x_fallo"] == fallo
    assert contexto["intervalo_valido"] is None
    evaluaciones = {evaluacion["x"]: evaluacion for evaluacion in contexto["extremos"]}
    assert evaluaciones[fallo]["valor"] is None
    assert evaluaciones[1]["valor"] == 0
    assert evaluaciones[fallo]["codigo"] == resultado.codigo_diagnostico
    json.dumps(asdict(resultado), default=str, allow_nan=False)


def test_ambos_extremos_invalidos_tienen_diagnosticos_individuales():
    """El fallo izquierdo no evita evaluar y registrar el derecho."""
    resultado = _resolver("sqrt(x)", (-2, -1))
    evaluaciones = resultado.contexto_fallo["extremos"]
    assert [evaluacion["x"] for evaluacion in evaluaciones] == [-2, -1]
    assert [evaluacion["codigo"] for evaluacion in evaluaciones] == ["DOMINIO_INVALIDO"] * 2
    assert resultado.contexto_fallo["x_fallo"] == -2


def test_capacidad_del_intervalo_prevalece_sobre_cero():
    """Un cero finito no habilita un ancho que el contrato no puede representar."""
    resultado = _resolver("x+1e308", (-1e308, 1e308))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "EVALUACION_NO_FINITA"
    assert resultado.contexto_fallo["etapa"] == "extremos"
    resultado = _resolver("x/2+5e307", (-1e308, 1e308))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "ANCHO_NO_REPRESENTABLE"
    assert resultado.contexto_fallo["etapa"] == "capacidad"
    assert resultado.contexto_fallo["x_fallo"] is None
    assert resultado.intervalo_final is None


@pytest.mark.parametrize("expresion", ["(x-1)/(x-0.1234)", "(x+1)/(x-0.1234)"])
def test_cero_extremo_conserva_advertencia_interior(expresion):
    """La restricción interior se conserva sin convertir el cero extremo en un error."""
    resultado = _resolver(expresion, (-1, 1))
    assert resultado.estado == "EXITO"
    assert resultado.codigo_diagnostico == "CERO_EVALUADO"
    assert resultado.aproximacion in (-1, 1)
    assert resultado.intervalo_final == (-1, 1)
    assert resultado.iteraciones == ()
    assert resultado.diagnostico["origen"] == "estructura"
    assert resultado.diagnostico["codigo"] == "SINGULARIDAD_DETECTADA"
    assert resultado.contexto_fallo is None
    assert "Continuidad no certificada" in resultado.advertencias[0]
    with pytest.raises(ValueError):
        comprobar_dominio_intervalo(expresion, (-1, 1))


def test_singularidad_estructural_no_inventa_abscisa_evaluada():
    """La detección analítica no se presenta como un fallo de evaluación puntual."""
    resultado = _resolver("1/(x-0.1234)", (-1, 1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "SINGULARIDAD_DETECTADA"
    assert resultado.contexto_fallo == {
        "etapa": "estructura", "x_fallo": None, "intervalo_valido": (-1, 1)}
    assert resultado.intervalo_final == (-1, 1)
    assert resultado.aproximacion is None


def test_sintaxis_invalida_no_inventa_intervalo_valido_ni_abscisa():
    """Los datos de una captura no equivalen a evaluaciones que nunca ocurrieron."""
    resultado = _resolver("sin()", (-1, 1))
    assert resultado.codigo_diagnostico == "EXPRESION_INVALIDA"
    assert resultado.contexto_fallo == {
        "etapa": "sintaxis", "x_fallo": None, "intervalo_valido": None}
    assert resultado.intervalo_final is None


def test_fallo_en_iteracion_conserva_filas_y_ultimo_intervalo_valido():
    """Un polo no afín alcanza la segunda muestra sin borrar la primera fila válida."""
    resultado = _resolver("(x-0.1)/(x*x-0.25)", (-1, 1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DOMINIO_INVALIDO"
    assert resultado.aproximacion is None
    assert len(resultado.iteraciones) == 1
    assert resultado.iteraciones[0].c == 0
    assert resultado.intervalo_final == (-1, 0)
    assert resultado.contexto_fallo == {
        "etapa": "iteracion", "x_fallo": -0.5, "intervalo_valido": (-1, 0)}
    assert resultado.metricas["iteraciones_totales"] == 1
    assert resultado.metrica_final == 2
    json.dumps(asdict(resultado), default=str, allow_nan=False)


def test_controlador_serializa_el_contexto_sin_perder_la_traza():
    """La adaptación pública mantiene datos de fallo finitos y el criterio solicitado."""
    respuesta = resolver_captura({"expresion": "(x-0.1)/(x*x-0.25)",
                                 "extremo_izquierdo": "-1", "extremo_derecho": "1",
                                 "decimales": "4", "limite_iteraciones": 100})
    assert respuesta["estado"] == "ERROR"
    assert respuesta["contexto_fallo"]["x_fallo"] == -0.5
    assert len(respuesta["iteraciones"]) == 1
    assert respuesta["intervalo_final"] == (-1, 0)
    assert respuesta["criterio_solicitado"] == {"tipo": "decimales", "parametro": 4}
    json.dumps(respuesta, allow_nan=False)
