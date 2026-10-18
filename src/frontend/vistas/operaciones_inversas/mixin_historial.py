"""Tarjetas y restauracion del historial de matrices inversas."""
from __future__ import annotations

import logging
from nicegui import ui
from src.frontend.vistas.mixin_sesion_matricial import MixinSesionMatricial

registro = logging.getLogger(__name__)


class MixinHistorialOperacionesInversas(MixinSesionMatricial):
    """Maneja el registro, visualización y restauración del historial de matrices invertidas."""

    def _restaurar_historial(self, elemento: dict):
        """Restaura los datos de una matriz guardada en el historial."""
        try:
            self.panel_matriz_cuadrada.cargar_matriz(elemento['datos'])
            ui.notify('Matriz restaurada', type='positive')
        except Exception:
            registro.exception("Error al restaurar la matriz del historial")
            ui.notify('No se pudo restaurar la matriz. Inténtalo de nuevo.', type='negative')
