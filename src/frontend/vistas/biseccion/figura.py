"""Figura temática para relacionar la función con la partición activa."""
import plotly.graph_objects as go

from src.frontend.tema import COLOR_TRANSPARENTE, PALETA_GRAFICOS, COLOR_SOLUCION
from src.frontend.vistas.geometria._colores_figuras import aplicar_colores_figura


def crear_figura(respuesta: dict, muestra: dict, fila: dict | None = None, inicial: bool = False) -> go.Figure:
    """Construye una figura sin unir huecos, con intervalo y aproximación rotulados."""
    entrada = respuesta["entrada"]
    if inicial:
        respuesta = {**respuesta, "intervalo_final": None, "aproximacion": None}
    inferior, superior = (fila["extremo_izquierdo"], fila["extremo_derecho"]) if fila else (
        respuesta.get("intervalo_final") or (entrada["extremo_izquierdo"], entrada["extremo_derecho"]))
    medio = fila["c"] if fila else respuesta.get("aproximacion")
    figura = go.Figure(go.Scatter(x=muestra["x"], y=muestra["y"], mode="lines", name="f(x)",
                                  connectgaps=False, line=dict(color=PALETA_GRAFICOS[2])))
    figura.add_trace(go.Scatter(x=[inferior, superior], y=[0, 0], mode="lines+markers", name="Intervalo [a, b]",
                               line=dict(color=PALETA_GRAFICOS[1], width=5, dash="dot")))
    if medio is not None:
        figura.add_trace(go.Scatter(x=[medio], y=[fila["f_c"] if fila else 0], mode="markers",
                                   name="Punto medio c" if fila else "Aproximación en x",
                                   marker=dict(color=COLOR_SOLUCION, size=11, symbol="diamond")))
    figura.update_layout(paper_bgcolor=COLOR_TRANSPARENTE, plot_bgcolor=COLOR_TRANSPARENTE,
                         margin=dict(l=40, r=15, t=25, b=40), height=340,
                         legend=dict(orientation="h", y=-0.25), uirevision="biseccion", hovermode=False,
                         xaxis_title="x", yaxis_title="f(x)", font_family="Space Grotesk, sans-serif")
    figura.update_xaxes(zeroline=True)
    figura.update_yaxes(zeroline=True)
    aplicar_colores_figura(figura, "papel")
    return figura
