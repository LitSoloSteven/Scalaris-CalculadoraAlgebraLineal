"""Escritura atómica con recuperación acotada de bloqueos transitorios de Windows."""
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

INTENTOS_REEMPLAZO = 8
ESPERA_INICIAL = 0.05
ESPERA_MAXIMA = 0.25
_BLOQUEOS_WINDOWS = frozenset({5, 32, 33})


class RespaldoObsoleto(Exception):
    """Indica que se eliminó o sustituyó el directorio que originó un respaldo pendiente."""


def identificar_directorio(directorio: Path) -> tuple[int, int, int]:
    """Devuelve identidad y creación estables del directorio; propaga errores de acceso o ausencia."""
    datos = directorio.stat()
    return datos.st_dev, datos.st_ino, getattr(datos, 'st_birthtime_ns', 0)


def comprobar_directorio(destino: Path, identidad: tuple[int, int, int] | None) -> None:
    """Rechaza un respaldo si su directorio fue eliminado o reemplazado desde que se programó."""
    if identidad is None:
        return
    try:
        actual = identificar_directorio(destino.parent)
    except FileNotFoundError as error:
        raise RespaldoObsoleto from error
    if actual != identidad:
        raise RespaldoObsoleto


def _crear_temporal(destino: Path, contenido: str, codificacion: str | None) -> Path:
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding=codificacion, dir=destino.parent,
                                         prefix=f'{destino.stem}.', suffix=f'{destino.suffix}.tmp', delete=False) as archivo:
            temporal = Path(archivo.name)
            archivo.write(contenido)
    except BaseException as error:
        if temporal is not None:
            try:
                temporal.unlink(missing_ok=True)
            except OSError:
                error.add_note('No se pudo retirar el archivo temporal de persistencia.')
        raise
    return temporal


def _ejecutar_con_reintentos(destino: Path, identidad: tuple[int, int, int] | None,
                            accion: Callable[[], object]) -> None:
    for intento in range(INTENTOS_REEMPLAZO):
        comprobar_directorio(destino, identidad)
        try:
            accion()
            return
        except PermissionError as error:
            if getattr(error, 'winerror', None) not in _BLOQUEOS_WINDOWS or intento == INTENTOS_REEMPLAZO - 1:
                raise
            time.sleep(min(ESPERA_INICIAL * 2 ** intento, ESPERA_MAXIMA))


def guardar_archivo_atomico(destino: Path, contenido: str, codificacion: str | None = 'utf-8', *,
                            directorio_esperado: tuple[int, int, int] | None = None) -> None:
    """Escribe texto completo y reintenta reemplazos bloqueados; propaga errores permanentes sin alterar el destino."""
    if directorio_esperado is None:
        destino.parent.mkdir(exist_ok=True)
    comprobar_directorio(destino, directorio_esperado)
    temporal = _crear_temporal(destino, contenido, codificacion)
    try:
        _ejecutar_con_reintentos(destino, directorio_esperado, lambda: temporal.replace(destino))
    finally:
        temporal.unlink(missing_ok=True)


def eliminar_archivo_persistente(destino: Path, directorio_esperado: tuple[int, int, int]) -> None:
    """Elimina el archivo revalidando su directorio en cada intento para no borrar una sesión nueva."""
    _ejecutar_con_reintentos(destino, directorio_esperado, lambda: destino.unlink(missing_ok=True))
