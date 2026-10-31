"""Presentación compartida del historial de capturas de modelos matriciales."""
from nicegui import ui

from src.frontend import textos


def renderizar_registro_captura(registro: dict, cargar) -> None:
    """Presenta un registro con restauración explícita y sin repetir el cálculo."""
    with ui.column().classes("w-full panel-tarjeta p-3"):
        ui.label(registro["hora"]).classes("texto-secundario")
        ui.label(registro["mensaje"]).classes("texto-principal")
        ui.button(textos.MODELOS_RESTAURAR, color=None, on_click=lambda evento: cargar(
            registro["captura"])).classes("boton-discreto").props("ripple=false")


def renderizar_historial_capturas(contenedor, registros: list[dict], cargar) -> None:
    """Actualiza el historial con su estado vacío y acciones de restauración."""
    contenedor.clear()
    with contenedor:
        if not registros:
            ui.label(textos.MODELOS_HISTORIAL_VACIO).classes("texto-secundario")
        for registro in registros:
            renderizar_registro_captura(registro, cargar)
