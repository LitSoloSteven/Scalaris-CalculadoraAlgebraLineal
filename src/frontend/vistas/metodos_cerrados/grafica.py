"""Gráfica única para la curva orientativa, los extremos y el procedimiento."""
import logging
import math

from nicegui import ui
from plotly import graph_objects as go

from src.frontend.componentes.colores_figuras import aplicar_colores_figura
from src.frontend.componentes.figura_funcion_real import crear_base
from src.frontend.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.controladores.actualizacion_cancelable import cancelar_actualizacion, programar_actualizacion
from src.frontend.controladores.biseccion.muestreo import separar_intervalo_sospechoso
from src.frontend.controladores.captura_real import real_capturado
from src.frontend.controladores.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION
from src.frontend.controladores.rango_exploracion_raices import RANGO_GRAFICA_DEFECTO, rango_grafica
from src.frontend.controladores.vista_previa_raices import preparar_vista_previa
from src.frontend.tema import PALETA_GRAFICOS
from src.frontend.vistas.biseccion.figura import crear_figura as figura_biseccion
from src.frontend.vistas.regla_falsa.figura import crear_figura as figura_regla_falsa

_MUESTRA_VACIA = {"x": [], "y": []}
_MENSAJE_INICIAL = "Escribe una función para ver la gráfica. El muestreo no demuestra continuidad."
_registro = logging.getLogger(__name__)


class GraficaMetodosCerrados:
    """Conserva identidad, zoom y curva mientras publica el resultado vigente."""

    def __init__(self, captura):
        self.captura = captura
        self.coordinador = CoordinadorTrabajosRaices(preparar_vista_previa)
        self.tarea = self.previa = self.resultado = self.fila = None
        self._solicitud = None
        self._revision = 0
        self._reencuadres = 0
        self._inicial = False
        self._cerrada = False

    def construir(self) -> None:
        """Monta el único nodo Plotly y su estado accesible."""
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Gráfica").classes("text-xl font-semibold texto-principal")
            self.ajuste = ui.button("Ajustar al intervalo", color=None, on_click=self.ajustar_intervalo).classes(
                "boton-discreto").props("ripple=false")
        self.estado = ui.label(_MENSAJE_INICIAL).classes("text-sm texto-secundario").props("role=status")
        self.nodo = ui.plotly(crear_base(_MUESTRA_VACIA)).classes("w-full min-w-0").props(
            'role=img aria-label="Gráfica de la función, el intervalo y la iteración activa"')
        self.nodo.on("plotly_afterplot", js_handler="() => window.scalaris?.sincronizarTemaPlotly?.()")
        self.actualizar()

    def actualizar(self) -> None:
        """Revoca la curva solo si cambia la función, la unidad o el rango de muestreo."""
        if not self._disponible():
            return
        solicitud = self.captura.captura_grafica()
        if solicitud != self._solicitud:
            self._solicitud = solicitud
            self._revision += 1
            self.coordinador.invalidar()
            cancelar_actualizacion(self.tarea)
            self.tarea = self.previa = None
            if str(solicitud["expresion"] or "").strip():
                self.estado.set_text("Preparando la gráfica…")
                self.tarea = programar_actualizacion(None, self._muestrear, self._disponible,
                                                      ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)
            else:
                self.estado.set_text(_MENSAJE_INICIAL)
        self._dibujar()

    def mostrar(self, resultado: dict | None, fila: dict | None = None, *, inicial: bool = False) -> None:
        """Representa un resultado o devuelve los marcadores a la captura."""
        self.resultado, self.fila, self._inicial = resultado, fila, inicial
        self._dibujar()

    def ajustar_intervalo(self) -> None:
        """Encuadra los extremos visibles sin alterarlos ni ejecutar otra resolución."""
        rango = _intervalo(self.captura.capturar())
        if rango is not None:
            self._reencuadres += 1
            self.captura.definir_rango(rango)

    def cerrar(self) -> None:
        """Revoca un muestreo en curso e impide publicar en un cliente desmontado."""
        self._cerrada = True
        self.coordinador.cerrar()
        cancelar_actualizacion(self.tarea)
        self._solicitud = None

    def reabrir(self) -> None:
        """Recupera la curva para la captura vigente después de reconectar."""
        self._cerrada = False
        self.coordinador.reabrir()
        self.actualizar()

    def _disponible(self) -> bool:
        return not self._cerrada and not self.nodo.is_deleted

    async def _muestrear(self) -> None:
        revision = self._revision
        try:
            previa = await self.coordinador.ejecutar(self._solicitud)
        except Exception:
            _registro.exception("No se pudo preparar la gráfica de métodos cerrados")
            previa = {"mensaje": "No se pudo dibujar la función. Revisa la expresión y el rango."}
        if previa is not None and self._disponible() and self._revision == revision:
            self.previa = previa
            self.estado.set_text(previa["mensaje"])
            self._dibujar()

    def _dibujar(self) -> None:
        if not self._disponible():
            return
        captura = self.captura.capturar()
        self.ajuste.set_enabled(_intervalo(captura) is not None)
        rango, muestra = self._encuadre()
        figura = _figura(self.resultado, self.fila, muestra, self._inicial)
        if self.resultado is None or not self.resultado["resultado"].get("entrada"):
            _marcar_extremos(figura, captura)
        figura.update_layout(uirevision=f"{self._revision}:{self._reencuadres}", margin_b=70)
        figura.update_xaxes(range=rango)
        aplicar_colores_figura(figura, "papel")
        self.nodo.update_figure(figura)

    def _encuadre(self) -> tuple:
        try:
            rango = rango_grafica(self.captura.captura_grafica())
        except ValueError:
            rango = RANGO_GRAFICA_DEFECTO
        muestra = (self.previa or {}).get("muestra")
        resultado = self.resultado or {}
        entrada = resultado.get("resultado", {}).get("entrada")
        intervalo = _intervalo(entrada) if entrada else None
        if intervalo and rango == RANGO_GRAFICA_DEFECTO and (intervalo[0] < rango[0] or intervalo[1] > rango[1]):
            return intervalo, resultado.get("muestra") or muestra
        return rango, muestra


def _figura(datos, fila, muestra, inicial) -> go.Figure:
    respuesta = (datos or {}).get("resultado", {})
    muestra = muestra or (datos or {}).get("muestra") or _MUESTRA_VACIA
    if not respuesta.get("entrada"):
        return crear_base(muestra)
    if datos["metodo"] == BISECCION:
        return _figura_biseccion(respuesta, muestra, fila, inicial)
    return _figura_regla_falsa(respuesta, muestra, fila, inicial)


def _figura_biseccion(respuesta, muestra, fila, inicial) -> go.Figure:
    evidencia = (respuesta.get("diagnostico") or {}).get("evidencia_discontinuidad")
    if evidencia:
        muestra = separar_intervalo_sospechoso(muestra, evidencia["intervalo"])
    return figura_biseccion(respuesta, muestra, fila, inicial)


def _figura_regla_falsa(respuesta, muestra, fila, inicial) -> go.Figure:
    filas = respuesta.get("iteraciones") or ()
    activa = fila or (filas[-1] if filas and not inicial else None)
    figura = figura_regla_falsa(respuesta, muestra, activa, inicial)
    if activa is None:
        _marcar_extremos(figura, respuesta["entrada"])
    return figura


def _marcar_extremos(figura: go.Figure, captura: dict) -> None:
    puntos = _extremos(captura)
    if puntos:
        valores, nombres = zip(*puntos)
        figura.add_trace(go.Scatter(x=valores, y=[0] * len(valores), text=nombres, textposition="top center",
                                   name="Extremos [a, b]", mode="markers+text",
                                   marker=dict(color=PALETA_GRAFICOS[1], size=9)))


def _intervalo(captura: dict) -> tuple[float, float] | None:
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
