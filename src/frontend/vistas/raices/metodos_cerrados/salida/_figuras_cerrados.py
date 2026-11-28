"""Construcción de figuras, marcadores y encuadre para métodos cerrados."""
import math
from nicegui import ui
from plotly import graph_objects as go

from src.frontend.componentes.raices.graficos.colores_figuras import aplicar_colores_figura
from src.frontend.componentes.raices.graficos.figura_funcion_real import crear_base
from src.frontend.controladores.raices.biseccion.adaptadores.muestreo import separar_intervalo_sospechoso
from src.frontend.controladores.raices.compartido.formato.captura_real import real_capturado
from src.frontend.controladores.raices.compartido.formato.rango_exploracion_raices import (
    RANGO_GRAFICA_DEFECTO,
    rango_grafica,
)
from src.frontend.controladores.raices.metodos_cerrados.adaptadores import BISECCION
from src.frontend.presentacion.tema import PALETA_GRAFICOS
from src.frontend.vistas.raices.biseccion.grafica.figura import crear_figura as figura_biseccion
from src.frontend.vistas.raices.regla_falsa.grafica.figura import crear_figura as figura_regla_falsa

MUESTRA_VACIA = {"x": [], "y": []}


def intervalo_fuera_del_rango_inicial(intervalo: tuple | None, rango: tuple) -> bool:
    """Indica si el intervalo del cálculo queda fuera del encuadre inicial por defecto."""
    return (intervalo is not None and rango == RANGO_GRAFICA_DEFECTO
            and (intervalo[0] < rango[0] or intervalo[1] > rango[1]))


def rango_base_cerrados(captura_rango: dict, resultado: dict | None, rango_detalle: tuple | None) -> tuple[float, float]:
    """Calcula el rango base del encuadre sin acoplarlo a movimientos previos de cámara."""
    if rango_detalle is not None:
        return rango_detalle
    entrada = (resultado or {}).get("resultado", {}).get("entrada")
    intervalo = intervalo_desde_captura(entrada) if entrada else None
    try:
        rango = rango_grafica(captura_rango)
    except ValueError:
        rango = RANGO_GRAFICA_DEFECTO
    return intervalo if intervalo_fuera_del_rango_inicial(intervalo, rango) else rango


def _muestra_de(fuente: dict | None) -> dict | None:
    return fuente.get("muestra") if isinstance(fuente, dict) else None


def _entrada_resultado(resultado: dict | None) -> dict | None:
    if not isinstance(resultado, dict):
        return None
    interno = resultado.get("resultado")
    return interno.get("entrada") if isinstance(interno, dict) else None


def _usa_muestra_resultado(resultado: dict | None, rango: tuple[float, float]) -> bool:
    entrada = _entrada_resultado(resultado)
    intervalo = intervalo_desde_captura(entrada) if entrada else None
    return intervalo_fuera_del_rango_inicial(intervalo, RANGO_GRAFICA_DEFECTO) and rango == intervalo


def calcular_encuadre(
    captura_rango: dict,
    resultado: dict | None,
    muestras: tuple[dict | None, dict | None],
    rangos: tuple[tuple | None, tuple | None],
) -> tuple[tuple[float, float], dict | None]:
    """Determina rango X y muestra de curva vigentes respetando encuadre manual o resultado."""
    previa, previa_camara = muestras
    rango_camara, rango_detalle = rangos
    muestra_previa, muestra_resultado = _muestra_de(previa), _muestra_de(resultado)
    if rango_camara is not None:
        return rango_camara, _muestra_de(previa_camara) or muestra_resultado or muestra_previa
    if rango_detalle is not None:
        return rango_detalle, muestra_resultado or muestra_previa
    rango = rango_base_cerrados(captura_rango, resultado, None)
    if _usa_muestra_resultado(resultado, rango):
        return rango, muestra_resultado or muestra_previa
    return rango, muestra_previa


def montar_panel_grafica(al_ajustar, al_restablecer, al_relayout, mensaje_inicial: str) -> tuple:
    """Monta cabecera, estado accesible y nodo Plotly de la gráfica compartida."""
    with ui.row().classes("w-full items-center justify-between gap-2 flex-wrap"):
        ui.label("Gráfica").classes("text-xl font-semibold texto-principal")
        with ui.row().classes("items-center gap-2 flex-wrap"):
            ajuste = ui.button("Ajustar al intervalo", color=None, on_click=al_ajustar).classes(
                "boton-discreto").props("ripple=false")
            restablecer = ui.button("Restablecer vista", color=None, on_click=al_restablecer).classes(
                "boton-discreto").props("ripple=false")
    estado = ui.label(mensaje_inicial).classes("text-sm texto-secundario").props("role=status aria-live=polite")
    with ui.element("div").classes("metodos-raices-grafica-superficie"):
        nodo = ui.plotly(crear_base(MUESTRA_VACIA)).classes("w-full min-w-0").props(
            'role=img aria-label="Gráfica de la función, el intervalo y la iteración activa"')
    nodo.on("plotly_afterplot", js_handler="() => window.scalaris?.sincronizarTemaPlotly?.()")
    nodo.on("plotly_relayout", al_relayout, js_handler=(
        f"datos => emit({{...datos, identidad: document.getElementById('{nodo.html_id}')?.layout?.meta}})"
    ))
    return ajuste, restablecer, estado, nodo


def preparar_figura_cerrados(
    datos: dict | None,
    fila: dict | None,
    muestra: dict | None,
    opciones: dict,
) -> tuple[go.Figure, dict]:
    """Construye la figura completa, agrega marcadores y prepara la respuesta de selección."""
    figura = construir_figura_cerrados(datos, fila, muestra, opciones["inicial"])
    if datos is None or not datos["resultado"].get("entrada"):
        marcar_extremos(figura, opciones["captura"])
    curva = figura.data[0]
    curva.update(hoverinfo="none", customdata=[opciones["identidad"]] * len(curva.x))
    figura.update_layout(hovermode="closest", uirevision=opciones["uirevision"], margin_b=70, meta=opciones["identidad"])
    if opciones["puntos_borrador"]:
        marcar_borrador(figura, opciones["puntos_borrador"])
    figura.update_xaxes(range=list(opciones["rango"]), autorange=False)
    aplicar_colores_figura(figura, "papel")
    return figura, {"estado": "EXITO", "muestra": {"x": curva.x, "y": curva.y}}


def marcar_borrador(figura: go.Figure, puntos: list[float]) -> None:
    """Agrega los extremos temporales del borrador seleccionado sobre la curva."""
    figura.add_trace(go.Scatter(
        x=puntos, y=[0] * len(puntos), text=("a", "b"),
        name="Intervalo del borrador", mode="markers+text", textposition="top center", hoverinfo="skip",
        marker=dict(color=PALETA_GRAFICOS[1], size=12),
    ))


def construir_figura_cerrados(datos, fila, muestra, inicial: bool) -> go.Figure:
    """Construye la figura para Bisección, Regla falsa o la curva previa."""
    respuesta = (datos or {}).get("resultado", {})
    muestra = muestra or (datos or {}).get("muestra") or MUESTRA_VACIA
    if not respuesta.get("entrada"):
        return crear_base(muestra)
    if datos["metodo"] == BISECCION:
        return _figura_biseccion(respuesta, muestra, fila, inicial)
    return _figura_regla_falsa(respuesta, muestra, fila, inicial)


def _figura_biseccion(respuesta, muestra, fila, inicial: bool) -> go.Figure:
    evidencia = (respuesta.get("diagnostico") or {}).get("evidencia_discontinuidad")
    if evidencia:
        muestra = separar_intervalo_sospechoso(muestra, evidencia["intervalo"])
    return figura_biseccion(respuesta, muestra, fila, inicial)


def _figura_regla_falsa(respuesta, muestra, fila, inicial: bool) -> go.Figure:
    filas = respuesta.get("iteraciones") or ()
    activa = fila or (filas[-1] if filas and not inicial else None)
    figura = figura_regla_falsa(respuesta, muestra, activa, inicial)
    if activa is None:
        marcar_extremos(figura, respuesta["entrada"])
    return figura


def marcar_extremos(figura: go.Figure, captura: dict) -> None:
    """Dibuja los extremos [a, b] capturados cuando todavía no hay iteración activa."""
    puntos = _extremos(captura)
    if puntos:
        valores, nombres = zip(*puntos)
        figura.add_trace(go.Scatter(
            x=valores, y=[0] * len(valores), text=nombres, textposition="top center",
            name="Extremos [a, b]", mode="markers+text",
            marker=dict(color=PALETA_GRAFICOS[1], size=9),
        ))


def intervalo_desde_captura(captura: dict) -> tuple[float, float] | None:
    """Devuelve el intervalo ordenado (a, b) si ambos extremos son finitos y a < b."""
    valores = sorted(valor for valor, _ in _extremos(captura))
    return (valores[0], valores[1]) if len(valores) == 2 and valores[0] < valores[1] else None


def _extremos(captura: dict) -> list[tuple[float, str]]:
    puntos = []
    for clave, nombre in (("extremo_izquierdo", "a"), ("extremo_derecho", "b")):
        try:
            valor = real_capturado(captura[clave], nombre)
        except ValueError:
            continue
        if math.isfinite(valor):
            puntos.append((valor, nombre))
    return puntos
