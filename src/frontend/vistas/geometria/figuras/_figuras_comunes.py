"""Funciones compartidas de disposicion y malla para figuras Plotly de geometria."""
from __future__ import annotations

from src.frontend.presentacion.tema import COLOR_CUADRICULA, COLOR_CERO, COLOR_TRANSPARENTE


def disposicion_2d(fig, *, rango_ejes: list[float], color_fuente: str, revision: str = "rectas"):
    """Aplica la disposicion comun de ejes, margenes y leyenda para figuras 2D."""
    fig.update_layout(
        paper_bgcolor=COLOR_TRANSPARENTE,
        plot_bgcolor=COLOR_TRANSPARENTE,
        font=dict(color=color_fuente, family='Space Grotesk, sans-serif'),
        margin=dict(l=44, r=20, t=44, b=56),
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
            yanchor='top',
            y=-0.16,
            xanchor='center',
            x=0.5,
        ),
    )


def disposicion_3d(fig, *, rango_ejes: list[float], color_fuente: str, revision: str = "planos"):
    """Aplica la disposicion comun de ejes y margenes para figuras 3D."""
    fig.update_layout(
        paper_bgcolor=COLOR_TRANSPARENTE,
        plot_bgcolor=COLOR_TRANSPARENTE,
        font=dict(color=color_fuente, family='Space Grotesk, sans-serif'),
        margin=dict(l=44, r=16, t=30, b=56),
        legend=dict(orientation='h', x=0.5, xanchor='center', y=0, yanchor='top'),
        scene=dict(
            xaxis=dict(backgroundcolor=COLOR_TRANSPARENTE, gridcolor=COLOR_CUADRICULA, range=rango_ejes),
            yaxis=dict(backgroundcolor=COLOR_TRANSPARENTE, gridcolor=COLOR_CUADRICULA, range=rango_ejes),
            zaxis=dict(backgroundcolor=COLOR_TRANSPARENTE, gridcolor=COLOR_CUADRICULA, range=rango_ejes),
            aspectmode='cube',
        ),
        uirevision=revision,
    )


