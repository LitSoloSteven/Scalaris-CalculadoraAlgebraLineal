"""Figura de función, secante y evaluaciones registradas sin cálculos de nuevas raíces."""
import plotly.graph_objects as go

from src.frontend.tema import COLOR_SOLUCION, COLOR_TRANSPARENTE, PALETA_GRAFICOS
from src.frontend.vistas.geometria._colores_figuras import aplicar_colores_figura


def crear_figura(respuesta: dict, muestra: dict | None, fila: dict | None = None,
                 inicial: bool = False) -> go.Figure:
    """Dibuja datos reales; distingue cruce en el eje x de evaluación f(c), sin unir huecos."""
    figura = go.Figure()
    if muestra is not None:
        figura.add_trace(_traza(muestra["x"], muestra["y"], "f(x), muestreo orientativo", PALETA_GRAFICOS[2], "lines"))
    if fila is not None:
        _agregar_iteracion(figura, fila)
    elif not inicial and respuesta["aproximacion"] is not None:
        figura.add_trace(_traza([respuesta["aproximacion"]], [0], "Cero evaluado en extremo", COLOR_SOLUCION))
    figura.update_layout(
        paper_bgcolor=COLOR_TRANSPARENTE, plot_bgcolor=COLOR_TRANSPARENTE,
        margin=dict(l=40, r=15, t=25, b=65), height=360,
        legend=dict(orientation="h", y=-0.3), uirevision="regla_falsa", hovermode="closest",
        xaxis_title="x", yaxis_title="f(x)", font_family="Space Grotesk, sans-serif",
    )
    aplicar_colores_figura(figura, "papel")
    return figura


def _traza(abscisas: list, ordenadas: list, nombre: str, color: str, modo: str = "markers") -> go.Scatter:
    return go.Scatter(x=abscisas, y=ordenadas, name=nombre, mode=modo, connectgaps=False,
                      line=dict(color=color, width=2), marker=dict(color=color, size=10))


def _agregar_iteracion(figura: go.Figure, fila: dict) -> None:
    figura.add_trace(_traza(
        [fila["extremo_izquierdo"], fila["extremo_derecho"]],
        [fila["valor_izquierdo"], fila["valor_derecho"]], "Secante por (a, f(a)) y (b, f(b))",
        PALETA_GRAFICOS[1], "lines+markers",
    ))
    figura.add_trace(_traza([fila["aproximacion"]], [0], "Cruce de secante (c, 0)", PALETA_GRAFICOS[0]))
    figura.add_trace(_traza([fila["aproximacion"]], [fila["valor_aproximacion"]],
                              "Evaluación (c, f(c))", COLOR_SOLUCION))
    figura.add_trace(_traza(list(fila["intervalo_siguiente"]), [0, 0],
                              "Intervalo siguiente del motor", PALETA_GRAFICOS[3], "lines+markers"))
