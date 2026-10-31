"""Tarjetas y restauracion del historial de matrices inversas."""
from __future__ import annotations

import logging
from src.frontend.componentes.sonido import notificar
from src.frontend.vistas.mixin_sesion_matricial import MixinSesionMatricial

registro = logging.getLogger(__name__)


class MixinHistorialOperacionesInversas(MixinSesionMatricial):
    """Maneja el registro, visualización y restauración del historial de matrices invertidas."""

    def _restaurar_historial(self, elemento: dict):
        """Restaura los datos de una matriz guardada en el historial."""
        try:
            self.panel_matriz_cuadrada.cargar_matriz(elemento['datos'])
            notificar('Matriz restaurada', type='positive')
        except Exception:
            registro.exception("Error al restaurar la matriz del historial")
            notificar('No se pudo restaurar la matriz. Inténtalo de nuevo.', type='negative')
