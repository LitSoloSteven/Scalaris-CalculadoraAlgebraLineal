"""Chips interactivos de sugerencias, preguntas de seguimiento y botón de explicación."""
from __future__ import annotations

import html
from typing import Any, Callable
from nicegui import ui


def _is_keyboard_event(evento: Any) -> bool:
    """Determina si un evento de interacción fue originado por teclado verificando detail."""
    args = getattr(evento, "args", evento)
    if isinstance(args, dict):
        return args.get("detail") == 0
    if isinstance(args, (int, float)):
        return args == 0
    if isinstance(args, (list, tuple)) and len(args) > 0:
        primer_elem = args[0]
        if isinstance(primer_elem, dict):
            return primer_elem.get("detail") == 0
        return primer_elem == 0
    return False


def render_chip_row(suggestions: Any, on_pick: Callable, *, variant: str = "dock", disabled: bool = False):
    """Renderiza la fila horizontal o bloque de preguntas sugeridas."""
    cls_container = "glosa-chips" + (" glosa-chips-inline" if variant == "inline" else "")
    if disabled:
        cls_container += " glosa-chips-deshabilitado"

    contenedor = ui.element("div").classes(cls_container).props(
        'role="group" aria-label="Preguntas sugeridas"'
    )
    if disabled:
        contenedor.props('aria-disabled="true"')

    botones = []
    with contenedor:
        for sugerencia in suggestions:
            btn = _crear_boton_chip(sugerencia, on_pick, variant=variant, disabled=disabled)
            botones.append(btn)

    return contenedor, botones


def _crear_boton_chip(sugerencia: Any, on_pick: Callable, *, variant: str, disabled: bool) -> ui.element:
    """Construye un botón individual de chip con su manejador de evento."""
    btn_cls = "glosa-chip" + (" glosa-chip-inline" if variant == "inline" else "")
    btn = ui.element("button").classes(btn_cls).props('type="button"')
    with btn:
        ui.html(f'<span class="glosa-chip-texto">{html.escape(sugerencia.text)}</span>')

    if disabled:
        btn.props('disabled aria-disabled="true"')

    def manejador(e):
        on_pick(sugerencia, _is_keyboard_event(e))

    btn.on("click", manejador, args=["detail"])
    return btn


def render_followups(followups: Any, on_pick: Callable, *, disabled: bool = False):
    """Renderiza las alternativas de seguimiento didáctico tras una respuesta."""
    cls_container = "glosa-followups w-full mt-2" + (" glosa-chips-deshabilitado" if disabled else "")
    contenedor = ui.element("div").classes(cls_container).props(
        'role="group" aria-label="Seguimientos" aria-live="off"'
    )
    if disabled:
        contenedor.props('aria-disabled="true"')

    botones = []
    with contenedor:
        for seguimiento in followups:
            btn = ui.element("button").classes("glosa-followup").props('type="button"')
            with btn:
                ui.html(f'<span class="glosa-chip-texto">{html.escape(seguimiento.label)}</span>')

            if disabled:
                btn.props('disabled aria-disabled="true"')

            def manejador(e, s=seguimiento):
                on_pick(s, _is_keyboard_event(e))

            btn.on("click", manejador, args=["detail"])
            botones.append(btn)

    return contenedor, botones


def render_explain_button(indice_paso: int, total_pasos: int, op: str, on_click: Callable, *, is_loading: bool = False) -> ui.button | None:
    """Renderiza el botón accesible 'Explicar paso' para un paso algebraico concreto."""
    from src.frontend import flags
    from src.frontend.suggestions import glosa_configured
    from src.frontend.componentes.icons import icon_svg

    if not flags.dock_enabled():
        return None

    configurado = glosa_configured()
    with ui.button(color=None).classes("glosa-explain-btn").props(
        f'aria-label="Explicar paso {indice_paso}" round flat ripple=false'
    ) as btn:
        ui.html(icon_svg("explicar_paso"))

    btn.tooltip("Explicar este paso" if configurado else "Glosa no está configurada")
    if is_loading or not configurado:
        btn.props("disabled")
        if is_loading:
            btn.classes("is-loading")
        return btn

    def manejador(e):
        if _is_keyboard_event(e):
            ui.run_javascript(
                "document.documentElement.setAttribute('data-glosa-instant', 'true'); "
                "setTimeout(() => document.documentElement.removeAttribute('data-glosa-instant'), 100);"
            )
        on_click(indice_paso)

    btn.on("click", manejador, args=["detail"])
    return btn


def render_focus_chip(text: str, on_remove: Callable) -> ui.element:
    """Renderiza la cápsula visual de foco activo en la cabecera del dock."""
    chip = ui.element("div").classes("glosa-explain-focus").props(f'title="{html.escape(text)}"')
    with chip:
        ui.icon("center_focus_strong").classes("glosa-explain-focus-icon")
        ui.label(text).classes("glosa-explain-focus-text")
        ui.button(icon="close", color=None, on_click=on_remove).classes(
            "glosa-explain-focus-close"
        ).props('round flat size=xs ripple=false aria-label="Quitar foco"').tooltip("Quitar foco")
    return chip
