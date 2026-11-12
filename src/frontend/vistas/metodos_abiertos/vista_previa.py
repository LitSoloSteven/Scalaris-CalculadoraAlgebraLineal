"""Vista previa con antirrebote y muestreo fuera del hilo de interfaz."""
import asyncio
import logging
from collections.abc import Callable

from nicegui import ui

from src.frontend.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.controladores.actualizacion_cancelable import cancelar_actualizacion, programar_actualizacion
from src.frontend.controladores.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.vista_previa_raices import preparar_vista_previa
from .figura_base import crear_figura_vacia

_registro = logging.getLogger(__name__)


class PanelVistaPrevia:
    """Conserva el nodo Plotly y publica solo la muestra correspondiente a la edición actual."""

    def __init__(self, obtener_expresion: Callable[[], str], actualizar_figura: Callable[[], None]):
        self._obtener_expresion = obtener_expresion
        self._actualizar_figura = actualizar_figura
        self.coordinador = CoordinadorTrabajosRaices(preparar_vista_previa)
        self.respuesta = self.tarea = None
        self._revision = 0
        self._cerrado = False

    def construir(self) -> None:
        """Monta el estado accesible y el nodo Plotly persistente."""
        ui.label("Gráfica previa").classes("text-xl font-semibold texto-principal")
        self.estado = ui.label("Escribe una función para ver su gráfica previa.").classes(
            "texto-secundario").props("role=status aria-live=polite aria-busy=false")
        self.grafica = ui.plotly(crear_figura_vacia()).classes("metodos-abiertos-grafica w-full").props(
            'role=img aria-label="Gráfica previa de la función con las aproximaciones del método"')
        self.grafica.on("plotly_afterplot", js_handler="() => window.scalaris?.sincronizarTemaPlotly?.()")
        ui.context.client.on_disconnect(self.cerrar)
        ui.context.client.on_delete(self.cerrar)
        ui.context.client.on_connect(self.reabrir)

    def programar(self) -> None:
        """Revoca la muestra anterior y prepara una nueva tras la pausa de escritura."""
        self._invalidar()
        expresion = str(self._obtener_expresion() or "").strip()
        if not expresion:
            self.estado.set_text("Escribe una función para ver su gráfica previa.")
            return
        self.estado.set_text("Preparando la gráfica de los datos actuales…")
        self.tarea = programar_actualizacion(
            None, self._actualizar, self.disponible, ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)

    async def actualizar(self) -> None:
        """Calcula inmediatamente la vista previa al cargar un ejemplo."""
        self._invalidar()
        if self.disponible():
            self.tarea = asyncio.current_task()
            await self._actualizar()

    async def _actualizar(self) -> None:
        tarea = asyncio.current_task()
        revision = self._revision
        captura = {"expresion": self._obtener_expresion(), "x_min": -10, "x_max": 10}
        self.estado.props("aria-busy=true")
        try:
            respuesta = await self.coordinador.ejecutar(captura)
            if respuesta is not None and self._vigente(revision, tarea, captura):
                self.respuesta = respuesta
                self.estado.set_text(respuesta["mensaje"])
                self._actualizar_figura()
        except asyncio.CancelledError:
            return
        except Exception:
            _registro.warning("No se pudo preparar la gráfica previa de métodos abiertos")
            if self._vigente(revision, tarea, captura):
                self.respuesta = None
                self.estado.set_text("No se pudo dibujar la función. Revisa la expresión.")
                self._actualizar_figura()
        finally:
            if self.tarea is tarea:
                self.tarea = None
                if not self.estado.is_deleted:
                    self.estado.props("aria-busy=false")

    def disponible(self) -> bool:
        """Indica si los nodos siguen activos y aceptan una publicación."""
        return not self._cerrado and not self.grafica.is_deleted and not self.estado.is_deleted

    def _vigente(self, revision: int, tarea, captura: dict) -> bool:
        return (self.disponible() and revision == self._revision and self.tarea is tarea
                and captura["expresion"] == self._obtener_expresion())

    def _invalidar(self) -> None:
        self._revision += 1
        self.coordinador.invalidar()
        cancelar_actualizacion(self.tarea)
        self.tarea = self.respuesta = None
        if hasattr(self, "estado") and not self.estado.is_deleted:
            self.estado.props("aria-busy=false")
        if hasattr(self, "grafica") and not self.grafica.is_deleted:
            self.grafica.update_figure(crear_figura_vacia())

    def cerrar(self) -> None:
        """Revoca publicaciones y trabajos pendientes al cerrar el cliente."""
        self._cerrado = True
        self.coordinador.cerrar()
        self._invalidar()

    def reabrir(self) -> None:
        """Acepta nuevas solicitudes y vuelve a muestrear la captura vigente."""
        self._cerrado = False
        self.coordinador.reabrir()
        self.programar()
