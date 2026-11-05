"""Gráfica previa cancelable, independiente del resultado y del rango de exploración."""
import asyncio
import logging

from nicegui import ui

from src.frontend.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.controladores.actualizacion_cancelable import cancelar_actualizacion, programar_actualizacion
from src.frontend.controladores.biseccion.vista_previa import preparar_vista_previa
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from .captura import GUIA_CONTINUIDAD
from .figura import crear_figura_previa
from .rango_grafica import construir_rango

registro = logging.getLogger(__name__)


class PanelVistaPrevia:
    """Mantiene una sola gráfica vigente con revisión propia y sin modificar el ejercicio."""

    def __init__(self, vista):
        self.vista = vista
        self.tarea = None
        self.respuesta = None
        self._revision_captura = 0
        self._identificador_calculo = 0
        self._cerrado = False

    def construir(self) -> None:
        """Monta rango, acción de reintento y estados accesibles sin exigir un cálculo previo."""
        with ui.column().classes("panel-tarjeta biseccion-panel-previa w-full gap-4 p-6"):
            ui.label("Gráfica previa").classes("text-xl font-semibold texto-principal")
            ui.label("Inspecciona la función antes de elegir un intervalo. El rango visual conserva tu cálculo.").classes(
                "text-sm texto-secundario")
            construir_rango(self)
            self.boton = ui.button("Actualizar gráfica", color=None, on_click=self.actualizar).classes(
                "boton-discreto").props("ripple=false")
            self.estado = ui.label("Escribe una función para ver su gráfica previa.").classes(
                "texto-secundario").props("role=status aria-live=polite")
            self.contenedor_resultados = ui.column().classes("w-full min-w-0")
            ui.label(GUIA_CONTINUIDAD).classes("text-sm texto-secundario")
        for campo in self._campos_captura():
            campo.on_value_change(self.programar)
            campo.on("keydown.enter", self.actualizar)
        ui.context.client.on_delete(self.cerrar)

    def _campos_captura(self) -> tuple:
        return self.minimo, self.maximo

    def capturar(self) -> dict:
        """Entrega solo expresión y rango visual; no incluye a/b ni criterio matemático."""
        return {"expresion": self.vista.expresion.value,
                "x_min": self.minimo.value, "x_max": self.maximo.value}

    def _sigue_montada(self) -> bool:
        return not self._cerrado and not self.contenedor_resultados.is_deleted

    def _invalidar(self) -> None:
        self._revision_captura += 1
        self._identificador_calculo += 1
        cancelar_actualizacion(self.tarea)
        self.tarea = None
        self.respuesta = None
        if not self.contenedor_resultados.is_deleted:
            self.contenedor_resultados.clear()
            self._mostrar_carga(False)

    def programar(self) -> None:
        """Sustituye la espera anterior con antirrebote y retira la gráfica de datos editados."""
        self._invalidar()
        if not self._sigue_montada():
            return
        if not str(self.vista.expresion.value or "").strip():
            self.estado.set_text("Escribe una función para ver su gráfica previa.")
            return
        self.estado.set_text("Preparando la gráfica de los datos actuales…")
        self.tarea = programar_actualizacion(
            None, self._actualizar, self._sigue_montada, ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)

    async def actualizar(self) -> None:
        """Dibuja inmediatamente al pedirlo por botón o Enter, cancelando la espera anterior."""
        if not self._sigue_montada():
            return
        self._invalidar()
        self.tarea = asyncio.current_task()
        await self._actualizar()

    async def _actualizar(self) -> None:
        tarea = asyncio.current_task()
        revision = self._revision_captura
        self._mostrar_carga(True)
        self.estado.set_text("Muestreando la función para la gráfica previa…")
        try:
            vigente = await ejecutar_calculo_vigente(self, self.capturar, preparar_vista_previa)
            if vigente is not None and self.tarea is tarea and self._sigue_montada():
                self._publicar(vigente[0])
        except Exception:
            registro.warning("No se pudo preparar la gráfica previa de bisección")
            if revision == self._revision_captura and self._sigue_montada():
                self.estado.set_text("No se pudo dibujar la función. Revisa los datos y actualiza la gráfica.")
        finally:
            if self.tarea is tarea:
                self.tarea = None
                self._mostrar_carga(False)

    def _mostrar_carga(self, ocupado: bool) -> None:
        if not self.boton.is_deleted:
            self.boton.set_enabled(not ocupado)
            self.boton.props("loading" if ocupado else "", remove="" if ocupado else "loading")

    def _publicar(self, respuesta: dict) -> None:
        self.respuesta = respuesta
        self.estado.set_text(respuesta["mensaje"])
        if respuesta["estado"] == "EXITO":
            with self.contenedor_resultados:
                self.grafica = ui.plotly(crear_figura_previa(respuesta)).classes("w-full biseccion-grafica")
                self.grafica.on("plotly_afterplot", js_handler="() => window.scalaris.sincronizarTemaPlotly()")

    def usar_intervalo(self) -> None:
        """Copia a/b al rango visual sin resolver ni invalidar el resultado del método."""
        if self._sigue_montada():
            self.minimo.set_value(self.vista.inferior.value)
            self.maximo.set_value(self.vista.superior.value)
            self.programar()

    def cerrar(self) -> None:
        """Descarta la respuesta y cancela la espera al desconectar o eliminar el cliente."""
        self._cerrado = True
        self._invalidar()

    def reabrir(self) -> None:
        """Solicita una gráfica nueva al reconectar sin reutilizar una respuesta anterior."""
        self._cerrado = False
        self.programar()
