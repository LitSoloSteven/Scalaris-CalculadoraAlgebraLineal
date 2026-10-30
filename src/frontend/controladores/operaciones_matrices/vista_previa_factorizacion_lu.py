"""Presentación saneada de la captura rectangular de LU."""
from src.frontend.controladores.operaciones_matrices.presentacion_matriz_previa import preparar_matriz_previa


def preparar_presentacion_factorizacion_lu(datos: list[list[str]], dimension: int) -> dict:
    """Prepara la matriz A para MathJax u orientación cuando excede el límite."""
    return preparar_matriz_previa(datos, dimension, ('bmatrix', 'factorizacion-lu-previa-matriz', 'A'))
