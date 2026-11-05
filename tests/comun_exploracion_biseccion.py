"""Preparación del panel y activación de sus controles reales en escenarios aislados."""
from nicegui import ui

from tests.comun_biseccion_criterios import captura_criterio


def preparar_exploracion(vista, expresion="x^2-1", paso=".5"):
    """Carga función y rango independiente sin ejecutar ningún servicio."""
    vista.cargar_captura({**captura_criterio(), "expresion": expresion})
    panel = vista.exploracion
    panel.minimo.set_value("-2")
    panel.maximo.set_value("2")
    panel.paso.set_value(paso)
    return panel


def acciones_exploracion(panel):
    """Devuelve botones de selección que pertenecen a los registros actuales."""
    return [elemento for elemento in panel.contenedor_resultados.descendants()
            if isinstance(elemento, ui.button)]


def activar_accion(boton):
    """Activa el manejador click del botón real como lo haría el transporte de NiceGUI."""
    manejador = next(evento.handler for evento in boton._event_listeners.values() if evento.type == "click")
    manejador(None)
