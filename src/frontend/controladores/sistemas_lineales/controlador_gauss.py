"""Controlador para la resolución de sistemas lineales mediante eliminación de Gauss."""
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.frontend.controladores.sistemas_lineales.flujo_comun import (
    ejecutar_flujo_sistema,
)


class ControladorGauss:
    """Gestiona la validación y ejecución del método de Gauss para sistemas lineales."""

    @staticmethod
    def procesar_sistema(carga_json: str) -> str:
        """Procesa el sistema lineal con el método de Gauss y genera pasos pedagógicos."""
        return ejecutar_flujo_sistema(carga_json, ResolutorGauss, "gauss")
