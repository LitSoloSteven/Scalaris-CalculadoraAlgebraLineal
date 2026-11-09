"""Contexto pedagógico y copia con trazas parciales y estados reales."""
import importlib
import json
from copy import deepcopy

import pytest

from src.backend.excepciones import ErrorDominio
from src.frontend.controladores.regla_falsa.contexto_regla_falsa import resumir_contexto_regla_falsa
from src.frontend.controladores.regla_falsa.controlador import resolver_captura
from src.frontend.controladores.regla_falsa.diagnostico import detalles_diagnostico
from src.frontend.controladores.regla_falsa.presentacion import avisos_resumen, metricas_resumen, titulo_estado
from src.frontend.controladores.regla_falsa.salidas_regla_falsa import datos_copia_regla_falsa, texto_copia_regla_falsa


def _captura():
    return {"expresion": "x^2-2", "extremo_izquierdo": "1", "extremo_derecho": "2"}


@pytest.mark.parametrize("cambios,campo", [
    ({}, "solucion"),
    ({"expresion": "x", "extremo_izquierdo": "0"}, "solucion"),
    ({"limite_iteraciones": 1}, "matriz_resultado"),
    ({"expresion": "x+"}, "matriz_resultado"),
    ({"expresion": "x^2+1"}, "matriz_resultado"),
])
def test_copia_y_contexto_mantienen_estado_y_magnitudes(cambios, campo):
    """Todas las salidas usan el estado real y comparten las métricas de presentación."""
    respuesta = resolver_captura(_captura() | cambios)
    original = deepcopy(respuesta)
    copia = datos_copia_regla_falsa(respuesta, 6)
    assert set(copia) == {campo}
    texto = copia[campo]
    assert texto == texto_copia_regla_falsa(respuesta, 6)
    assert titulo_estado(respuesta) in texto and respuesta["mensaje"] in texto
    for etiqueta, valor in metricas_resumen(respuesta) + detalles_diagnostico(respuesta):
        assert f"{etiqueta}: {valor}" in texto
    assert all(aviso in texto for aviso in avisos_resumen(respuesta))
    contexto = resumir_contexto_regla_falsa(respuesta)
    assert contexto["estado"] == respuesta["estado"]
    assert contexto["aproximacion"] == respuesta["aproximacion"]
    assert contexto["total_iteraciones"] == respuesta["iteraciones_totales"]
    assert "iteraciones" not in contexto and respuesta == original
    json.dumps(contexto, allow_nan=False)


def test_contexto_sin_resultado_y_raiz_de_extremo_no_inventa_filas():
    """La ausencia de cálculo y el éxito sin filas conservan sus estados separados."""
    assert resumir_contexto_regla_falsa(None) is None
    respuesta = resolver_captura(_captura() | {"expresion": "x", "extremo_izquierdo": 0})
    contexto = resumir_contexto_regla_falsa(respuesta)
    assert contexto["aproximacion"] == 0 and "ultima_fila_valida" not in contexto
    assert "x ≈ 0.000000" in texto_copia_regla_falsa(respuesta, 6)


def test_contexto_copia_la_evidencia_y_solo_la_ultima_fila():
    """Los consumidores pedagógicos no pueden mutar ni arrastrar el historial del resultado."""
    respuesta = resolver_captura(_captura())
    contexto = resumir_contexto_regla_falsa(respuesta)
    assert contexto["ultima_fila_valida"] == respuesta["iteraciones"][-1]
    contexto["ultima_fila_valida"]["aproximacion"] = 0
    contexto["informe_continuidad"]["mensaje"] = "otro"
    assert respuesta["iteraciones"][-1]["aproximacion"] != 0
    assert respuesta["informe_continuidad"]["mensaje"] != "otro"


def test_error_tras_filas_validas_conserva_contexto_sin_aproximacion_final(monkeypatch):
    """Un fallo de evaluación conserva las filas del motor y se describe como error."""
    motor = importlib.import_module("src.backend.resolutores.raices.regla_falsa")
    evaluar_original = motor.evaluar
    llamadas = []

    def evaluar_con_fallo(funcion, valor):
        llamadas.append(valor)
        if len(llamadas) == 3:
            raise ErrorDominio("La evaluación no pertenece al dominio.", "DOMINIO_INVALIDO")
        return evaluar_original(funcion, valor)

    monkeypatch.setattr(motor, "evaluar", evaluar_con_fallo)
    respuesta = resolver_captura(_captura())
    assert respuesta["estado"] == "ERROR" and respuesta["iteraciones_totales"] == 2
    assert respuesta["entrada"] is None and respuesta["aproximacion"] is None
    assert respuesta["intervalo_final"] == respuesta["contexto_fallo"]["intervalo_valido"]
    detalles = dict(detalles_diagnostico(respuesta))
    assert detalles["Etapa del fallo"] == "Evaluación de la secante"
    assert detalles["Filas válidas conservadas"] == "2"
    assert detalles["Última muestra válida c"] == format(respuesta["iteraciones"][-1]["aproximacion"], ".17g")
    contexto = resumir_contexto_regla_falsa(respuesta)
    assert contexto["ultima_fila_valida"] == respuesta["iteraciones"][-1]
    assert contexto["contexto_fallo"] == respuesta["contexto_fallo"]
    texto = datos_copia_regla_falsa(respuesta, 6)["matriz_resultado"]
    assert "Aproximación no disponible" in texto and "Convergió" not in texto
    json.dumps(respuesta, allow_nan=False)
