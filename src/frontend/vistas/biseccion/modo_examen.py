"""Controles y detalle visible del modo examen de bisección."""
from nicegui import ui

from src.frontend.controladores.biseccion.salidas_biseccion import COLUMNAS_EXAMEN, datos_examen


def crear_interruptor_examen(vista=None) -> ui.switch:
    """Crea el control individual con su preferencia o un control local para el lote."""
    etiqueta = "Modo examen" if vista is not None else "Modo examen del lote"
    interruptor = ui.switch(etiqueta, value=bool(vista and vista.modo_examen)).classes(
        "biseccion-interruptor-examen texto-principal")
    if vista is not None:
        interruptor.on_value_change(lambda evento: setattr(vista, "modo_examen", evento.value))
    return interruptor


def mostrar_accion_examen(interruptor: ui.switch, fila: dict, estado: str) -> None:
    """Muestra el detalle del paso activo cuando el modo examen está encendido."""
    detalle = datos_examen(fila, estado)
    with ui.column().classes("w-full gap-1").bind_visibility_from(interruptor, "value"):
        for clave, etiqueta in COLUMNAS_EXAMEN:
            ui.label(f"{etiqueta}: {detalle[clave]}").classes("biseccion-numero text-sm")
