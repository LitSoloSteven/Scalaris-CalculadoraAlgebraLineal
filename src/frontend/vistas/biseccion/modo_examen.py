"""Controles y detalle visible del modo examen de bisección."""
from nicegui import ui

from src.frontend.controladores.biseccion.salidas_biseccion import COLUMNAS_EXAMEN, datos_examen


_CLASE_CONTROL_EXAMEN = "biseccion-interruptor-examen texto-principal"


def crear_interruptor_examen(vista) -> ui.switch:
    """Crea el control del resultado con la preferencia de la vista actual."""
    return ui.switch("Modo examen", value=vista.modo_examen,
                     on_change=lambda evento: setattr(vista, "modo_examen", evento.value)).classes(_CLASE_CONTROL_EXAMEN)


def crear_control_examen_lote() -> ui.checkbox:
    """Crea la opción de mostrar el examen en las tablas y copias del lote actual."""
    return ui.checkbox("Modo examen del lote").classes(_CLASE_CONTROL_EXAMEN)


def mostrar_accion_examen(interruptor: ui.switch, fila: dict, estado: str) -> None:
    """Muestra el detalle del paso activo cuando el modo examen está encendido."""
    detalle = datos_examen(fila, estado)
    with ui.column().classes("w-full gap-1").bind_visibility_from(interruptor, "value"):
        for clave, etiqueta in COLUMNAS_EXAMEN:
            ui.label(f"{etiqueta}: {detalle[clave]}").classes("biseccion-numero text-sm")
