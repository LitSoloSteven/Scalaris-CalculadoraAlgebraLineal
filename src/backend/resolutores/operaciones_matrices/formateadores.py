"""Formateadores especificos de LaTeX para operaciones con matrices."""

from src.backend.constantes import TOLERANCIA_COINCIDENCIA_FRACCION
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import numero_a_latex


def matriz_a_latex(matriz: Matriz, eps: float = TOLERANCIA_COINCIDENCIA_FRACCION) -> str:
    """Renderiza una matriz en formato LaTeX bmatrix."""
    filas_texto = []
    for r in range(matriz.filas):
        valores = [numero_a_latex(matriz.obtener(r, c)) for c in range(matriz.columnas)]
        filas_texto.append(" & ".join(valores))
    cuerpo = " \\\\\n".join(filas_texto)
    return f"\\begin{{bmatrix}}\n{cuerpo}\n\\end{{bmatrix}}"


def sumar_restar_matriz_a_latex(
    matriz_a: Matriz,
    matriz_b: Matriz,
    operador: str = "+",
) -> str:
    """Renderiza la suma o resta elemento a elemento en formato LaTeX."""
    filas_texto = []
    for r in range(matriz_a.filas):
        valores = []
        for c in range(matriz_a.columnas):
            operando_a_texto = numero_a_latex(matriz_a.obtener(r, c))
            operando_b_texto = numero_a_latex(matriz_b.obtener(r, c))
            operando_a_formateado = f"({operando_a_texto})" if operando_a_texto.startswith("-") else operando_a_texto
            operando_b_formateado = f"({operando_b_texto})" if operando_b_texto.startswith("-") else operando_b_texto
            valores.append(f"{operando_a_formateado} {operador} {operando_b_formateado}")
        filas_texto.append(" & ".join(valores))
    cuerpo = " \\\\\n".join(filas_texto)
    return f"\\begin{{bmatrix}}\n{cuerpo}\n\\end{{bmatrix}}"


def multiplicar_matriz_a_latex(matriz_a: Matriz, matriz_b: Matriz) -> str:
    """Renderiza el producto matricial fila por columna en formato LaTeX."""
    numero_filas, numero_intermedias, numero_columnas = matriz_a.filas, matriz_a.columnas, matriz_b.columnas
    filas_texto = []
    for r in range(numero_filas):
        valores = []
        for c in range(numero_columnas):
            terminos = []
            for k in range(numero_intermedias):
                operando_a_texto = numero_a_latex(matriz_a.obtener(r, k))
                operando_b_texto = numero_a_latex(matriz_b.obtener(k, c))
                terminos.append(f"({operando_a_texto})({operando_b_texto})")
            valores.append(" + ".join(terminos))
        filas_texto.append(" & ".join(valores))
    cuerpo = " \\\\\n".join(filas_texto)
    return f"\\begin{{bmatrix}}\n{cuerpo}\n\\end{{bmatrix}}"


def matriz_particionada_a_latex(matriz: Matriz, numero_columnas_izquierda: int) -> str:
    """Renderiza una matriz aumentada particionada con linea vertical divisoria."""
    total = matriz.columnas
    derecha = total - numero_columnas_izquierda
    if numero_columnas_izquierda < 1 or derecha < 1:
        return matriz_a_latex(matriz)

    especificacion = ("c" * numero_columnas_izquierda) + "|" + ("c" * derecha)
    filas = []
    for i in range(matriz.filas):
        valores = [numero_a_latex(matriz.obtener(i, j)) for j in range(total)]
        filas.append(" & ".join(valores))
    cuerpo = " \\\\ ".join(filas)
    return rf"\left[ \begin{{array}}{{{especificacion}}} {cuerpo} \end{{array}} \right]"
