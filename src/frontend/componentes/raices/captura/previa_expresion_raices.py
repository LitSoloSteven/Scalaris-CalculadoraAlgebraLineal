"""Previa de la expresión con antirrebote y variantes de presentación."""
from nicegui import ui

from src.frontend.componentes.reproductor_pasos.formato.cuerpos import renderizar_latex
from src.frontend.controladores.compartido.sesion.actualizacion_cancelable import (
    cancelar_actualizacion,
    programar_actualizacion,
)
from src.frontend.controladores.raices.compartido.formato.formato_funcion_real import formatear_expresion
from src.frontend.nucleo.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS


class PreviaExpresion:
    """Mantiene una región de fórmula independiente del diagnóstico y del gráfico."""

    def __init__(self, *, solo_matematica: bool = False, mensaje_vacio: str = "", mensaje_error: str = ""):
        self._tarea = None
        self._expresion = None
        self._cerrada = False
        self._solo_matematica = solo_matematica
        self._mensaje_vacio = mensaje_vacio
        self._mensaje_error = mensaje_error
        self.estado = None
        if solo_matematica:
            with ui.column().classes("previa-formula-bloque w-full min-w-0 gap-1"):
                self.region = ui.column().classes("previa-formula-matematica w-full min-w-0 gap-1")
                self.estado = ui.label(mensaje_vacio).classes(
                    "previa-formula-estado text-sm texto-secundario"
                ).props("role=status aria-live=polite")
        else:
            self.region = ui.column().classes("w-full min-w-0 gap-1").props("aria-live=polite")
        ui.context.client.on_delete(self.cerrar)

    def programar(self, expresion: str) -> None:
        """Retira la fórmula anterior y espera una pausa antes de componer."""
        if self._cerrada or self.region.is_deleted or expresion == self._expresion:
            return
        self._expresion = expresion
        cancelar_actualizacion(self._tarea)
        self._tarea = None
        self.region.clear()
        if expresion.strip():
            self._actualizar_estado("")
            self._tarea = programar_actualizacion(
                None,
                self._publicar,
                lambda: not self.region.is_deleted,
                ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS,
            )
            return
        self._actualizar_estado(self._mensaje_vacio)

    def refrescar(self, expresion: str) -> None:
        """Retira cualquier fórmula previa y vuelve a evaluar la expresión recibida."""
        self._expresion = None
        self.programar(expresion)

    async def _publicar(self) -> None:
        try:
            formula = formatear_expresion(self._expresion)
        except ValueError:
            if not self.region.is_deleted:
                self.region.clear()
            if self._solo_matematica:
                self._actualizar_estado(self._mensaje_error, advertencia=True)
            return
        if self._cerrada or self.region.is_deleted:
            return
        self._actualizar_estado("")
        with self.region:
            if self._solo_matematica:
                renderizar_latex(
                    formula["latex"],
                    vigilar_region=True,
                    etiqueta_accesible=f"Fórmula capturada: {formula['texto']}",
                )
            else:
                ui.label(formula["texto"]).classes("text-sm texto-secundario break-all")
                renderizar_latex(formula["latex"], vigilar_region=True)

    def _actualizar_estado(self, texto: str, *, advertencia: bool = False) -> None:
        if self.estado is None or self.estado.is_deleted:
            return
        self.estado.set_text(texto)
        if advertencia:
            self.estado.classes(remove="texto-secundario", add="texto-advertencia")
        else:
            self.estado.classes(remove="texto-advertencia", add="texto-secundario")

    def cerrar(self) -> None:
        """Cancela la espera y retira la fórmula de la región."""
        self._cerrada = True
        self._expresion = None
        cancelar_actualizacion(self._tarea)
        self._tarea = None
        if not self.region.is_deleted:
            self.region.clear()
        self._actualizar_estado("")

    def reabrir(self, expresion: str) -> None:
        """Regenera la representación de la captura vigente."""
        self._cerrada = False
        self.programar(expresion)
