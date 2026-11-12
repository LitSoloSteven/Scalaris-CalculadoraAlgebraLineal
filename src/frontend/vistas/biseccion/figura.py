"""Figura temática para relacionar la función con la partición activa."""
import plotly.graph_objects as go

from src.backend.resolutores.raices.contrato_biseccion import ESTADO_DISCONTINUIDAD
from src.frontend.tema import PALETA_GRAFICOS, COLOR_SOLUCION
from src.frontend.vistas.geometria._colores_figuras import aplicar_colores_figura
from src.frontend.componentes.figura_funcion_real import crear_base as _crear_base, crear_figura_previa


def crear_figura(respuesta: dict, muestra: dict, fila: dict | None = None, inicial: bool = False) -> go.Figure:
    """Construye una figura sin unir huecos, con intervalo y aproximación rotulados."""
    entrada = respuesta["entrada"]
    if inicial:
        respuesta = {**respuesta, "intervalo_final": None, "aproximacion": None}
    inferior, superior = (fila["extremo_izquierdo"], fila["extremo_derecho"]) if fila else (
        respuesta.get("intervalo_final") or (entrada["extremo_izquierdo"], entrada["extremo_derecho"]))
    medio = fila["c"] if fila else respuesta.get("aproximacion")
    figura = _crear_base(muestra)
    figura.add_trace(go.Scatter(x=[inferior, superior], y=[0, 0], mode="lines+markers", name="Intervalo [a, b]",
                               line=dict(color=PALETA_GRAFICOS[1], width=5, dash="dot")))
    if medio is not None:
        valor, etiqueta = _ordenada_marcador(respuesta, fila)
        figura.add_trace(go.Scatter(x=[medio], y=[valor], mode="markers", name=etiqueta,
                                   marker=dict(color=COLOR_SOLUCION, size=11, symbol="diamond")))
    aplicar_colores_figura(figura, "papel")
    return figura


def _ordenada_marcador(respuesta: dict, fila: dict | None) -> tuple[float | None, str]:
    if fila is not None:
        return fila["f_c"], "Punto medio c"
    if respuesta.get("estado") == ESTADO_DISCONTINUIDAD:
        filas = respuesta.get("iteraciones") or ()
        return (filas[-1]["f_c"] if filas else None), "Muestra provisional"
    return 0, "Aproximación en x"
