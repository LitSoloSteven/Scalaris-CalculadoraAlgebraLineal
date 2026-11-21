"""Preparacion de etiquetas y valores escapados de la solucion de un sistema."""
import html
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import formatear_variable_para_latex, separar_indice_variable
from src.backend.utilidades.reconstruccion_matrices import reconstruir_matriz


def formatear_elemento_solucion(variable: str, valor: str) -> tuple[str, str, str]:
    """Devuelve variable HTML, variable LaTeX y valor escapados para presentar."""
    nombre = html.escape(str(variable))
    letras, indice = separar_indice_variable(nombre)
    subindice = f'<sub>{indice}</sub>' if indice is not None else ''
    return f'<i>{letras}</i>{subindice}', formatear_variable_para_latex(nombre), html.escape(str(valor))


def preparar_matriz_paso(datos: dict) -> Matriz:
    """Delega la reconstruccion exacta de la matriz usada para presentar el paso."""
    return reconstruir_matriz(datos)
