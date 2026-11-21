"""Diagnóstico previo del intervalo en el método activo."""
import logging

from nicegui import ui

from src.frontend.componentes.raices.resultados.informe_continuidad_raices import mostrar_consulta_continuidad
from src.frontend.nucleo.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.controladores.compartido.sesion.actualizacion_cancelable import cancelar_actualizacion, programar_actualizacion
from src.frontend.controladores.raices.biseccion.ejecucion.continuidad_intervalo import consultar_continuidad as consultar_biseccion
from src.frontend.controladores.raices.compartido.ejecucion.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION, REGLA_FALSA
from src.frontend.controladores.regla_falsa.continuidad_intervalo import CLAVES_CONTINUIDAD, consultar_continuidad

_REGISTRO = logging.getLogger(__name__)
_CONSULTAS = {BISECCION: consultar_biseccion, REGLA_FALSA: consultar_continuidad}
_CAMPOS = (*CLAVES_CONTINUIDAD, "cero_preferido", "metodo")


class ContinuidadMetodosCerrados:
    """Comparte una región y acota las consultas pendientes de cada método."""

    def __init__(self, vista):
        self.vista = vista
        self.trabajos = {metodo: CoordinadorTrabajosRaices(consultar) for metodo, consultar in _CONSULTAS.items()}
        self.tarea = self._solicitud = None
        self._revision = 0

    def construir(self) -> None:
        """Monta un diagnóstico que se actualiza con los extremos manuales."""
        self.region = ui.column().classes("w-full min-w-0 gap-1").props("role=status aria-live=polite")
        self.actualizar()

    def actualizar(self) -> None:
        """Consulta si cambió el intervalo y lo oculta al publicar el resultado final."""
        if self.region.is_deleted or self.vista._cerrada:
            return
        captura = self.vista.capturar()
        solicitud = {clave: captura.get(clave) for clave in _CAMPOS}
        activa = self.vista.ultimo_resultado is None and not self.vista.en_busqueda
        self.region.set_visibility(activa)
        if not activa:
            self.cancelar()
            return
        if solicitud == self._solicitud:
            return
        self.cancelar()
        self._solicitud = solicitud
        if all(str(solicitud[clave] or "").strip() for clave in CLAVES_CONTINUIDAD[:3]):
            self._mostrar({"mensaje": "Consultando la continuidad del intervalo…"})
            self.tarea = programar_actualizacion(None, self._consultar, lambda: not self.region.is_deleted,
                                                 ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)
        else:
            self.region.clear()

    def cancelar(self) -> None:
        """Revoca la consulta y su publicación al salir de la captura manual."""
        self._revision += 1
        self._solicitud = None
        cancelar_actualizacion(self.tarea)
        self.tarea = None
        for trabajo in self.trabajos.values():
            trabajo.invalidar()

    async def _consultar(self) -> None:
        revision, solicitud = self._revision, self._solicitud
        if solicitud is None:
            return
        try:
            respuesta = await self.trabajos[solicitud["metodo"]].ejecutar(solicitud)
        except Exception:
            _REGISTRO.exception("No se pudo consultar la continuidad del intervalo")
            respuesta = {"mensaje": "Revisa la función y los extremos para consultar la continuidad."}
        if respuesta is not None and revision == self._revision and not self.region.is_deleted:
            self._mostrar(respuesta)

    def _mostrar(self, respuesta: dict) -> None:
        self.region.clear()
        with self.region:
            mostrar_consulta_continuidad(respuesta, "texto-principal", "text-sm texto-secundario",
                                        respuesta.get("mensaje"))
