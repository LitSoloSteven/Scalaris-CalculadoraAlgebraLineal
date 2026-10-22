"""Preparación numérica y LaTeX de la vista previa de inversa."""
import html
from src.backend.constantes import DIMENSION_MAXIMA_AUMENTADA_PREVIA_INVERSA
from src.backend.utilidades.validadores import ValidadorMatriz


def sanitizar_valor_latex(valor: str) -> str:
    """Sanitiza o marca celda inválida para representación LaTeX."""
    if not valor or valor == '0':
        return '0'
    correcto, _, _ = ValidadorMatriz.parsear_numero_exacto(valor)
    if not correcto:
        return r"\color{gray}{?}"
    return valor


def generar_latex_vista_previa(
    datos: list[list[str]], dimension: int
) -> tuple[str, str | None, list[str]]:
    """Construye las cadenas LaTeX de A y [A | I] para la vista previa."""
    filas_latex = [" & ".join(sanitizar_valor_latex(valor) for valor in fila) for fila in datos]
    latex_matriz_entrada = html.escape(
        r"\begin{bmatrix} " + r" \\ ".join(filas_latex) + r" \end{bmatrix}"
    )
    identificadores = ['inversa-previa-matriz']
    aumentada_latex = None

    if dimension <= DIMENSION_MAXIMA_AUMENTADA_PREVIA_INVERSA:
        filas_aumentadas = []
        for i, fila in enumerate(datos):
            izquierda = " & ".join(sanitizar_valor_latex(valor) for valor in fila)
            derecha = " & ".join('1' if i == j else '0' for j in range(dimension))
            filas_aumentadas.append(f"{izquierda} & {derecha}")
        especificacion = "c" * dimension + "|" + "c" * dimension
        aumentada_latex = html.escape(
            rf"\left[ \begin{{array}}{{{especificacion}}} "
            + r" \\ ".join(filas_aumentadas)
            + r" \end{array} \right]"
        )
        identificadores.append('inversa-previa-aumentada')

    return latex_matriz_entrada, aumentada_latex, identificadores
