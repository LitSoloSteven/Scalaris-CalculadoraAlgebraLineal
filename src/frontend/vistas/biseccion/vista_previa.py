"""Gráfica previa cancelable, independiente del resultado y del rango de exploración."""
import asyncio
import logging

from nicegui import ui
from src.backend.resolutores.raices.unidades_angulares import opciones_unidad

from src.frontend.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.controladores.actualizacion_cancelable import programar_actualizacion
from src.frontend.controladores.biseccion.vista_previa import preparar_vista_previa, rango_grafica, RANGO_GRAFICA_DEFECTO
from src.frontend.controladores.biseccion.vigencia_panel import invalidar_panel
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from .captura import GUIA_CONTINUIDAD
from .grafico_compartido import GraficoCompartido
from .rango_grafica import construir_rango, sincronizar_rango

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
        """Monta la región del gráfico y enlaza los controles previamente construidos."""
        with ui.column().classes("panel-tarjeta biseccion-panel-previa w-full gap-4 p-6") as panel:
            self.panel = panel
            ui.label("Gráfica previa").classes("text-xl font-semibold texto-principal")
            ui.label("Inspecciona la función antes de elegir un intervalo. El rango visual conserva tu cálculo.").classes(
                "text-sm texto-secundario")
            self.estado = ui.label("Escribe una función para ver su gráfica previa.").classes(
                "texto-secundario").props("role=status aria-live=polite aria-busy=false")
            self.contenedor_resultados = ui.column().classes("w-full min-w-0")
            self.compartido = GraficoCompartido()
            self.grafica = self.compartido.nodo
            self.grafica.on("plotly_relayout", self._encuadrar)
            ui.label(GUIA_CONTINUIDAD).classes("text-sm texto-secundario")
        for panel in (self, self.vista.exploracion):
            for campo in (panel.minimo, panel.maximo):
                campo.on_value_change(lambda _, origen=panel: self._editar_rango(origen))
        for campo in (self.minimo, self.maximo):
            campo.on("keydown.enter", self.actualizar)
        ui.context.client.on_delete(self.cerrar)

    def construir_controles(self) -> None:
        """Monta los campos de rango visual en las opciones del intervalo."""
        construir_rango(self)

    def _editar_rango(self, origen) -> None:
        if not self.vista._cargando_captura:
            sincronizar_rango(self.vista, (origen.minimo.value, origen.maximo.value))

    def _encuadrar(self, evento) -> None:
        if not self._sigue_montada() or self.respuesta is None:
            return
        nuevo = _rango_evento(evento.args)
        if nuevo is None:
            return
        try:
            if nuevo == rango_grafica(self.capturar()):
                return
        except ValueError:
            pass
        sincronizar_rango(self.vista, tuple(map(str, nuevo)))

    def _campos_captura(self) -> tuple:
        return self.minimo, self.maximo

    def capturar(self) -> dict:
        """Entrega solo expresión y rango visual; no incluye a/b ni criterio matemático."""
        return {"expresion": self.vista.expresion.value,
                "x_min": self.minimo.value, "x_max": self.maximo.value,
                **opciones_unidad(self.vista.unidad_angular.value)}

    def actualizar_marcas(self) -> None:
        """Actualiza la marca del intervalo capturado sin volver a muestrear la función."""
        self.compartido.sospecha(None)
        try:
            par = rango_grafica({"x_min": self.vista.inferior.value, "x_max": self.vista.superior.value})
        except ValueError:
            par = None
        self.compartido.intervalo(par)

    def _sigue_montada(self) -> bool:
        return not self._cerrado and not self.contenedor_resultados.is_deleted

    def _invalidar(self) -> None:
        invalidar_panel(self)
        self.compartido.retirar_curva()
        if not self.contenedor_resultados.is_deleted:
            self._mostrar_carga(False)

    def programar(self) -> None:
        """Sustituye la espera anterior con antirrebote y retira la gráfica de datos editados."""
        self._invalidar()
        if not self._sigue_montada():
            return
        if not str(self.vista.expresion.value or "").strip():
            self.compartido.publicar_curva(None)
            self.estado.set_text("Escribe una función para ver su gráfica previa.")
            return
        self.estado.set_text("Preparando la gráfica de los datos actuales…")
        self.tarea = programar_actualizacion(
            None, self._actualizar, self._sigue_montada, ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)

    async def actualizar(self) -> None:
        """Dibuja inmediatamente al pulsar Enter, cancelando la espera anterior."""
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
                self.estado.set_text("No se pudo dibujar la función. Revisa la función o el rango.")
        finally:
            if self.tarea is tarea:
                self.tarea = None
                self._mostrar_carga(False)

    def _mostrar_carga(self, ocupado: bool) -> None:
        if not self.estado.is_deleted:
            self.estado.props(f"aria-busy={str(ocupado).lower()}")

    def _publicar(self, respuesta: dict) -> None:
        self.respuesta = respuesta
        self.estado.set_text(respuesta["mensaje"])
        if respuesta["estado"] == "EXITO":
            self.compartido.publicar_curva(respuesta)

    def usar_intervalo(self) -> None:
        """Copia a/b al rango visual sin resolver ni invalidar el resultado del método."""
        if self._sigue_montada():
            try:
                rango = (str(self.vista.inferior.value), str(self.vista.superior.value))
                rango_grafica({"x_min": rango[0], "x_max": rango[1]})
            except ValueError:
                self.estado.set_text("Introduce extremos a < b para ajustar el gráfico.")
                return
            sincronizar_rango(self.vista, rango)

    def cerrar(self) -> None:
        """Descarta la respuesta y cancela la espera al desconectar o eliminar el cliente."""
        self._cerrado = True
        self._invalidar()

    def reabrir(self) -> None:
        """Solicita una gráfica nueva al reconectar sin reutilizar una respuesta anterior."""
        self._cerrado = False
        self.programar()


def _rango_evento(datos) -> tuple[float, float] | None:
    if not isinstance(datos, dict):
        return None
    if datos.get("xaxis.autorange") is True:
        return RANGO_GRAFICA_DEFECTO
    par = datos.get("xaxis.range") or (datos.get("xaxis.range[0]"), datos.get("xaxis.range[1]"))
    if not isinstance(par, (tuple, list)) or len(par) != 2:
        return None
    try:
        return rango_grafica({"x_min": par[0], "x_max": par[1]})
    except ValueError:
        return None
