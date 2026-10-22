"""Ejecución y presentación del cálculo solicitado desde la vista de Leontief."""
import json

from nicegui import ui

from src.frontend.controladores.operaciones_matrices import ControladorLeontief
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from src.frontend.controladores.operaciones_matrices.capturas_modelos import capturar_leontief
from ._renderizado_leontief import renderizar_resultado_leontief

from ._estados_modelos import ejecutar_modelo


class MixinCalculoLeontief:
    """Coordina el botón de cálculo, la captura y la respuesta del controlador."""

    async def _calcular(self, boton):
        await ejecutar_modelo(self, boton, self._calcular_nucleo)

    async def _calcular_nucleo(self):
        calculo = await ejecutar_calculo_vigente(
            self, lambda: capturar_leontief(self),
            lambda captura: ControladorLeontief.procesar(json.dumps(captura)),
        )
        if calculo is None:
            return
        respuesta, self._huella_resultado = calculo
        self.ultimo_resultado = json.loads(respuesta)
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(remove="items-center justify-center", add="items-start justify-start")
            renderizar_resultado_leontief(self.ultimo_resultado)
        ui.run_javascript("window.scalaris.renderizarMathJax();")
