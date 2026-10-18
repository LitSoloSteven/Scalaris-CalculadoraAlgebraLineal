"""Gestión de estado de foco analítico en pasos concretos para Glosa."""
from __future__ import annotations

from typing import Any
from nicegui import ui
from src.frontend.componentes.glosa_sugerencias import renderizar_capsula_foco


def crear_accion_explicacion(panel: Any, pasos: Any):
    """Crea una acción que envía al panel la captura y posición del paso seleccionado."""
    if not panel:
        return None

    def explicar(paso):
        """Transmite los metadatos del reproductor con su índice y total actuales."""
        panel.disparar_explicacion_paso({
            **(paso.meta_explicar or {}), "indice": paso.indice + 1, "total": len(pasos),
        })
    return explicar


class FocoGlosaMixin:
    """Fija, limpia y presenta la cápsula del paso que Glosa debe explicar."""

    foco_explicacion: dict[str, Any] | None = None

    @ui.refreshable
    def renderizar_capsula_foco_interfaz(self) -> None:
        """Renderiza la cápsula visual de paso activo si existe foco establecido."""
        foco = getattr(self, "foco_explicacion", None)
        if not foco:
            return
        texto = f"Paso {foco['indice']}: {foco['operacion']}"
        renderizar_capsula_foco(texto, self.limpiar_foco_explicacion)

    def establecer_foco_explicacion(self, meta_paso: dict[str, Any]) -> None:
        """Establece el foco en un paso específico y actualiza la interfaz."""
        self.foco_explicacion = meta_paso
        self._refrescar_foco()

    def limpiar_foco_explicacion(self) -> None:
        """Elimina el foco activo y refresca el contenedor visual."""
        self.foco_explicacion = None
        self._refrescar_foco()

    def _refrescar_foco(self) -> None:
        if any(destino.instance is self for destino in self.renderizar_capsula_foco_interfaz.targets):
            self.renderizar_capsula_foco_interfaz.refresh()
