"""Vista didáctica opcional de la decisión de cada secante."""
from nicegui import ui

from src.frontend.controladores.regla_falsa.presentacion_examen import datos_examen


def crear_interruptor_examen(vista) -> ui.switch:
    """Crea una preferencia visual de sesión que no pertenece a la captura matemática."""
    return ui.switch("Modo examen", value=vista.modo_examen,
                     on_change=lambda evento: setattr(vista, "modo_examen", evento.value)).classes("texto-principal")


def mostrar_accion_examen(interruptor: ui.switch, fila: dict) -> None:
    """Explica la misma fila que usa la secante sin alterar el reproductor ni la tabla."""
    with ui.column().classes("w-full min-w-0 gap-1").bind_visibility_from(interruptor, "value"):
        for etiqueta, valor in datos_examen(fila):
            ui.label(f"{etiqueta}: {valor}").classes("regla-falsa-numero text-sm texto-principal")
