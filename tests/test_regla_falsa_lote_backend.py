"""Comportamiento de lotes de falsa posición, paridad y límites globales."""
import json
from dataclasses import asdict, replace
from importlib import import_module

import pytest

from src.backend.resolutores.raices.contrato_exploracion import CandidatoExploracion
from src.backend.resolutores.raices.contrato_lote_regla_falsa import EntradaLoteReglaFalsa
from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.contrato_regla_falsa_ampliada import ConfiguracionReglaFalsa
from src.backend.resolutores.raices.contrato_resolucion_multiple import CandidatoResolucion
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada
from src.backend.resolutores.raices.regla_falsa_ampliada import resolver_regla_falsa_configurada
from src.backend.resolutores.raices.resolucion_multiple_regla_falsa import resolver_candidatos_regla_falsa


def _entrada(expresion="x^3-x", criterio=None, limite=100):
    base = EntradaReglaFalsa(expresion=expresion, extremo_izquierdo=-2,
                            extremo_derecho=2, limite_iteraciones=limite)
    configuracion = ConfiguracionReglaFalsa(base, criterio or CriterioParada("residuo", 1e-6))
    candidatos = tuple(CandidatoResolucion(f"raiz-{indice}", CandidatoExploracion("cruce", intervalo))
                       for indice, intervalo in enumerate(((-1.2, -.8), (-.2, .2), (.8, 1.2))))
    return EntradaLoteReglaFalsa(configuracion, candidatos)


def test_tres_raices_con_orden_y_trazas_independientes():
    """Conserva identificadores y filas propias alrededor de las tres raíces del polinomio."""
    entrada = _entrada()
    lote = resolver_candidatos_regla_falsa(entrada)
    assert [registro.identificador for registro in lote.resultados] == [c.identificador for c in entrada.candidatos]
    assert [registro.estado for registro in lote.resultados] == ["EXITO"] * 3
    assert [r.respuesta.resultado.aproximacion for r in lote.resultados] == pytest.approx([-1, 0, 1], abs=1e-6)
    assert len({id(r.respuesta.resultado.iteraciones) for r in lote.resultados}) == 3
    assert lote.filas_generadas == sum(len(r.respuesta.resultado.iteraciones) for r in lote.resultados)
    assert lote.evaluaciones_reservadas == 306
    assert not lote.presupuesto_agotado
    assert "omitir raíces" in lote.advertencias[0]
    json.dumps(asdict(lote), allow_nan=False)


@pytest.mark.parametrize("criterio", [CriterioParada("residuo", 1e-6), CriterioParada("ancho", .2),
    CriterioParada("decimales", 1), CriterioParada("relativo", 1), CriterioParada("iteraciones", 2)])
def test_paridad_con_resoluciones_individuales(criterio):
    """Los cinco criterios conservan exactamente el resultado configurado por intervalo."""
    entrada = _entrada(criterio=criterio)
    for registro, candidato in zip(resolver_candidatos_regla_falsa(entrada).resultados, entrada.candidatos):
        inferior, superior = candidato.candidato.intervalo
        individual = replace(entrada.configuracion, entrada=replace(entrada.configuracion.entrada,
                             extremo_izquierdo=inferior, extremo_derecho=superior))
        assert registro.respuesta == resolver_regla_falsa_configurada(individual)
        assert registro.respuesta.resultado.metodo == "regla_falsa"
        assert registro.informe_continuidad == registro.respuesta.resultado.informe_continuidad


@pytest.mark.parametrize("presupuesto,ejecutados", [(1, 0), (101, 0), (102, 1), (203, 1), (204, 2), (306, 3)])
def test_reserva_estricta_sin_ejecutar_candidatos_fuera_de_presupuesto(monkeypatch, presupuesto, ejecutados):
    """Reserva el coste máximo antes de cualquier llamada y no recorta el criterio solicitado."""
    modulo = import_module("src.backend.resolutores.raices.resolucion_multiple_regla_falsa")
    llamadas = []
    def resolver(configuracion):
        llamadas.append(configuracion)
        return resolver_regla_falsa_configurada(configuracion)
    monkeypatch.setattr(modulo, "resolver_regla_falsa_configurada", resolver)
    lote = resolver_candidatos_regla_falsa(replace(_entrada(), presupuesto_evaluaciones=presupuesto))
    assert len(llamadas) == ejecutados
    assert lote.evaluaciones_reservadas == ejecutados * 102 <= presupuesto
    assert lote.presupuesto_agotado == (ejecutados < 3)
    assert all(r.estado == "PRESUPUESTO_AGOTADO" and r.respuesta is None and r.evaluaciones_reservadas == 0
               for r in lote.resultados[ejecutados:])


@pytest.mark.parametrize("presupuesto", [0, -1, True, 1.5, 4097, float("inf")])
def test_presupuestos_invalidos_no_son_truncados(presupuesto):
    """Rechaza tipos y magnitudes no permitidos mediante ValueError global."""
    with pytest.raises(ValueError):
        resolver_candidatos_regla_falsa(replace(_entrada(), presupuesto_evaluaciones=presupuesto))


@pytest.mark.parametrize("identificador", ["", "   ", "x" * 65, None, 7])
def test_identificadores_invalidos_rechazan_el_lote(identificador):
    """El identificador estable debe ser texto no vacío y acotado a 64 caracteres."""
    entrada = _entrada()
    with pytest.raises(ValueError):
        resolver_candidatos_regla_falsa(replace(entrada, candidatos=(replace(entrada.candidatos[0],
                                                                           identificador=identificador),)))


def test_formas_globales_duplicados_y_limites_de_cantidad():
    """Valida el contrato antes de resolver y admite exactamente dieciséis registros únicos."""
    entrada = _entrada()
    registros = tuple(replace(entrada.candidatos[0], identificador=str(indice)) for indice in range(16))
    assert len(resolver_candidatos_regla_falsa(replace(entrada, candidatos=registros)).resultados) == 16
    invalidas = [None, replace(entrada, configuracion=None), replace(entrada, candidatos=()),
                replace(entrada, candidatos=list(entrada.candidatos)), replace(entrada, candidatos=(None,)),
                replace(entrada, candidatos=(entrada.candidatos[0],) * 2),
                replace(entrada, candidatos=registros + (replace(registros[0], identificador="extra"),))]
    for invalida in invalidas:
        with pytest.raises(ValueError):
            resolver_candidatos_regla_falsa(invalida)


def test_configuracion_global_invalida_falla_antes_de_evaluar(monkeypatch):
    """Sintaxis, unidad, entrada y criterio inválidos impiden iniciar cualquier candidato."""
    modulo = import_module("src.backend.resolutores.raices.resolucion_multiple_regla_falsa")
    def prohibir(_configuracion):
        pytest.fail("No debe resolver con una configuración global inválida")
    monkeypatch.setattr(modulo, "resolver_regla_falsa_configurada", prohibir)
    entrada = _entrada()
    base = entrada.configuracion
    configuraciones = [replace(base, entrada=None), replace(base, criterio=None),
                      replace(base, criterio=CriterioParada("iteraciones", 101)),
                      replace(base, entrada=replace(base.entrada, expresion="x+")),
                      replace(base, entrada=replace(base.entrada, unidad_angular="otra"))]
    for configuracion in configuraciones:
        with pytest.raises(ValueError):
            resolver_candidatos_regla_falsa(replace(entrada, configuracion=configuracion))
