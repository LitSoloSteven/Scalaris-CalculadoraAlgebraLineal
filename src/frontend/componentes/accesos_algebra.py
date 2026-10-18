"""Menú compartido de herramientas avanzadas de álgebra."""
from nicegui import ui
from src.frontend.constantes import OPERACION_DETERMINANTE
from src.frontend.navegacion import ruta_de
from src.frontend.componentes.menu_accesible import vincular_estado_menu


def renderizar_accesos_algebra() -> None:
    """Añade accesos reales a determinante, Leontief y transformaciones."""
    with ui.button("Más álgebra", color=None).classes("boton-discreto").props(
        'ripple=false aria-haspopup="menu" aria-label="Más herramientas de álgebra"'
    ) as boton:
        with ui.menu() as menu:
            vincular_estado_menu(boton, menu)
            _renderizar_enlaces()


def _renderizar_enlaces() -> None:
    for etiqueta, destino in (
        ("Determinante", f"{ruta_de('matrices')}?operacion={OPERACION_DETERMINANTE}"),
        ("Modelo de Leontief", ruta_de("leontief")),
        ("Transformaciones lineales", ruta_de("transformaciones")),
    ):
        ui.menu_item(etiqueta, on_click=lambda ruta=destino: ui.navigate.to(ruta)).classes("texto-principal").props('role="menuitem"')
