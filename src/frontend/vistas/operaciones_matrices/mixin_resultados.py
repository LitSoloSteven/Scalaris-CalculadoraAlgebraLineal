"""Mixin de evaluación y presentación de resultados para Operaciones de Matrices."""

from __future__ import annotations

import asyncio
import json
import logging
import html

from ._cuerpo_reproductor_matrices import renderizar_cuerpo_matrices

from nicegui import ui
from src.frontend.componentes.avisos_resultado import mostrar_error_inesperado
from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.controladores.sesion_matricial import actualizar_contexto
from src.frontend.controladores.captura_contexto import capturar_matrices

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
            ui.notify('Ingresa una expresión para evaluar.', type='warning')
            return

        if getattr(self, "_calculando", False):
            return
        self._calculando = True
        self.ultimo_resultado = None
        boton.props("loading")
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.label("Evaluando…").props('role="status" aria-live="polite"')
        try:
            await self._evaluar_nucleo(boton, expresion)
        except asyncio.CancelledError:
            self.restablecer_resultados()
            raise
        except Exception as error:
            self._mostrar_error_inesperado(error)
        finally:
            self._calculando = False
            boton.props(remove="loading")

    def _mostrar_error_inesperado(self, error):
        """Muestra un mensaje accesible ante excepciones imprevistas."""
        registro.error("Error inesperado al evaluar la expresión: %s", type(error).__name__)
        mostrar_error_inesperado(self.contenedor_resultados)

    def _obtener_matrices_json(self) -> str | None:
        """Extrae el diccionario de matrices del panel de captura como JSON."""
        return json.dumps(self.panel_captura_matrices.obtener_datos_crudos())

    async def _evaluar_nucleo(self, boton, expresion):
        """Ejecuta el cálculo en el controlador y dibuja la interfaz de resultados."""
        version = self._version_solicitud
        await asyncio.sleep(0.1)
        if version != self._version_solicitud or self.entrada_expresion.value != expresion:
            self.restablecer_resultados()
            return

        matrices_json = self._obtener_matrices_json()
        if matrices_json is None:
            return

        respuesta_json = ControladorOperacionesMatrices.procesar_expresion(
            expresion, matrices_json
        )
        respuesta = json.loads(respuesta_json)
        self.ultimo_resultado = respuesta

        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(
                remove='items-center justify-center', add='items-start justify-start'
            )
            self._renderizar_estado_y_sugerencias(respuesta)
            self._renderizar_seccion_pasos(respuesta)
            self._renderizar_resultado_final(respuesta)

        ui.run_javascript('if(window.scalaris && window.scalaris.renderizarMathJax) window.scalaris.renderizarMathJax();')

        self._actualizar_huella_ia(expresion)

    def _actualizar_huella_ia(self, expresion: str):
        """Registra la huella de entrada y programa la actualización de Glosa."""
        from src.ai.huellas import calcular_huella

        entrada = capturar_matrices(self.panel_captura_matrices.matrices, expresion)
        self._huella_resultado = calcular_huella(entrada)
        actualizar_contexto(self)

    def _renderizar_estado_y_sugerencias(self, respuesta: dict):
        """Presenta el estado recibido y las sugerencias contextuales de Glosa."""
        if respuesta.get("estado") == "ERROR":
            with ui.row().classes('items-center gap-2 px-4 py-2 distintivo-error mb-4 w-fit'):
                ui.icon('close', size='sm')
                ui.label(respuesta.get("mensaje", "Error desconocido")).classes('font-bold')
        else:
            with ui.row().classes('items-center gap-2 px-4 py-2 distintivo-exito mb-6 w-fit'):
                ui.icon('check', size='sm')
                ui.label(respuesta.get("mensaje", "Éxito")).classes('font-bold')

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
            with ui.row().classes('w-full justify-center items-center panel-tarjeta p-6 overflow-x-auto'):
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
