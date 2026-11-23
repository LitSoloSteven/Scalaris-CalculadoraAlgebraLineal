"""Construcción de figuras Plotly para conjuntos afines y primitivos compartidos."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

from src.backend.constantes import TOLERANCIA_CERO_GRAFICO
from src.backend.geometria.base.muestreo import superficie_plano
from src.frontend.presentacion.tema import (
    COLORES_TEXTO_GRAFICOS,
    COLOR_CUADRICULA,
    COLOR_MARCADOR_BORDE,
    COLOR_MARCADOR_CLARO,
    COLOR_SOLUCION,
    COLOR_TRANSPARENTE,
    PALETA_GRAFICOS,
)
from ._colores_figuras import aplicar_colores_figura
from ._figuras_comunes import disposicion_2d, disposicion_3d

_LIMITE_VISUAL = 1e12
_LIMITE_TEXTO_COORDENADA = 256
_OPACIDAD_PLANO = 0.45


@dataclass(frozen=True)
class _GeometriaAfin:
    dimension: int
    punto: tuple[float, ...]
    p_frac: tuple[Fraction, ...]
    d_vis: tuple[tuple[float, ...], ...]
    d_fracs: tuple[tuple[Fraction, ...], ...]
    rango: list[float]


def interpretar_vectores_visuales(
    vectores: tuple, dimension_ambiente: int
) -> tuple[tuple[tuple[Fraction, ...], ...], tuple[tuple[float, ...], ...]]:
    """Convierte vectores exactos a Fraction y float validando rango visual."""
    fracciones = []
    coordenadas = []
    for vector in vectores:
        if len(vector) != dimension_ambiente:
            raise ValueError("Dimensión incompatible")
        fila_fraccion = tuple(_parsear_fraccion(celda) for celda in vector)
        fila_visual = tuple(_convertir_visual(valor) for valor in fila_fraccion)
        fracciones.append(fila_fraccion)
        coordenadas.append(fila_visual)
    return tuple(fracciones), tuple(coordenadas)


def _parsear_fraccion(celda: object) -> Fraction:
    if isinstance(celda, Fraction):
        return celda
    texto = str(celda).strip()
    if len(texto) > _LIMITE_TEXTO_COORDENADA:
        raise ValueError("Coordenada extensa")
    return Fraction(texto)


def _convertir_visual(valor: Fraction) -> float:
    numero = float(valor)
    if not math.isfinite(numero) or abs(numero) > _LIMITE_VISUAL:
        raise ValueError("Coordenada fuera de rango visual")
    if valor != 0 and abs(numero) < TOLERANCIA_CERO_GRAFICO:
        raise ValueError("Coordenada inferior al umbral visual")
    return numero


def calcular_rango_visual(puntos: tuple[tuple[float, ...], ...]) -> list[float]:
    """Calcula un rango simétrico que incluye todos los puntos y vectores."""
    mayor = max((abs(valor) for punto in puntos for valor in punto), default=1.0)
    limite = 5.0 if mayor <= 4.0 else mayor * 1.25
    return [-limite, limite]


def aplicar_layout_1d(figura, rango: list[float], fuente: str) -> None:
    """Configura la disposición compartida para escenas en una dimensión."""
    figura.update_layout(
        paper_bgcolor=COLOR_TRANSPARENTE,
        plot_bgcolor=COLOR_TRANSPARENTE,
        font=dict(color=fuente, family="Space Grotesk, sans-serif"),
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(gridcolor=COLOR_CUADRICULA, zerolinecolor=COLOR_MARCADOR_BORDE, range=rango),
        yaxis=dict(visible=False, range=[-1.0, 1.0]),
        uirevision="subespacios-1d",
    )


def agregar_flecha_2d(
    figura, origen: tuple[float, float], destino: tuple[float, float], nombre: str, color: str
) -> None:
    """Dibuja un vector 2D desde origen hasta destino con marcador de flecha."""
    import plotly.graph_objects as graficos

    figura.add_trace(graficos.Scatter(
        x=[origen[0], destino[0]], y=[origen[1], destino[1]],
        mode="lines+markers", name=nombre, line=dict(color=color, width=3),
        marker=dict(color=color, size=[0, 10], symbol=["circle", "arrow"], angleref="previous"),
    ))


def agregar_flecha_3d(
    figura, origen: tuple[float, float, float], destino: tuple[float, float, float], nombre: str, color: str
) -> None:
    """Dibuja un vector 3D desde origen hasta destino con marcador terminal."""
    import plotly.graph_objects as graficos

    figura.add_trace(graficos.Scatter3d(
        x=[origen[0], destino[0]], y=[origen[1], destino[1]], z=[origen[2], destino[2]],
        mode="lines", name=nombre, line=dict(color=color, width=5),
    ))
    figura.add_trace(graficos.Scatter3d(
        x=[destino[0]], y=[destino[1]], z=[destino[2]], mode="markers", name=nombre,
        showlegend=False, marker=dict(size=5, color=color),
    ))


def agregar_plano_desde_vectores(
    figura, punto: tuple[Fraction, ...], vectores: tuple[tuple[Fraction, ...], ...],
    rango: list[float], nombre: str,
) -> bool:
    """Construye la superficie de un plano en ℝ³ pasando por un punto y dos direcciones."""
    import plotly.graph_objects as graficos

    primero, segundo = vectores
    normal = (
        primero[1] * segundo[2] - primero[2] * segundo[1],
        primero[2] * segundo[0] - primero[0] * segundo[2],
        primero[0] * segundo[1] - primero[1] * segundo[0],
    )
    escala = max(abs(valor) for valor in normal)
    if escala == 0:
        return False
    coeficientes = [float(valor / escala) for valor in normal]
    termino = float(sum((normal[i] * punto[i] for i in range(3)), Fraction(0)) / escala)
    if not math.isfinite(termino):
        return False
    malla = superficie_plano(coeficientes, termino, rango)
    if malla is None:
        return False
    figura.add_trace(graficos.Surface(
        x=malla[0], y=malla[1], z=malla[2], name=nombre,
        showscale=False, opacity=_OPACIDAD_PLANO, colorscale=[[0, COLOR_SOLUCION], [1, COLOR_SOLUCION]],
    ))
    return True


def preparar_figura_afin(resultado: dict, *, tema: str = "papel"):
    """Construye la figura Plotly de un conjunto afín p + ker(A) en ℝ¹..ℝ³."""
    dimension = int(resultado.get("dimension_ambiente") or 0)
    particular_crudo = resultado.get("particular")
    if not particular_crudo:
        return None
    try:
        p_fracs, p_vis = interpretar_vectores_visuales((particular_crudo,), dimension)
        d_fracs, d_vis = interpretar_vectores_visuales(tuple(resultado.get("direcciones") or ()), dimension)
    except (OverflowError, ValueError):
        return None
    punto = p_vis[0]
    extremos = [punto, *(tuple(a + b for a, b in zip(punto, dir_v)) for dir_v in d_vis)]
    rango = calcular_rango_visual(tuple(extremos))
    geometria = _GeometriaAfin(dimension, punto, p_fracs[0], d_vis, d_fracs, rango)
    return _armar_figura_afin(geometria, tema)


def _armar_figura_afin(geometria: _GeometriaAfin, tema: str):
    import plotly.graph_objects as graficos

    figura = graficos.Figure()
    fuente = COLORES_TEXTO_GRAFICOS.get(tema, COLORES_TEXTO_GRAFICOS["papel"])
    if geometria.dimension == 1:
        _escena_afin_1d(figura, geometria.punto, geometria.rango, fuente)
    elif geometria.dimension == 2:
        if not _escena_afin_2d(figura, geometria.punto, geometria.d_vis, geometria.rango):
            return None
        disposicion_2d(figura, rango_ejes=geometria.rango, color_fuente=fuente, revision="subespacios-2d")
    else:
        if not _escena_afin_3d(figura, geometria):
            return None
        disposicion_3d(figura, rango_ejes=geometria.rango, color_fuente=fuente, revision="subespacios-3d")
    aplicar_colores_figura(figura, tema)
    return figura


def _escena_afin_1d(figura, punto: tuple[float, ...], rango: list[float], fuente: str) -> None:
    import plotly.graph_objects as graficos

    figura.add_trace(graficos.Scatter(
        x=rango, y=[0.0, 0.0], mode="lines", name="Eje ℝ¹", line=dict(color=COLOR_MARCADOR_BORDE, width=2),
    ))
    figura.add_trace(graficos.Scatter(
        x=[0.0], y=[0.0], mode="markers", name="Origen (0) ∉ W",
        marker=dict(color=COLOR_MARCADOR_CLARO, size=9, line=dict(color=COLOR_MARCADOR_BORDE, width=2)),
    ))
    figura.add_trace(graficos.Scatter(
        x=[punto[0]], y=[0.0], mode="markers", name="Punto particular p",
        marker=dict(color=COLOR_SOLUCION, size=11, line=dict(color=COLOR_MARCADOR_BORDE, width=2)),
    ))
    aplicar_layout_1d(figura, rango, fuente)


def _escena_afin_2d(
    figura, punto: tuple[float, ...], d_vis: tuple[tuple[float, ...], ...], rango: list[float]
) -> bool:
    import plotly.graph_objects as graficos

    if len(d_vis) == 1:
        direccion = d_vis[0]
        mayor = max(abs(direccion[0]), abs(direccion[1]))
        if mayor <= 0:
            return False
        factor = (2.0 * rango[1]) / mayor
        figura.add_trace(graficos.Scatter(
            x=[punto[0] - direccion[0] * factor, punto[0] + direccion[0] * factor],
            y=[punto[1] - direccion[1] * factor, punto[1] + direccion[1] * factor],
            mode="lines", name="Recta afín", line=dict(color=COLOR_SOLUCION, width=4), opacity=0.75,
        ))
        agregar_flecha_2d(
            figura, (punto[0], punto[1]), (punto[0] + direccion[0], punto[1] + direccion[1]),
            "d_1", PALETA_GRAFICOS[0],
        )
    figura.add_trace(graficos.Scatter(
        x=[0.0], y=[0.0], mode="markers", name="Origen (0) ∉ W",
        marker=dict(color=COLOR_MARCADOR_CLARO, size=9, line=dict(color=COLOR_MARCADOR_BORDE, width=2)),
    ))
    figura.add_trace(graficos.Scatter(
        x=[punto[0]], y=[punto[1]], mode="markers", name="Punto particular p",
        marker=dict(color=COLOR_SOLUCION, size=11, line=dict(color=COLOR_MARCADOR_BORDE, width=2)),
    ))
    return True


def _escena_afin_3d(figura, geometria: _GeometriaAfin) -> bool:
    import plotly.graph_objects as graficos

    punto, d_vis, rango = geometria.punto, geometria.d_vis, geometria.rango
    if len(d_vis) == 1 and not _recta_afin_3d(figura, punto, d_vis[0], rango):
        return False
    if len(d_vis) == 2 and not agregar_plano_desde_vectores(
        figura, geometria.p_frac, geometria.d_fracs, rango, "Plano afín"
    ):
        return False
    for indice, direccion in enumerate(d_vis):
        destino = (punto[0] + direccion[0], punto[1] + direccion[1], punto[2] + direccion[2])
        agregar_flecha_3d(
            figura, (punto[0], punto[1], punto[2]), destino,
            f"d_{indice + 1}", PALETA_GRAFICOS[indice % len(PALETA_GRAFICOS)],
        )
    figura.add_trace(graficos.Scatter3d(
        x=[0.0], y=[0.0], z=[0.0], mode="markers", name="Origen (0) ∉ W",
        marker=dict(color=COLOR_MARCADOR_CLARO, size=6, line=dict(color=COLOR_MARCADOR_BORDE, width=2)),
    ))
    figura.add_trace(graficos.Scatter3d(
        x=[punto[0]], y=[punto[1]], z=[punto[2]], mode="markers", name="Punto particular p",
        marker=dict(color=COLOR_SOLUCION, size=7, line=dict(color=COLOR_MARCADOR_BORDE, width=2)),
    ))
    return True


def _recta_afin_3d(figura, punto: tuple[float, ...], direccion: tuple[float, ...], rango: list[float]) -> bool:
    import plotly.graph_objects as graficos

    mayor = max(abs(valor) for valor in direccion)
    if mayor <= 0:
        return False
    factor = (2.0 * rango[1]) / mayor
    figura.add_trace(graficos.Scatter3d(
        x=[punto[0] - direccion[0] * factor, punto[0] + direccion[0] * factor],
        y=[punto[1] - direccion[1] * factor, punto[1] + direccion[1] * factor],
        z=[punto[2] - direccion[2] * factor, punto[2] + direccion[2] * factor],
        mode="lines", name="Recta afín", line=dict(color=COLOR_SOLUCION, width=4), opacity=0.8,
    ))
    return True
