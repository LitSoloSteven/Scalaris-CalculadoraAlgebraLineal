"""Gráfica única para la curva orientativa, los extremos y el procedimiento."""
import logging
import math
from types import SimpleNamespace

from nicegui import ui
from plotly import graph_objects as go

from src.frontend.componentes.raices.graficos.colores_figuras import aplicar_colores_figura
from src.frontend.componentes.raices.graficos.figura_funcion_real import crear_base
from src.frontend.nucleo.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.controladores.compartido.sesion.actualizacion_cancelable import cancelar_actualizacion, programar_actualizacion
from src.frontend.controladores.biseccion.muestreo import separar_intervalo_sospechoso
from src.frontend.controladores.raices.compartido.formato.captura_real import real_capturado
from src.frontend.controladores.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION
from src.frontend.controladores.raices.compartido.formato.rango_exploracion_raices import RANGO_GRAFICA_DEFECTO, rango_evento_distinto, rango_grafica
from src.frontend.controladores.raices.compartido.exploracion.vista_previa_raices import preparar_vista_previa
from src.frontend.presentacion.tema import PALETA_GRAFICOS
from src.frontend.vistas.biseccion.figura import crear_figura as figura_biseccion
from src.frontend.vistas.regla_falsa.figura import crear_figura as figura_regla_falsa
from src.frontend.vistas.regla_falsa.seleccion_grafico import SeleccionGrafico

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
        self._revision_seleccion = 0
        self._puntos_borrador = []
        self._rango_detalle = None
        self._mostrando_detalle = False
        self.respuesta = None
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
        self.nodo.on("plotly_relayout", self._encuadrar_busqueda, js_handler=(
            f"datos => emit({{...datos, identidad: document.getElementById('{self.nodo.html_id}')?.layout?.meta}})"
        ))
        destino = SimpleNamespace(vista_previa=self, inferior=self.captura.inferior,
                                  cargar_captura=self.captura.vista.aplicar_intervalo)
        self.seleccion = SeleccionGrafico(destino)
        self.seleccion.construir()
        self.actualizar()

    @property
    def grafica(self):
        """Expone el nodo estable a la selección compartida."""
        return self.nodo

    @property
    def identidad(self) -> str:
        """Identifica la curva y la vigencia de sus eventos."""
        return f"{self._revision}:{self._revision_seleccion}"

    def actualizar(self) -> None:
        """Revoca la curva solo si cambia la función, la unidad o el rango de muestreo."""
        if not self.disponible():
            return
        solicitud = self._captura_rango()
        if solicitud != self._solicitud:
            self._solicitud = solicitud
            self._revision += 1
            self.coordinador.invalidar()
            cancelar_actualizacion(self.tarea)
            self.tarea = self.previa = None
            if str(solicitud["expresion"] or "").strip():
                self.estado.set_text("Preparando la gráfica…")
                self.tarea = programar_actualizacion(None, self._muestrear, self.disponible,
                                                      ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)
            else:
                self.estado.set_text(_MENSAJE_INICIAL)
        self._dibujar()

    def mostrar(self, resultado: dict | None, fila: dict | None = None, *, inicial: bool = False) -> None:
        """Representa un resultado o devuelve los marcadores a la captura."""
        detalle = resultado is not None and self.captura.vista.candidato_activo is not None
        if self._mostrando_detalle != detalle:
            self.cancelar_seleccion()
        if self._mostrando_detalle and not detalle:
            self._rango_detalle = None
            self._reencuadres += 1
        self._mostrando_detalle = detalle
        self.resultado, self.fila, self._inicial = resultado, fila, inicial
        self._dibujar()

    def ajustar_intervalo(self) -> None:
        """Encuadra los extremos visibles sin alterarlos ni ejecutar otra resolución."""
        rango = self._intervalo_visible()
        if rango is not None:
            self._reencuadres += 1
            if self._mostrando_detalle:
                self._rango_detalle = rango
                self._dibujar()
            else:
                self.captura.definir_rango(rango)

    def _intervalo_visible(self) -> tuple[float, float] | None:
        if self._mostrando_detalle:
            entrada = self.resultado["resultado"].get("entrada")
            return _intervalo(entrada) if entrada else None
        return _intervalo(self.captura.capturar())

    def cancelar_seleccion(self) -> None:
        """Invalida clics y descarta los extremos del borrador antes de cambiar de contexto."""
        self._revision_seleccion += 1
        self.seleccion.cancelar()

    def editar_rango_busqueda(self) -> None:
        """Actualiza el muestreo cuando cambia el rango del modo exploratorio."""
        if self.disponible() and self.captura.vista.en_busqueda:
            self.cancelar_seleccion()
            try:
                rango = rango_grafica(self._captura_rango())
            except ValueError:
                pass
            else:
                self.captura.definir_rango(rango, sincronizar=False)
            self.actualizar()

    def dibujar_borrador(self, puntos: list[float]) -> None:
        """Actualiza las marcas editables dentro del único nodo Plotly."""
        self._puntos_borrador = puntos
        self._dibujar()

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

    def disponible(self) -> bool:
        """Indica si la gráfica sigue montada y admite eventos."""
        return not self._cerrada and not self.nodo.is_deleted

    async def _muestrear(self) -> None:
        revision = self._revision
        try:
            previa = await self.coordinador.ejecutar(self._solicitud)
        except Exception:
            _registro.exception("No se pudo preparar la gráfica de métodos cerrados")
            previa = {"mensaje": "No se pudo dibujar la función. Revisa la expresión y el rango."}
        if previa is not None and self.disponible() and self._revision == revision:
            self.previa = previa
            self.estado.set_text(previa["mensaje"])
            self._dibujar()

    def _dibujar(self) -> None:
        if not self.disponible():
            return
        captura = self.captura.capturar()
        self.ajuste.set_enabled(self._intervalo_visible() is not None)
        rango, muestra = self._encuadre()
        figura = _figura(self.resultado, self.fila, muestra, self._inicial)
        if self.resultado is None or not self.resultado["resultado"].get("entrada"):
            _marcar_extremos(figura, captura)
        self._preparar_seleccion(figura)
        figura.update_layout(uirevision=f"{self._revision}:{self._reencuadres}", margin_b=70, meta=self.identidad)
        figura.update_xaxes(range=rango)
        aplicar_colores_figura(figura, "papel")
        self.nodo.update_figure(figura)

    def _preparar_seleccion(self, figura: go.Figure) -> None:
        curva = figura.data[0]
        curva.update(hoverinfo="none", customdata=[self.identidad] * len(curva.x))
        figura.update_layout(hovermode="closest")
        self.respuesta = {"estado": "EXITO", "muestra": {"x": curva.x, "y": curva.y}}
        if self._puntos_borrador:
            _marcar_borrador(figura, self._puntos_borrador)

    def _captura_rango(self) -> dict:
        captura = self.captura.captura_grafica()
        if self.captura.vista.en_busqueda:
            captura.update(self.captura.vista.exploracion.capturar_rango())
        return captura

    def _encuadrar_busqueda(self, evento) -> None:
        if not self.disponible() or not self.captura.vista.en_busqueda or self._mostrando_detalle:
            return
        datos = evento.args
        if self.previa is None or not isinstance(datos, dict) or datos.get("identidad") != self.identidad:
            return
        rango = rango_evento_distinto(datos, self._captura_rango())
        if rango is not None:
            self.captura.vista.exploracion.definir_rango(rango)

    def _encuadre(self) -> tuple:
        try:
            rango = rango_grafica(self._captura_rango())
        except ValueError:
            rango = RANGO_GRAFICA_DEFECTO
        muestra = (self.previa or {}).get("muestra")
        resultado = self.resultado or {}
        if self._rango_detalle is not None:
            return self._rango_detalle, resultado.get("muestra") or muestra
        entrada = resultado.get("resultado", {}).get("entrada")
        intervalo = _intervalo(entrada) if entrada else None
        if _intervalo_fuera_del_rango_inicial(intervalo, rango):
            return intervalo, resultado.get("muestra") or muestra
        return rango, muestra


def _intervalo_fuera_del_rango_inicial(intervalo: tuple | None, rango: tuple) -> bool:
    return (intervalo is not None and rango == RANGO_GRAFICA_DEFECTO
            and (intervalo[0] < rango[0] or intervalo[1] > rango[1]))


def _marcar_borrador(figura: go.Figure, puntos: list[float]) -> None:
    figura.add_trace(go.Scatter(
        x=puntos, y=[0] * len(puntos), text=("a", "b"),
        name="Intervalo del borrador", mode="markers+text", textposition="top center", hoverinfo="skip",
        marker=dict(color=PALETA_GRAFICOS[1], size=12),
    ))


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
