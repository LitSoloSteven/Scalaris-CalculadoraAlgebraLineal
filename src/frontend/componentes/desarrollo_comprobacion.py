"""Presentacion de comprobaciones preparadas por el backend sin reinterpretar sus datos."""
from nicegui import ui
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex


def mostrar_desarrollo(traza: list[dict], titulo: str = "Ver desarrollo de la comprobacion") -> None:
    """Muestra identidad, sustitucion, desarrollo y conclusion en una expansion accesible."""
    if not traza:
        return
    with ui.expansion(titulo, icon="fact_check").classes("w-full panel-tarjeta"):
        for paso in traza:
            ui.label(paso["descripcion"]).classes("font-bold texto-principal")
            renderizar_latex(paso["detalle_latex"])
            ui.label(paso["explicacion"]).classes("texto-secundario")
