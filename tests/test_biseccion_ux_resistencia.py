"""Casos extremos que llegan a la gráfica y a la lista de candidatos."""
import asyncio
import json
from types import SimpleNamespace

import pytest

from src.frontend.controladores.biseccion.exploracion import resolver_exploracion
from src.frontend.controladores.biseccion.formato_expresion import formatear_expresion
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


@pytest.mark.parametrize(("expresion", "minimo", "maximo", "cantidad"), [
    ("x^2+1", "-2", "2", 0),
    ("x", "-1", "1", 1),
    ("sin(x)", "0.1", "51", 16),
])
def test_lista_de_candidatos_con_0_1_y_16_resultados(expresion, minimo, maximo, cantidad):
    """Las tres densidades producen respuestas finitas para una sola capa visual."""
    respuesta = resolver_exploracion({
        "expresion": expresion, "x_min": minimo, "x_max": maximo, "paso": "0.1",
    })
    assert respuesta["estado"] == "EXITO"
    assert len(respuesta["candidatos"]) == cantidad
    json.dumps(respuesta, allow_nan=False)


def test_rango_extremo_rechaza_la_malla_antes_de_evaluar():
    """Un paso diminuto sobre un rango amplio conserva un estado acotado."""
    respuesta = resolver_exploracion({
        "expresion": "x", "x_min": "-1e100", "x_max": "1e100", "paso": "1e-100",
    })
    assert respuesta["estado"] == "ERROR"
    assert respuesta["evaluaciones"] == 0 and not respuesta["candidatos"]
    assert respuesta["mensaje"]


def test_formula_larga_preserva_coeficientes_sin_truncarlos():
    """La proyección que recibe MathJax conserva todos los dígitos de la expresión."""
    coeficiente = "123456789012345678901234567890"
    representacion = formatear_expresion(f"{coeficiente}*x-({coeficiente}+1)")
    assert representacion["latex"].count(coeficiente) == 2


def test_preparacion_interactiva_publica_desde_su_tarea(monkeypatch):
    """Simula la respuesta JavaScript sin reemplazar la tarea ni su contexto de UI."""
    async def _comprobar(vista):
        vista.cargar_captura(captura_criterio())
        await vista.resolver()
        reproductor = vista.reproductor_pasos
        boton = next(elemento for elemento in reproductor.tarjeta.descendants()
                     if elemento._props.get("aria-label") == "Paso siguiente")
        evento = next(evento for evento in boton._event_listeners.values() if evento.type == "click")
        evento.handler(SimpleNamespace(args={"detail": 1}))
        assert reproductor.indice_actual == 0
        await asyncio.wait_for(reproductor.tarea_paso, timeout=2)
        assert reproductor.indice_actual == 1
        assert reproductor.estado_paso.text == ""

    ejecutar_escenario(monkeypatch, _comprobar)


def test_salir_del_procedimiento_restaura_el_indice_visible(monkeypatch):
    """Cancelar una preparación no deja el deslizador apuntando al destino descartado."""
    async def _comprobar(vista):
        vista.cargar_captura(captura_criterio())
        await vista.resolver()
        reproductor = vista.reproductor_pasos
        deslizador = reproductor.deslizador
        deslizador.set_value(3)
        evento = next(evento for evento in deslizador._event_listeners.values() if evento.type == "change")
        evento.handler(SimpleNamespace(args=[3, False]))
        assert reproductor.indice_solicitado == 3
        pendiente = reproductor.tarea_paso
        reproductor.pausar()
        await asyncio.gather(pendiente, return_exceptions=True)
        assert deslizador.value == reproductor.indice_actual == 0
        assert reproductor.estado_paso.text == ""

    ejecutar_escenario(monkeypatch, _comprobar)
