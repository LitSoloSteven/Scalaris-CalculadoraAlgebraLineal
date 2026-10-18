"""Cálculo y estados de resultado para transformaciones lineales."""
import json
from nicegui import ui
from ._estados_modelos import mostrar_estado
from src.frontend.controladores.operaciones_matrices import ControladorTransformaciones
from ._renderizado_transformaciones import renderizar_resultado_transformaciones

from ._estados_modelos import ejecutar_modelo


class MixinCalculoTransformaciones:
    """Orquesta el análisis de la matriz capturada y presenta su resultado."""

    async def _analizar(self, boton):
        await ejecutar_modelo(self, boton, self._analizar_nucleo)

    async def _analizar_nucleo(self):
        coeficientes_crudos = []
        for i in range(self.filas):
            fila = [self.entradas_coeficientes[i][j].value or "0" for j in range(self.columnas)]
            coeficientes_crudos.append(fila)

        variables_crudas = [entrada.value.strip() for entrada in self.entradas_variables]
        variables = [variable if variable else f"x{j+1}" for j, variable in enumerate(variables_crudas)]

        carga = json.dumps({"matriz_transformacion": coeficientes_crudos, "nombres_variables": variables})
        respuesta_json = ControladorTransformaciones.procesar(carga)
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
