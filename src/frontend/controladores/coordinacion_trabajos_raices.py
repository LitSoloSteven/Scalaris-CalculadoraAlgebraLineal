"""Una plaza real de trabajador y un borrador reemplazable por responsabilidad."""
import asyncio
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from nicegui import run


@dataclass(frozen=True)
class _Solicitud:
    captura: dict
    revision: int
    respuesta: asyncio.Future


class CoordinadorTrabajosRaices:
    """Serializa un controlador por cliente sin liberar su plaza al cancelar la espera."""

    def __init__(self, calcular: Callable[[dict], Any]):
        self._calcular = calcular
        self._revision = 0
        self._pendiente = None
        self._tarea = None
        self._cerrado = False
        self.activos = 0

    @property
    def pendientes(self) -> int:
        """Devuelve cero o uno según exista un borrador aún no ejecutado."""
        return int(self._pendiente is not None)

    async def ejecutar(self, captura: dict) -> Any:
        """Devuelve solo la respuesta vigente; propaga errores vigentes y cancelación."""
        if self._cerrado:
            return None
        self.invalidar()
        solicitud = _Solicitud(deepcopy(captura), self._revision, asyncio.get_running_loop().create_future())
        self._pendiente = solicitud
        if self._tarea is None:
            self._tarea = asyncio.create_task(self._procesar())
        try:
            return await asyncio.shield(solicitud.respuesta)
        except asyncio.CancelledError:
            solicitud.respuesta.cancel()
            if self._pendiente is solicitud:
                self._pendiente = None
            raise

    def invalidar(self) -> None:
        """Revoca publicaciones y elimina el borrador sin cancelar trabajo real."""
        self._revision += 1
        if self._pendiente is not None:
            self._terminar(self._pendiente)
            self._pendiente = None

    def cerrar(self) -> None:
        """Descarta el borrador y bloquea solicitudes hasta reabrir el cliente."""
        self._cerrado = True
        self.invalidar()

    def reabrir(self) -> None:
        """Acepta nuevas capturas sin recuperar publicaciones de la sesión anterior."""
        self._cerrado = False

    async def esperar_cierre(self) -> None:
        """Espera el trabajo real conservado; cancelar esta espera no lo detiene."""
        if self._tarea is not None:
            await asyncio.shield(self._tarea)

    async def _procesar(self) -> None:
        try:
            while self._pendiente is not None:
                solicitud, self._pendiente = self._pendiente, None
                await self._resolver(solicitud)
        finally:
            self._tarea = None

    async def _resolver(self, solicitud: _Solicitud) -> None:
        self.activos = 1
        try:
            resultado = await run.io_bound(self._calcular, solicitud.captura)
        except Exception as error:
            self._terminar(solicitud, error=error)
        else:
            self._terminar(solicitud, resultado)
        finally:
            self.activos = 0

    def _terminar(self, solicitud: _Solicitud, resultado=None, error: Exception | None = None) -> None:
        if solicitud.respuesta.done():
            return
        if self._cerrado or solicitud.revision != self._revision:
            solicitud.respuesta.set_result(None)
        elif error is not None:
            solicitud.respuesta.set_exception(error)
        else:
            solicitud.respuesta.set_result(resultado)
