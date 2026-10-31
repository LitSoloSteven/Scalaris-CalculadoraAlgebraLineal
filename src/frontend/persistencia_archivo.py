"""Adaptador de respaldos NiceGUI que conserva lectura y formato del almacenamiento."""
import asyncio

from nicegui import background_tasks, core
from nicegui.helpers import unlink_with_retry, unlink_with_retry_async
from nicegui.persistence import FilePersistentDict
from nicegui.persistence.serialization import dumps

from src.frontend.archivo_atomico import guardar_archivo_atomico


class DiccionarioPersistenteSeguro(FilePersistentDict):
    """Mantiene la API del diccionario de NiceGUI y reemplaza sus respaldos con archivos atómicos."""

    def backup(self) -> None:
        """Programa el respaldo si hay bucle activo; en arranque escribe o elimina el archivo directamente."""
        if core.is_loop_running():
            background_tasks.create_lazy(self._respaldar_asincrono(), name=f'persistencia:{self.filepath.resolve()}')
        elif self:
            guardar_archivo_atomico(self.filepath, dumps(self, str(self.filepath), indent=self.indent), self.encoding)
        else:
            unlink_with_retry(self.filepath, missing_ok=True)

    @background_tasks.await_on_shutdown
    async def _respaldar_asincrono(self) -> None:
        if not self:
            await unlink_with_retry_async(self.filepath, missing_ok=True)
            return
        contenido = dumps(self, str(self.filepath), indent=self.indent)
        await asyncio.to_thread(guardar_archivo_atomico, self.filepath, contenido, self.encoding)
