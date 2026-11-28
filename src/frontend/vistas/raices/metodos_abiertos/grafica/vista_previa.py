"""Vista previa con antirrebote, remuestreo dinámico de cámara y muestreo fuera de UI."""
import asyncio
import logging
from collections.abc import Callable

from nicegui import ui

from src.frontend.controladores.compartido.sesion.actualizacion_cancelable import (
    cancelar_actualizacion,
    programar_actualizacion,
)
from src.frontend.controladores.raices.compartido.ejecucion.coordinacion_trabajos_raices import (
    CoordinadorTrabajosRaices,
)
from src.frontend.controladores.raices.compartido.exploracion.vista_previa_raices import preparar_vista_previa
from src.frontend.controladores.raices.compartido.formato.rango_exploracion_raices import (
    RANGO_GRAFICA_DEFECTO,
    interpretar_relayout_x,
)
from src.frontend.nucleo.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from .figura_base import crear_figura_vacia

_registro = logging.getLogger(__name__)
_MENSAJE_INICIAL = "Escribe una función para ver su gráfica previa."


class PanelVistaPrevia:
    """Conserva el nodo Plotly y remuestrea sobre el rango visible vigente."""

    def __init__(self, obtener_expresion: Callable[[], str], actualizar_figura: Callable[[], None]):
        self._obtener_expresion = obtener_expresion
        self._actualizar_figura = actualizar_figura
        self.coordinador = CoordinadorTrabajosRaices(preparar_vista_previa)
        self.respuesta = self.tarea = self.titulo = None
        self._rango_base = RANGO_GRAFICA_DEFECTO
        self._rango_camara = None
        self._revision = self._revision_ejercicio = self._reencuadres = 0
        self._cerrado = False

    @property
    def identidad(self) -> str:
        """Identifica el ejercicio vigente frente a eventos tardíos de relayout."""
        return str(self._revision_ejercicio)

    @property
    def rango_activo(self) -> tuple[float, float]:
        """Devuelve el rango visible de la cámara o el rango base del ejercicio."""
        return self._rango_camara if self._rango_camara is not None else self._rango_base

    @property
    def rango_camara(self) -> tuple[float, float] | None:
        """Devuelve el encuadre manual solicitado por la persona usuaria, si existe."""
        return self._rango_camara

    @property
    def revision_vista(self) -> str:
        """Mantiene la revisión de cámara estable al remuestrear y la cambia al restablecer."""
        return f"metodos-abiertos:{self._revision_ejercicio}:{self._reencuadres}"

    def construir(self) -> None:
        """Monta la cabecera, el estado accesible y el nodo Plotly persistente."""
        with ui.row().classes("w-full items-center justify-between gap-2 flex-wrap"):
            self.titulo = ui.label("Gráfica previa").classes("text-xl font-semibold texto-principal")
            self.restablecer = ui.button("Restablecer vista", color=None, on_click=self.restablecer_vista).classes(
                "boton-discreto"
            ).props("ripple=false")
        self.estado = ui.label(_MENSAJE_INICIAL).classes(
            "texto-secundario").props("role=status aria-live=polite aria-busy=false")
        with ui.element("div").classes("metodos-raices-grafica-superficie metodos-abiertos-grafica-superficie"):
            self.grafica = ui.plotly(crear_figura_vacia()).classes("metodos-abiertos-grafica w-full").props(
                'role=img aria-label="Gráfica previa de la función con las aproximaciones del método"')
        self.grafica.on("plotly_afterplot", js_handler="() => window.scalaris?.sincronizarTemaPlotly?.()")
        self.grafica.on("plotly_relayout", self._encuadrar, js_handler=(
            f"datos => emit({{...datos, identidad: document.getElementById('{self.grafica.html_id}')?.layout?.meta}})"
        ))
        ui.context.client.on_disconnect(self.cerrar)
        ui.context.client.on_delete(self.cerrar)
        ui.context.client.on_connect(self.reabrir)

    def establecer_titulo(self, texto: str) -> None:
        """Actualiza el encabezado de la gráfica sin reconstruir el nodo Plotly."""
        if self.titulo is not None and not self.titulo.is_deleted:
            self.titulo.set_text(texto)

    def reiniciar_encuadre(self) -> None:
        """Restaura el rango inicial tras editar la expresión o limpiar la captura."""
        self._rango_base = RANGO_GRAFICA_DEFECTO
        self._rango_camara = None
        self._revision_ejercicio += 1
        self._reencuadres += 1

    def restablecer_vista(self) -> None:
        """Recupera el encuadre base sin alterar función, semillas ni resultado previo."""
        self._rango_camara = None
        self._reencuadres += 1
        if self._muestra_cubre_rango(self._rango_base):
            self.estado.set_text(self.respuesta["mensaje"])
            self._actualizar_figura()
            return
        self._programar_muestreo(limpiar_previa=False)

    def ajustar_rango_base(self, rango: tuple[float, float] | None) -> None:
        """Amplía el muestreo base al calcular si la solución queda fuera de la muestra vigente."""
        if rango is None or (self._muestra_cubre_rango(rango) and self.respuesta is not None):
            return
        self._rango_base = rango
        if self._rango_camara is None:
            self._programar_muestreo(limpiar_previa=False)

    def programar(self) -> None:
        """Revoca la muestra anterior y prepara una nueva tras la pausa de escritura."""
        self._programar_muestreo(limpiar_previa=True)

    def _programar_muestreo(self, *, limpiar_previa: bool) -> None:
        if limpiar_previa:
            self._invalidar()
        else:
            self._detener_solicitud_pendiente()
        expresion = str(self._obtener_expresion() or "").strip()
        if not expresion:
            self.estado.set_text(_MENSAJE_INICIAL)
            if not limpiar_previa:
                self._actualizar_figura()
            return
        mensaje = "Preparando la gráfica de los datos actuales…" if limpiar_previa else "Actualizando la gráfica…"
        self.estado.set_text(mensaje)
        self.tarea = programar_actualizacion(
            None, self._actualizar, self.disponible, ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)

    async def actualizar(self) -> None:
        """Calcula inmediatamente la vista previa al restaurar un ejercicio o iniciar pruebas."""
        self._invalidar()
        if self.disponible():
            self.tarea = asyncio.current_task()
            await self._actualizar()

    async def _actualizar(self) -> None:
        tarea = asyncio.current_task()
        revision = self._revision
        rango = self.rango_activo
        captura = {"expresion": self._obtener_expresion(), "x_min": rango[0], "x_max": rango[1]}
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

    def _encuadrar(self, evento) -> None:
        datos = getattr(evento, "args", None)
        if not self.disponible() or not isinstance(datos, dict) or datos.get("identidad") != self.identidad:
            return
        relayout = interpretar_relayout_x(datos, self._rango_base)
        if relayout is None:
            return
        if relayout["tipo"] == "invalido":
            self.estado.set_text(relayout["mensaje"])
        elif relayout["tipo"] == "restablecer":
            self.restablecer_vista()
        elif relayout["rango"] != self.rango_activo:
            self._rango_camara = relayout["rango"]
            self._programar_muestreo(limpiar_previa=False)

    def _muestra_cubre_rango(self, rango: tuple[float, float]) -> bool:
        if not self.respuesta or self.respuesta.get("estado") != "EXITO":
            return False
        entrada = self.respuesta.get("entrada") or {}
        inicio = entrada.get("extremo_izquierdo")
        fin = entrada.get("extremo_derecho")
        return inicio is not None and fin is not None and inicio <= rango[0] and fin >= rango[1]

    def disponible(self) -> bool:
        """Indica si los nodos siguen activos y aceptan una publicación."""
        return not self._cerrado and not self.grafica.is_deleted and not self.estado.is_deleted

    def _vigente(self, revision: int, tarea, captura: dict) -> bool:
        rango_captura = (captura["x_min"], captura["x_max"])
        return (self.disponible() and revision == self._revision and self.tarea is tarea
                and captura["expresion"] == self._obtener_expresion()
                and rango_captura == self.rango_activo)

    def _detener_solicitud_pendiente(self) -> None:
        self._revision += 1
        self.coordinador.invalidar()
        cancelar_actualizacion(self.tarea)
        self.tarea = None
        if hasattr(self, "estado") and not self.estado.is_deleted:
            self.estado.props("aria-busy=false")

    def _invalidar(self) -> None:
        self._detener_solicitud_pendiente()
        self.respuesta = None
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
