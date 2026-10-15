"""Marcado HTML de la matriz con la fila y la columna del cofactor tachadas y el menor resaltado."""
from __future__ import annotations

from src.backend.models.matrix import Matrix
from src.frontend.components.reproductor_pasos.catalogo import STACKED_FRAC_MAX_N
from src.frontend.components.reproductor_pasos.html_tablas import formatear_valor

CLASE_COEFICIENTE = "det-coef cell-pivot"
CLASE_CRUZ = "det-cruz"
CLASE_MENOR = "det-menor"


def _clase_celda(i: int, j: int, fila: int, columna: int) -> str:
    """Clasifica una celda como coeficiente elegido, cruz descartada o parte del menor."""
    if i == fila and j == columna:
        return CLASE_COEFICIENTE
    if i == fila or j == columna:
        return CLASE_CRUZ
    return CLASE_MENOR


def _fila_html(matriz: Matrix, i: int, fila: int, columna: int, apilada: bool) -> str:
    """Construye la fila i con su etiqueta y las clases de cada celda."""
    celdas = [f"<th class='row-label'>F{i + 1}</th>"]
    for j in range(matriz.cols):
        valor = formatear_valor(matriz.get(i, j), apilada=apilada)
        celdas.append(f'<td class="{_clase_celda(i, j, fila, columna)}">{valor}</td>')
    return f"<tr>{''.join(celdas)}</tr>"


def html_tabla_cofactor(matriz: Matrix, fila: int, columna: int) -> str:
    """Dibuja A tachando la fila y columna del cofactor y resaltando el menor.

    Args:
        matriz: Instancia de Matrix a renderizar.
        fila: Índice 0-based de la fila a eliminar.
        columna: Índice 0-based de la columna a eliminar.

    Returns:
        String HTML con la tabla de celdas formateadas y clases CSS específicas.

    Raises:
        ValueError: Si los índices de fila o columna están fuera de rango.
    """
    if not isinstance(matriz, Matrix):
        raise ValueError("Se esperaba una instancia de Matrix.")
    if not (0 <= fila < matriz.rows and 0 <= columna < matriz.cols):
        raise ValueError(
            f"Índices de cofactor [{fila}, {columna}] fuera de rango "
            f"para una matriz de {matriz.rows}×{matriz.cols}."
        )

    compacta = matriz.rows > STACKED_FRAC_MAX_N
    encabezado = "<th class='row-label'></th>" + "".join(
        f"<th>C{j + 1}</th>" for j in range(matriz.cols)
    )
    filas = "".join(
        _fila_html(matriz, i, fila, columna, not compacta) for i in range(matriz.rows)
    )
    clase = "inv-table compact" if compacta else "inv-table"
    etiqueta = f"Matriz con la fila {fila + 1} y la columna {columna + 1} tachadas"
    return (
        f'<div class="inv-scroll"><table class="{clase}" aria-label="{etiqueta}">'
        f"<thead><tr>{encabezado}</tr></thead><tbody>{filas}</tbody></table></div>"
    )