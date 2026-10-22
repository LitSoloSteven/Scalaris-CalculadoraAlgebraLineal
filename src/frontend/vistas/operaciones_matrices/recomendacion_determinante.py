"""Presentación y vigencia de la recomendación automática de Determinantes."""
import asyncio
import logging
from nicegui import run, ui

from src.frontend.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.controladores.actualizacion_cancelable import cancelar_actualizacion, programar_actualizacion
from src.frontend.controladores.operaciones_matrices.controlador_determinante import ControladorDeterminante
from src.frontend.controladores.operaciones_matrices.recomendacion_determinante import metodo_recomendado_disponible
from src.frontend import textos

registro = logging.getLogger(__name__)


class RecomendacionDeterminante:
    """Mantiene una sugerencia informativa sin sustituir la elección de la persona."""

    def __init__(self, vista):
        """Asocia la captura y prepara el estado de una única recomendación cancelable."""
        self.vista = vista
        self.tarea = None
        self.respuesta = None

    def construir(self) -> None:
        """Monta el estado vivo y una acción persistente para aceptar la sugerencia."""
        with ui.column().classes('determinantes-recomendacion w-full min-w-0') as self.contenedor:
            self.contenedor.props('role=status aria-live=polite aria-atomic=true')
            self.mensajes = ui.column().classes('w-full min-w-0 gap-2')
            self.boton_usar = ui.button(
                textos.DETERMINANTES_USAR_RECOMENDADO, on_click=self.usar_recomendado, color=None,
            ).classes('boton-discreto determinantes-usar-metodo').props('ripple=false')
        self.boton_usar.set_visibility(False)

    def cancelar(self) -> None:
        """Retira la tarea pendiente y hace obsoleta cualquier respuesta en vuelo."""
        cancelar_actualizacion(self.tarea)
        self.tarea = None
        self.respuesta = None

    def programar(self) -> None:
        """Reemplaza la recomendación después de una edición o un redimensionado."""
        self.cancelar()
        self.actualizar_eleccion()
        vacia = self.vista.esta_completamente_vacio()
        self._mostrar_mensaje(textos.DETERMINANTES_RECOMENDACION_VACIA if vacia
                              else textos.DETERMINANTES_RECOMENDACION_ESPERA)
        if not vacia:
            self.tarea = programar_actualizacion(
                None, self._actualizar, self._sigue_montada, ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS,
            )

    def _sigue_montada(self) -> bool:
        return not self.contenedor.is_deleted

    async def _actualizar(self) -> None:
        tarea = asyncio.current_task()
        try:
            respuesta = await run.io_bound(ControladorDeterminante.recomendar_captura, self.vista._capturar())
        except asyncio.CancelledError:
            raise
        except Exception:
            registro.warning('No se pudo actualizar la recomendación del determinante')
            respuesta = {'estado': 'ERROR', 'mensaje': textos.DETERMINANTES_RECOMENDACION_ERROR}
        if tarea.cancelling() or tarea is not self.tarea or not self._sigue_montada():
            return
        self.respuesta = respuesta
        self._mostrar_respuesta()
        self.actualizar_eleccion()

    def _mostrar_mensaje(self, mensaje: str, error: bool = False) -> None:
        self.contenedor.props.update({'role': 'alert' if error else 'status',
                                     'aria-live': 'assertive' if error else 'polite'})
        self.mensajes.clear()
        with self.mensajes:
            ui.label(mensaje).classes('texto-secundario w-full')

    def _mostrar_respuesta(self) -> None:
        if not self.respuesta or self.respuesta.get('estado') != 'EXITO':
            mensaje = (self.respuesta or {}).get('mensaje', textos.DETERMINANTES_RECOMENDACION_ERROR)
            self._mostrar_mensaje(mensaje, error=True)
            return
        self._mostrar_mensaje(textos.DETERMINANTES_RECOMENDACION.format(
            nombre=self.respuesta['nombre_legible'], justificacion=self.respuesta['justificacion']))
        with self.mensajes:
            ui.label(self.respuesta['limites_cofactores']).classes('texto-secundario text-sm w-full')

    def actualizar_eleccion(self) -> None:
        """Muestra la acción solo si la recomendación vigente difiere del método elegido."""
        metodo = metodo_recomendado_disponible(self.respuesta, self.vista.metodos_determinante.value)
        self.boton_usar.set_visibility(metodo is not None)

    def usar_recomendado(self) -> None:
        """Aplica la sugerencia vigente únicamente ante la acción explícita de la persona."""
        metodo = metodo_recomendado_disponible(self.respuesta, self.vista.metodos_determinante.value)
        if metodo is not None and self._sigue_montada():
            self.vista.metodos_determinante.set_value(metodo)
            identificador = self.vista.metodos_determinante.botones[metodo].html_id
            ui.run_javascript(f"document.getElementById('{identificador}')?.focus()")
