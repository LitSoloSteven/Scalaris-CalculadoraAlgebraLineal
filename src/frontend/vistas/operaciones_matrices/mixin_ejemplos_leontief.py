"""Selección y carga de ejemplos de Leontief."""
from nicegui import ui
from src.frontend.componentes.captura_modelos import construir_ejemplos, llenar_entradas
from ._ejemplos_leontief import EJEMPLOS_LEONTIEF


class MixinEjemplosLeontief:
    """Carga datos internos de ejemplo en los controles de captura."""

    def _construir_ejemplos(self):
        construir_ejemplos(EJEMPLOS_LEONTIEF, self._cargar_ejemplo, "Ejemplos precargados")

    def _cargar_ejemplo(self, ejemplo: dict):
        coeficientes = ejemplo["matriz_coeficientes"]
        self.numero_sectores = len(coeficientes)
        self._generar_cuadricula()
        self._generar_entradas_demanda()
        self._generar_entradas_sectores()
        for entradas, valores in zip(self.entradas_coeficientes, coeficientes):
            llenar_entradas(entradas, valores)
        llenar_entradas(self.entradas_demanda, ejemplo["vector_demanda"])
        llenar_entradas(self.entradas_sectores, ejemplo.get("nombres_sectores", []))
        self._restablecer_resultados()
        ui.notify(f"Ejemplo '{ejemplo['nombre']}' cargado.", type="positive", position="top")
