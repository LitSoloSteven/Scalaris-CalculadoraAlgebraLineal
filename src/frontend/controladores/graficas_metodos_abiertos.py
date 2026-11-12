"""Gráficas Plotly de apoyo para los métodos abiertos de raíces."""
import math

import plotly.graph_objects as go

from src.frontend.componentes.colores_figuras import aplicar_colores_figura
from src.frontend.componentes.figura_funcion_real import crear_base
from src.frontend.controladores.muestreo_raices import muestrear_funcion
from src.frontend.tema import COLOR_SOLUCION, PALETA_GRAFICOS


def crear_figura_secante(resultado) -> go.Figure:
    """Dibuja f(x), las aproximaciones calculadas y la última recta secante."""
    entrada = resultado.entrada
    if entrada is None:
        raise ValueError("No hay datos válidos para dibujar la función.")

    filas = resultado.iteraciones
    abscisas = [entrada.x_anterior, entrada.x_actual]
    if filas:
        abscisas.extend(fila.x_siguiente for fila in filas)
    if resultado.aproximacion is not None:
        abscisas.append(resultado.aproximacion)

    muestra = _muestrear(
        entrada.expresion,
        abscisas,
        entrada.unidad_angular,
    )
    figura = crear_base(muestra)
    figura.update_layout(
        title="Método de la secante",
        hovermode="closest",
        showlegend=True,
        uirevision="grafica-secante",
        margin=dict(l=45, r=20, t=55, b=65),
        height=420,
        legend=dict(orientation="h", y=-0.25),
    )

    if filas:
        xs = [filas[0].x_anterior, filas[0].x_actual]
        ys = [filas[0].f_anterior, filas[0].f_actual]
        xs.extend(fila.x_siguiente for fila in filas)
        ys.extend(fila.f_siguiente for fila in filas)
        figura.add_trace(go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            name="Aproximaciones",
            marker=dict(color=PALETA_GRAFICOS[0], size=9),
            hovertemplate="x = %{x:.8g}<br>f(x) = %{y:.8g}<extra>Aproximación</extra>",
        ))

        ultima = filas[-1]
        figura.add_trace(go.Scatter(
            x=[ultima.x_anterior, ultima.x_actual, ultima.x_siguiente],
            y=[ultima.f_anterior, ultima.f_actual, 0],
            mode="lines+markers",
            name="Última recta secante",
            line=dict(color=PALETA_GRAFICOS[1], width=2, dash="dash"),
            marker=dict(color=PALETA_GRAFICOS[1], size=7),
            hovertemplate="x = %{x:.8g}<br>y = %{y:.8g}<extra>Secante</extra>",
        ))

    if resultado.aproximacion is not None:
        etiqueta = "Raíz aproximada" if resultado.estado == "EXITO" else "Última aproximación"
        figura.add_trace(go.Scatter(
            x=[resultado.aproximacion],
            y=[0],
            mode="markers",
            name=etiqueta,
            marker=dict(color=COLOR_SOLUCION, size=13, symbol="diamond"),
            hovertemplate="x = %{x:.10g}<br>y = 0<extra>%{fullData.name}</extra>",
        ))

    _finalizar(figura)
    return figura


def crear_figura_newton_raphson(resultado) -> go.Figure:
    """Dibuja f(x), la sucesión de Newton y la última recta tangente."""
    entrada = resultado.entrada
    if entrada is None:
        raise ValueError("No hay datos válidos para dibujar la función.")

    filas = resultado.iteraciones
    abscisas = [entrada.aproximacion_inicial]
    abscisas.extend(fila.x_siguiente for fila in filas)
    if resultado.aproximacion is not None:
        abscisas.append(resultado.aproximacion)

    muestra = _muestrear(entrada.expresion, abscisas, "radianes")
    figura = crear_base(muestra)
    figura.update_layout(
        title="Método de Newton-Raphson",
        hovermode="closest",
        showlegend=True,
        uirevision="grafica-newton-raphson",
        margin=dict(l=45, r=20, t=55, b=65),
        height=420,
        legend=dict(orientation="h", y=-0.25),
    )

    if filas:
        xs = [filas[0].x_actual]
        ys = [filas[0].valor_funcion]
        xs.extend(fila.x_siguiente for fila in filas)
        ys.extend(fila.valor_siguiente for fila in filas)
        figura.add_trace(go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            name="Aproximaciones",
            marker=dict(color=PALETA_GRAFICOS[0], size=9),
            hovertemplate="x = %{x:.8g}<br>f(x) = %{y:.8g}<extra>Aproximación</extra>",
        ))

        ultima = filas[-1]
        figura.add_trace(go.Scatter(
            x=[ultima.x_actual, ultima.x_siguiente],
            y=[ultima.valor_funcion, 0],
            mode="lines+markers",
            name="Última recta tangente",
            line=dict(color=PALETA_GRAFICOS[1], width=2, dash="dash"),
            marker=dict(color=PALETA_GRAFICOS[1], size=7),
            hovertemplate="x = %{x:.8g}<br>y = %{y:.8g}<extra>Tangente</extra>",
        ))

    if resultado.aproximacion is not None:
        etiqueta = "Raíz aproximada" if resultado.estado == "EXITO" else "Última aproximación"
        figura.add_trace(go.Scatter(
            x=[resultado.aproximacion],
            y=[0],
            mode="markers",
            name=etiqueta,
            marker=dict(color=COLOR_SOLUCION, size=13, symbol="diamond"),
            hovertemplate="x = %{x:.10g}<br>y = 0<extra>%{fullData.name}</extra>",
        ))

    _finalizar(figura)
    return figura


def _muestrear(expresion: str, abscisas: list[float], unidad_angular: str) -> dict:
    """Muestrea f(x) alrededor de las aproximaciones sin unir huecos del dominio."""
    valores = [float(valor) for valor in abscisas if math.isfinite(float(valor))]
    if not valores:
        raise ValueError("No hay aproximaciones finitas para determinar el rango de la gráfica.")

    inferior, superior = min(valores), max(valores)
    amplitud = superior - inferior
    escala = max(abs(inferior), abs(superior), 1.0)
    if not math.isfinite(amplitud):
        raise ValueError("El rango de las aproximaciones excede la capacidad de la gráfica.")
    margen = max(amplitud * 0.25, escala * 0.08)
    x_min, x_max = inferior - margen, superior + margen
    if not math.isfinite(x_min) or not math.isfinite(x_max) or x_min >= x_max:
        raise ValueError("No se puede representar el rango de las aproximaciones.")
    return muestrear_funcion({
        "expresion": expresion,
        "extremo_izquierdo": x_min,
        "extremo_derecho": x_max,
        "unidad_angular": unidad_angular,
    })


def _finalizar(figura: go.Figure) -> None:
    """Aplica la paleta temática y garantiza ejes y=0 y x=0 visibles."""
    figura.update_xaxes(title_text="x", zeroline=True)
    figura.update_yaxes(title_text="f(x)", zeroline=True)
    aplicar_colores_figura(figura, "papel")
