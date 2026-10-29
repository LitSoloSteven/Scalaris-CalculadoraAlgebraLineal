"""Presentación saneada compartida de matrices en la vista previa."""
import html

from src.backend.resolutores.operaciones_matrices.vista_previa_inversa import sanitizar_valor_latex
from src.frontend.controladores.vista_previa_matricial import orientacion_limite_previa


def preparar_matriz_previa(datos: list[list[str]], dimension: int, opciones: tuple[str, str, str]) -> dict:
    """Prepara datos y dimensión con entorno, identificador y prefijo indicados."""
    limite = orientacion_limite_previa(dimension)
    if limite:
        return limite
    entorno, identificador, prefijo = opciones
    filas = [' & '.join(sanitizar_valor_latex(valor) for valor in fila) for fila in datos]
    matriz = html.escape(r'\begin{' + entorno + '} ' + r' \\ '.join(filas) + r' \end{' + entorno + '}')
    return {'estado': 'exito', 'identificadores': [identificador],
            'bloques': [(identificador, f'{prefijo} = {matriz}')]}
