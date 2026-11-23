"""Construcción de figuras Plotly exactas para el análisis de subespacios."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Any

from src.backend.constantes import TOLERANCIA_CERO_GRAFICO
from src.backend.geometria.base.muestreo import superficie_plano
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    NOTA_DIMENSION_SUPERIOR,
    NOTA_GRAFICA_NO_DISPONIBLE,
)
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
class ResultadoFiguraSubespacio:
    """Agrupa la figura preparada, su descripción accesible y el motivo si no aplica."""

    disponible: bool
    figura: Any | None
    descripcion: str
    motivo_indisponible: str | None
    es_1d: bool = False


def preparar_figura_subespacio(
    resultado: dict, *, tema: str = "papel"
) -> ResultadoFiguraSubespacio:
    """Genera una figura Plotly en dimensiones 1 a 3 o explica por qué no se grafica."""
    dimension_ambiente = int(resultado.get("dimension_ambiente") or 0)
    descripcion = str(resultado.get("descripcion_geometrica") or "")
    if dimension_ambiente > 3:
        return ResultadoFiguraSubespacio(False, None, descripcion, NOTA_DIMENSION_SUPERIOR)
    if dimension_ambiente < 1:
        return ResultadoFiguraSubespacio(False, None, descripcion, NOTA_GRAFICA_NO_DISPONIBLE)
    try:
        fracciones, coordenadas = _interpretar_base(resultado.get("base") or (), dimension_ambiente)
    except (OverflowError, ValueError):
        return ResultadoFiguraSubespacio(False, None, descripcion, NOTA_GRAFICA_NO_DISPONIBLE)
    figura = _construir_figura_por_dimension(
        dimension_ambiente,
        coordenadas,
        fracciones,
        tuple(resultado.get("etiquetas_generadores_base") or ()),
        tema,
    )
    if figura is None:
        return ResultadoFiguraSubespacio(False, None, descripcion, NOTA_GRAFICA_NO_DISPONIBLE)
    return ResultadoFiguraSubespacio(True, figura, descripcion, None, es_1d=dimension_ambiente == 1)


def _interpretar_base(
    base: tuple, dimension_ambiente: int
) -> tuple[tuple[tuple[Fraction, ...], ...], tuple[tuple[float, ...], ...]]:
    fracciones = []
    coordenadas = []
    for vector in base:
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


def _calcular_rango(coordenadas: tuple[tuple[float, ...], ...]) -> list[float]:
    mayor = max((abs(valor) for vector in coordenadas for valor in vector), default=1.0)
    limite = 5.0 if mayor <= 4.0 else mayor * 1.25
    return [-limite, limite]


def _construir_figura_por_dimension(
    dimension_ambiente: int,
    coordenadas: tuple[tuple[float, ...], ...],
    fracciones: tuple[tuple[Fraction, ...], ...],
    etiquetas: tuple[str, ...],
    tema: str,
):
    import plotly.graph_objects as graficos

    figura = graficos.Figure()
    rango = _calcular_rango(coordenadas)
    fuente = COLORES_TEXTO_GRAFICOS.get(tema, COLORES_TEXTO_GRAFICOS["papel"])
    if dimension_ambiente == 1:
        _armar_escena_1d(figura, coordenadas, etiquetas, rango, fuente)
    elif dimension_ambiente == 2:
        _armar_escena_2d(figura, coordenadas, etiquetas, rango)
        disposicion_2d(figura, rango_ejes=rango, color_fuente=fuente, revision="subespacios-2d")
    else:
        if not _armar_escena_3d(figura, coordenadas, fracciones, etiquetas, rango):
            return None
        disposicion_3d(figura, rango_ejes=rango, color_fuente=fuente, revision="subespacios-3d")
    aplicar_colores_figura(figura, tema)
    return figura


def _agregar_origen(figura, dimension: int, *, destacado: bool) -> None:
    import plotly.graph_objects as graficos

    color_relleno = COLOR_SOLUCION if destacado else COLOR_MARCADOR_CLARO
    marcador = dict(color=color_relleno, size=10 if dimension < 3 else 7, line=dict(color=COLOR_MARCADOR_BORDE, width=2))
    coordenadas = dict(x=[0.0], y=[0.0], mode="markers", name="Origen (0)", marker=marcador, hoverinfo="name")
    if dimension == 3:
        coordenadas["z"] = [0.0]
        figura.add_trace(graficos.Scatter3d(**coordenadas))
        return
    figura.add_trace(graficos.Scatter(**coordenadas))


def _agregar_flecha_2d(figura, destino: tuple[float, float], nombre: str, color: str) -> None:
    import plotly.graph_objects as graficos

    figura.add_trace(graficos.Scatter(
        x=[0.0, destino[0]], y=[0.0, destino[1]], mode="lines+markers", name=nombre,
        line=dict(color=color, width=3),
        marker=dict(color=color, size=[0, 10], symbol=["circle", "arrow"], angleref="previous"),
    ))


def _agregar_flecha_3d(figura, destino: tuple[float, float, float], nombre: str, color: str) -> None:
    import plotly.graph_objects as graficos

    figura.add_trace(graficos.Scatter3d(
        x=[0.0, destino[0]], y=[0.0, destino[1]], z=[0.0, destino[2]],
        mode="lines", name=nombre, line=dict(color=color, width=5),
    ))
    figura.add_trace(graficos.Scatter3d(
        x=[destino[0]], y=[destino[1]], z=[destino[2]], mode="markers", name=nombre,
        showlegend=False, marker=dict(size=5, color=color),
    ))


def _etiqueta_base(etiquetas: tuple[str, ...], indice: int) -> str:
    return etiquetas[indice] if indice < len(etiquetas) else f"b_{indice + 1}"


def _armar_escena_1d(figura, coordenadas: tuple, etiquetas: tuple[str, ...], rango: list[float], fuente: str) -> None:
    import plotly.graph_objects as graficos

    figura.add_trace(graficos.Scatter(
        x=rango, y=[0.0, 0.0], mode="lines", name="Eje ℝ¹",
        line=dict(color=COLOR_MARCADOR_BORDE, width=2),
    ))
    if coordenadas:
        figura.add_trace(graficos.Scatter(
            x=rango, y=[0.0, 0.0], mode="lines", name="Subespacio W = ℝ¹",
            line=dict(color=COLOR_SOLUCION, width=6), opacity=0.45,
        ))
        _agregar_flecha_2d(figura, (coordenadas[0][0], 0.0), _etiqueta_base(etiquetas, 0), PALETA_GRAFICOS[0])
    _agregar_origen(figura, 1, destacado=not coordenadas)
    figura.update_layout(
        paper_bgcolor=COLOR_TRANSPARENTE, plot_bgcolor=COLOR_TRANSPARENTE,
        font=dict(color=fuente, family="Space Grotesk, sans-serif"),
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(gridcolor=COLOR_CUADRICULA, zerolinecolor=COLOR_MARCADOR_BORDE, range=rango),
        yaxis=dict(visible=False, range=[-1.0, 1.0]),
        uirevision="subespacios-1d",
    )


def _armar_escena_2d(figura, coordenadas: tuple, etiquetas: tuple[str, ...], rango: list[float]) -> None:
    import plotly.graph_objects as graficos

    dimension = len(coordenadas)
    if dimension == 1:
        mayor = max(abs(coordenadas[0][0]), abs(coordenadas[0][1]))
        factor = rango[1] / mayor
        figura.add_trace(graficos.Scatter(
            x=[-coordenadas[0][0] * factor, coordenadas[0][0] * factor],
            y=[-coordenadas[0][1] * factor, coordenadas[0][1] * factor],
            mode="lines", name="Recta generada",
            line=dict(color=COLOR_SOLUCION, width=4), opacity=0.75,
        ))
    elif dimension == 2:
        inicio, fin = rango
        figura.add_trace(graficos.Scatter(
            x=[inicio, fin, fin, inicio, inicio], y=[inicio, inicio, fin, fin, inicio],
            mode="lines", name="Espacio ambiente ℝ²",
            line=dict(color=COLOR_SOLUCION, width=2, dash="dot"), opacity=0.65,
        ))
    for indice, vector in enumerate(coordenadas):
        _agregar_flecha_2d(figura, (vector[0], vector[1]), _etiqueta_base(etiquetas, indice), PALETA_GRAFICOS[indice])
    _agregar_origen(figura, 2, destacado=dimension == 0)


def _armar_escena_3d(
    figura, coordenadas: tuple, fracciones: tuple, etiquetas: tuple[str, ...], rango: list[float],
) -> bool:
    import plotly.graph_objects as graficos

    dimension = len(coordenadas)
    if dimension == 1:
        _agregar_recta_3d(figura, coordenadas[0], rango)
    elif dimension == 2 and not _agregar_plano_3d(figura, fracciones, rango):
        return False
    elif dimension == 3:
        _agregar_ejes_3d(figura, rango, graficos)
    for indice, vector in enumerate(coordenadas):
        _agregar_flecha_3d(figura, (vector[0], vector[1], vector[2]), _etiqueta_base(etiquetas, indice), PALETA_GRAFICOS[indice])
    _agregar_origen(figura, 3, destacado=dimension == 0)
    return True


def _agregar_recta_3d(figura, direccion: tuple[float, ...], rango: list[float]) -> None:
    import plotly.graph_objects as graficos

    mayor = max(abs(valor) for valor in direccion)
    factor = rango[1] / mayor
    figura.add_trace(graficos.Scatter3d(
        x=[-direccion[0] * factor, direccion[0] * factor],
        y=[-direccion[1] * factor, direccion[1] * factor],
        z=[-direccion[2] * factor, direccion[2] * factor],
        mode="lines", name="Recta generada", line=dict(color=COLOR_SOLUCION, width=4), opacity=0.8,
    ))


def _agregar_plano_3d(figura, fracciones: tuple, rango: list[float]) -> bool:
    import plotly.graph_objects as graficos

    primero, segundo = fracciones
    normal = (
        primero[1] * segundo[2] - primero[2] * segundo[1],
        primero[2] * segundo[0] - primero[0] * segundo[2],
        primero[0] * segundo[1] - primero[1] * segundo[0],
    )
    escala = max(abs(valor) for valor in normal)
    if escala == 0:
        return False
    coeficientes = [float(valor / escala) for valor in normal]
    malla = superficie_plano(coeficientes, 0.0, rango)
    if malla is None:
        return False
    figura.add_trace(graficos.Surface(
        x=malla[0], y=malla[1], z=malla[2], name="Plano generado",
        showscale=False, opacity=_OPACIDAD_PLANO, colorscale=[[0, COLOR_SOLUCION], [1, COLOR_SOLUCION]],
    ))
    return True


def _agregar_ejes_3d(figura, rango: list[float], graficos) -> None:
    ejes = ((rango, [0.0, 0.0], [0.0, 0.0]), ([0.0, 0.0], rango, [0.0, 0.0]), ([0.0, 0.0], [0.0, 0.0], rango))
    for indice, (eje_x, eje_y, eje_z) in enumerate(ejes):
        figura.add_trace(graficos.Scatter3d(
            x=eje_x, y=eje_y, z=eje_z, mode="lines",
            name="Ejes de ℝ³", showlegend=indice == 0,
            line=dict(color=COLOR_MARCADOR_BORDE, width=2, dash="dot"),
        ))
