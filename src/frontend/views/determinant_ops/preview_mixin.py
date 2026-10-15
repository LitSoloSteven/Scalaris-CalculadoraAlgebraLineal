"""Vista previa en vivo del determinante con LaTeX para la vista de Determinantes."""
from __future__ import annotations

import asyncio
import html
import itertools
import json
import logging

from nicegui import ui

from src.frontend.views.determinant_ops._config import PREVIEW_MAX_N
from src.frontend.views.determinant_ops._vista_previa import (
    contar_invalidas,
    latex_vista_previa,
)

logger = logging.getLogger(__name__)

RETARDO_VISTA_PREVIA_S = 0.3
CLASE_TEXTO_ORIENTATIVO = "text-sec italic text-sm mt-4 text-center"
MENSAJE_ERROR_VISTA_PREVIA = "No se pudo generar la vista previa."

_CONTADOR_IDS = itertools.count()


def _pintar_aviso_invalidas(cantidad: int) -> None:
    """Avisa cuántas celdas no son válidas y qué hacer para poder calcular."""
    with ui.row().classes("items-center gap-2 px-4 py-2 badge-warning w-fit mt-3").props(
        'role="status"'
    ):
        ui.icon("warning_amber", size="sm")
        ui.label(
            f"Celdas no válidas: {cantidad}. Corrige las celdas marcadas con ? para calcular."
        ).classes("font-bold")


class DeterminantOpsPreviewMixin:
    """Genera la vista previa del determinante con debounce.

    Requiere en la vista: square_panel, preview_container y preview_task.
    """

    def _trigger_live_preview(self) -> None:
        """Cancela la vista previa pendiente y programa otra tras el debounce."""
        if self.preview_task is not None and not self.preview_task.done():
            self.preview_task.cancel()
        self.preview_task = asyncio.create_task(self._update_preview())

    async def _update_preview(self) -> None:
        """Espera el debounce y repinta el contenedor de la vista previa."""
        try:
            await asyncio.sleep(RETARDO_VISTA_PREVIA_S)
            if self._contenedor_previa_eliminado():
                return
            self.preview_container.clear()
            with self.preview_container:
                self._pintar_vista_previa()
        except asyncio.CancelledError:
            return
        except Exception:
            self._mostrar_error_vista_previa()

    def _contenedor_previa_eliminado(self) -> bool:
        """Indica si el contenedor ya no existe o fue destruido con la página."""
        contenedor = self.preview_container
        return contenedor is None or contenedor.is_deleted

    def _pintar_vista_previa(self) -> None:
        """Dibuja la matriz en LaTeX o el mensaje orientativo si es demasiado grande."""
        n = self.square_panel.n
        if n > PREVIEW_MAX_N:
            ui.label(
                f"La vista previa está disponible hasta {PREVIEW_MAX_N}×{PREVIEW_MAX_N}."
            ).classes(CLASE_TEXTO_ORIENTATIVO)
            return
        datos = self.square_panel.get_matrix_data()
        latex = latex_vista_previa(datos)
        if not latex:
            ui.label(MENSAJE_ERROR_VISTA_PREVIA).classes(CLASE_TEXTO_ORIENTATIVO)
            return
        identificador = f"det-preview-{next(_CONTADOR_IDS)}"
        ui.html(
            f'<div id="{identificador}" class="math-scroll-container math-label w-full">'
            f"$$ {html.escape(latex)} $$</div>"
        )
        ui.run_javascript(f"typesetMathWhenReady({json.dumps([identificador])});")
        invalidas = contar_invalidas(datos)
        if invalidas:
            _pintar_aviso_invalidas(invalidas)

    def _mostrar_error_vista_previa(self) -> None:
        """Registra el fallo y deja un mensaje en el contenedor si sigue vivo."""
        logger.error("Error al actualizar la vista previa de determinantes", exc_info=True)
        if self._contenedor_previa_eliminado():
            return
        self.preview_container.clear()
        with self.preview_container:
            ui.label(MENSAJE_ERROR_VISTA_PREVIA).classes(CLASE_TEXTO_ORIENTATIVO)
