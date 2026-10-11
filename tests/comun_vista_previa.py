"""Construcción de la vista previa usada por las pruebas de caracterización."""
import html
import re
from src.backend.utils.validators import MatrixValidator


def construir_vista_previa_latex(matriz_a, vector_b):
    """Devuelve matriz y ecuaciones LaTeX, o el aviso de entrada correspondiente."""
    if not matriz_a or len(matriz_a) == 0 or len(matriz_a[0]) == 0:
        return None, "La matriz está vacía."
    filas, columnas = len(matriz_a), len(matriz_a[0])
    matriz_latex = _construir_matriz_aumentada(matriz_a, vector_b, columnas)
    if filas * columnas > 48:
        return matriz_latex, "Sistema demasiado grande para vista previa en ecuaciones."
    if not _celdas_validas(matriz_a, vector_b):
        return matriz_latex, "Corrige los valores inválidos para ver las ecuaciones."
    ecuaciones = _construir_ecuaciones(matriz_a, vector_b)
    if not ecuaciones:
        return matriz_latex, "No hay ecuaciones válidas."
    ecuaciones_latex = re.sub(r'x(\d+)', r'x_{\1}', r" \\ ".join(ecuaciones))
    sistema_latex = r" \begin{cases} " + ecuaciones_latex + r" \end{cases} "
    return matriz_latex, html.escape(sistema_latex)


def _sanear_celda(valor):
    if not valor:
        return '0'
    valido, _, _ = MatrixValidator.parse_number_exact(valor)
    return valor if valido else r"\color{gray}{?}"


def _construir_matriz_aumentada(matriz_a, vector_b, columnas):
    lineas = []
    for i, fila in enumerate(matriz_a):
        coeficientes = [_sanear_celda(valor) for valor in fila]
        independiente = _sanear_celda(vector_b[i] if i < len(vector_b) else '0')
        lineas.append(" & ".join(coeficientes) + f" & {independiente}")
    especificacion = "c" * columnas + "|c"
    matriz_latex = (rf"\left[ \begin{{array}}{{{especificacion}}} "
                    + r" \\ ".join(lineas) + r" \end{array} \right]")
    return html.escape(matriz_latex)


def _celdas_validas(matriz_a, vector_b):
    coeficientes_validos = _coeficientes_validos(matriz_a)
    independientes_validos = _independientes_validos(vector_b, len(matriz_a))
    return coeficientes_validos and independientes_validos


def _coeficientes_validos(matriz_a):
    columnas = len(matriz_a[0])
    for fila in matriz_a:
        for j in range(columnas):
            valor = fila[j]
            if valor and not MatrixValidator.parse_number_exact(valor)[0]:
                return False
    return True


def _independientes_validos(vector_b, filas):
    for i in range(filas):
        valor = vector_b[i] if i < len(vector_b) else ''
        if valor and not MatrixValidator.parse_number_exact(valor)[0]:
            return False
    return True


def _construir_ecuaciones(matriz_a, vector_b):
    ecuaciones = []
    for i, fila in enumerate(matriz_a):
        terminos = _terminos_ecuacion(fila)
        if not terminos:
            if vector_b[i] and vector_b[i] != '0':
                ecuaciones.append(f"0 = {vector_b[i]}")
        else:
            independiente = vector_b[i] if vector_b[i] else '0'
            ecuaciones.append(" ".join(terminos) + f" = {independiente}")
    return ecuaciones


def _terminos_ecuacion(fila):
    terminos = []
    for j, valor in enumerate(fila):
        if not valor or valor == '0' or not MatrixValidator.parse_number_exact(valor)[0]:
            continue
        signo = "-" if valor.startswith("-") else "+"
        absoluto = valor.lstrip("+-").strip()
        termino = f"x{j+1}" if absoluto in ("1", "") else f"{absoluto}x{j+1}"
        _anadir_termino(terminos, signo, termino)
    return terminos


def _anadir_termino(terminos, signo, termino):
    if not terminos and signo == "+":
        terminos.append(termino)
    elif not terminos and signo == "-":
        terminos.append(f"-{termino}")
    else:
        terminos.append(f"{signo} {termino}")
