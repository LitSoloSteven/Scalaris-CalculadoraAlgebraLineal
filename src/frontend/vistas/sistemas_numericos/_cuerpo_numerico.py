"""Cuerpos numéricos que generan el HTML del paso solicitado sin conservar tablas acumuladas."""
from collections.abc import Callable
from typing import Any
from nicegui import ui
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.modelo import PasoReproductor


class _CuerpoNumerico:
    """Renderiza contenido inmediato o diferido y una fórmula opcional del paso actual."""

    def __init__(self, contenido: str | Callable[[], str], expresion_latex: str | None = None) -> None:
        self._contenido = contenido
        self.expresion_latex = expresion_latex

    def __call__(self) -> None:
        ui.html(str(self)).classes("w-full")
        if self.expresion_latex:
            renderizar_latex(self.expresion_latex)

    def __str__(self) -> str:
        return self._contenido() if callable(self._contenido) else self._contenido


def renderizar_cuerpo_numerico(paso: PasoReproductor, contenedor: Any) -> None:
    """Presenta un cuerpo didáctico interno mediante una acción o una plantilla HTML escapada."""
    with contenedor:
        if callable(paso.cuerpo):
            paso.cuerpo()
        elif isinstance(paso.cuerpo, str):
            ui.html(paso.cuerpo)
