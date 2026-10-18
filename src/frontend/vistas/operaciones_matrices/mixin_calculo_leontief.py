"""Ejecución y presentación del cálculo solicitado desde la vista de Leontief."""
import json

from nicegui import ui

from src.frontend.controladores.operaciones_matrices import ControladorLeontief
from ._renderizado_leontief import renderizar_resultado_leontief

from ._estados_modelos import ejecutar_modelo


class MixinCalculoLeontief:
    """Coordina el botón de cálculo, la captura y la respuesta del controlador."""

    async def _calcular(self, boton):
        await ejecutar_modelo(self, boton, self._calcular_nucleo)

    async def _calcular_nucleo(self):
        coeficientes = [[entrada.value or "0" for entrada in fila] for fila in self.entradas_coeficientes]
        demanda = [entrada.value or "0" for entrada in self.entradas_demanda]
        sectores = [entrada.value.strip() or f"Sector {indice + 1}"
                    for indice, entrada in enumerate(self.entradas_sectores)]
        carga = json.dumps({"matriz_coeficientes": coeficientes, "vector_demanda": demanda, "nombres_sectores": sectores})
        self.ultimo_resultado = json.loads(ControladorLeontief.procesar(carga))
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(remove="items-center justify-center", add="items-start justify-start")
            renderizar_resultado_leontief(self.ultimo_resultado)
        ui.run_javascript("window.scalaris.renderizarMathJax();")
