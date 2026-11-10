"""Controles comunes para confirmar extremos sin ejecutar un método."""
from collections.abc import Callable
from nicegui import ui


def construir_borrador(seleccion, instruccion: str, al_editar: Callable[[], None]) -> None:
    """Monta inicio, campos, estado y acciones usando callbacks de la selección."""
    seleccion.inicio = ui.button("Seleccionar en el gráfico", color=None, on_click=seleccion.iniciar).classes(
        "boton-discreto")
    seleccion.region = ui.column().classes("w-full gap-2")
    with seleccion.region:
        ui.label(instruccion).classes("text-sm texto-secundario")
        seleccion.campos = tuple(ui.input(etiqueta).classes("w-full matriz-entrada").props(
            "inputmode=decimal maxlength=64") for etiqueta in ("Extremo a del borrador", "Extremo b del borrador"))
        seleccion.estado = ui.label().classes("texto-secundario").props("role=status aria-live=polite")
        with ui.row().classes("w-full gap-2"):
            ui.button("Confirmar intervalo", color=None, on_click=seleccion.confirmar).classes("boton-principal")
            ui.button("Cancelar", color=None, on_click=lambda: seleccion.cancelar(devolver_foco=True)).classes(
                "boton-discreto")
    seleccion.region.on("keydown.escape", lambda: seleccion.cancelar(devolver_foco=True))
    for campo in seleccion.campos:
        campo.on_value_change(al_editar)
    seleccion.region.set_visibility(False)
