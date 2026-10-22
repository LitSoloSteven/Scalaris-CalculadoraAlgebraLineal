"""Entrada textual, contexto y activadores del panel lateral de Glosa."""
from __future__ import annotations

from typing import Any
from nicegui import ui
from src.frontend.componentes.glosa_entrada import EstiloEntradaGlosa, construir_entrada_glosa
from src.frontend.componentes.iconos import icono_svg


def construir_pie_lateral(instancia: Any) -> None:
    """Ensambla el pie del panel lateral con contexto, sugerencias y área de captura."""
    with ui.column().classes(
        "w-full p-4 border-t border-[var(--border-input)] bg-[var(--bg-elevated)] flex-shrink-0"
    ):
        instancia.renderizar_pildora_contexto()

        instancia.contenedor_foco = ui.row().classes("w-full mt-2 empty:hidden")
        with instancia.contenedor_foco:
            instancia.renderizar_capsula_foco_interfaz()

        instancia.contenedor_sugerencias = ui.column().classes("w-full mt-2")
        instancia._identificadores_sugerencias = ()
        instancia._renderizar_sugerencias_laterales()

        construir_entrada_glosa(instancia, EstiloEntradaGlosa(
            clases_contenedor="w-full items-end gap-2 no-wrap mt-2",
            clases_campo="flex-1 glosa-entrada glosa-campo-entrada",
            clases_boton="boton-principal w-10 h-10 p-0 mb-1 flex-shrink-0 glosa-boton-enviar",
            texto_ayuda="Pregunta algo sobre tu ejercicio...",
            etiqueta_envio="Enviar",
        ))


def renderizar_pildora_contexto(instancia: Any) -> None:
    """Muestra el estado del contexto algebraico activo y su interruptor."""
    habilitado = instancia._almacen.get("ia_contexto_habilitado", True)
    contexto = None
    if habilitado and hasattr(instancia.interfaz_activa, "obtener_contexto_ia"):
        try:
            contexto = instancia.interfaz_activa.obtener_contexto_ia()
        except Exception:
            contexto = None

    if contexto is None or getattr(contexto, "vacio", False):
        _renderizar_pildora_vacia(instancia, habilitado)
        return

    _renderizar_pildora_activa(instancia, contexto, habilitado)


def _renderizar_pildora_vacia(instancia: Any, habilitado: bool) -> None:
    """Indica la ausencia de contexto disponible."""
    with ui.row().classes("w-full items-center justify-between px-2 py-1 glosa-contexto-panel"):
        ui.label("Sin contexto del ejercicio").classes("text-xs texto-secundario")
        ui.switch("Auto-adjuntar", value=habilitado, on_change=instancia._alternar_contexto).classes(
            "text-xs"
        ).props("dense size=sm")


def _renderizar_pildora_activa(instancia: Any, contexto: Any, habilitado: bool) -> None:
    """Construye la etiqueta con el nombre de la herramienta activa y su frescura."""
    etiqueta = f"Viendo: {contexto.etiqueta}"
    if contexto.desactualizado:
        etiqueta = "Los datos cambiaron desde el último cálculo"
    elif contexto.nota_ventana:
        etiqueta += f" ({contexto.nota_ventana})"

    clases = "glosa-contexto row items-center gap-2 w-full justify-between px-3 py-2 glosa-contexto-panel glosa-contexto-borde"
    if contexto.desactualizado:
        clases += " desactualizado"

    with ui.row().classes(clases):
        with ui.row().classes("items-center gap-2 min-w-0 flex-1"):
            ui.icon("visibility", size="xs").classes("texto-acento")
            ui.label(etiqueta).classes("glosa-contexto-etiqueta truncate text-xs font-semibold").tooltip(etiqueta)

        with ui.row().classes("items-center gap-3 flex-shrink-0"):
            ui.switch(value=habilitado, on_change=instancia._alternar_contexto).props(
                'dense size=sm aria-label="Incluir el contexto del ejercicio"'
            ).tooltip("Activar/desactivar contexto")


def construir_boton_y_fondo() -> None:
    """Genera el botón flotante (FAB) y el fondo oscuro modal (scrim)."""
    with ui.button(color=None).classes("glosa-boton-flotante").props(
        'ripple=false data-glosa-alternar aria-controls="glosa-panel-lateral" aria-expanded="false" aria-label="Abrir Glosa"'
    ) as boton_flotante:
        ui.html(icono_svg("glosa")).classes("texto-acento")
    boton_flotante.tooltip("Abrir Glosa")

    ui.element("div").classes("glosa-fondo-modal").props("data-glosa-cerrar")
