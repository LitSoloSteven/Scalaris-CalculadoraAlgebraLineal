"""Figura temática compartida para muestras reales con huecos."""
import plotly.graph_objects as go

from src.frontend.tema import COLOR_TRANSPARENTE, PALETA_GRAFICOS
from src.frontend.componentes.colores_figuras import aplicar_colores_figura


def crear_figura_previa(respuesta: dict) -> go.Figure:
    """Dibuja la función en el rango visual sin simular un resultado matemático."""
    figura = crear_base(respuesta["muestra"])
    entrada = respuesta["entrada"]
    rango = (entrada["extremo_izquierdo"], entrada["extremo_derecho"])
    figura.update_layout(uirevision=f"previa:{entrada['expresion']}:{rango}", showlegend=False)
    figura.update_xaxes(range=rango, autorange=False)
    aplicar_colores_figura(figura, "papel")
    return figura


def crear_base(muestra: dict) -> go.Figure:
    """Construye ejes y curva sin conectar evaluaciones inválidas ni mostrar coordenadas emergentes."""
    figura = go.Figure(go.Scatter(x=muestra["x"], y=muestra["y"], mode="lines", name="f(x)",
                                  connectgaps=False, line=dict(color=PALETA_GRAFICOS[2])))
    figura.update_layout(paper_bgcolor=COLOR_TRANSPARENTE, plot_bgcolor=COLOR_TRANSPARENTE,
                         margin=dict(l=40, r=15, t=25, b=40), height=340,
                         legend=dict(orientation="h", y=-0.25), uirevision="biseccion", hovermode=False,
                         xaxis_title="x", yaxis_title="f(x)", font_family="Space Grotesk, sans-serif")
    figura.update_xaxes(zeroline=True)
    figura.update_yaxes(zeroline=True)
    return figura
