"""Gestión de estado de foco analítico en pasos concretos para Glosa."""
from __future__ import annotations

from typing import Any
from nicegui import ui
from src.frontend.componentes.glosa_chips import render_focus_chip


class FocoGlosaMixin:
    """Provee métodos para fijar, limpiar y renderizar el chip de foco de explicación."""

    explain_focus: dict[str, Any] | None = None

    @ui.refreshable
    def render_focus_chip_ui(self) -> None:
        """Renderiza la cápsula visual de paso activo si existe foco establecido."""
        foco = getattr(self, "explain_focus", None)
        if not foco:
            return
        texto = f"Paso {foco['index']}: {foco['op']}"
        render_focus_chip(texto, self.clear_explain_focus)

    def set_explain_focus(self, meta_paso: dict[str, Any]) -> None:
        """Establece el foco en un paso específico y actualiza la interfaz."""
        self.explain_focus = meta_paso
        if hasattr(self, "render_focus_chip_ui"):
            self.render_focus_chip_ui.refresh()

    def clear_explain_focus(self) -> None:
        """Elimina el foco activo y refresca el contenedor visual."""
        self.explain_focus = None
        if hasattr(self, "render_focus_chip_ui"):
            self.render_focus_chip_ui.refresh()
