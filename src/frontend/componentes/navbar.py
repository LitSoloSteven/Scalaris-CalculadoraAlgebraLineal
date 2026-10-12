"""Barra de navegación contextual y de acceso rápido para Scalaris."""
from __future__ import annotations

import html
import json
from typing import Any
from nicegui import ui


from src.frontend import flags
from src.frontend.componentes.icons import icon_svg
from src.frontend.componentes.selector_tema import renderizar_boton_tema
from src.frontend.navigation import (
    HUB_ROUTE,
    NAV_FLAT_ORDER,
    default_item_key,
    nav_item_href,
    nav_items,
    pillar_for_route,
    tool_by_id,
    tool_by_route,
)


def create_navbar(active_ui=None, active_route: str = "/", active_key: str | None = None, al_alternar_ia=None):
    """Genera la barra de navegación contextual plana o por pilares según flags."""
    clave_activa = default_item_key(active_route) if active_key is None else active_key

    with ui.header().classes("nav-header").props("reveal"):
        _renderizar_logotipo()
        with ui.element("div").classes("panel-card nav-pill pointer-events-auto"):
            if not flags.nav_v2():
                _renderizar_barra_plana(active_ui, active_route, al_alternar_ia)
            else:
                _renderizar_barra_pilares(active_route, clave_activa)

    if flags.nav_v2():
        _registrar_navegacion_reciente(active_route)


def _renderizar_logotipo() -> None:
    """Renderiza el logotipo interactivo enlazado al inicio."""
    with ui.link(target="/").classes(
        "brand-logo-link brand-corner-link pointer-events-auto select-none no-underline"
    ).props('aria-label="Scalaris - Inicio"').tooltip("Scalaris: Inicio"):
        ui.html(
            '<div class="brand-logo-container flex items-center justify-center">'
            '<img src="/assets/LogoOscuro.png" alt="Scalaris" class="brand-logo brand-logo-dark" />'
            '<img src="/assets/LogoClaro.png" alt="Scalaris" class="brand-logo brand-logo-light" />'
            '</div>'
        )


def _renderizar_barra_plana(active_ui: Any, active_route: str, al_alternar_ia=None) -> None:
    """Renderiza la botonera lineal de herramientas en modo clásico."""
    with ui.row().classes("items-center gap-4"):
        for tool_id in NAV_FLAT_ORDER:
            tool = tool_by_id(tool_id)
            is_active = (active_route == tool.route)
            aria_current = ' aria-current="page"' if is_active else ""
            props_str = f'flat ripple=false href="{tool.route}" aria-label="{tool.name}"{aria_current}'
            clase = "btn-neo-icon p-0" + (" nav-active" if is_active else "")
            with ui.button(color=None).classes(clase).props(props_str).tooltip(tool.name):
                ui.html(icon_svg(tool.icon))

        if not flags.dock_enabled():
            def toggle_ai():
                if active_ui and hasattr(active_ui, "ai_panel"):
                    active_ui.ai_panel.toggle()

            with ui.button(on_click=al_alternar_ia or toggle_ai, color=None).classes(
                "btn-neo-icon p-0 text-main"
            ).props('flat ripple=false aria-label="Glosa"').tooltip("Glosa"):
                ui.html(icon_svg("tutor_ia"))

        ui.element("div").classes("nav-sep")
        renderizar_boton_tema()


def _renderizar_barra_pilares(active_route: str, clave_activa: str) -> None:
    """Renderiza la botonera contextual por pilares temáticos (v2)."""
    with ui.element("a").classes("nav-trigger nav-home").props(
        f'href="{HUB_ROUTE}" aria-label="Inicio" title="Inicio"'
    ).tooltip("Inicio"):
        ui.html(icon_svg("inicio"))

    pillar = pillar_for_route(active_route)
    items = nav_items(pillar.id) if pillar is not None else ()
    with ui.element("div").classes("nav-center"):
        _renderizar_items_centro(pillar, items, clave_activa)

    with ui.element("div").classes("theme-switcher-btn nav-theme"):
        renderizar_boton_tema()


def _renderizar_items_centro(pillar: Any, items: Any, clave_activa: str) -> None:
    """Renderiza el distintivo del pilar y los accesos a sus herramientas."""
    if pillar is None or len(items) == 0:
        return
    with ui.element("span").classes("nav-pillar"):
        ui.html(icon_svg(pillar.icon))
        ui.html(html.escape(pillar.short_name), tag="span").classes("nav-pillar-name")

    with ui.element("nav").classes("nav-items").props(
        f'aria-label="Herramientas de {pillar.short_name}"'
    ):
        for item in items:
            _renderizar_item_pilar(item, clave_activa)



def _renderizar_item_pilar(item: Any, clave_activa: str) -> None:
    """Renderiza un elemento de navegación individual dentro de un pilar."""
    is_active = (item.key == clave_activa)
    item_classes = "nav-trigger nav-item" + (" nav-active" if is_active else "")
    item_props = f'href="{nav_item_href(item)}" aria-label="{item.label}" title="{item.label}"'
    if is_active:
        item_props += ' aria-current="page"'
    with ui.element("a").classes(item_classes).props(item_props).tooltip(item.label):
        ui.html(icon_svg(item.icon))
        ui.html(html.escape(item.label), tag="span").classes("nav-label-full")
        ui.html(html.escape(item.short_label), tag="span").classes("nav-label-short")


def _registrar_navegacion_reciente(active_route: str) -> None:
    """Registra la herramienta activa en el historial reciente del cliente y centra el foco."""
    from nicegui import context
    try:
        if not getattr(context.client, "has_socket_connection", False):
            return
        active_tool = tool_by_route(active_route)
        if active_tool is not None:
            ui.run_javascript(
                f"window.scalaris?.recientes?.registrar?.({json.dumps(active_tool.id)});"
            )
        ui.run_javascript("window.scalaris?.navegacion?.centrarActivo?.();")
    except Exception:
        pass

