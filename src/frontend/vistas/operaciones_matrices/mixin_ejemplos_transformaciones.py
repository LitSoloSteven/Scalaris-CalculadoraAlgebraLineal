"""Selección y carga de ejemplos de Transformaciones."""
from nicegui import ui
from src.frontend.componentes.captura_modelos import construir_ejemplos, llenar_entradas
from ._ejemplos_transformaciones import EJEMPLOS_TRANSFORMACIONES


class MixinEjemplosTransformaciones:
    """Carga datos internos de ejemplo en los controles de captura."""

    def _construir_ejemplos(self):
        construir_ejemplos(EJEMPLOS_TRANSFORMACIONES, self._cargar_ejemplo, "Ejemplos precargados")

    def _cargar_ejemplo(self, ejemplo: dict):
        coeficientes = ejemplo["matriz_transformacion"]
        self.filas, self.columnas = len(coeficientes), len(coeficientes[0])
        self._generar_cuadricula()
        self._generar_entradas_variables()
        for entradas, valores in zip(self.entradas_coeficientes, coeficientes):
            llenar_entradas(entradas, valores)
        llenar_entradas(self.entradas_variables, ejemplo.get("nombres_variables", []))
        self._restablecer_resultados()
        ui.notify(f"Ejemplo '{ejemplo['nombre']}' cargado.", type="positive", position="top")
