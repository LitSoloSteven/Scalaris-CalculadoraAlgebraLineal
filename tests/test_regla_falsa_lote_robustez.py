"""Revalidación, coste efectivo y aislamiento del motor de falsa posición múltiple."""
import json
import math
from dataclasses import asdict, replace
from importlib import import_module

import pytest

from src.backend.resolutores.raices.contrato_exploracion import CandidatoExploracion
from src.backend.resolutores.raices.contrato_lote_regla_falsa import EntradaLoteReglaFalsa
from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.contrato_regla_falsa_ampliada import ConfiguracionReglaFalsa
from src.backend.resolutores.raices.contrato_resolucion_multiple import CandidatoResolucion
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada
from src.backend.resolutores.raices.resolucion_multiple_regla_falsa import resolver_candidatos_regla_falsa


def _lote(expresion="x^2-2", intervalo=(1, 2), **opciones):
    base = EntradaReglaFalsa(expresion=expresion, extremo_izquierdo=-10, extremo_derecho=10, **opciones)
    configuracion = ConfiguracionReglaFalsa(base, CriterioParada("residuo", 1e-6))
    return EntradaLoteReglaFalsa(configuracion, (CandidatoResolucion("elegido", CandidatoExploracion("cruce", intervalo)),))


@pytest.mark.parametrize("candidato", [None, CandidatoExploracion("contacto", (1, 2)),
    CandidatoExploracion("restriccion", (1, 2)), CandidatoExploracion("cruce", (2, 1)),
    CandidatoExploracion("cruce", (1, 1)), CandidatoExploracion("cruce", (float("nan"), 2)),
    CandidatoExploracion("cruce", (1, float("inf"))), CandidatoExploracion("cruce", (True, 2)),
    CandidatoExploracion("cruce", (1, 10 ** 400)), CandidatoExploracion("cruce", (1,)),
    CandidatoExploracion("cero_evaluado", (1, 2), 1.5), CandidatoExploracion("cero_evaluado", (1, 2), 1)])
def test_candidato_invalido_no_borra_los_resultados_validos(candidato):
    """Forma, finitud, aptitud y ceros obsoletos quedan aislados por identificador."""
    entrada = _lote()
    candidatos = (CandidatoResolucion("invalido", candidato), entrada.candidatos[0])
    lote = resolver_candidatos_regla_falsa(replace(entrada, candidatos=candidatos))
    assert [r.estado for r in lote.resultados] == ["NO_APTO", "EXITO"]
    assert lote.resultados[0].respuesta is None
    assert lote.resultados[1].respuesta.resultado.aproximacion == pytest.approx(math.sqrt(2), abs=1e-6)
    json.dumps(asdict(lote), allow_nan=False)


def test_cero_del_candidato_prevalece_sobre_la_configuracion_comun():
    """Con dos extremos nulos conserva el segundo y descarta una preferencia común ajena."""
    entrada = _lote("x*(x-1)", (0, 1))
    configuracion = replace(entrada.configuracion, cero_preferido=-10)
    candidato = CandidatoResolucion("segundo", CandidatoExploracion("cero_evaluado", (0, 1), 1))
    lote = resolver_candidatos_regla_falsa(replace(entrada, configuracion=configuracion, candidatos=(candidato,)))
    respuesta = lote.resultados[0].respuesta
    assert respuesta.resultado.aproximacion == 1
    assert respuesta.resultado.iteraciones == ()
    assert respuesta.cumplimiento == "NO_APLICA"
    assert entrada.configuracion.cero_preferido is None


def test_cambios_de_signo_y_dominio_se_revalidan_con_la_funcion_actual():
    """El motor devuelve fallo matemático individual y mantiene una respuesta finita."""
    for expresion, estado in (("x^2+1", "SIN_CAMBIO_DE_SIGNO"), ("1/(x-1.5)", "ERROR"),
                              ("sqrt(x)-1", "ERROR")):
        intervalo = (-1, 2) if expresion.startswith("sqrt") else (1, 2)
        lote = resolver_candidatos_regla_falsa(_lote(expresion, intervalo))
        assert lote.resultados[0].estado == estado
        assert lote.resultados[0].respuesta.resultado.aproximacion is None
        json.dumps(asdict(lote), allow_nan=False)


def test_unidad_angular_procede_de_la_entrada_comun():
    """Los ceros y el informe usan grados sin introducir una unidad contradictoria en el lote."""
    lote = resolver_candidatos_regla_falsa(_lote("sin(x)", (170, 190), unidad_angular="grados"))
    registro = lote.resultados[0]
    assert registro.estado == "EXITO"
    assert registro.respuesta.resultado.aproximacion == pytest.approx(180)
    assert registro.respuesta.resultado.entrada.unidad_angular == "grados"
    assert registro.informe_continuidad["unidad_angular"] == "grados"


@pytest.mark.parametrize("expresion,intervalo,limite", [("x^2-2", (1, 2), 1), ("x^2-2", (1, 2), 100),
    ("x*(x-1)", (0, 1), 5), ("sqrt(x)-1", (-1, 4), 5), ("1/(x-.1234)", (0, 1), 5)])
def test_coste_real_no_supera_la_reserva_de_dos_extremos_mas_limite(monkeypatch, expresion, intervalo, limite):
    """Cuenta invocaciones reales a la función compilada, incluidos intentos fallidos de extremo."""
    preparacion = import_module("src.backend.resolutores.raices.preparacion_regla_falsa")
    compilar_original = preparacion.compilar
    evaluaciones = []
    def compilar_contando(*argumentos, **opciones):
        funcion = compilar_original(*argumentos, **opciones)
        def contar(abscisa):
            evaluaciones.append(abscisa)
            return funcion(abscisa)
        return contar
    monkeypatch.setattr(preparacion, "compilar", compilar_contando)
    lote = resolver_candidatos_regla_falsa(_lote(expresion, intervalo, limite_iteraciones=limite))
    assert 2 <= len(evaluaciones) <= lote.evaluaciones_reservadas == limite + 2
    if limite == 1:
        assert len(evaluaciones) == 3
        assert lote.resultados[0].estado == "LIMITE_ITERACIONES"


def test_lote_nunca_invoca_los_resolutores_de_biseccion(monkeypatch):
    """Una llamada al motor o lote de bisección hace fallar la comprobación de exclusividad."""
    def prohibir(*_argumentos, **_opciones):
        pytest.fail("Regla falsa no debe ejecutar bisección")
    biseccion = import_module("src.backend.resolutores.raices.biseccion")
    multiple = import_module("src.backend.resolutores.raices.resolucion_multiple")
    monkeypatch.setattr(biseccion, "biseccion", prohibir)
    monkeypatch.setattr(biseccion, "resolver_intervalo_preparado", prohibir)
    monkeypatch.setattr(multiple, "resolver_candidatos", prohibir)
    monkeypatch.setattr(multiple, "resolver_intervalo_preparado", prohibir)
    assert resolver_candidatos_regla_falsa(_lote()).resultados[0].estado == "EXITO"


def test_estancamiento_conserva_aproximacion_provisional_y_filas():
    """Un intervalo de flotantes vecinos conserva el cierre del motor sin declarar éxito."""
    centro = math.sqrt(2)
    entrada = _lote(intervalo=(math.nextafter(centro, 0), centro))
    configuracion = replace(entrada.configuracion, criterio=CriterioParada("relativo", 1e-30))
    lote = resolver_candidatos_regla_falsa(replace(entrada, configuracion=configuracion))
    registro = lote.resultados[0]
    assert registro.estado == "ESTANCAMIENTO"
    assert registro.respuesta.resultado.aproximacion is not None
    assert registro.respuesta.cumplimiento != "CUMPLIDO"
    assert lote.filas_generadas == len(registro.respuesta.resultado.iteraciones)
    json.dumps(asdict(lote), allow_nan=False)


def test_fallo_interno_no_filtra_detalles_ni_aborta_el_lote(monkeypatch):
    """Una excepción inesperada conserva los registros siguientes y publica un error genérico."""
    modulo = import_module("src.backend.resolutores.raices.resolucion_multiple_regla_falsa")
    original = modulo.resolver_regla_falsa_configurada
    llamadas = []
    def fallar_primero(configuracion):
        llamadas.append(configuracion)
        if len(llamadas) == 1:
            raise RuntimeError("detalle privado")
        return original(configuracion)
    monkeypatch.setattr(modulo, "resolver_regla_falsa_configurada", fallar_primero)
    entrada = _lote()
    candidatos = (replace(entrada.candidatos[0], identificador="fallo"), entrada.candidatos[0])
    lote = resolver_candidatos_regla_falsa(replace(entrada, candidatos=candidatos))
    assert [r.estado for r in lote.resultados] == ["ERROR", "EXITO"]
    assert "detalle privado" not in lote.resultados[0].mensaje
