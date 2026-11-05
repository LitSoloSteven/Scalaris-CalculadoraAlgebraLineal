"""Aceptación del muestreo previo y de su independencia del cálculo principal."""
import asyncio
import json
import math

import pytest
from nicegui import background_tasks, ui

from src.frontend.controladores.biseccion import muestreo
from src.frontend.controladores.biseccion.vista_previa import preparar_vista_previa
from src.frontend.vistas.biseccion.figura import crear_figura_previa
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario
from tests.comun_exploracion_biseccion import activar_accion


@pytest.mark.parametrize("expresion", ["x^2-2", "sin(x)", "1e-200*(x-1)", "x^2+1"])
def test_previa_sin_tolerancia_ni_encierro(expresion):
    """Función y rango bastan para dibujar sin ejecutar el motor de bisección."""
    respuesta = preparar_vista_previa({"expresion": expresion, "x_min": "-2", "x_max": "2"})
    assert respuesta["estado"] == "EXITO"
    assert len(respuesta["muestra"]["x"]) == 401
    assert respuesta["muestra"]["x"][0] == -2 and respuesta["muestra"]["x"][-1] == 2
    assert "iteraciones" not in respuesta and "aproximacion" not in respuesta
    json.dumps(respuesta, allow_nan=False)


@pytest.mark.parametrize("cambio", [
    {"x_min": ""}, {"x_max": None}, {"x_min": True}, {"x_min": "nan"}, {"x_max": "inf"},
    {"x_max": "1e999"}, {"x_min": "2"}, {"x_max": "-3"}, {"x_max": "1" * 65},
    {"expresion": None}, {"expresion": ""}, {"expresion": "x" * 513},
    {"expresion": "__import__('os')"}, {"expresion": "x.__class__"}, {"expresion": "[x][0]"},
    {"expresion": "sin()"}, {"expresion": "1e-999"},
])
def test_captura_invalida_devuelve_error_finito(cambio):
    """Campos vacíos, recursos excesivos y sintaxis ajena se rechazan sin excepciones técnicas."""
    respuesta = preparar_vista_previa({"expresion": "x", "x_min": "-2", "x_max": "2", **cambio})
    assert respuesta["estado"] == "ERROR" and respuesta["mensaje"]
    assert "muestra" not in respuesta
    json.dumps(respuesta, allow_nan=False)


@pytest.mark.parametrize("captura", [None, [], "funcion"])
def test_forma_invalida_es_controlada(captura):
    """El adaptador no presupone un diccionario en llamadas directas."""
    assert preparar_vista_previa(captura)["estado"] == "ERROR"


@pytest.mark.parametrize("expresion, minimo, maximo, mensaje", [
    ("1/x", "-1", "1", "huecos"), ("sqrt(x)", "-2", "-1", "No hay muestras"),
    ("exp(x)", "1000", "1001", "No hay muestras"),
])
def test_huecos_y_rango_sin_valores_reales(expresion, minimo, maximo, mensaje):
    """La gráfica conserva huecos explícitos y explica un rango totalmente inválido."""
    respuesta = preparar_vista_previa({"expresion": expresion, "x_min": minimo, "x_max": maximo})
    figura = crear_figura_previa(respuesta)
    assert mensaje in respuesta["mensaje"]
    assert respuesta["muestra"]["huecos"] and None in figura.data[0].y
    assert figura.data[0].connectgaps is False and figura.layout.hovermode is False
    assert len(figura.data) == 1 and tuple(figura.layout.xaxis.range) == (float(minimo), float(maximo))
    json.dumps(respuesta, allow_nan=False)


def test_presupuesto_fijo_y_extremos_grandes(monkeypatch):
    """Incluso con ancho no representable se consumen exactamente las muestras previstas."""
    evaluadas = []
    def funcion(valor):
        """Registra cada evaluación real para comprobar el presupuesto y su finitud."""
        evaluadas.append(valor)
        return valor
    monkeypatch.setattr(muestreo, "compilar", lambda expresion: funcion)
    respuesta = preparar_vista_previa({"expresion": "x", "x_min": "-1e308", "x_max": "1e308"})
    assert respuesta["estado"] == "EXITO" and len(evaluadas) == muestreo.MUESTRAS_GRAFICA
    assert all(math.isfinite(valor) for valor in evaluadas)
    assert evaluadas[0] == -1e308 and evaluadas[-1] == 1e308
    json.dumps(respuesta, allow_nan=False)


def test_montaje_vacio_y_dibujo_automatico_sin_criterio(monkeypatch):
    """El antirrebote dibuja sin a/b ni precisión y no crea resultado ni historial."""
    async def comprobar(vista):
        """Carga solo la función y espera la tarea real programada desde el campo."""
        panel = vista.vista_previa
        assert panel.minimo.value == "-10" and panel.maximo.value == "10"
        assert panel.tarea is None and "Escribe una función" in panel.estado.text
        vista.decimales.set_value(None)
        vista.expresion.set_value("x^2-1")
        await panel.tarea
        assert panel.respuesta["estado"] == "EXITO"
        assert panel.grafica.figure.layout.hovermode is False
        assert vista.ultimo_resultado is None and vista.historial == []
        assert vista.inferior.value == "" and vista.superior.value == ""
        assert vista.obtener_contexto_ia().resultado is None
    ejecutar_escenario(monkeypatch, comprobar)


def test_rango_formato_y_copia_conservan_resultado_y_candidatos(monkeypatch):
    """Editar el rango y su formato no cambia huella, contexto, historial ni reproductor."""
    async def comprobar(vista):
        """Resuelve el ejercicio, explora y compara identidades tras las acciones visuales."""
        vista.cargar_captura(captura_criterio())
        await vista.resolver()
        panel = vista.vista_previa
        resultado, reproductor, huella = vista.ultimo_resultado, vista.reproductor_pasos, vista._huella_resultado
        contexto, captura = vista.obtener_contexto_ia().resultado, vista.capturar()
        exploracion = vista.exploracion
        exploracion.usar_intervalo()
        await exploracion.explorar()
        candidatos = exploracion.respuesta
        panel.minimo.set_value("-3")
        panel.maximo.set_value("3")
        await panel.tarea
        vista.formato.set_value(9)
        copiar = next(elemento for elemento in panel.minimo.client.elements.values()
                      if isinstance(elemento, ui.button) and elemento.text == "Copiar a y b a la gráfica")
        activar_accion(copiar)
        await panel.tarea
        assert (panel.minimo.value, panel.maximo.value) == ("1", "2")
        assert vista.ultimo_resultado is resultado and vista.reproductor_pasos is reproductor
        assert vista._huella_resultado == huella and vista.capturar() == captura
        assert vista.obtener_contexto_ia().resultado == contexto and len(vista.historial) == 1
        assert exploracion.respuesta is candidatos
    ejecutar_escenario(monkeypatch, comprobar)


def test_error_y_reintento_no_ocultan_resultado_principal(monkeypatch):
    """Un rango visual inválido retira solo la previa y permite reintentar por su botón."""
    async def comprobar(vista):
        """Conserva la resolución ante error local y activa el manejador asíncrono real."""
        vista.cargar_captura(captura_criterio())
        await vista.resolver()
        panel, resultado = vista.vista_previa, vista.ultimo_resultado
        panel.minimo.set_value("20")
        await panel.tarea
        assert panel.respuesta["estado"] == "ERROR" and panel.boton.enabled
        assert not list(panel.contenedor_resultados.descendants())
        assert vista.ultimo_resultado is resultado
        panel.minimo.set_value("-2")
        pendientes = []
        monkeypatch.setattr(background_tasks, "create_or_defer",
                            lambda corrutina, **opciones: pendientes.append(asyncio.create_task(corrutina)))
        activar_accion(panel.boton)
        await asyncio.gather(*pendientes)
        assert panel.respuesta["estado"] == "EXITO" and panel.boton.enabled
        assert vista.ultimo_resultado is resultado
    ejecutar_escenario(monkeypatch, comprobar)
