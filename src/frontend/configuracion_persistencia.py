"""Registro del adaptador de archivos en la fábrica de almacenamiento de NiceGUI."""
import nicegui.storage as almacenamiento_nicegui
from nicegui.persistence import FilePersistentDict

from src.frontend.persistencia_archivo import DiccionarioPersistenteSeguro


def configurar_persistencia() -> None:
    """Activa respaldos seguros para sesiones nuevas sin modificar archivos ni el backend Redis."""
    actual = almacenamiento_nicegui.FilePersistentDict
    if actual is DiccionarioPersistenteSeguro:
        return
    if actual is not FilePersistentDict:
        raise RuntimeError('El almacenamiento de archivos ya tiene otro adaptador configurado.')
    setattr(almacenamiento_nicegui, 'FilePersistentDict', DiccionarioPersistenteSeguro)
