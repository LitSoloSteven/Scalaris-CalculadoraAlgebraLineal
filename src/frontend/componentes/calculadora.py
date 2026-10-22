"""Teclado en pantalla interactivo para captura de matrices y ecuaciones."""
from __future__ import annotations

from typing import Any
from nicegui import ui


class PanelCalculadora:
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
    def inyectar_recursos_cliente() -> None:
        """Inyecta la etiqueta script del teclado virtual en la cabecera."""
        ui.add_head_html('<script src="/assets/js/calculadora.js" defer></script>')

    def _teclado_matriz(self) -> None:
        """Renderiza la cuadrícula de botones para modo matricial."""
        with ui.grid(columns=4).classes("w-full gap-4"):
            for simbolo in self.simbolos_matriz:
                self._crear_boton_tecla(simbolo, "h-14 text-xl")

    def _teclado_ecuaciones(self) -> None:
        """Renderiza la cuadrícula de botones para modo de ecuaciones con variables."""
        with ui.grid(columns=5).classes("w-full gap-3"):
            for simbolo in self.simbolos_ecuaciones:
                self._crear_boton_tecla(simbolo, "h-12 text-lg")

    def _crear_boton_tecla(self, simbolo: str, clase_tamano: str) -> None:
        """Construye un botón accesible para un símbolo del teclado."""
        if not simbolo:
            ui.label("").classes(f"w-full {clase_tamano}")
            return

        clase_extra = "calculadora-boton-limpiar" if simbolo == "C" else "texto-principal"
        clases = f"calculadora-boton w-full {clase_tamano} p-0 font-bold {clase_extra}"
        codigo_cliente = (
            f"if(window.scalaris && window.scalaris.calculadora) "
            f"window.scalaris.calculadora.insertarSimbolo('{simbolo}')"
        )
        ui.button(
            simbolo, on_click=lambda: ui.run_javascript(codigo_cliente), color=None
        ).classes(clases).props('ripple=false flat aria-label="' + simbolo + '"')

    def _construir_paneles_modo(self, pestanas_modo: Any) -> None:
        """Renderiza los paneles tabulados para alternar entre matriz y ecuaciones."""
        with ui.tab_panels(pestanas_modo, value="Matriz").classes(
            "w-full flex-1 bg-transparent p-0 overflow-hidden"
        ).props('animated transition-prev="slide-right" transition-next="slide-left"'):
            with ui.tab_panel("Matriz").classes("p-0 h-full flex flex-col justify-center"):
                self._teclado_matriz()
            with ui.tab_panel("Ecuaciones").classes("p-0 h-full flex flex-col justify-center"):
                self._teclado_ecuaciones()

    def construir(self, pestanas_modo: Any = None) -> None:
        """Construye el contenedor visual completo de la calculadora."""
        with ui.column().classes("w-full h-full p-6 flex flex-col justify-between panel-tarjeta"):
            ui.label("Calculadora").classes("texto-principal font-bold mb-4 text-center w-full text-lg")

            if pestanas_modo is not None:
                self._construir_paneles_modo(pestanas_modo)
            else:
                with ui.column().classes("w-full flex-1 justify-center"):
                    self._teclado_matriz()

