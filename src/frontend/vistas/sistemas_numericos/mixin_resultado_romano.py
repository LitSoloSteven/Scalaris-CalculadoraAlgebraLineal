"""Mixin para renderizado de resultados y reproductor interactivo de números romanos."""

from __future__ import annotations

from typing import Any

from nicegui import ui
from ._cuerpo_numerico import renderizar_cuerpo_numerico
from src.frontend.componentes.glosa_foco import crear_accion_explicacion

from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from .pasos_romanos import construir_pasos_romanos


class MixinResultadoRomano:
    """Maneja la presentación del resultado de operaciones romanas y el reproductor de pasos."""

    def _renderizar_tarjeta_resultado_destacado(self, presentacion, resultado_romano: str) -> None:
        """Presenta la operación recibida y su resultado romano en una tarjeta destacada."""
        with ui.column().classes("w-full panel-tarjeta p-6 rounded-2xl gap-4"):
            with ui.row().classes("w-full justify-between items-center"):
                with ui.row().classes("items-center gap-2"):
                    ui.label("RESULTADO DE LA OPERACIÓN").classes("text-xs font-bold tracking-widest texto-secundario")
                    ui.label(presentacion.nombre.upper()).classes(
                        "text-[10px] font-extrabold px-2.5 py-0.5 rounded border"
                    ).classes("numericos-resultado")
                ui.button(
                    icon="content_copy",
                    on_click=lambda: self.copiar(resultado_romano),
                    color=None,
                ).classes("boton-icono w-9 h-9 p-0 texto-secundario").props(
                    'flat round aria-label="Copiar resultado romano"'
                ).tooltip("Copiar resultado romano")

            with ui.row().classes("w-full items-center justify-center gap-4 py-4 flex-wrap text-center"):
                ui.label(presentacion.operandos[0]).classes("text-3xl md:text-4xl font-extrabold texto-secundario font-mono")
                ui.label(presentacion.simbolo).classes("text-2xl font-bold texto-secundario")
                ui.label(presentacion.operandos[1]).classes("text-3xl md:text-4xl font-extrabold texto-secundario font-mono")
                ui.label("=").classes("text-2xl font-bold texto-secundario")
                ui.label(resultado_romano).classes(
                    "text-4xl md:text-5xl font-black font-mono tracking-wider px-6 py-2.5 rounded-xl border"
                ).classes("numericos-resultado")

    def _renderizar_reproductor_romano(self, resultado: Any, operacion: str) -> None:
        """Construye y monta el reproductor interactivo con las fases de la operación."""
        if getattr(self, "reproductor", None) is not None:
            self.reproductor.detener()

        pasos, grupos = construir_pasos_romanos(resultado, operacion)
        if not pasos:
            return

        accion_glosa = crear_accion_explicacion(getattr(self, "panel_ia", None), pasos)

        self.reproductor = ReproductorPasos(pasos, grupos, renderizar_cuerpo=renderizar_cuerpo_numerico, identificador="romanos", opciones={'titulo': "Procedimiento paso a paso", 'lineas_ayuda': _LINEAS_AYUDA_ROMANOS, 'tipos_leyenda': (
                "decodificacion",
                "operacion",
                "validacion",
                "definicion",
                "iteracion",
                "producto",
                "construccion",
                "resultado",
            ), 'al_explicar': accion_glosa, 'esta_ocupado': lambda: bool(
                getattr(getattr(self, "panel_ia", None), "_esta_enviando", False)
            )})
        self.reproductor.construir()


_LINEAS_AYUDA_ROMANOS = (
    "• Decodificación: convierte los números romanos a su valor decimal equivalente.",
    "• Operación: realiza el cálculo aritmético (en multiplicación mediante sumas sucesivas).",
    "• Construcción canónica: resta vorazmente los símbolos romanos de mayor a menor valor.",
    "• Puedes avanzar paso a paso o utilizar la reproducción automática.",
)
