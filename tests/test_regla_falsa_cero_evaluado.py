"""Cumplimiento del criterio y presentación cuando Regla falsa evalúa un cero."""
import pytest

from src.backend.resolutores.raices.biseccion.contratos.criterios_biseccion import CriterioParada
from src.backend.resolutores.raices.regla_falsa.contratos.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.regla_falsa.contratos.contrato_regla_falsa_ampliada import ConfiguracionReglaFalsa
from src.backend.resolutores.raices.regla_falsa.motor.regla_falsa_ampliada import resolver_regla_falsa_configurada
from src.frontend.controladores.raices.regla_falsa.ejecucion.ejecucion_ampliada import resolver_presentacion
from src.frontend.controladores.raices.regla_falsa.presentacion.presentacion_ampliada import (
    datos_criterio, etiqueta_configurada,
)
from tests.comun_regla_falsa_vista import captura_regla_falsa


@pytest.mark.parametrize(("tipo", "parametro"), [
    ("residuo", 1e-6), ("ancho", 1e-6), ("decimales", 6), ("relativo", 1e-6), ("iteraciones", 5),
])
def test_cero_en_primera_secante_cierra_sin_aplicar_el_criterio(tipo, parametro):
    """Mantiene el motivo real y el cero aunque la métrica pedida no exista todavía."""
    entrada = EntradaReglaFalsa(expresion="x-2", extremo_izquierdo=0, extremo_derecho=4)
    salida = resolver_regla_falsa_configurada(ConfiguracionReglaFalsa(entrada, CriterioParada(tipo, parametro)))

    assert salida.resultado.estado == "EXITO"
    assert salida.resultado.motivo_parada == "raiz_en_aproximacion"
    assert salida.resultado.aproximacion == 2.0
    assert salida.resultado.residuo == 0
    assert salida.resultado.iteraciones_totales == 1
    assert salida.cumplimiento == "NO_APLICA"


def test_cero_elegido_en_extremo_no_completa_el_conteo():
    """Conserva la selección de un extremo cero y la ausencia de iteraciones."""
    entrada = EntradaReglaFalsa(expresion="x-2", extremo_izquierdo=2, extremo_derecho=5)
    salida = resolver_regla_falsa_configurada(ConfiguracionReglaFalsa(entrada, CriterioParada("iteraciones", 5), 2.0))

    assert salida.resultado.estado == "EXITO"
    assert salida.resultado.motivo_parada == "raiz_en_extremo"
    assert salida.resultado.aproximacion == 2.0
    assert salida.resultado.iteraciones == ()
    assert salida.cumplimiento == "NO_APLICA"
    assert salida.metrica_final is None


@pytest.mark.parametrize("inferior", ["0", "2"])
def test_resultado_configurado_presenta_el_cero_sin_rotulo_provisional(inferior):
    """El adaptador y la vista conservan el éxito con un conteo pendiente."""
    captura = captura_regla_falsa(expresion="x-2", extremo_izquierdo=inferior, extremo_derecho="4",
                                  criterio={"tipo": "iteraciones", "parametro": "5"})
    datos = resolver_presentacion(captura)
    respuesta, ampliado = datos["resultado"], datos["ampliado"]

    assert dict(datos_criterio(ampliado, respuesta))["Cumplimiento"] == "Raíz exacta evaluada (residuo 0)"
    assert etiqueta_configurada(respuesta, ampliado) == "Aproximación de la raíz"
