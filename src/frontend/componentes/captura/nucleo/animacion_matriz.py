"""Adaptador cliente de la transición de captura matricial."""
import json
from nicegui import ui


async def animar_redimension_matriz(accion: str, selector: str) -> None:
    """Ejecuta la acción sobre el selector y tolera la ausencia del cliente."""
    try:
        await ui.run_javascript(f"return window.scalaris?.cuadricula?.animarRedimensionCuadrada({json.dumps(selector)}, {json.dumps(accion)});")
    except Exception:
        pass
