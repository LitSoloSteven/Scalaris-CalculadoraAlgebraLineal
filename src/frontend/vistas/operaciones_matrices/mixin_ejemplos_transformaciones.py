"""Selección y carga de ejemplos de Transformaciones."""
from nicegui import ui
from src.frontend.componentes.captura_modelos import construir_ejemplos
from ._ejemplos_transformaciones import EJEMPLOS_TRANSFORMACIONES
from .carga_modelos import cargar_captura_modelo


class MixinEjemplosTransformaciones:
    """Carga datos internos de ejemplo en los controles de captura."""

    def _construir_ejemplos(self):
        construir_ejemplos(EJEMPLOS_TRANSFORMACIONES, self._cargar_ejemplo, "Ejemplos precargados")

    def _cargar_ejemplo(self, ejemplo: dict):
        cargar_captura_modelo(self, ejemplo)
        ui.notify(f"Ejemplo '{ejemplo['nombre']}' cargado.", type="positive", position="top")
