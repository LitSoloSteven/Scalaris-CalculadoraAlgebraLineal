"""Pie de interacción, entrada textual, píldora de contexto y activadores del dock."""
from __future__ import annotations

from typing import Any
from nicegui import ui
from src.frontend.componentes.icons import icon_svg


def construir_pie_dock(instancia: Any) -> None:
    """Ensambla el pie interactivo del dock con contexto, chips y área de captura."""
    with ui.column().classes(
        "w-full p-4 border-t border-[var(--border-input)] bg-[var(--bg-elevated)] flex-shrink-0"
    ):
        instancia.render_context_pill()

        instancia.focus_chip_container = ui.row().classes("w-full mt-2 empty:hidden")
        with instancia.focus_chip_container:
            instancia.render_focus_chip_ui()

        instancia.dock_chips_container = ui.column().classes("w-full mt-2")
        instancia._last_chips_ids = ()
        instancia._render_dock_chips()

        _construir_barra_entrada(instancia)


def _construir_barra_entrada(instancia: Any) -> None:
    """Construye el campo de texto expandible y el botón accesible de envío."""
    with ui.row().classes("w-full items-end gap-2 no-wrap mt-2"):
        instancia.input_field = ui.textarea(
            placeholder="Pregunta algo sobre tu ejercicio..."
        ).classes("flex-1 glosa-input glosa-campo-entrada").props("borderless autogrow")
        instancia.input_field.on("keydown.enter.prevent.exact", instancia.send_message_dock)

        ui.button(icon="send", on_click=instancia.send_message_dock, color=None).classes(
            "btn-primary w-10 h-10 p-0 mb-1 flex-shrink-0 glosa-boton-enviar"
        ).props('ripple=false aria-label="Enviar"').tooltip("Enviar")


def renderizar_pildora_contexto(instancia: Any) -> None:
    """Muestra el estado del contexto algebraico activo y su interruptor."""
    enabled = instancia._storage.get("ai_ctx_enabled", True)
    ctx_obj = None
    if enabled and hasattr(instancia.active_ui, "obtener_contexto_ia"):
        try:
            ctx_obj = instancia.active_ui.obtener_contexto_ia()
        except Exception:
            ctx_obj = None

    if ctx_obj is None or getattr(ctx_obj, "empty", False):
        _renderizar_pildora_vacia(instancia, enabled)
        return

    _renderizar_pildora_activa(instancia, ctx_obj, enabled)


def _renderizar_pildora_vacia(instancia: Any, enabled: bool) -> None:
    """Indica la ausencia de contexto disponible."""
    with ui.row().classes("w-full items-center justify-between px-2 py-1 glosa-ctx-panel"):
        ui.label("Sin contexto del ejercicio").classes("text-xs text-sec")
        ui.switch("Auto-adjuntar", value=enabled, on_change=instancia._toggle_ctx).classes(
            "text-xs"
        ).props("dense size=sm")


def _renderizar_pildora_activa(instancia: Any, ctx_obj: Any, enabled: bool) -> None:
    """Construye la etiqueta con el nombre de la herramienta activa y su frescura."""
    lbl = f"Viendo: {ctx_obj.label}"
    if ctx_obj.stale:
        lbl = "Los datos cambiaron desde el último cálculo"
    elif ctx_obj.window_note:
        lbl += f" ({ctx_obj.window_note})"

    classes = "glosa-ctx row items-center gap-2 w-full justify-between px-3 py-2 glosa-ctx-panel glosa-ctx-borde"
    if ctx_obj.stale:
        classes += " desactualizado"

    with ui.row().classes(classes):
        with ui.row().classes("items-center gap-2 min-w-0 flex-1"):
            ui.icon("visibility", size="xs").classes("text-accent")
            ui.label(lbl).classes("glosa-ctx-label truncate text-xs font-semibold").tooltip(lbl)

        with ui.row().classes("items-center gap-3 flex-shrink-0"):
            ui.switch(value=enabled, on_change=instancia._toggle_ctx).props(
                'dense size=sm aria-label="Incluir el contexto del ejercicio"'
            ).tooltip("Activar/desactivar contexto")


def construir_fab_y_scrim() -> None:
    """Genera el botón flotante (FAB) y el fondo oscuro modal (scrim)."""
    with ui.button(color=None).classes("glosa-fab").props(
        'ripple=false data-glosa-toggle aria-controls="glosa-dock" aria-expanded="false" aria-label="Abrir Glosa"'
    ) as fab:
        ui.html(icon_svg("glosa")).classes("text-accent")
    fab.tooltip("Abrir Glosa")

    ui.element("div").classes("glosa-scrim").props("data-glosa-close")
