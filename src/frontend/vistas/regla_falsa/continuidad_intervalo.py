"""Consulta previa acotada y revocable del intervalo de regla falsa."""
import asyncio

from nicegui import ui

from src.frontend.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.controladores.actualizacion_cancelable import cancelar_actualizacion, programar_actualizacion
from src.frontend.controladores.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.regla_falsa.continuidad_intervalo import CLAVES_CONTINUIDAD, consultar_continuidad
from src.frontend.controladores.biseccion.presentacion import numero
from src.frontend.vistas.biseccion.continuidad_intervalo import mostrar_informe


class PanelContinuidad:
    """Mantiene una plaza real y evita que un diagnóstico antiguo sustituya al resultado final."""

    def __init__(self, vista):
        self.vista = vista
        self.coordinador = CoordinadorTrabajosRaices(consultar_continuidad)
        self.tarea = self.respuesta = self._clave = None
        self._revision = 0
        self._cerrado = False

    def construir(self) -> None:
        """Monta la región viva del diagnóstico previo sin modificar los campos de captura."""
        self.region = ui.column().classes("w-full min-w-0 gap-1").props("role=status aria-live=polite")
        self.programar()

    def capturar(self) -> dict:
        """Entrega solo expresión, unidad y extremos; excluye parámetros de parada."""
        captura = self.vista.capturar()
        return {clave: captura.get(clave) for clave in CLAVES_CONTINUIDAD}

    def programar(self) -> None:
        """Revoca datos antiguos y consulta únicamente si cambió la geometría del intervalo."""
        if not self.disponible():
            return
        self.region.set_visibility(self.vista.ultimo_resultado is None)
        captura = self.capturar()
        if captura == self._clave:
            return
        self._clave = captura
        self._revision += 1
        self.coordinador.invalidar()
        cancelar_actualizacion(self.tarea)
        self.tarea = self.respuesta = None
        completo = all(str(captura[clave] or "").strip() for clave in CLAVES_CONTINUIDAD[:3])
        if not completo:
            self._mostrar("Completa la función y ambos extremos para consultar la continuidad.")
            return
        self._mostrar("Consultando la continuidad del intervalo…")
        self.tarea = programar_actualizacion(None, self._consultar, self.disponible,
                                            ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)

    async def _consultar(self) -> None:
        tarea, revision, destino = asyncio.current_task(), self._revision, self.region
        captura = self.capturar()
        try:
            respuesta = await self.coordinador.ejecutar(captura)
            if respuesta is not None and self._vigente(revision, destino, captura):
                self.respuesta = respuesta
                self._mostrar(respuesta.get("mensaje"))
        except asyncio.CancelledError:
            return
        except Exception:
            if self._vigente(revision, destino, captura):
                self._mostrar("No se pudo consultar la continuidad. Revisa la función y los extremos.")
        finally:
            if self.tarea is tarea:
                self.tarea = None

    def _vigente(self, revision: int, destino, captura: dict) -> bool:
        return (self.disponible() and revision == self._revision and destino is self.region
                and captura == self.capturar())

    def _mostrar(self, mensaje: str | None = None) -> None:
        self.region.clear()
        self.region.set_visibility(self.vista.ultimo_resultado is None)
        with self.region:
            ui.label("Continuidad previa; el diagnóstico del cálculo será la referencia final.").classes(
                "text-sm texto-secundario")
            respuesta = self.respuesta or {}
            if respuesta.get("informe") is not None:
                mostrar_informe(respuesta["informe"])
                for evaluacion in respuesta["evaluaciones"]:
                    valor = evaluacion["mensaje"] if evaluacion["codigo"] else numero(evaluacion["valor"], True)
                    ui.label(f"f({numero(evaluacion['abscisa'], True)}) = {valor}").classes(
                        "regla-falsa-numero text-sm texto-secundario")
            if mensaje or respuesta.get("fallo"):
                ui.label(mensaje or respuesta["fallo"]["mensaje"]).classes("texto-advertencia text-sm")

    def disponible(self) -> bool:
        """Indica si los nodos y el cliente admiten publicaciones."""
        return not self._cerrado and not self.region.is_deleted

    def cerrar(self) -> None:
        """Revoca pendientes al desconectar sin liberar prematuramente el trabajador real."""
        self._cerrado = True
        self._revision += 1
        self._clave = self.respuesta = None
        self.coordinador.cerrar()
        cancelar_actualizacion(self.tarea)
        self.tarea = None

    def reabrir(self) -> None:
        """Consulta de nuevo la captura actual tras la reconexión."""
        self._cerrado = self.region.is_deleted
        if not self._cerrado:
            self.coordinador.reabrir()
            self.programar()
