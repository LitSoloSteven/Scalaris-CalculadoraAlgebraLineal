"""Descubrimiento completo de código y estilos sujetos a auditoría."""
from tests.comun import RAIZ

EXTENSIONES_AUDITADAS = {".py", ".js", ".css", ".html"}
RUTAS_AUDITADAS = sorted(
    ruta for carpeta in ("src", "tests")
    for ruta in (RAIZ / carpeta).rglob("*")
    if ruta.is_file() and ruta.suffix in EXTENSIONES_AUDITADAS
)
