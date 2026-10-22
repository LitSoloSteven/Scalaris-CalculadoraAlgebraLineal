"""Configuración de temas, paletas y recursos estáticos de Scalaris."""
import json
from pathlib import Path
from string import Template
from nicegui import ui

from src.frontend import banderas
from src.frontend.recursos_vistas import seleccionar_recursos
from src.frontend.versionado_recursos import versionar_html

# Paletas de color con ratio de contraste no textual >= 3.0:1 verificado en cada tema
PALETAS_POR_TEMA: dict[str, list[str]] = {
    "papel": ["#C71F47", "#0D7A53", "#1D6FB8", "#B45309", "#6D28D9"],
    "marea": ["#B91C47", "#0D6E48", "#145A96", "#9A4500", "#5B21B6"],
    "medianoche": ["#FB7185", "#34D399", "#38BDF8", "#FBBF24", "#A78BFA"],
}

COLORES_SOLUCION_POR_TEMA: dict[str, str] = {
    "papel": "#BE123C",
    "marea": "#B91C47",
    "medianoche": "#F43F5E",
}

COLORES_TEXTO_GRAFICOS: dict[str, str] = {
    "papel": "#23262E",
    "marea": "#0B1F33",
    "medianoche": "#EAF6FF",
}

COLORES_CUADRICULA_GRAFICOS: dict[str, str] = {
    "papel": "#5A6070",
    "marea": "#1F3A52",
    "medianoche": "#B1D4F0",
}

PALETA_GRAFICOS = PALETAS_POR_TEMA["papel"]
COLOR_MARCADOR_CLARO = "#FFFFFF"
COLOR_MARCADOR_BORDE = "#23262E"
COLOR_CUADRICULA = "rgba(128,128,128,0.2)"
COLOR_CERO = "rgba(128,128,128,0.5)"
COLOR_TRANSPARENTE = "rgba(0,0,0,0)"
COLOR_SOLUCION = COLORES_SOLUCION_POR_TEMA["papel"]
OPACIDAD_PLANOS = 0.85


def obtener_paleta_tema(tema: str = "papel") -> list[str]:
    """Devuelve la paleta de colores con contraste óptimo para el tema solicitado."""
    return PALETAS_POR_TEMA.get(tema, PALETAS_POR_TEMA["papel"])


def obtener_color_solucion(tema: str = "papel") -> str:
    """Devuelve el color de solución con contraste garantizado para el tema."""
    return COLORES_SOLUCION_POR_TEMA.get(tema, COLORES_SOLUCION_POR_TEMA["papel"])


_CONFIGURACION_GRAFICOS_JSON = json.dumps(
    {
        "paletas": PALETAS_POR_TEMA,
        "solucion": COLORES_SOLUCION_POR_TEMA,
        "texto": COLORES_TEXTO_GRAFICOS,
        "cuadricula": COLORES_CUADRICULA_GRAFICOS,
    }
)

def _etiquetas_recursos_cliente(nombre_catalogo: str) -> str:
    catalogo = Path(__file__).parent / "recursos" / nombre_catalogo
    return "\n".join(f'<script src="/assets/js/{nombre}"></script>'
                     for nombre in json.loads(catalogo.read_text(encoding="utf-8")))

_PLANTILLAS = Path(__file__).parent / "recursos" / "plantillas"
_CABECERA_HTML = Template((_PLANTILLAS / "cabecera.html").read_text(encoding="utf-8")).substitute(
    configuracion_graficos=_CONFIGURACION_GRAFICOS_JSON.replace("<", "\\u003c"),
    plantilla_presentacion=(_PLANTILLAS / "presentacion.html").read_text(encoding="utf-8"),
    etiquetas_interacciones=_etiquetas_recursos_cliente("catalogo_interacciones.json"),
    etiquetas_captura=_etiquetas_recursos_cliente("catalogo_captura.json"),
)
_CABECERA_GLOSA_HTML = (_PLANTILLAS / "cabecera_glosa.html").read_text(encoding="utf-8")


def configurar_tema(vista: str = "") -> None:
    """Configura fuentes, estilos, MathJax y recursos cliente de la interfaz."""
    def agregar(cabecera: str) -> None:
        """Prepara la cabecera antes de que la conexión pueda enviar el HTML inicial."""
        seleccion = seleccionar_recursos(cabecera, vista)
        ui.add_head_html(versionar_html(seleccion) if vista else seleccion)

    agregar(_CABECERA_HTML)
    if banderas.panel_lateral_habilitado():
        agregar(_CABECERA_GLOSA_HTML)
