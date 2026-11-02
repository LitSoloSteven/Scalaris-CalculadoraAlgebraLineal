"""Adaptador de respaldos NiceGUI que conserva lectura y formato del almacenamiento."""
import asyncio

from nicegui import background_tasks, core
from nicegui.persistence import FilePersistentDict
from nicegui.persistence.serialization import dumps

from src.frontend.archivo_atomico import (
    RespaldoObsoleto, comprobar_directorio, eliminar_archivo_persistente,
    guardar_archivo_atomico, identificar_directorio,
)


class DiccionarioPersistenteSeguro(FilePersistentDict):
    """Mantiene la API del diccionario de NiceGUI y reemplaza sus respaldos con archivos atómicos."""

    def backup(self) -> None:
        """Programa el respaldo si hay bucle activo; en arranque escribe o elimina el archivo directamente."""
        if self:
            self.filepath.parent.mkdir(exist_ok=True)
        try:
            identidad = identificar_directorio(self.filepath.parent)
        except FileNotFoundError:
            return
        if core.is_loop_running():
            background_tasks.create_lazy(self._respaldar_asincrono(identidad), name=f'persistencia:{self.filepath.resolve()}')
        elif self:
            guardar_archivo_atomico(self.filepath, dumps(self, str(self.filepath), indent=self.indent), self.encoding,
                                    directorio_esperado=identidad)
        else:
            eliminar_archivo_persistente(self.filepath, identidad)

    @background_tasks.await_on_shutdown
    async def _respaldar_asincrono(self, identidad: tuple[int, int, int]) -> None:
        try:
            comprobar_directorio(self.filepath, identidad)
            if not self:
                await asyncio.to_thread(eliminar_archivo_persistente, self.filepath, identidad)
                return
            contenido = dumps(self, str(self.filepath), indent=self.indent)
            await asyncio.to_thread(guardar_archivo_atomico, self.filepath, contenido, self.encoding,
                                    directorio_esperado=identidad)
        except (RespaldoObsoleto, FileNotFoundError):
            return
