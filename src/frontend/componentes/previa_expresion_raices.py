"""Previa de la expresión con antirrebote y alternativa de texto."""
from nicegui import ui

from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.controladores.actualizacion_cancelable import cancelar_actualizacion, programar_actualizacion
from src.frontend.controladores.formato_funcion_real import formatear_expresion


class PreviaExpresion:
    """Mantiene una región de fórmula independiente del diagnóstico y del gráfico."""

    def __init__(self):
        self._tarea = None
        self._expresion = None
        self._cerrada = False
        self.region = ui.column().classes("w-full min-w-0 gap-1").props("aria-live=polite")
        ui.context.client.on_delete(self.cerrar)

    def programar(self, expresion: str) -> None:
        """Retira la fórmula anterior y espera una pausa antes de componer."""
        if self._cerrada or self.region.is_deleted or expresion == self._expresion:
            return
        self._expresion = expresion
        cancelar_actualizacion(self._tarea)
        self.region.clear()
        if expresion.strip():
            self._tarea = programar_actualizacion(None, self._publicar, lambda: not self.region.is_deleted,
                                                   ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)

    async def _publicar(self) -> None:
        try:
            formula = formatear_expresion(self._expresion)
        except ValueError:
            return
        with self.region:
            ui.label(formula["texto"]).classes("text-sm texto-secundario break-all")
            renderizar_latex(formula["latex"], vigilar_region=True)

    def cerrar(self) -> None:
        """Cancela la espera y retira la fórmula de la región."""
        self._cerrada = True
        self._expresion = None
        cancelar_actualizacion(self._tarea)
        if not self.region.is_deleted:
            self.region.clear()

    def reabrir(self, expresion: str) -> None:
        """Regenera la representación de la captura vigente."""
        self._cerrada = False
        self.programar(expresion)
