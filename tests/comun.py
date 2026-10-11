"""Utilidades comunes y compartidas para la suite de pruebas."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

ARCHIVOS_CSS = [
    RAIZ / "src" / "frontend" / "assets" / "css" / "tokens.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "base.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "layout.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "componentes_entradas.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "componentes_controles.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_navegacion.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_hub_matriz.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_hub_popovers.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_hub_adaptable.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_glosa_dock.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_glosa_componentes.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_inversa.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "movimiento.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "reproductor_pasos.css",
]


def leer_css_completo() -> str:
    """Lee y concatena el conjunto ordenado de hojas de estilo en orden de cascada."""
    return "\n".join(archivo.read_text(encoding="utf-8") for archivo in ARCHIVOS_CSS)
