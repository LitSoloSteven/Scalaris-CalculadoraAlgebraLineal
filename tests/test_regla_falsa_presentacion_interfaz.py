"""Presentación fiel de éxito, aproximaciones provisionales y diagnósticos."""
import math

import pytest

from src.frontend.controladores.regla_falsa.controlador import resolver_captura
from src.frontend.controladores.regla_falsa.diagnostico import detalles_diagnostico
from src.frontend.controladores.regla_falsa.presentacion import (
    aproximacion_presentada, avisos_resumen, etiqueta_aproximacion,
    metricas_principales, metricas_resumen, titulo_estado,
)


def _respuesta(cambios=None):
    captura = {"expresion": "x^2-2", "extremo_izquierdo": "1", "extremo_derecho": "2"}
    return resolver_captura(captura | (cambios or {}))


@pytest.mark.parametrize("cambios,titulo,etiqueta", [
    ({}, "Convergió por tolerancia de residuo", "Aproximación de la raíz"),
    ({"expresion": "x", "extremo_izquierdo": "0"},
     "Cero evaluado en un extremo, sin iteraciones", "Aproximación de la raíz"),
    ({"expresion": "x-1.5"}, "Cero evaluado en la aproximación de la secante", "Aproximación de la raíz"),
    ({"limite_iteraciones": "1"}, "Límite de iteraciones; tolerancia no alcanzada", "Aproximación provisional"),
    ({"extremo_izquierdo": math.nextafter(math.sqrt(2), -math.inf),
      "extremo_derecho": math.sqrt(2), "tolerancia": "1e-30"},
     "Estancamiento numérico; tolerancia no alcanzada", "Aproximación provisional"),
    ({"expresion": "x^2+1"}, "Sin cambio de signo", "Aproximación no disponible"),
    ({"expresion": "x+"}, "Error de entrada o evaluación", "Aproximación no disponible"),
])
def test_rotulos_siguen_estado_y_motivo_del_motor(cambios, titulo, etiqueta):
    """Los límites nunca se rotulan como éxito ni un cero válido como dato ausente."""
    respuesta = _respuesta(cambios)
    assert titulo_estado(respuesta) == titulo
    assert etiqueta_aproximacion(respuesta) == etiqueta


def test_metricas_y_precision_visual_no_alteran_los_datos():
    """El formato conserva residuo, conteo y tolerancia y no introduce cotas geométricas."""
    respuesta = _respuesta()
    original = respuesta["aproximacion"]
    assert aproximacion_presentada(respuesta, 4) == "x ≈ 1.4142"
    assert respuesta["aproximacion"] == original
    metricas = dict(metricas_resumen(respuesta))
    assert metricas["Tolerancia de residuo"] == format(respuesta["entrada"]["tolerancia"], ".17g")
    assert metricas["Residuo |f(c)|"] == format(respuesta["residuo"], ".17g")
    assert metricas["Iteraciones"] == "9" and metricas["Continuidad"] == "CONFIRMADA"
    assert not any("Cota" in etiqueta for etiqueta in metricas)


def test_presentacion_admite_cero_y_ausencia_de_entrada():
    """Raíz cero, errores léxicos y errores sintácticos producen métricas legibles."""
    cero = _respuesta({"expresion": "x", "extremo_izquierdo": "0"})
    assert aproximacion_presentada(cero, 2) == "x ≈ 0.00"
    assert dict(metricas_principales(cero))["Residuo |f(c)|"] == "0"
    for respuesta in (_respuesta({"expresion": "x+"}), resolver_captura({})):
        assert respuesta["entrada"] is None
        assert aproximacion_presentada(respuesta, 6) == "No disponible"
        assert dict(metricas_principales(respuesta))["Iteraciones"] == "0"
        assert detalles_diagnostico(respuesta)


@pytest.mark.parametrize("precision", [-1, 16, True, "2.5", None])
def test_precision_visual_invalida_se_rechaza(precision):
    """La preferencia de visualización reutiliza la validación existente."""
    with pytest.raises(ValueError):
        aproximacion_presentada(_respuesta(), precision)


def test_diagnostico_de_extremos_no_atribuye_una_secante():
    """Un fallo de dominio inicial conserva la evaluación y no inventa filas válidas."""
    respuesta = _respuesta({"expresion": "sqrt(x)", "extremo_izquierdo": "-1"})
    detalles = dict(detalles_diagnostico(respuesta))
    assert detalles["Etapa del fallo"] == "Evaluación de extremos"
    assert detalles["Abscisa evaluada con fallo"] == "-1"
    assert detalles["Filas válidas conservadas"] == "0"
    assert "Última muestra válida c" not in detalles


def test_diagnostico_estructural_no_inventa_una_abscisa():
    """Una restricción interior sigue siendo estructural y conserva el informe del dominio."""
    respuesta = _respuesta({"expresion": "1/x", "extremo_izquierdo": "-1"})
    detalles = dict(detalles_diagnostico(respuesta))
    assert detalles["Etapa del fallo"] == "Análisis estructural"
    assert detalles["Abscisa evaluada con fallo"] == "No corresponde a una evaluación puntual."
    assert respuesta["informe_continuidad"]["mensaje"] in avisos_resumen(respuesta)


def test_avisos_conservan_normalizacion_y_no_certifican_continuidad():
    """Los avisos del dominio mantienen su mensaje y se deduplican para las salidas."""
    respuesta = _respuesta({"expresion": "sin(x)", "extremo_izquierdo": "4", "extremo_derecho": "2"})
    informe = respuesta["informe_continuidad"]
    assert informe["estado"] == "NO_VERIFICADA"
    assert set(respuesta["advertencias"]) <= set(avisos_resumen(respuesta))
    assert informe["mensaje"] in avisos_resumen(respuesta)
    respuesta["advertencias"] += respuesta["advertencias"]
    assert len(avisos_resumen(respuesta)) == len(set(avisos_resumen(respuesta)))
