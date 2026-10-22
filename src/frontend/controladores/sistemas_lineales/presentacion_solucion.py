"""Preparacion de etiquetas y valores escapados de la solucion de un sistema."""
import html
import re
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.reconstruccion_matrices import reconstruir_matriz


def formatear_elemento_solucion(variable: str, valor: str) -> tuple[str, str, str]:
    """Devuelve variable HTML, variable LaTeX y valor escapados para presentar."""
    nombre = html.escape(str(variable))
    coincidencia = re.fullmatch(r'([a-zA-Z]+)(\d+)', nombre)
    if coincidencia:
        letras, indice = coincidencia.groups()
        return f'<i>{letras}</i><sub>{indice}</sub>', f'{letras}_{{{indice}}}', html.escape(str(valor))
    latex = f'\\text{{{nombre}}}' if len(nombre) > 1 else nombre
    return f'<i>{nombre}</i>', latex, html.escape(str(valor))


def preparar_matriz_paso(datos: dict) -> Matriz:
    """Delega la reconstruccion exacta de la matriz usada para presentar el paso."""
    return reconstruir_matriz(datos)
