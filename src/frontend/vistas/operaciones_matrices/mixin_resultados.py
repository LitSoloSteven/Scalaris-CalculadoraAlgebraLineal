"""Mixin de evaluación y presentación de resultados para Operaciones de Matrices."""

from __future__ import annotations

import asyncio
import json
import logging
import html

from ._cuerpo_reproductor_matrices import renderizar_cuerpo_matrices

from nicegui import ui
from src.frontend.componentes.sonido import notificar
from src.frontend.componentes.avisos_resultado import mostrar_error_inesperado, renderizar_aviso_resultado
from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.componentes.exportacion_pdf.integracion import region_pdf, completar_exportacion, identificador_raiz
from src.frontend.controladores.exportacion_pdf.vigencia import EnlacePDF
from src.frontend.componentes.acciones_matriz import renderizar_acciones_matriz
from src.frontend import textos
from src.frontend.controladores.sesion_matricial import actualizar_contexto
from src.frontend.controladores.captura_contexto import capturar_matrices, capturar_matrices_documento
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente

from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.controladores.operaciones_matrices import (
    ControladorOperacionesMatrices,
)
from src.frontend.vistas.operaciones_matrices._pasos_reproductor import construir_pasos_matrices

registro = logging.getLogger(__name__)


class MixinResultadosOperacionesMatrices:
    """Gestiona la ejecución y el renderizado interactivo de operaciones matriciales."""

    async def evaluar_expresion(self, boton):
        """Valida la expresión y coordina el botón de carga."""
        expresion = self.entrada_expresion.value
        if not expresion:
            self.restablecer_resultados()
            notificar('Ingresa una expresión para evaluar.', type='warning')
            return

        if getattr(self, "_calculando", False):
            return
        self._calculando = True
        version = self._version_solicitud
        self.ultimo_resultado = None
        boton.props("loading")
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.label("Evaluando…").props('role="status" aria-live="polite"')
        try:
            await self._evaluar_nucleo(boton, expresion)
        except asyncio.CancelledError:
            if not self.contenedor_resultados.is_deleted and version == self._version_solicitud:
                self.restablecer_resultados()
            raise
        except Exception as error:
            self._mostrar_error_inesperado(error)
        finally:
            self._calculando = False
            if not boton.is_deleted:
                boton.props(remove="loading")

    def _mostrar_error_inesperado(self, error):
        """Muestra un mensaje accesible ante excepciones imprevistas."""
        registro.error("Error inesperado al evaluar la expresión: %s", type(error).__name__)
        mostrar_error_inesperado(self.contenedor_resultados)

    async def _evaluar_nucleo(self, boton, expresion):
        """Ejecuta el cálculo en el controlador y dibuja la interfaz de resultados."""
        version = self._version_solicitud
        await asyncio.sleep(0.1)
        if self.contenedor_resultados.is_deleted:
            return
        if version != self._version_solicitud or self.entrada_expresion.value != expresion:
            self.restablecer_resultados()
            return

        captura = self._capturar_evaluacion()
        calculo = await ejecutar_calculo_vigente(
            self, self._capturar_evaluacion,
            lambda captura: ControladorOperacionesMatrices.procesar_expresion(
                captura['expresion'], json.dumps(captura['matrices'])),
        )
        if calculo is None:
            return
        respuesta_json, _ = calculo
        respuesta = json.loads(respuesta_json)
        self.ultimo_resultado = respuesta
        self._actualizar_huella_ia(expresion)

        self._presentar_evaluacion(respuesta, captura['matrices'])
        ui.run_javascript('if(window.scalaris && window.scalaris.renderizarMathJax) window.scalaris.renderizarMathJax();')

    def _presentar_evaluacion(self, respuesta: dict, matrices: dict) -> None:
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(
                remove='items-center justify-center', add='items-start justify-start'
            )
            with region_pdf('matrices-resumen'):
                self._renderizar_estado_y_sugerencias(respuesta)
            self._renderizar_seccion_pasos(respuesta)
            self._renderizar_resultado_final(respuesta)
            self._renderizar_transferencias(respuesta, matrices)
            enlace = EnlacePDF(self, lambda: capturar_matrices(
                self.panel_captura_matrices.matrices, self.entrada_expresion.value),
                identificador_raiz(self.contenedor_resultados),
                lambda: (self.contenedor_resultados, self.ultimo_resultado,
                         self._version_solicitud, self._version_solicitud),
                leer_entrada_documental=lambda: capturar_matrices_documento(
                    self.panel_captura_matrices.obtener_datos_crudos(), self.entrada_expresion.value))
            completar_exportacion(self, 'matrices', respuesta, enlace)

    def _capturar_evaluacion(self) -> dict:
        return {'expresion': self.entrada_expresion.value,
                'matrices': self.panel_captura_matrices.obtener_datos_crudos()}

    def _renderizar_transferencias(self, respuesta: dict, matrices: dict) -> None:
        if respuesta.get('estado') != 'EXITO':
            return
        for nombre, matriz in matrices.items():
            ui.label(textos.TRANSFERENCIA_MATRIZ_CAPTURADA.format(nombre=nombre)).classes(
                'font-semibold texto-principal')
            renderizar_acciones_matriz('matrices', matriz['datos'])


    def _actualizar_huella_ia(self, expresion: str):
        """Registra la huella de entrada y programa la actualización de Glosa."""
        from src.ai.huellas import calcular_huella

        entrada = capturar_matrices(self.panel_captura_matrices.matrices, expresion)
        self._huella_resultado = calcular_huella(entrada)
        actualizar_contexto(self)

    def _renderizar_estado_y_sugerencias(self, respuesta: dict):
        """Presenta el estado recibido y las sugerencias contextuales de Glosa."""
        if respuesta.get("estado") == "ERROR":
            renderizar_aviso_resultado(respuesta.get("mensaje", "Error desconocido"), 'close',
                                      'items-center gap-2 px-4 py-2 distintivo-error mb-4 w-fit')
        else:
            renderizar_aviso_resultado(respuesta.get("mensaje", "Éxito"), 'check',
                                      'items-center gap-2 px-4 py-2 distintivo-exito mb-6 w-fit')

        if getattr(self, 'panel_ia', None):
            self.panel_ia.renderizar_sugerencias_en_linea()

    def _renderizar_seccion_pasos(self, respuesta: dict):
        """Monta el reproductor interactivo si la expresión produjo suboperaciones."""
        if getattr(self, "reproductor_pasos", None) is not None:
            self.reproductor_pasos.detener()

        pasos, grupos = construir_pasos_matrices(respuesta)
        if not pasos:
            return

        accion_glosa = crear_accion_explicacion(getattr(self, "panel_ia", None), pasos)

        self.reproductor_pasos = ReproductorPasos(pasos, grupos, renderizar_cuerpo=renderizar_cuerpo_matrices, identificador="matrices", opciones={'titulo': "Evaluación paso a paso", 'lineas_ayuda': _LINEAS_AYUDA_MATRICES, 'tipos_leyenda': ("operacion",), 'al_explicar': accion_glosa, 'esta_ocupado': lambda: bool(
                getattr(getattr(self, "panel_ia", None), "_esta_enviando", False)
            )})
        self.reproductor_pasos.construir()


    def _renderizar_resultado_final(self, respuesta: dict):
        """Muestra el resultado final si la evaluación incluyó más de una suboperación."""
        mostrar_resultado_final = len(respuesta.get("pasos_segmento", [])) != 1
        if (
            mostrar_resultado_final
            and respuesta.get("variable_final")
            and respuesta.get("matriz_resultado_latex")
        ):
            ui.label('Resultado Final:').classes('font-bold text-xl texto-principal mt-6 mb-4')
            with ui.row().classes('w-full justify-center items-center panel-tarjeta p-6 overflow-x-auto').props('data-pdf-captura=matrices-resultado'):
                ui.html(
                    f'<div class="matematicas-desplazamiento matematicas-etiqueta text-2xl font-bold">'
                    f'$$ {html.escape(respuesta["variable_final"])} = {html.escape(respuesta["matriz_resultado_latex"])} $$'
                    f'</div>'
                )


_LINEAS_AYUDA_MATRICES = (
    "• Cada paso muestra una suboperación de la expresión evaluada.",
    "• La flecha indica la transición de la forma simbólica a la matriz resultante.",
    "• Puedes desplegar el detalle celda a celda para consultar las operaciones aritméticas.",
)
