"""El motor conserva autoridad sobre estado, criterios y diagnósticos frente a la gráfica."""
import json

import pytest

from src.backend.resolutores.raices.contrato_biseccion import CONTINUIDAD_CONDICIONAL
from src.frontend.controladores.biseccion import controlador
from src.frontend.controladores.biseccion.presentacion import construir_pasos
from src.frontend.controladores.biseccion.presentacion_criterio import avisos_resumen, texto_resumen
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


@pytest.mark.parametrize("tipo,parametro", [
    ("decimales", 2), ("ancho", ".01"), ("relativo", "1"), ("residuo", ".1"), ("iteraciones", 3),
])
@pytest.mark.parametrize("huecos", [False, True])
def test_grafica_no_cambia_estado_mensaje_criterio_ni_diagnostico(monkeypatch, tipo, parametro, huecos):
    """Incluso una gráfica sin muestras válidas no reescribe las conclusiones del dominio."""
    captura = captura_criterio(tipo, parametro)
    motor = controlador.resolver_captura(captura)
    monkeypatch.setattr(controlador, "muestrear_funcion", lambda entrada: {"x": [], "y": [], "huecos": huecos})
    respuesta = controlador.calcular_presentacion(captura)
    assert {clave: respuesta[clave] for clave in motor} == motor
    assert bool(respuesta.get("aviso_grafica")) is huecos
    assert respuesta["diagnostico"]["codigo"] == respuesta["codigo_diagnostico"]
    assert respuesta["metricas"]["continuidad"] == CONTINUIDAD_CONDICIONAL
    assert construir_pasos(respuesta) == construir_pasos(motor)
    if huecos:
        assert respuesta["aviso_grafica"] in avisos_resumen(respuesta)
        assert respuesta["aviso_grafica"] in texto_resumen(respuesta, 4)
    json.dumps(respuesta, allow_nan=False)


def test_cero_extremo_con_polo_no_cambia_de_estado_al_dibujar():
    """Un hueco gráfico no descarta el cero válido ni borra la advertencia estructural."""
    captura = {**captura_criterio(), "expresion": "(x-1)/(x-0.125)",
               "extremo_izquierdo": "-1", "extremo_derecho": "1"}
    motor = controlador.resolver_captura(captura)
    respuesta = controlador.calcular_presentacion(captura)
    assert respuesta["estado"] == "EXITO"
    assert respuesta["aproximacion"] == 1
    assert not respuesta["iteraciones"]
    assert respuesta["muestra"]["huecos"]
    assert respuesta["diagnostico"] == motor["diagnostico"]
    assert respuesta["codigo_diagnostico"] == "CERO_EVALUADO"
    assert respuesta["diagnostico"]["codigo"] == "SINGULARIDAD_DETECTADA"
    assert respuesta["advertencias"] == motor["advertencias"]
    assert "Continuidad no certificada" in texto_resumen(respuesta, 4)


@pytest.mark.parametrize("expresion,intervalo,limite,estado", [
    ("x**2+1", ("-1", "1"), 100, "SIN_CAMBIO_DE_SIGNO"),
    ("x**2-2", ("1", "2"), 2, "PRECISION_NO_ALCANZADA"),
    ("sin(x)", ("1e16", "10000000000000004"), 100, "PRECISION_NO_ALCANZADA"),
    ("1/x", ("-1", "1"), 100, "ERROR"),
])
def test_cierres_excepcionales_conservan_clasificacion_backend(monkeypatch, expresion, intervalo, limite, estado):
    """Mismo signo, límite, estancamiento y singularidad mantienen su código sin certificar continuidad."""
    captura = {**captura_criterio(), "expresion": expresion, "extremo_izquierdo": intervalo[0],
               "extremo_derecho": intervalo[1], "limite_iteraciones": limite}
    motor = controlador.resolver_captura(captura)
    monkeypatch.setattr(controlador, "muestrear_funcion", lambda entrada: {"x": [], "y": [], "huecos": True})
    respuesta = controlador.calcular_presentacion(captura)
    assert respuesta["estado"] == estado
    assert {clave: respuesta[clave] for clave in motor} == motor
    assert respuesta["diagnostico"]["codigo"] == respuesta["codigo_diagnostico"]
    assert respuesta["metricas"]["continuidad"] == CONTINUIDAD_CONDICIONAL
    json.dumps(respuesta, allow_nan=False)


def test_contexto_de_glosa_y_copia_comparten_diagnostico_y_aviso_visual(monkeypatch):
    """La presentación expone la misma autoridad matemática y separa el aviso de la gráfica."""
    async def comprobar(vista):
        """Publica un cálculo con hueco visual simulado y comprueba sus consumidores."""
        vista.cargar_captura(captura_criterio())
        monkeypatch.setattr(controlador, "muestrear_funcion", lambda entrada: {"x": [], "y": [], "huecos": True})
        await vista.resolver()
        respuesta = vista.ultimo_resultado
        contexto = vista.obtener_contexto_ia().resultado
        assert respuesta["estado"] == contexto["estado"] == "EXITO"
        assert contexto["diagnostico"] == respuesta["diagnostico"]
        assert contexto["aviso_grafica"] == respuesta["aviso_grafica"]
        assert contexto["aviso_grafica"] in texto_resumen(respuesta, 4)
        textos = [getattr(elemento, "text", "") for elemento in vista.contenedor_resultados.descendants()]
        assert contexto["aviso_grafica"] in textos
    ejecutar_escenario(monkeypatch, comprobar)
