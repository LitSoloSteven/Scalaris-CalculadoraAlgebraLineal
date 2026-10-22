"""Orquestación de captura, cálculo y presentación de operaciones vectoriales."""
import json
import logging

from nicegui import run, ui
from src.backend.utilidades.estado_captura import captura_vacia

from src.ai.huellas import calcular_huella
from src.backend.constantes import DIMENSION_MAXIMA_VECTORES
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
        self._revision_calculo = 0
        self._montada = True
        self._calculando = False
        self.panel_suma_resta = PanelCapturaVectores("vectores_suma", opciones={'minimo_vectores': 2, 'maximo_vectores': 2})
        self.panel_escalar = PanelCapturaVectores("vectores_escalar", opciones={'minimo_vectores': 1, 'maximo_vectores': 1})
        self.panel_combinacion = PanelCapturaVectores("vectores_combinacion", opciones={'minimo_vectores': 2, 'maximo_vectores': 9, 'permitir_orientacion': False, 'orientacion_inicial': "columna", 'etiqueta_primer_vector': "b"})
        self.panel_independencia = PanelCapturaVectores("vectores_independencia", opciones={
            'minimo_vectores': 1, 'maximo_vectores': DIMENSION_MAXIMA_VECTORES, 'permitir_orientacion': False, 'orientacion_inicial': "columna"})
        self.paneles = {
            "suma_resta": self.panel_suma_resta,
            "escalar": self.panel_escalar,
            "combinacion_lineal": self.panel_combinacion,
            "independencia": self.panel_independencia,
        }
        for panel in self.paneles.values():
            panel.al_cambiar_datos = self._al_cambiar_vectores

    @property
    def panel_vectorial(self):
        """Devuelve el panel de captura correspondiente a la pestaña activa."""
        return self.paneles[self.operacion_activa]

    def _al_cambiar_vectores(self):
        self._revision_calculo += 1
        self.resultado_actual = None
        self._retirar_foco_explicacion()
        self.renderizar_estado_vacio()
        actualizar_contexto(self)

    def al_cambiar_pestana(self, evento):
        """Selecciona la operación del evento y retira los resultados anteriores."""
        if evento.value not in self.paneles or evento.value == self.operacion_activa:
            return
        self.operacion_activa = evento.value
        self._vaciar_resultado()

    def limpiar(self):
        """Vacía las celdas de la operación activa conservando dimensión y orientación."""
        self.limpiar_todo()

    def limpiar_todo(self) -> None:
        """Vacía la captura activa y retira el resultado y la explicación."""
        for vector in self.panel_vectorial.vectores.values():
            vector["celdas"].clear()
        if self.operacion_activa == 'escalar':
            self.valor_escalar = ''
            self.entrada_escalar.set_value('')
        self.panel_vectorial.renderizar_todos_vectores()
        self._vaciar_resultado()

    def esta_completamente_vacio(self) -> bool:
        """Consulta las celdas y el escalar solo de la operación activa."""
        valores = [valor for vector in self.panel_vectorial.vectores.values()
                   for valor in vector['celdas'].values()]
        if self.operacion_activa == 'escalar':
            valores.append(self.valor_escalar)
        return captura_vacia(valores, False)

    def _vaciar_resultado(self):
        self._huella_resultado = None
        self._al_cambiar_vectores()

    def _retirar_foco_explicacion(self):
        if self.panel_ia:
            self.panel_ia.limpiar_foco_explicacion()

    def construir(self):
        """Monta los paneles de operaciones, los resultados y el asistente del cliente actual."""
        self.panel_ia = PanelIA(self)
        ui.context.client.on_delete(self._desmontar)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("vectores"), al_alternar_ia=self.panel_ia.alternar)
        self.panel_suma_resta.inyectar_recursos_cliente()
        with (
            ui.element('div').classes('vectores-marco w-full'),
            ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 vista-raiz vectores-vista"),
            ui.element("div").classes("disposicion-dividida mb-8"),
        ):
            controles.construir_panel_izquierdo(self)
            with ui.column().classes("disposicion-panel p-8 bg-[var(--bg-page)]") as self.panel_resultados:
                self.renderizar_estado_vacio()
        self.panel_ia.construir()

    async def calcular(self):
        """Delega la captura al controlador y restaura el botón incluso ante fallos."""
        if self._calculando:
            return
        self._calculando = True
        revision = self._revision_calculo
        entrada = contexto.entrada_actual(self)
        self.resultado_actual = None
        self._huella_resultado = None
        self._retirar_foco_explicacion()
        self.renderizar_estado_vacio()
        self.boton_calcular.disable()
        self.boton_calcular.props("loading")
        with self.panel_resultados:
            ui.label("Calculando…").props('role="status" aria-live="polite"')
        try:
            respuesta = await run.io_bound(resolver_captura, self.operacion_activa, self._opciones_calculo(), self._capturar())
            if self._montada and revision == self._revision_calculo:
                self._publicar_calculo(json.loads(respuesta), entrada)
        except Exception:
            registro.error("Error inesperado al calcular operaciones con vectores")
            if self._montada and revision == self._revision_calculo:
                self._publicar_calculo({"estado": "ERROR", "mensaje": "No pudimos calcular. Revisa los datos e inténtalo de nuevo."}, entrada)
                ui.notify("No pudimos calcular. Revisa los datos e inténtalo de nuevo.", type="negative")
        finally:
            self._calculando = False
            if not self.boton_calcular.is_deleted:
                self.boton_calcular.enable()
                self.boton_calcular.props(remove="loading")

    def _publicar_calculo(self, respuesta: dict, entrada: dict) -> None:
        self.renderizar_resultado(respuesta)
        self.resultado_actual = respuesta
        self._huella_resultado = calcular_huella(entrada)
        actualizar_contexto(self)
        ui.run_javascript("window.scalaris?.renderizarMathJax?.();")

    def _desmontar(self) -> None:
        self._montada = False
        self._revision_calculo += 1
        if self.reproductor_pasos is not None:
            self.reproductor_pasos.detener()

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
