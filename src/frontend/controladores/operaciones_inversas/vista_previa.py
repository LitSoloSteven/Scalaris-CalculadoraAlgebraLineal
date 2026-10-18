"""Delegación de la preparación matemática de la vista previa de inversa."""
from src.backend.resolutores.operaciones_matrices.vista_previa_inversa import generar_latex_vista_previa
from src.backend.constantes import DIMENSION_MAXIMA_LATEX_INVERSA
from src.backend.utilidades.estado_captura import opciones_dimension_inversa


def preparar_vista_previa_inversa(datos: list[list[str]], dimension: int) -> tuple[str, str | None, list[str]]:
    """Devuelve los bloques LaTeX y sus identificadores serializables."""
    return generar_latex_vista_previa(datos, dimension)


def preparar_presentacion_previa(datos: list[list[str]], dimension: int) -> dict:
    """Devuelve el estado, orientacion y bloques listos para presentar la captura."""
    if not opciones_dimension_inversa(dimension)['mostrar_latex']:
        return {'estado': 'limite', 'mensaje': f'Vista previa disponible hasta {DIMENSION_MAXIMA_LATEX_INVERSA}×{DIMENSION_MAXIMA_LATEX_INVERSA}.'}
    matriz, aumentada, identificadores = preparar_vista_previa_inversa(datos, dimension)
    return {'estado': 'exito', 'matriz_latex': matriz, 'aumentada_latex': aumentada, 'identificadores': identificadores}
