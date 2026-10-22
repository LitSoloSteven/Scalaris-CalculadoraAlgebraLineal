"""Controlador para la resolución de sistemas lineales mediante Gauss-Jordan."""
from src.backend.resolutores.sistemas_lineales.gauss_jordan import (
    ResolutorGaussJordan,
)
from src.frontend.controladores.sistemas_lineales.flujo_comun import (
    ejecutar_flujo_sistema,
)


class ControladorGaussJordan:
    """Gestiona la validación y ejecución del método de Gauss-Jordan para sistemas lineales."""

    @staticmethod
    def procesar_sistema(carga_json: str) -> str:
        """Procesa el sistema con el método de Gauss-Jordan y genera pasos pedagógicos."""
        return ejecutar_flujo_sistema(carga_json, ResolutorGaussJordan, "gauss-jordan")
