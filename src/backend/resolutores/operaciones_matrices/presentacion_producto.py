"""Descripcion de productos matriciales a partir de celdas ya calculadas."""
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import formatear_fraccion_texto, numero_a_latex


def describir_producto_celda(izquierda: Matriz, derecha: Matriz, fila: int, columna: int, valor) -> tuple[str, str]:
    """Devuelve texto y LaTeX de los operandos y valor de una celda del producto."""
    pares = [(izquierda.obtener(fila, indice), derecha.obtener(indice, columna))
             for indice in range(izquierda.columnas)]
    texto = " + ".join(f"({formatear_fraccion_texto(primer_valor)})·({formatear_fraccion_texto(segundo_valor)})"
                       for primer_valor, segundo_valor in pares)
    latex = " + ".join(f"({numero_a_latex(primer_valor)})({numero_a_latex(segundo_valor)})"
                       for primer_valor, segundo_valor in pares)
    return (f"{texto} = {formatear_fraccion_texto(valor)}",
            f"C_{{{fila+1},{columna+1}}} = {latex} = {numero_a_latex(valor)}")
