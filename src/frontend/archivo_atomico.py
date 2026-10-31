"""Escritura atómica con recuperación acotada de bloqueos transitorios de Windows."""
import tempfile
import time
from pathlib import Path

INTENTOS_REEMPLAZO = 8
ESPERA_INICIAL = 0.05
ESPERA_MAXIMA = 0.25
_BLOQUEOS_WINDOWS = frozenset({5, 32, 33})


def _crear_temporal(destino: Path, contenido: str, codificacion: str | None) -> Path:
    destino.parent.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding=codificacion, dir=destino.parent,
                                     prefix=f'{destino.stem}.', suffix=f'{destino.suffix}.tmp', delete=False) as archivo:
        temporal = Path(archivo.name)
        try:
            archivo.write(contenido)
        except BaseException:
            archivo.close()
            temporal.unlink(missing_ok=True)
            raise
    return temporal


def _reemplazar(temporal: Path, destino: Path) -> None:
    for intento in range(INTENTOS_REEMPLAZO):
        try:
            temporal.replace(destino)
            return
        except PermissionError as error:
            if getattr(error, 'winerror', None) not in _BLOQUEOS_WINDOWS or intento == INTENTOS_REEMPLAZO - 1:
                raise
            time.sleep(min(ESPERA_INICIAL * 2 ** intento, ESPERA_MAXIMA))


def guardar_archivo_atomico(destino: Path, contenido: str, codificacion: str | None = 'utf-8') -> None:
    """Escribe texto completo y reintenta reemplazos bloqueados; propaga errores permanentes sin alterar el destino."""
    temporal = _crear_temporal(destino, contenido, codificacion)
    try:
        _reemplazar(temporal, destino)
    finally:
        temporal.unlink(missing_ok=True)
