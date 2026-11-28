"""Carga programática de casos de prueba y sesión para Leontief."""
from src.frontend.componentes.aplicacion.base.sonido import notificar
from src.frontend.vistas.algebra.operaciones_matrices.compartido.carga_modelos import cargar_captura_modelo


class MixinEjemplosLeontief:
    """Carga datos estructurados en los controles de captura."""

    def _cargar_ejemplo(self, ejemplo: dict):
        cargar_captura_modelo(self, ejemplo)
        notificar(f"Ejemplo '{ejemplo['nombre']}' cargado.", type="positive", position="top")
