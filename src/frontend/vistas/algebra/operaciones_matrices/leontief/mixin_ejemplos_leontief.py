"""Selección y carga de ejemplos de Leontief."""
from src.frontend.componentes.aplicacion.base.sonido import notificar
from src.frontend.componentes.captura.matrices.captura_modelos import construir_ejemplos
from src.frontend.vistas.algebra.operaciones_matrices.leontief.apoyo._ejemplos_leontief import EJEMPLOS_LEONTIEF
from src.frontend.vistas.algebra.operaciones_matrices.compartido.carga_modelos import cargar_captura_modelo


class MixinEjemplosLeontief:
    """Carga datos internos de ejemplo en los controles de captura."""

    def _construir_ejemplos(self):
        construir_ejemplos(EJEMPLOS_LEONTIEF, self._cargar_ejemplo, "Ejemplos precargados")

    def _cargar_ejemplo(self, ejemplo: dict):
        cargar_captura_modelo(self, ejemplo)
        notificar(f"Ejemplo '{ejemplo['nombre']}' cargado.", type="positive", position="top")
