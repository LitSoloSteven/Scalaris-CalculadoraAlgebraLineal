"""Contratos, presupuestos y paridad del motor al resolver varios candidatos."""
import json
import math
from dataclasses import asdict, replace

import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion
from src.backend.resolutores.raices.contrato_exploracion import CandidatoExploracion, EntradaExploracion
from src.backend.resolutores.raices.contrato_resolucion_multiple import CandidatoResolucion, EntradaResolucionMultiple
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada
from src.backend.resolutores.raices.exploracion_intervalos import explorar_intervalos
from src.backend.resolutores.raices.limites_resolucion_multiple import (
    EVALUACIONES_AUXILIARES_CANDIDATO, MAXIMO_CANDIDATOS_MULTIPLE, MAXIMO_EVALUACIONES_CANDIDATO,
)
from src.backend.resolutores.raices.resolucion_multiple import resolver_candidatos
from src.frontend.controladores.biseccion.resolucion_multiple import resolver_lote
from tests.comun_biseccion_criterios import captura_criterio


def _entrada(expresion="sin(x)", criterio=None, limite=100):
    candidatos = explorar_intervalos(EntradaExploracion(expresion, 1, 10, .1)).candidatos
    registros = tuple(CandidatoResolucion(f"candidato-{indice}", candidato)
                      for indice, candidato in enumerate(candidatos, 1) if candidato.tipo in ("cruce", "cero_evaluado"))
    return EntradaResolucionMultiple(EntradaBiseccion(expresion, 1, 10, 6, limite, criterio=criterio), registros)


def test_tres_raices_con_trazas_independientes():
    """Sin en [1,10] conserva tres respuestas y el aviso de exploración no exhaustiva."""
    entrada = _entrada()
    lote = resolver_candidatos(entrada)
    assert len(lote.resultados) == 3 and not lote.presupuesto_agotado
    assert [registro.resultado.aproximacion for registro in lote.resultados] == pytest.approx(
        [math.pi, 2 * math.pi, 3 * math.pi], abs=1e-6)
    assert len({id(registro.resultado.iteraciones) for registro in lote.resultados}) == 3
    for registro in lote.resultados:
        assert registro.resultado == biseccion(registro.entrada)
        assert all(registro.entrada.extremo_izquierdo <= fila.c <= registro.entrada.extremo_derecho
                   for fila in registro.resultado.iteraciones)
    assert lote.filas_generadas == sum(len(registro.resultado.iteraciones) for registro in lote.resultados)
    assert lote.evaluaciones_reservadas == 3 * (100 + EVALUACIONES_AUXILIARES_CANDIDATO)
    assert "omitir raíces" in lote.advertencias[0] and lote.unidad_angular == "radianes"


@pytest.mark.parametrize("criterio", [CriterioParada("decimales", 2), CriterioParada("ancho", .01),
    CriterioParada("relativo", 1), CriterioParada("residuo", .01), CriterioParada("iteraciones", 3)])
def test_configuracion_preservada_y_paridad_individual(criterio):
    """Cada candidato conserva su criterio, límite y traza exacta frente a resolver por separado."""
    lote = resolver_candidatos(_entrada(criterio=criterio))
    for registro in lote.resultados:
        assert registro.entrada.criterio == criterio and registro.entrada.limite_iteraciones == 100
        assert registro.resultado == biseccion(registro.entrada)
        if criterio.tipo == "iteraciones":
            assert registro.estado == "ITERACIONES_COMPLETADAS" and len(registro.resultado.iteraciones) == 3


@pytest.mark.parametrize("presupuesto, ejecutados", [(105, 0), (106, 1), (211, 1), (212, 2), (318, 3)])
def test_presupuesto_estricto_sin_recortar_criterios(presupuesto, ejecutados):
    """Se reserva antes de evaluar y se conserva una salida explícita por candidato no ejecutado."""
    lote = resolver_candidatos(replace(_entrada(), presupuesto_evaluaciones=presupuesto))
    assert len(lote.resultados) == 3
    assert sum(registro.resultado is not None for registro in lote.resultados) == ejecutados
    assert lote.evaluaciones_reservadas == ejecutados * 106 <= presupuesto
    assert lote.presupuesto_agotado == (ejecutados < 3)
    assert all(registro.estado == "PRESUPUESTO_AGOTADO" and registro.evaluaciones_reservadas == 0
               for registro in lote.resultados[ejecutados:])


@pytest.mark.parametrize("presupuesto", [0, -1, True, 1.5, 4097, float("inf")])
def test_presupuesto_invalido_se_rechaza(presupuesto):
    """No se truncan ni aceptan presupuestos no enteros o superiores al máximo global."""
    with pytest.raises(ValueError):
        resolver_candidatos(replace(_entrada(), presupuesto_evaluaciones=presupuesto))


def test_limites_individual_y_de_cantidad():
    """El máximo individual deriva de 500 y los lotes excesivos se rechazan sin truncar."""
    entrada = _entrada(criterio=CriterioParada("iteraciones", 500), limite=500)
    registros = tuple(replace(entrada.candidatos[0], identificador=str(indice)) for indice in range(16))
    lote = resolver_candidatos(replace(entrada, candidatos=registros))
    assert MAXIMO_EVALUACIONES_CANDIDATO == 506
    assert lote.evaluaciones_reservadas == 8 * 506 and len(lote.resultados) == MAXIMO_CANDIDATOS_MULTIPLE
    with pytest.raises(ValueError):
        resolver_candidatos(replace(entrada, candidatos=registros + (replace(registros[0], identificador="otro"),)))
    with pytest.raises(ValueError):
        resolver_candidatos(replace(entrada, configuracion=replace(entrada.configuracion, limite_iteraciones=501)))


@pytest.mark.parametrize("identificador", ["", " ", "a" * 65, 1, None])
def test_identificadores_invalidos(identificador):
    """Un identificador debe ser textual, no vacío y acotado para cada resultado."""
    entrada = _entrada()
    with pytest.raises(ValueError):
        resolver_candidatos(replace(entrada, candidatos=(replace(entrada.candidatos[0], identificador=identificador),)))


def test_identificadores_duplicados_y_unidad_invalida():
    """No se aceptan colisiones de resultados ni unidades distintas del contrato vigente."""
    entrada = _entrada()
    with pytest.raises(ValueError):
        resolver_candidatos(replace(entrada, candidatos=entrada.candidatos[:1] * 2))
    with pytest.raises(ValueError):
        resolver_candidatos(replace(entrada, unidad_angular="grados"))


@pytest.mark.parametrize("candidato", [
    CandidatoExploracion("posible_contacto", (-1, 1)), CandidatoExploracion("segmento_invalido", (-1, 1)),
    CandidatoExploracion("cruce", (2, 2)), CandidatoExploracion("cruce", (3, 2)),
    CandidatoExploracion("cruce", (True, 2)), CandidatoExploracion("cruce", (float("nan"), 2)),
    CandidatoExploracion("cruce", (-(10 ** 1000), 2)), CandidatoExploracion("cruce", (2, 3)),
    CandidatoExploracion("cero_evaluado", (0, 2), 1, 0), CandidatoExploracion("cero_evaluado", (0, 2), 0, 0),
])
def test_candidatos_no_aptos_no_bloquean_otro(candidato):
    """Ni etiquetas falsas ni valores de muestra antiguos bastan para invocar una bisección."""
    configuracion = EntradaBiseccion("x-1", 0, 2, 4)
    valido = CandidatoExploracion("cruce", (0, 2))
    lote = resolver_candidatos(EntradaResolucionMultiple(configuracion, (
        CandidatoResolucion("invalido", candidato), CandidatoResolucion("valido", valido))))
    assert lote.resultados[0].estado == "NO_APTO" and lote.resultados[0].resultado is None
    assert lote.resultados[1].resultado.aproximacion == 1


def test_polo_individual_y_cero_extremo():
    """Una singularidad conserva su error y no impide devolver el cero de otro intervalo."""
    configuracion = EntradaBiseccion("(x-2)/x", -1, 1, 4)
    candidatos = (CandidatoResolucion("polo", CandidatoExploracion("cruce", (-1, 1))),
                  CandidatoResolucion("cero", CandidatoExploracion("cero_evaluado", (1, 2), 2, 0)))
    lote = resolver_candidatos(EntradaResolucionMultiple(configuracion, candidatos))
    assert lote.resultados[0].resultado.codigo_diagnostico == "SINGULARIDAD_DETECTADA"
    assert lote.resultados[1].resultado.aproximacion == 2
    assert lote.resultados[1].resultado.iteraciones == ()


def test_adaptador_json_y_extremos_principales_vacios():
    """El lote usa sus intervalos candidatos y el mismo adaptador finito del cálculo individual."""
    entrada = _entrada()
    captura = {**captura_criterio(), "expresion": "sin(x)", "extremo_izquierdo": "", "extremo_derecho": ""}
    datos = {"configuracion": captura, "candidatos": tuple(asdict(registro) for registro in entrada.candidatos)}
    respuesta = resolver_lote(datos)
    assert respuesta["estado"] == "LOTE_COMPLETADO" and len(respuesta["resultados"]) == 3
    for registro in respuesta["resultados"]:
        assert registro["respuesta"]["criterio_solicitado"] == {"tipo": "decimales", "parametro": 4}
    json.dumps(respuesta, allow_nan=False)


@pytest.mark.parametrize("captura", [None, {}, {"configuracion": {}, "candidatos": []},
    {"configuracion": {}, "candidatos": [{"candidato": {"intervalo": [0]}}]}])
def test_adaptador_captura_invalida(captura):
    """Las entradas de forma inválida reciben un error público serializable."""
    respuesta = resolver_lote(captura)
    assert respuesta["estado"] == "ERROR" and respuesta["resultados"] == ()
    json.dumps(respuesta, allow_nan=False)
