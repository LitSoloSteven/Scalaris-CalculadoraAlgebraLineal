"""Teclado en pantalla interactivo para captura de matrices y ecuaciones."""
from __future__ import annotations

from typing import Any
from nicegui import ui


class CalculatorPanel:
    """Panel de calculadora virtual con teclas numéricas, operadores y variables."""

    def __init__(self) -> None:
        self.simbolos_matriz = [
            "7", "8", "9", "/",
            "4", "5", "6", "-",
            "1", "2", "3", ".",
            "+", "0", "±", "C",
        ]
        self.simbolos_ecuaciones = [
            "7", "8", "9", "+", "-",
            "4", "5", "6", "w", "/",
            "1", "2", "3", "x", "y",
            "0", ".", "=", "z", "C",
        ]

    @staticmethod
    def inject_scripts() -> None:
        """Inyecta la etiqueta script del teclado virtual en la cabecera."""
        ui.add_head_html('<script src="/assets/js/calculadora.js" defer></script>')

    def _keypad_matriz(self) -> None:
        """Renderiza la cuadrícula de botones para modo matricial."""
        with ui.grid(columns=4).classes("w-full gap-4"):
            for sym in self.simbolos_matriz:
                self._crear_boton_tecla(sym, "h-14 text-xl")

    def _keypad_ecuaciones(self) -> None:
        """Renderiza la cuadrícula de botones para modo de ecuaciones con variables."""
        with ui.grid(columns=5).classes("w-full gap-3"):
            for sym in self.simbolos_ecuaciones:
                self._crear_boton_tecla(sym, "h-12 text-lg")

    def _crear_boton_tecla(self, sym: str, tamano_cls: str) -> None:
        """Construye un botón accesible para un símbolo del teclado."""
        if not sym:
            ui.label("").classes(f"w-full {tamano_cls}")
            return

        clase_extra = "btn-neo-calc-limpiar" if sym == "C" else "text-main"
        clases = f"btn-neo-calc w-full {tamano_cls} p-0 font-bold {clase_extra}"
        js_cmd = (
            f"if(window.scalaris && window.scalaris.calculadora) "
            f"window.scalaris.calculadora.insertarSimbolo('{sym}')"
        )
        ui.button(
            sym, on_click=lambda s=sym: ui.run_javascript(js_cmd), color=None
        ).classes(clases).props('ripple=false flat aria-label="' + sym + '"')

    def _construir_paneles_modo(self, mode_tabs: Any) -> None:
        """Renderiza los paneles tabulados para alternar entre matriz y ecuaciones."""
        with ui.tab_panels(mode_tabs, value="Matriz").classes(
            "w-full flex-1 bg-transparent p-0 overflow-hidden"
        ).props('animated transition-prev="slide-right" transition-next="slide-left"'):
            with ui.tab_panel("Matriz").classes("p-0 h-full flex flex-col justify-center"):
                self._keypad_matriz()
            with ui.tab_panel("Ecuaciones").classes("p-0 h-full flex flex-col justify-center"):
                self._keypad_ecuaciones()

    def build(self, mode_tabs: Any = None) -> None:
        """Construye el contenedor visual completo de la calculadora."""
        with ui.column().classes("w-full h-full p-6 flex flex-col justify-between panel-card"):
            ui.label("Calculadora").classes("text-main font-bold mb-4 text-center w-full text-lg")

            if mode_tabs is not None:
                self._construir_paneles_modo(mode_tabs)
            else:
                with ui.column().classes("w-full flex-1 justify-center"):
                    self._keypad_matriz()

