"""Previa nativa de Plotly con un trabajador real y una sola captura pendiente."""
import asyncio
import logging
from uuid import uuid4

import plotly.graph_objects as go
from nicegui import ui

from src.ai.huellas import calcular_huella
from src.frontend.componentes.figura_funcion_real import crear_figura_previa
from src.frontend.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.controladores.actualizacion_cancelable import cancelar_actualizacion, programar_actualizacion
from src.frontend.controladores.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.rango_exploracion_raices import RANGO_GRAFICA_DEFECTO
from src.frontend.controladores.vista_previa_raices import preparar_vista_previa
from src.frontend.tema import PALETA_GRAFICOS
from .rango_previo import construir_rango, sincronizar_rango

_registro = logging.getLogger(__name__)
_ESTADO_INICIAL = "Escribe una función para ver su gráfica previa."


class PanelVistaPrevia:
    """Publica curvas identificadas sin mezclar el rango visual con los extremos del método."""

    def __init__(self, vista):
        self.vista = vista
        self.coordinador = CoordinadorTrabajosRaices(preparar_vista_previa)
        self.respuesta = self.tarea = None
        self.identidad = ""
        self._revision = 0
        self._cerrado = False

    def construir(self) -> None:
        """Monta rango, orientación y un nodo estable con eventos nativos y sin tooltips."""
        with ui.column().classes("panel-tarjeta w-full gap-4 p-6"):
            ui.label("Gráfica previa").classes("text-xl font-semibold texto-principal")
            construir_rango(self)
            self.estado = ui.label(_ESTADO_INICIAL).classes("texto-secundario").props(
                "role=status aria-live=polite aria-busy=false")
            self.grafica = ui.plotly(self._figura()).classes("regla-falsa-grafica w-full").props(
                'role=img aria-label="Gráfica previa de la función; selección alternativa en campos de texto"')
            self.grafica.on("plotly_afterplot", js_handler="() => window.scalaris?.sincronizarTemaPlotly?.()")
            ui.label("El muestreo no certifica raíces ni continuidad. Los huecos no se conectan.").classes(
                "text-sm texto-secundario")

    def capturar(self) -> dict:
        """Entrega únicamente expresión, unidad y rango visual, sin extremos ni parada."""
        return {"expresion": self.vista.expresion.value, "unidad_angular": self.vista.unidad_angular.value,
                "x_min": self.minimo.value, "x_max": self.maximo.value}

    def sincronizar_busqueda(self) -> None:
        """Recibe el rango de búsqueda conservando el resultado matemático."""
        sincronizar_rango(self, self.vista.exploracion)

    def invalidar(self) -> None:
        """Revoca muestra, borrador y espera sin liberar un trabajador aún activo."""
        self._revision += 1
        self.coordinador.invalidar()
        cancelar_actualizacion(self.tarea)
        self.tarea = self.respuesta = None
        self.identidad = ""
        if hasattr(self.vista, "seleccion_grafico"):
            self.vista.seleccion_grafico.cancelar()
        if not self.grafica.is_deleted:
            self.grafica.update_figure(self._figura())
        self._mostrar_carga(False)

    def programar(self) -> None:
        """Retira la curva anterior y sustituye el borrador pendiente tras una pausa de edición."""
        self.invalidar()
        if not self._montada():
            return
        if not str(self.vista.expresion.value or "").strip():
            self.estado.set_text(_ESTADO_INICIAL)
            return
        self.estado.set_text("Preparando la gráfica de los datos actuales…")
        self.tarea = programar_actualizacion(None, self._actualizar, self._montada,
                                            ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)

    async def actualizar(self) -> None:
        """Solicita inmediatamente una curva y cancela solo la espera sustituida."""
        if self._montada():
            self.invalidar()
            self.tarea = asyncio.current_task()
            await self._actualizar()

    async def _actualizar(self) -> None:
        tarea = asyncio.current_task()
        revision, destino = self._revision, self.grafica
        captura = self.capturar()
        huella = calcular_huella(captura)
        self._mostrar_carga(True)
        try:
            respuesta = await self.coordinador.ejecutar(captura)
            if respuesta is not None and self._vigente(revision, destino, huella):
                self.respuesta = respuesta
                self.identidad = uuid4().hex
                self.estado.set_text(respuesta["mensaje"])
                self.grafica.update_figure(self._figura())
        except asyncio.CancelledError:
            return
        except Exception:
            _registro.warning("No se pudo preparar la gráfica previa de regla falsa")
            if self._vigente(revision, destino, huella):
                self.estado.set_text("No se pudo dibujar la función. Revisa la función o el rango.")
        finally:
            if self.tarea is tarea:
                self.tarea = None
                self._mostrar_carga(False)

    def _montada(self) -> bool:
        return not self._cerrado and not self.grafica.is_deleted and not self.estado.is_deleted

    def _vigente(self, revision: int, destino, huella: str) -> bool:
        return (self._montada() and revision == self._revision and destino is self.grafica
                and huella == calcular_huella(self.capturar()))

    def _mostrar_carga(self, ocupada: bool) -> None:
        if not self.estado.is_deleted:
            self.estado.props(f"aria-busy={str(ocupada).lower()}")

    def _figura(self) -> dict:
        respuesta = self.respuesta
        if respuesta is None or respuesta["estado"] != "EXITO":
            respuesta = {"entrada": {"expresion": "", "extremo_izquierdo": RANGO_GRAFICA_DEFECTO[0],
                                     "extremo_derecho": RANGO_GRAFICA_DEFECTO[1]}, "muestra": {"x": [], "y": []}}
        figura = crear_figura_previa(respuesta)
        figura.update_layout(hovermode="closest")
        figura.data[0].update(hoverinfo="none", customdata=[self.identidad] * len(respuesta["muestra"]["x"]))
        figura.add_trace(go.Scatter(x=[], y=[], mode="markers+text", textposition="top center",
                                   hoverinfo="skip", marker=dict(color=PALETA_GRAFICOS[1], size=12)))
        return {**figura.to_plotly_json(), "config": {"displayModeBar": False, "responsive": True}}

    def dibujar_borrador(self, puntos: list[float]) -> None:
        """Actualiza solo los marcadores sin reemplazar el nodo ni el encuadre del usuario."""
        if not self.grafica.is_deleted:
            self.grafica.run_plot_method("restyle", {"x": [puntos], "y": [[0] * len(puntos)],
                                                    "text": [["a", "b"][:len(puntos)]]}, [1])

    def cerrar(self) -> None:
        """Bloquea publicaciones y retira la captura pendiente al desconectar o eliminar."""
        self._cerrado = True
        self.coordinador.cerrar()
        self.invalidar()

    def reabrir(self) -> None:
        """Prepara datos actuales tras reconectar sin reutilizar eventos de curvas anteriores."""
        self._cerrado = self.grafica.is_deleted
        if not self._cerrado:
            self.coordinador.reabrir()
            self.programar()
