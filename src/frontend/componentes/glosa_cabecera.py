"""Cabecera accesible y controles de cierre del dock de Glosa."""
from __future__ import annotations

from typing import Callable
from nicegui import ui
from src.frontend.componentes.icons import icon_svg


def construir_cabecera_dock(al_limpiar: Callable) -> None:
    """Construye la barra superior fija del dock con título, botón de vaciado y botón de cierre."""
    with ui.row().classes(
        "w-full items-center justify-between p-4 border-b border-[var(--border-input)] flex-shrink-0"
    ):
        with ui.row().classes("items-center gap-3 min-w-0 flex-1"):
            ui.html(icon_svg("glosa")).classes("text-accent flex-shrink-0")
            with ui.column().classes("gap-0 min-w-0 w-full"):
                ui.label("Glosa").classes("font-bold text-lg text-main truncate w-full").tooltip("Glosa")
                ui.label("Notas al margen de cada paso").classes(
                    "text-sec fs-small truncate w-full"
                ).tooltip("Notas al margen de cada paso")

        with ui.row().classes("gap-2 flex-shrink-0 ml-2"):
            ui.button(icon="delete_sweep", on_click=al_limpiar, color=None).classes(
                "btn-neo-icon w-8 h-8 p-0 text-sec"
            ).props('ripple=false aria-label="Limpiar conversación"').tooltip("Limpiar conversación")
            ui.button(icon="close", color=None).classes("btn-neo-icon w-8 h-8 p-0").props(
                'ripple=false data-glosa-close aria-label="Cerrar Glosa"'
            ).tooltip("Cerrar")
