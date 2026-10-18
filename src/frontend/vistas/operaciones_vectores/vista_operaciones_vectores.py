"""Orquestación de captura, cálculo y presentación de operaciones vectoriales."""
import json
import logging

from nicegui import ui

from src.ai.huellas import calcular_huella
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.captura_vectores import PanelCapturaVectores
from src.frontend.navegacion import ruta_de
from src.frontend.controladores.sesion_matricial import actualizar_contexto
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
        self.panel_suma_resta = PanelCapturaVectores("vectores_suma", opciones={'minimo_vectores': 2, 'maximo_vectores': 2})
        self.panel_escalar = PanelCapturaVectores("vectores_escalar", opciones={'minimo_vectores': 1, 'maximo_vectores': 1})
        self.panel_combinacion = PanelCapturaVectores("vectores_combinacion", opciones={'minimo_vectores': 2, 'maximo_vectores': 9, 'permitir_orientacion': False, 'orientacion_inicial': "columna", 'etiqueta_primer_vector': "b"})
        self.paneles = {
            "suma_resta": self.panel_suma_resta,
            "escalar": self.panel_escalar,
            "combinacion_lineal": self.panel_combinacion,
        }
        for panel in self.paneles.values():
            panel.al_cambiar_datos = self._al_cambiar_vectores

    @property
    def panel_vectorial(self):
        """Devuelve el panel de captura correspondiente a la pestaña activa."""
        return self.paneles[self.operacion_activa]

    def _al_cambiar_vectores(self):
        actualizar_contexto(self)

    def al_cambiar_pestana(self, evento):
        """Selecciona la operación del evento y retira los resultados anteriores."""
        if evento.value not in self.paneles or evento.value == self.operacion_activa:
            return
        self.operacion_activa = evento.value
        self._vaciar_resultado()

    def limpiar(self):
        """Vacía las celdas de la operación activa conservando dimensión y orientación."""
        for vector in self.panel_vectorial.vectores.values():
            vector["celdas"].clear()
        self.panel_vectorial.renderizar_todos_vectores()
        self._vaciar_resultado()

    def _vaciar_resultado(self):
        self.resultado_actual = None
        self._huella_resultado = None
        self._retirar_foco_explicacion()
        self.renderizar_estado_vacio()
        self._al_cambiar_vectores()

    def _retirar_foco_explicacion(self):
        if self.panel_ia:
            self.panel_ia.limpiar_foco_explicacion()

    def construir(self):
        """Monta los tres paneles, los resultados y el asistente en el cliente actual."""
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("vectores"), al_alternar_ia=self.panel_ia.alternar)
        self.panel_suma_resta.inyectar_recursos_cliente()
        with (
            ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 vista-raiz vectores-vista"),
            ui.element("div").classes("disposicion-dividida mb-8"),
        ):
            controles.construir_panel_izquierdo(self)
            with ui.column().classes("disposicion-panel p-8 bg-[var(--bg-page)]") as self.panel_resultados:
                self.renderizar_estado_vacio()
        self.panel_ia.construir()

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
                "escalar": self.valor_escalar, "objetivo": self.panel_combinacion.etiqueta_fija_primer_vector}

    def _capturar(self):
        return capturar_vectores(self.panel_vectorial.vectores, self.panel_vectorial.dimension)

    def obtener_contexto_ia(self):
        """Devuelve el ejercicio y solo el resultado que corresponde a sus entradas."""
        return contexto.obtener_contexto(self)

    def obtener_senales_ia(self):
        """Devuelve las señales de entrada y resultado para las sugerencias."""
        return contexto.obtener_senales(self)
