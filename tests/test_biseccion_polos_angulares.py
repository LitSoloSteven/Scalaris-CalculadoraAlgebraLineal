"""Polos afines identificados por dominio sin confundir escala con singularidad."""
import json
import math
from dataclasses import asdict
from fractions import Fraction

import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion
from src.backend.resolutores.raices.contrato_exploracion import CandidatoExploracion, EntradaExploracion
from src.backend.resolutores.raices.contrato_resolucion_multiple import CandidatoResolucion, EntradaResolucionMultiple
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada
from src.backend.resolutores.raices.dominio_intervalo import comprobar_dominio_intervalo
from src.backend.resolutores.raices.errores_numericos import ErrorSingularidad
from src.backend.resolutores.raices.exploracion_intervalos import explorar_intervalos
from src.backend.resolutores.raices.polos_trigonometricos import comprobar_polos_tangente
from src.backend.resolutores.raices.resolucion_multiple import resolver_candidatos


@pytest.mark.parametrize("expresion,intervalo,unidad", [
    ("tan(x)", (1, 2), "radianes"),
    ("tan(-x)", (1, 2), "radianes"),
    ("tan(2*x+1)", (0, 1), "radianes"),
    ("sin(tan(x))", (1, 2), "radianes"),
    ("1e-200*tan(x)", (1, 2), "radianes"),
    ("tan(x)", (89, 91), "grados"),
    ("tan(x)", (-91, -89), "grados"),
    ("tan(2*x+30)", (29, 31), "grados"),
    ("tan(30-2*x)", (-31, -29), "grados"),
    ("tan(x/2)", (179, 181), "grados"),
    ("tan(90)", (0, 1), "grados"),
    ("tan(x)", (90, 91), "grados"),
    ("tan(x)", (89, 90), "grados"),
])
def test_restriccion_tangente_afin(expresion, intervalo, unidad):
    """Identifica polos en argumentos afines anidados, invertidos y constantes."""
    with pytest.raises(ErrorSingularidad, match="tangente.*polo"):
        comprobar_dominio_intervalo(expresion, intervalo, unidad_angular=unidad)


@pytest.mark.parametrize("criterio", [CriterioParada("relativo", 1), CriterioParada("ancho", .01),
    CriterioParada("decimales", 4), CriterioParada("residuo", 1e20), CriterioParada("iteraciones", 1)])
def test_polo_impide_exito_de_cualquier_criterio(criterio):
    """Ni residuo amplio ni pocas filas pueden convertir un polo identificado en raíz."""
    resultado = biseccion(EntradaBiseccion("tan(x)", 1, 2, 4, criterio=criterio))
    assert resultado.estado == "ERROR" and resultado.codigo_diagnostico == "SINGULARIDAD_DETECTADA"
    assert resultado.aproximacion is None and resultado.iteraciones == ()
    assert resultado.diagnostico["origen"] == "estructura"
    assert resultado.contexto_fallo["x_fallo"] is None
    assert resultado.intervalo_final == (1, 2)
    assert resultado.criterio_solicitado == criterio


@pytest.mark.parametrize("expresion,intervalo,unidad", [
    ("tan(x)", (-1, 1), "radianes"),
    ("tan(x)", (2, 4), "radianes"),
    ("tan(x)", (89, 89.1), "radianes"),
    ("tan(x)", (1, 2), "grados"),
    ("tan(x)", (91, 269), "grados"),
    ("tan(x)", (-89, 89), "grados"),
    ("tan(1e300)", (0, 1), "radianes"),
    ("tan(1e300)", (0, 1), "grados"),
    ("tan(0*x+1)", (-1e308, 1e308), "radianes"),
    ("1e300*(x-.1)", (-1, 1), "radianes"),
    ("1e-200*(x*x+1)", (-1, 1), "radianes"),
    ("tan(x*x)", (1, 2), "radianes"),
])
def test_no_inventa_polos_por_escala_o_ast_no_afin(expresion, intervalo, unidad):
    """La ausencia de restricción identificada conserva continuidad sin certificar."""
    comprobar_dominio_intervalo(expresion, intervalo, unidad_angular=unidad)


@pytest.mark.parametrize("signo", [-1, 1])
def test_fronteras_pi_sin_tolerancia_arbitraria(signo):
    """Un rango en un lado de las cotas de pi/2 no se rechaza por cercanía al polo."""
    inferior = Fraction(math.pi) / 2
    superior = Fraction(math.nextafter(math.pi, math.inf)) / 2
    comprobar_polos_tangente((signo * inferior, signo * inferior), "radianes")
    comprobar_polos_tangente((signo * superior, signo * superior), "radianes")
    with pytest.raises(ErrorSingularidad):
        comprobar_polos_tangente(tuple(sorted((signo * inferior, signo * superior))), "radianes")


def test_muchos_periodos_sin_enumeracion_ni_flotantes_intermedios():
    """Un rango astronómico y una pendiente desbordada se analizan con racionales acotados."""
    for expresion in ("tan(x)", "tan(1e308*x)"):
        with pytest.raises(ErrorSingularidad):
            comprobar_dominio_intervalo(expresion, (-1e308, 1e308))


def test_extremo_cero_conserva_prioridad_y_aviso_interior():
    """Un cero extremo evaluable no se pierde por el polo interior reconocido."""
    resultado = biseccion(EntradaBiseccion("x*tan(x)", 0, 2, 4))
    assert resultado.estado == "EXITO" and resultado.codigo_diagnostico == "CERO_EVALUADO"
    assert resultado.aproximacion == 0 and resultado.iteraciones == ()
    assert resultado.diagnostico["codigo"] == "SINGULARIDAD_DETECTADA"
    assert "tangente" in resultado.advertencias[0]


def test_extremo_invalido_precede_a_polo_interior():
    """El análisis estructural no oculta overflow real de un extremo."""
    resultado = biseccion(EntradaBiseccion("exp(x)+tan(x)", 1, 1000, 4))
    assert resultado.estado == "ERROR" and resultado.diagnostico["origen"] == "extremos"
    assert resultado.contexto_fallo["x_fallo"] == 1000


@pytest.mark.parametrize("unidad,intervalo", [("radianes", (1, 2)), ("grados", (89, 91))])
def test_exploracion_no_ofrece_biseccion_sobre_polo(unidad, intervalo):
    """Un cambio de signo a través de tan se publica como discontinuidad sin evaluaciones extra."""
    exploracion = explorar_intervalos(EntradaExploracion("tan(x)", *intervalo,
                                      intervalo[1] - intervalo[0], unidad_angular=unidad))
    assert exploracion.evaluaciones == 2
    assert len(exploracion.candidatos) == 1
    assert exploracion.candidatos[0].tipo == "discontinuidad"
    assert "tangente" in exploracion.candidatos[0].mensaje
    json.dumps(asdict(exploracion), allow_nan=False)


def test_lote_reevalua_un_cruce_que_atraviesa_polo():
    """Una etiqueta externa de cruce no evita el diagnóstico compartido del motor."""
    configuracion = EntradaBiseccion("tan(x)", 1, 2, 4)
    candidato = CandidatoResolucion("polo", CandidatoExploracion("cruce", (1, 2)))
    lote = resolver_candidatos(EntradaResolucionMultiple(configuracion, (candidato,)))
    resultado = lote.resultados[0].resultado
    assert resultado == biseccion(configuracion)
    assert resultado.codigo_diagnostico == "SINGULARIDAD_DETECTADA"
    assert resultado.aproximacion is None


@pytest.mark.parametrize("expresion,intervalo", [
    ("(x-90)*tan(x)", (90, 91)),
    ("(x-91)*tan(x)", (90, 91)),
    ("(x-89)*tan(x)", (89, 90)),
    ("x*tan(90)", (0, 1)),
])
def test_polo_extremo_invalida_cero_flotante(expresion, intervalo):
    """Un valor finito de math.tan no convierte un extremo indefinido en cero válido."""
    resultado = biseccion(EntradaBiseccion(expresion, *intervalo, 4, unidad_angular="grados"))
    assert resultado.estado == "ERROR" and resultado.codigo_diagnostico == "SINGULARIDAD_DETECTADA"
    assert resultado.aproximacion is None and resultado.iteraciones == ()
    assert resultado.contexto_fallo["etapa"] == "estructura"
    assert resultado.contexto_fallo["x_fallo"] is None


def test_cero_valido_en_grados_con_polo_solo_interior():
    """El rechazo de extremos indefinidos conserva el cero válido y su aviso de polo interior."""
    resultado = biseccion(EntradaBiseccion("x*tan(x)", 0, 100, 4, unidad_angular="grados"))
    assert resultado.estado == "EXITO" and resultado.codigo_diagnostico == "CERO_EVALUADO"
    assert resultado.aproximacion == 0 and resultado.iteraciones == ()
    assert resultado.diagnostico["codigo"] == "SINGULARIDAD_DETECTADA"
