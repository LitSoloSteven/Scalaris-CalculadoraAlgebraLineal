"""Cálculo y estados de resultado para transformaciones lineales."""
import json
from nicegui import ui
from ._estados_modelos import mostrar_estado
from src.frontend.controladores.operaciones_matrices import ControladorTransformaciones
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from src.frontend.controladores.operaciones_matrices.capturas_modelos import capturar_transformaciones
from ._renderizado_transformaciones import renderizar_resultado_transformaciones

from ._estados_modelos import ejecutar_modelo


class MixinCalculoTransformaciones:
    """Orquesta el análisis de la matriz capturada y presenta su resultado."""

    async def _analizar(self, boton):
        await ejecutar_modelo(self, boton, self._analizar_nucleo)

    async def _analizar_nucleo(self):
        calculo = await ejecutar_calculo_vigente(
            self, lambda: capturar_transformaciones(self),
            lambda captura: ControladorTransformaciones.procesar(json.dumps(captura)),
        )
        if calculo is None:
            return
        respuesta_json, self._huella_resultado = calculo
        respuesta = json.loads(respuesta_json)
        self.ultimo_resultado = respuesta

        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(
                remove="items-center justify-center", add="items-start justify-start"
            )
            renderizar_resultado_transformaciones(respuesta)

        ui.run_javascript("if(window.scalaris && window.scalaris.renderizarMathJax) window.scalaris.renderizarMathJax();")

    def _restablecer_resultados(self):
        self.ultimo_resultado = None
        mostrar_estado(self.contenedor_resultados, "Ingresa la matriz A y presiona Analizar.")
