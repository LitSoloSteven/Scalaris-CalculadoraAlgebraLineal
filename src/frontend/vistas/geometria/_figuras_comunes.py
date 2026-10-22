"""Funciones compartidas de disposicion y malla para figuras Plotly de geometria."""
from __future__ import annotations

from src.frontend.tema import COLOR_CUADRICULA, COLOR_CERO, COLOR_TRANSPARENTE


def disposicion_2d(fig, *, rango_ejes: list[float], color_fuente: str, revision: str = "rectas"):
    """Aplica la disposicion comun de ejes, margenes y leyenda para figuras 2D."""
    fig.update_layout(
        paper_bgcolor=COLOR_TRANSPARENTE,
        plot_bgcolor=COLOR_TRANSPARENTE,
        font=dict(color=color_fuente, family='Space Grotesk, sans-serif'),
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(
            gridcolor=COLOR_CUADRICULA,
            zerolinecolor=COLOR_CERO,
            range=rango_ejes,
            scaleanchor='y',
            scaleratio=1,
            constrain='domain',
        ),
        yaxis=dict(
            gridcolor=COLOR_CUADRICULA,
            zerolinecolor=COLOR_CERO,
            range=rango_ejes,
        ),
        uirevision=revision,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
    )


def disposicion_3d(fig, *, rango_ejes: list[float], color_fuente: str, revision: str = "planos"):
    """Aplica la disposicion comun de ejes y margenes para figuras 3D."""
    fig.update_layout(
        paper_bgcolor=COLOR_TRANSPARENTE,
        plot_bgcolor=COLOR_TRANSPARENTE,
        font=dict(color=color_fuente, family='Space Grotesk, sans-serif'),
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(backgroundcolor=COLOR_TRANSPARENTE, gridcolor=COLOR_CUADRICULA, range=rango_ejes),
            yaxis=dict(backgroundcolor=COLOR_TRANSPARENTE, gridcolor=COLOR_CUADRICULA, range=rango_ejes),
            zaxis=dict(backgroundcolor=COLOR_TRANSPARENTE, gridcolor=COLOR_CUADRICULA, range=rango_ejes),
            aspectmode='cube',
        ),
        uirevision=revision,
    )


