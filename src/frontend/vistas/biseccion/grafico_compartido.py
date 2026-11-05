"""Gráfico persistente con trazas independientes para la curva y el intervalo."""
import json

from nicegui import ui
from plotly import graph_objects as go

from src.frontend.controladores.biseccion.muestreo import separar_intervalo_sospechoso
from src.frontend.controladores.biseccion.vista_previa import RANGO_GRAFICA_DEFECTO
from src.frontend.tema import COLOR_SOLUCION, PALETA_GRAFICOS
from src.frontend.vistas.geometria._colores_figuras import aplicar_colores_figura
from .figura import crear_figura_previa, _ordenada_marcador
from .modos_captura import MODO_BUSQUEDA


def mostrar_paso_principal(vista, respuesta: dict, paso=None) -> None:
    """Publica la marca individual cuando el detalle de lote no ocupa el gráfico."""
    if _muestra_lote(vista):
        return
    vista.vista_previa.compartido.resultado(respuesta, paso.cuerpo if paso else None,
                                            inicial=bool(paso and paso.tipo == "planteamiento"))


def restaurar_grafico_principal(vista) -> None:
    """Recupera la marca del paso individual vigente o del intervalo capturado."""
    if _muestra_lote(vista):
        return
    if vista.ultimo_resultado is None:
        vista.vista_previa.actualizar_marcas()
        return
    reproductor = vista.reproductor_pasos
    paso = reproductor.pasos[reproductor.indice_actual] if reproductor else None
    mostrar_paso_principal(vista, vista.ultimo_resultado, paso)


def _muestra_lote(vista) -> bool:
    return vista.modos.value == MODO_BUSQUEDA and vista.resolucion_multiple.detalle_activo


class GraficoCompartido:
    """Conserva el nodo Plotly y publica marcadores sin reenviar la curva."""

    def __init__(self):
        self._marcas = ([], [], [], [], "Aproximación en x")
        self._borrador = []
        self._curva = None
        self._sospecha = None
        with ui.element("div").classes("biseccion-marco-grafico w-full") as self.marco:
            self.nodo = ui.plotly(self._figura(None)).classes("w-full biseccion-grafica")
        self.nodo.on("plotly_afterplot", js_handler=(
            f"() => window.scalaris.graficoBiseccion.actualizar(document.getElementById('{self.nodo.html_id}'))"
        ))

    def publicar_curva(self, respuesta: dict | None) -> None:
        """Reemplaza el muestreo visible y conserva las marcas vigentes."""
        if not self.nodo.is_deleted:
            self._curva = respuesta
            self.nodo.update_figure(self._figura(self._curva_visible()))

    def retirar_curva(self) -> None:
        """Retira las muestras obsoletas conservando el rango y los marcadores."""
        if self._curva is not None and not self.nodo.is_deleted:
            self._curva = None
            self.nodo.run_plot_method("restyle", {"x": [[]], "y": [[]]}, [0])

    def sospecha(self, intervalo: tuple | None) -> None:
        """Aplica o retira el corte diagnosticado sin realizar nuevas evaluaciones."""
        if self._sospecha == intervalo or self.nodo.is_deleted:
            return
        self._sospecha = intervalo
        curva = self._curva_visible()
        if curva is not None:
            self.nodo.run_plot_method("restyle", {"y": [curva["muestra"]["y"]]}, [0])

    def _curva_visible(self) -> dict | None:
        if self._curva is None or self._sospecha is None:
            return self._curva
        muestra = separar_intervalo_sospechoso(self._curva["muestra"], self._sospecha)
        return {**self._curva, "muestra": muestra}

    def borrador(self, puntos: list[float]) -> None:
        """Dibuja los extremos elegidos sin sobrescribir el intervalo del cálculo."""
        self._borrador = puntos
        if not self.nodo.is_deleted:
            self.nodo.run_plot_method("restyle", {
                "x": [puntos], "y": [[0] * len(puntos)], "text": [["a", "b"][:len(puntos)]],
            }, [3])

    def intervalo(self, intervalo: tuple | None, punto: tuple | None = None) -> None:
        """Actualiza extremos y punto seleccionado con una única operación de Plotly."""
        extremos = list(intervalo) if intervalo is not None else []
        abscisa, ordenada, nombre = punto if punto is not None else (None, None, "Aproximación en x")
        abscisas = [] if abscisa is None else [abscisa]
        ordenadas = [] if ordenada is None else [ordenada]
        self._marcas = extremos, [0] * len(extremos), abscisas, ordenadas, nombre
        if not self.nodo.is_deleted:
            marcas = {
                "x": [extremos, abscisas], "y": [self._marcas[1], ordenadas],
                "name": ["Intervalo [a, b]", nombre],
            }
            self.marco.props["data-biseccion-marcas"] = json.dumps([marcas, _posicion_banda(extremos)])

    def resultado(self, respuesta: dict, fila: dict | None = None, *, inicial: bool = False) -> None:
        """Representa el intervalo publicado de un resultado o de su paso activo."""
        evidencia = (respuesta.get("diagnostico") or {}).get("evidencia_discontinuidad")
        self.sospecha(evidencia["intervalo"] if evidencia else None)
        entrada = respuesta.get("entrada")
        if entrada is None:
            return
        intervalo = entrada["extremo_izquierdo"], entrada["extremo_derecho"]
        if fila:
            intervalo = fila["extremo_izquierdo"], fila["extremo_derecho"]
        elif not inicial:
            intervalo = respuesta.get("intervalo_final") or intervalo
        abscisa = fila["c"] if fila else None if inicial else respuesta.get("aproximacion")
        punto = (abscisa, *_ordenada_marcador(respuesta, fila)) if abscisa is not None else None
        self.intervalo(intervalo, punto)

    def _figura(self, respuesta: dict | None) -> go.Figure:
        if respuesta is None:
            minimo, maximo = RANGO_GRAFICA_DEFECTO
            respuesta = {"muestra": {"x": [], "y": []}, "entrada": {
                "expresion": "", "extremo_izquierdo": minimo, "extremo_derecho": maximo}}
        figura = crear_figura_previa(respuesta)
        extremos, ceros, abscisas, ordenadas, nombre = self._marcas
        figura.add_trace(go.Scatter(x=extremos, y=ceros, mode="lines+markers", name="Intervalo [a, b]",
                                   line=dict(color=PALETA_GRAFICOS[1], width=5, dash="dot")))
        figura.add_trace(go.Scatter(x=abscisas, y=ordenadas, mode="markers", name=nombre,
                                   marker=dict(color=COLOR_SOLUCION, size=11, symbol="diamond")))
        figura.add_trace(go.Scatter(x=self._borrador, y=[0] * len(self._borrador), mode="markers+text",
                                   text=["a", "b"][:len(self._borrador)], textposition="top center",
                                   name="Extremos del borrador", marker=dict(color=PALETA_GRAFICOS[1], size=12)))
        posicion = _posicion_banda(extremos)
        figura.add_shape(type="rect", xref="x", yref="paper", y0=0, y1=1, layer="below",
                         x0=posicion["shapes[0].x0"], x1=posicion["shapes[0].x1"],
                         visible=posicion["shapes[0].visible"], line_width=0,
                         fillcolor=PALETA_GRAFICOS[1], opacity=0.14)
        aplicar_colores_figura(figura, "papel")
        return figura


def _posicion_banda(extremos: list) -> dict:
    inferior, superior = extremos or (0, 0)
    return {"shapes[0].x0": inferior, "shapes[0].x1": superior, "shapes[0].visible": bool(extremos)}
