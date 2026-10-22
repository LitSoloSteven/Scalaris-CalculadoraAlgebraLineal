"""Presentación saneada de la captura con notación de determinante."""
import html

from src.backend.resolutores.operaciones_matrices.vista_previa_inversa import sanitizar_valor_latex
from src.frontend.controladores.vista_previa_matricial import orientacion_limite_previa


def preparar_presentacion_determinante(datos: list[list[str]], dimension: int) -> dict:
    """Prepara |A| para MathJax o devuelve orientación si supera el límite."""
    limite = orientacion_limite_previa(dimension)
    if limite:
        return limite
    filas = [' & '.join(sanitizar_valor_latex(valor) for valor in fila) for fila in datos]
    matriz = html.escape(r'\begin{vmatrix} ' + r' \\ '.join(filas) + r' \end{vmatrix}')
    identificador = 'determinante-previa-matriz'
    return {'estado': 'exito', 'identificadores': [identificador],
            'bloques': [(identificador, f'|A| = {matriz}')]}
