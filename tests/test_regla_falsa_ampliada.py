"""Contratos numéricos de la configuración ampliada sin alterar el motor clásico."""
import json
import math
from dataclasses import asdict, replace

import pytest

from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.contrato_regla_falsa_ampliada import ConfiguracionReglaFalsa
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada
from src.backend.resolutores.raices.regla_falsa import regla_falsa
from src.backend.resolutores.raices.regla_falsa_ampliada import resolver_regla_falsa_configurada

ENTRADA = EntradaReglaFalsa(expresion="x^2-2", extremo_izquierdo=1, extremo_derecho=2)


def ejecutar(tipo, parametro, entrada=ENTRADA):
    """Resuelve un criterio sobre una entrada canónica para contrastar su autoridad."""
    return resolver_regla_falsa_configurada(ConfiguracionReglaFalsa(entrada, CriterioParada(tipo, parametro)))


def test_residuo_conserva_exactamente_el_resultado_clasico():
    """Compara el sobre completo y las nueve filas con el método clásico."""
    ampliado = ejecutar("residuo", 1e-6)
    assert ampliado.resultado == regla_falsa(ENTRADA)
    assert ampliado.resultado.iteraciones_totales == 9
    assert ampliado.cumplimiento == "CUMPLIDO"


@pytest.mark.parametrize("tipo,parametro", [("residuo", 1e-6), ("ancho", 0.7), ("decimales", 0),
                                             ("relativo", 1), ("iteraciones", 1)])
def test_criterios_publican_metricas_finitas_y_respetan_la_ultima_iteracion(tipo, parametro):
    """Verifica métrica posterior, JSON finito y prioridad frente al límite global."""
    ampliado = ejecutar(tipo, parametro)
    json.dumps(asdict(ampliado), allow_nan=False)
    fila = ampliado.resultado.iteraciones[-1]
    if tipo in ("ancho", "decimales"):
        assert ampliado.metrica_final == fila.intervalo_siguiente[1] - fila.intervalo_siguiente[0]
    ultima = ejecutar(tipo, parametro, replace(ENTRADA, limite_iteraciones=fila.i))
    assert ultima.resultado.codigo_diagnostico != "LIMITE_ITERACIONES"


def test_conteo_no_usa_tolerancia_clasica_como_segunda_parada():
    """El conteo gobierna la parada aunque el residuo ya satisfaga la tolerancia clásica."""
    ampliado = ejecutar("iteraciones", 1, replace(ENTRADA, tolerancia=100))
    assert ampliado.cumplimiento == "CONTEO_COMPLETADO"
    assert ampliado.resultado.aproximacion == pytest.approx(4 / 3)
    assert "precision" in ampliado.resultado.mensaje


def test_igualdad_no_satisface_umbral_estricto():
    """La igualdad con el umbral no satisface los criterios definidos mediante menor que."""
    primera = ejecutar("iteraciones", 1).resultado.iteraciones[0]
    for tipo, metrica in (("residuo", primera.residuo), ("ancho", 2 - primera.aproximacion)):
        salida = ejecutar(tipo, metrica, replace(ENTRADA, limite_iteraciones=1))
        assert salida.cumplimiento == "NO_CUMPLIDO"
        assert salida.resultado.codigo_diagnostico == "LIMITE_ITERACIONES"


def test_relativo_no_aplica_en_primera_fila_y_no_cierra_por_inmovilidad():
    """Distingue un porcentaje ausente del cierre excepcional por estancamiento."""
    primera = ejecutar("relativo", 1e-30, replace(ENTRADA, limite_iteraciones=1))
    assert primera.metrica_final is None
    assert primera.cumplimiento == "NO_APLICA"
    centro = math.sqrt(2)
    vecinos = replace(ENTRADA, extremo_izquierdo=math.nextafter(centro, 0), extremo_derecho=centro)
    salida = ejecutar("relativo", 1e-30, vecinos)
    assert salida.resultado.codigo_diagnostico == "ESTANCAMIENTO_NUMERICO"


def test_cero_elegido_preserva_el_extremo_derecho_sin_cambiar_el_clasico():
    """Revalida el cero elegido y conserva el extremo predeterminado de la API clásica."""
    entrada = replace(ENTRADA, expresion="x*(x-1)", extremo_izquierdo=0, extremo_derecho=1)
    configuracion = ConfiguracionReglaFalsa(entrada, CriterioParada("residuo", 1e-6), 1)
    salida = resolver_regla_falsa_configurada(configuracion)
    assert salida.resultado.aproximacion == 1
    assert salida.resultado.iteraciones == ()
    assert salida.cumplimiento == "NO_APLICA"
    assert regla_falsa(entrada).aproximacion == 0
    for cero in (0.5, True, float("nan"), float("inf"), "1"):
        with pytest.raises(ValueError):
            resolver_regla_falsa_configurada(replace(configuracion, cero_preferido=cero))


@pytest.mark.parametrize("criterio", [None, CriterioParada("otro", 1), CriterioParada("residuo", True),
                                    CriterioParada("iteraciones", 1000000)])
def test_configuracion_invalida_lanza_value_error(criterio):
    """Rechaza criterios desconocidos, tipos inválidos y conteos incompatibles."""
    with pytest.raises(ValueError):
        resolver_regla_falsa_configurada(ConfiguracionReglaFalsa(ENTRADA, criterio))
