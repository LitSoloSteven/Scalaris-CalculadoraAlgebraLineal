"""Componente de selección de tema reutilizable para Scalaris."""
from __future__ import annotations

from nicegui import ui
from src.frontend.componentes.icons import icon_svg


def render_theme_button():
    """Renderiza el botón de tema con su menú desplegable accesible."""
    theme_btn = ui.button(color=None).classes("btn-neo-icon p-0 text-main").props(
        'flat ripple=false aria-label="Seleccionar Tema" aria-haspopup="menu" aria-expanded="false"'
    ).tooltip("Seleccionar Tema")

    with theme_btn:
        ui.html(icon_svg("temas"))
        theme_menu = ui.menu().classes("p-2 min-w-[150px]")
        theme_menu.on("show", lambda _, b=theme_btn: b.props('aria-expanded="true"'))
        theme_menu.on("hide", lambda _, b=theme_btn: b.props('aria-expanded="false"'))

        with theme_menu:
            _renderizar_opciones_tema()

    return theme_btn


def _renderizar_opciones_tema() -> None:
    """Genera las tres alternativas de tema gráfico con su muestra de color."""
    opciones = (
        ("Papel", "papel"),
        ("Marea", "marea"),
        ("Medianoche", "medianoche"),
    )
    for etiqueta, id_tema in opciones:
        with ui.menu_item(
            on_click=lambda t=id_tema: ui.run_javascript(f"setTheme('{t}')")
        ).classes("rounded-lg mb-1 flex items-center gap-3 w-full"):
            ui.html(f'<div class="tema-muestra tema-muestra-{id_tema}"></div>')
            ui.label(etiqueta).classes("flex-1")
            ui.html(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
                f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
                f'class="tema-marca-activa tema-marca-{id_tema}">'
                f'<polyline points="20 6 9 17 4 12"></polyline></svg>'
            )
