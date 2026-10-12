"""Orquestación de captura, cálculo y presentación de operaciones vectoriales."""
import json
import logging

from nicegui import ui

from src.ai.huellas import calcular_huella
from src.frontend.componentes.ai_panel import AIPanel
from src.frontend.componentes.app_shell import create_app_shell
from src.frontend.componentes.vector_capture import VectorCapturePanel
from src.frontend.navigation import route_of
from . import contexto, controles
from .mixin_resultados import MixinResultadosVectores
from src.frontend.controladores.operaciones_vectores.captura import (
    capturar_vectores, resolver_captura,
)

registro = logging.getLogger(__name__)


class VistaOperacionesVectores(MixinResultadosVectores):
    """Coordina los paneles activos sin interpretar los números del ejercicio."""

    def __init__(self):
        self.operacion_activa = "suma_resta"
        self.panel_ia = None
        self.panel_resultados = None
        self.resultado_actual = None
        self.boton_calcular = None
        self.reproductor_pasos = None
        self._huella_resultado = None
        self.operacion_suma_resta = "suma"
        self.orientacion_estricta = False
        self.valor_escalar = "2"
        self.panel_suma_resta = VectorCapturePanel("vectores_suma", min_vectors=2, max_vectors=2)
        self.panel_escalar = VectorCapturePanel("vectores_escalar", min_vectors=1, max_vectors=1)
        self.panel_combinacion = VectorCapturePanel(
            "vectores_combinacion", min_vectors=2, max_vectors=9,
            allow_orientation_toggle=False, default_orientation="column",
            first_vector_fixed_label="b",
        )
        self.paneles = {
            "suma_resta": self.panel_suma_resta,
            "escalar": self.panel_escalar,
            "combinacion_lineal": self.panel_combinacion,
        }
        for panel in self.paneles.values():
            panel.on_data_change = self._al_cambiar_vectores

    @property
    def panel_vectorial(self):
        """Devuelve el panel de captura correspondiente a la pestaña activa."""
        return self.paneles[self.operacion_activa]

    def _al_cambiar_vectores(self):
        if self.panel_ia:
            self.panel_ia.programar_actualizacion_contexto()

    def al_cambiar_pestana(self, evento):
        """Selecciona la operación del evento y retira los resultados anteriores."""
        if evento.value not in self.paneles or evento.value == self.operacion_activa:
            return
        self.operacion_activa = evento.value
        self._vaciar_resultado()

    def limpiar(self):
        """Vacía las celdas de la operación activa conservando dimensión y orientación."""
        for vector in self.panel_vectorial.vectors.values():
            vector["cache"].clear()
        self.panel_vectorial.render_all_vectors()
        self._vaciar_resultado()

    def _vaciar_resultado(self):
        self.resultado_actual = None
        self._huella_resultado = None
        self._retirar_foco_explicacion()
        self.renderizar_estado_vacio()
        self._al_cambiar_vectores()

    def _retirar_foco_explicacion(self):
        if self.panel_ia:
            self.panel_ia.clear_explain_focus()

    def construir(self):
        """Monta los tres paneles, los resultados y el asistente en el cliente actual."""
        self.panel_ia = AIPanel(self)
        create_app_shell(self, active_route=route_of("vectores"), al_alternar_ia=self.panel_ia.toggle)
        self.panel_suma_resta.inject_scripts()
        with ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 view-root"):
            with ui.element("div").classes("layout-split mb-8"):
                controles.construir_panel_izquierdo(self)
                with ui.column().classes("layout-pane p-8 bg-[var(--bg-page)]") as self.panel_resultados:
                    self.renderizar_estado_vacio()
        self.panel_ia.build()

    async def calcular(self):
        """Delega la captura al controlador y restaura el botón incluso ante fallos."""
        self.boton_calcular.disable()
        self.boton_calcular.props("loading")
        try:
            respuesta = resolver_captura(self.operacion_activa, self._opciones_calculo(), self._capturar())
            self.resultado_actual = json.loads(respuesta)
            self._huella_resultado = calcular_huella(contexto.entrada_actual(self))
            self._retirar_foco_explicacion()
            self.renderizar_resultado(self.resultado_actual)
            self._al_cambiar_vectores()
            ui.run_javascript("window.scalaris?.renderizarMathJax?.();")
        except Exception:
            registro.error("Error inesperado al calcular operaciones con vectores")
            ui.notify("Ocurrió un error inesperado al procesar el cálculo. Inténtalo de nuevo.", type="negative")
        finally:
            self.boton_calcular.enable()
            self.boton_calcular.props(remove="loading")

    def _opciones_calculo(self):
        return {"operacion": self.operacion_suma_resta, "estricto": self.orientacion_estricta,
                "escalar": self.valor_escalar, "objetivo": self.panel_combinacion.first_vector_fixed_label}

    def _capturar(self):
        return capturar_vectores(self.panel_vectorial.vectors, self.panel_vectorial.dim)

    def obtener_contexto_ia(self):
        """Devuelve el ejercicio y solo el resultado que corresponde a sus entradas."""
        return contexto.obtener_contexto(self)

    def obtener_senales_ia(self):
        """Devuelve las señales de entrada y resultado para las sugerencias."""
        return contexto.obtener_senales(self)
