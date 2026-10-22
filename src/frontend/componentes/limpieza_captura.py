"""Botón y confirmación de vaciado con movimiento opcional del cliente."""
import logging
from collections.abc import Callable
from typing import Protocol

from nicegui import ui
from src.frontend.textos import (
    LIMPIAR, LIMPIEZA_CANCELAR, LIMPIEZA_DESCRIPCION, LIMPIEZA_TITULO,
    LIMPIEZA_SIN_DATOS,
)

registro = logging.getLogger(__name__)


class CapturaLimpiable(Protocol):
    """Contrato de presencia de datos y vaciado de una captura."""

    def esta_completamente_vacio(self) -> bool:
        """Indica si la captura carece de texto significativo."""

    def limpiar_todo(self) -> None:
        """Vacía entradas y retira el estado calculado de la vista."""


class LimpiezaCaptura:
    """Coordina una captura y su vigencia sin depender de contenedores concretos."""

    def __init__(self, captura: CapturaLimpiable, sigue_montada: Callable[[], bool]):
        self.captura = captura
        self.sigue_montada = sigue_montada
        self.dialogo = None
        self.boton = None
        self._limpiando = False
        self._contenedor_captura = None

    def construir(self) -> None:
        """Monta la acción accesible, con espacio estable en filas estrechas."""
        ui.add_head_html('<link rel="stylesheet" href="/assets/css/limpieza_captura.css">')
        ui.context.slot.parent.classes('limpieza-acciones')
        self._contenedor_captura = ui.context.client.content
        self.boton = ui.button(icon='delete', on_click=self.confirmar, color=None).classes(
            'boton-discreto flex-1 py-3'
        ).style('flex-shrink: 0;').props(
            f'ripple=false id="boton-limpiar-principal" aria-label="{LIMPIAR}"'
        )
        with self.boton:
            ui.tooltip(LIMPIAR).props('target="#boton-limpiar-principal"')

    async def confirmar(self) -> None:
        """Abre una única confirmación modal o avisa de una captura vacía."""
        if self._limpiando or not self.sigue_montada():
            return
        if self.captura.esta_completamente_vacio():
            ui.notify(LIMPIEZA_SIN_DATOS, type='info', position='top')
            return
        if self.dialogo is None:
            self._construir_dialogo()
        self.dialogo.open()

    def _construir_dialogo(self) -> None:
        # QDialog conserva su trampa de foco y devuelve el foco al activador al cerrar.
        with ui.dialog().props('transition-duration=120') as self.dialogo:
            with ui.card().classes('panel-tarjeta p-6'):
                ui.label(LIMPIEZA_TITULO).classes('text-xl font-bold mb-4')
                ui.label(LIMPIEZA_DESCRIPCION).classes('text-sm texto-secundario mb-6')
                with ui.row().classes('w-full justify-end gap-3'):
                    ui.button(LIMPIEZA_CANCELAR, on_click=self.dialogo.close, color=None).classes(
                        'boton-discreto px-4'
                    ).props('ripple=false autofocus')
                    ui.button(LIMPIAR, on_click=lambda: self.ejecutar(), color=None).classes(
                        'boton-principal px-4'
                    ).props('ripple=false')
        self.dialogo.on('hide', self._devolver_foco)

    def _devolver_foco(self) -> None:
        if self.sigue_montada():
            ui.run_javascript("document.getElementById('boton-limpiar-principal')?.focus()")

    async def ejecutar(self, dialogo=None) -> None:
        """Anima y vacía una sola vez; un fallo de JavaScript no impide limpiar."""
        if self._limpiando or not self.sigue_montada():
            return
        self._limpiando = True
        if self._contenedor_captura is not None:
            self._contenedor_captura.props('inert')
        if dialogo is not None or self.dialogo is not None:
            (dialogo or self.dialogo).close()
        try:
            await ui.run_javascript(
                'return window.scalaris?.movimiento?.permitido() && '
                'window.scalaris?.animarRecoleccionBasura ? '
                'window.scalaris.animarRecoleccionBasura() : Promise.resolve()', timeout=2.0,
            )
        except Exception:
            registro.warning('No se pudo completar el movimiento de limpieza')
        finally:
            try:
                if self.sigue_montada():
                    self.captura.limpiar_todo()
            finally:
                self._limpiando = False
                self._liberar_captura()

    def _liberar_captura(self) -> None:
        contenedor = self._contenedor_captura
        if contenedor is not None and not contenedor.is_deleted:
            contenedor.props(remove='inert')
            self._devolver_foco()


def crear_boton_limpieza(captura: CapturaLimpiable, sigue_montada: Callable[[], bool]) -> LimpiezaCaptura:
    """Construye y devuelve el control común para una captura aún montada."""
    control = LimpiezaCaptura(captura, sigue_montada)
    control.construir()
    return control
