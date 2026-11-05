"""Contadores efectivos, candidatos únicos y aislamiento del refinamiento respecto a bisección."""
import json
from dataclasses import asdict
from importlib import import_module

import pytest

from src.backend.resolutores.raices import contactos_eje
from src.backend.resolutores.raices.contrato_exploracion import EntradaExploracion
from src.backend.resolutores.raices.exploracion_intervalos import explorar_intervalos
from src.backend.resolutores.raices.evaluador_funcion import compilar
from src.backend.resolutores.raices.limites_exploracion import MAXIMO_EVALUACIONES_REFINAMIENTO


@pytest.mark.parametrize("expresion,intervalo,paso,tipo", [
    ("x*x", (-1, 1), .5, "cero_evaluado"),
    ("(x-1)**2", (0, 2), .5, "cero_evaluado"),
    ("x*x", (-.6, .4), .5, "posible_contacto"),
    ("(x-1)**2", (.4, 1.4), .5, "posible_contacto"),
    ("(x-.125)**2", (-.5, .5), .5, "cero_evaluado"),
])
def test_ceros_o_contactos_segun_la_malla(expresion, intervalo, paso, tipo):
    """Las raíces pares se inspeccionan como cero real evaluado o mínimo provisional sin duplicados."""
    resultado = explorar_intervalos(EntradaExploracion(expresion, *intervalo, paso))
    assert len(resultado.candidatos) == 1 and resultado.candidatos[0].tipo == tipo
    candidato = resultado.candidatos[0]
    if candidato.evidencia_contacto is not None:
        assert abs(candidato.valor) < abs(candidato.evidencia_contacto.valor_inicial)
    if tipo == "posible_contacto":
        assert "no certifica" in candidato.mensaje
    else:
        assert candidato.abscisa in candidato.intervalo and candidato.valor == 0
    esperadas = 5 if intervalo[1] - intervalo[0] == 2 else 3
    assert resultado.evaluaciones == esperadas
    json.dumps(asdict(resultado), allow_nan=False)


@pytest.mark.parametrize("presupuesto", [0, 1, 2, 23, 24, 25, 511, 512])
def test_global_instrumentado_conserva_pendientes(monkeypatch, presupuesto):
    """El global se comparte en orden y cuenta intentos reales sin omitir semillas sin reserva."""
    modulo = import_module("src.backend.resolutores.raices.exploracion_intervalos")
    llamadas = []
    def compilar_contada(expresion):
        """Registra cada llamada real del cierre compartido sin agregar evaluaciones propias."""
        funcion = compilar(expresion)
        def evaluar_contada(abscisa):
            """Cuenta evaluaciones de malla y sondeos por igual."""
            llamadas.append(abscisa)
            return funcion(abscisa)
        return evaluar_contada
    monkeypatch.setattr(modulo, "compilar", compilar_contada)
    monkeypatch.setattr(contactos_eje, "MAXIMO_EVALUACIONES_REFINAMIENTO", presupuesto)
    resultado = explorar_intervalos(EntradaExploracion("sin(x-.1)**2+.000001", 0, 200, .5))
    assert resultado.evaluaciones == 401
    assert resultado.evaluaciones_refinamiento == presupuesto - presupuesto % 2
    assert len(llamadas) == resultado.evaluaciones + resultado.evaluaciones_refinamiento
    assert resultado.refinamientos * 2 == resultado.evaluaciones_refinamiento
    assert resultado.refinamiento_agotado and len(resultado.candidatos) > 22
    evidencias = [candidato.evidencia_contacto for candidato in resultado.candidatos]
    assert sum(evidencia.evaluaciones for evidencia in evidencias) == resultado.evaluaciones_refinamiento
    assert any(evidencia.evaluaciones == 0 for evidencia in evidencias)
    assert all(evidencia.evaluaciones <= 24 for evidencia in evidencias)
    assert "presupuesto auxiliar" in resultado.advertencias[-1]
    json.dumps(asdict(resultado), allow_nan=False)


@pytest.mark.parametrize("expresion", ["1e-200", "x*x+1", "1e200*(x*x+1)", "exp(x)", "1/x", "tan(x)"])
def test_sin_semilla_no_hay_trabajo_auxiliar(expresion):
    """Magnitudes, mínimos débiles, polos y huecos no activan refinamientos indiscriminados."""
    resultado = explorar_intervalos(EntradaExploracion(expresion, -1, 1, .5))
    assert resultado.evaluaciones_refinamiento == resultado.refinamientos == 0
    assert not resultado.refinamiento_agotado


@pytest.mark.parametrize("unidad", ["radianes", "grados"])
def test_unidad_propagada_a_sondeos(unidad):
    """El centro refinado conserva la función angular exacta de la captura en ambas unidades."""
    expresion = "sin(x-.1)**2"
    resultado = explorar_intervalos(EntradaExploracion(expresion, -1, 1, .5, unidad_angular=unidad))
    candidato = resultado.candidatos[0]
    assert resultado.unidad_angular == unidad and resultado.evaluaciones_refinamiento > 0
    assert candidato.valor == compilar(expresion, unidad_angular=unidad)(candidato.abscisa)


def test_explorar_contactos_no_ejecuta_biseccion(monkeypatch):
    """La búsqueda entrega candidatos sin ejecutar ni mezclar trazas del motor individual."""
    modulo = import_module("src.backend.resolutores.raices.biseccion")
    def impedir_motor(*argumentos, **opciones):
        """Falla si la exploración intenta resolver un contacto automáticamente."""
        pytest.fail("La exploración no debe ejecutar bisección.")
    monkeypatch.setattr(modulo, "biseccion", impedir_motor)
    resultado = explorar_intervalos(EntradaExploracion("(x-.1)**2", -1, 1, .5))
    assert resultado.candidatos[0].tipo == "posible_contacto"
    assert resultado.evaluaciones_refinamiento <= MAXIMO_EVALUACIONES_REFINAMIENTO


def test_dos_ceros_refinados_son_unicos_y_con_vecino_valido():
    """Dos valles separados conservan sus ceros evaluados sin registros repetidos ni intervalos degenerados."""
    resultado = explorar_intervalos(EntradaExploracion("(x-.125)**2*(x-2.125)**2", -.5, 2.5, .5))
    ceros = [candidato for candidato in resultado.candidatos if candidato.tipo == "cero_evaluado"]
    assert [candidato.abscisa for candidato in ceros] == [.125, 2.125]
    assert len({candidato.abscisa for candidato in ceros}) == 2
    assert all(candidato.abscisa in candidato.intervalo for candidato in ceros)
    assert all(candidato.intervalo[0] < candidato.intervalo[1] for candidato in ceros)


def test_fallo_en_sondeo_conserva_registro_y_contabilidad():
    """Un polo no afín descubierto al refinar no se une ni se transforma en un contacto exitoso."""
    resultado = explorar_intervalos(EntradaExploracion("(x-.02)**2/((x*x-.0625)**2)", -.5, .5, .5))
    assert len(resultado.candidatos) == 1 and resultado.candidatos[0].tipo == "segmento_invalido"
    assert resultado.evaluaciones == 3 and resultado.evaluaciones_refinamiento == 2
    assert resultado.candidatos[0].evidencia_contacto.motivo == "segmento_invalido"
    json.dumps(asdict(resultado), allow_nan=False)
