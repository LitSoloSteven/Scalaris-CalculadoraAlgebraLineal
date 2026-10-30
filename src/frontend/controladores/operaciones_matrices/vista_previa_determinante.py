"""Presentación saneada de la captura con notación de determinante."""
from src.frontend.controladores.operaciones_matrices.presentacion_matriz_previa import preparar_matriz_previa


def preparar_presentacion_determinante(datos: list[list[str]], dimension: int) -> dict:
    """Prepara |A| para MathJax o devuelve orientación si supera el límite."""
    return preparar_matriz_previa(datos, dimension, ('vmatrix', 'determinante-previa-matriz', '|A|'))
