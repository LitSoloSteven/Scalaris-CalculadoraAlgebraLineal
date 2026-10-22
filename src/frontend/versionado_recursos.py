"""Huellas de contenido de los recursos propios para invalidar cachés de despliegues."""
import hashlib
import re
from pathlib import Path

_RECURSOS = Path(__file__).parent / "recursos"
_URL_RECURSO = re.compile(r'(?P<atributo>\b(?:src|href)=")(?P<url>/assets/(?:js|css)/[\w-]+\.(?:js|css))"')


def _calcular_versiones() -> dict[str, str]:
    return {f"/assets/{ruta.relative_to(_RECURSOS).as_posix()}": hashlib.sha256(ruta.read_bytes()).hexdigest()
            for carpeta in ("js", "css") for ruta in (_RECURSOS / carpeta).iterdir()
            if ruta.is_file() and ruta.suffix == f".{carpeta}"}


_VERSIONES = _calcular_versiones()


def versionar_html(cabecera: str) -> str:
    """Añade la huella de contenido a src y href conocidos sin tocar URL externas."""
    def versionar(coincidencia: re.Match[str]) -> str:
        """Añade la huella al atributo de un recurso presente en el inventario."""
        url = coincidencia.group("url")
        version = _VERSIONES.get(url)
        if version is None:
            return coincidencia.group()
        return f'{coincidencia.group("atributo")}{url}?v={version}"'

    return _URL_RECURSO.sub(versionar, cabecera)
