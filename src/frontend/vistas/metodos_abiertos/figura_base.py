"""Figuras vacías que conservan las dimensiones y el tema de Scalaris."""
import plotly.graph_objects as go

from src.frontend.tema import COLOR_TRANSPARENTE


def crear_figura_vacia() -> go.Figure:
    """Crea ejes sin trazas para los estados inicial y vacío de la gráfica."""
    figura = go.Figure()
    figura.update_layout(
        height=350, margin=dict(l=40, r=20, t=15, b=40),
        paper_bgcolor=COLOR_TRANSPARENTE, plot_bgcolor=COLOR_TRANSPARENTE,
        xaxis_title="x", yaxis_title="f(x)", font_family="Space Grotesk, sans-serif",
    )
    return figura
