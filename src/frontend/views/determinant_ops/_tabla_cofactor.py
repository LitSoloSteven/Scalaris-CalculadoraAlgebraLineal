"""Generación de marcado HTML de la matriz con el cofactor y menor resaltados."""
from __future__ import annotations

import html
from typing import Any

from src.backend.models.matrix import Matrix
from src.frontend.components.reproductor_pasos.catalogo import STACKED_FRAC_MAX_N
from src.frontend.components.reproductor_pasos.html_tablas import formatear_val


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

    n = matriz.rows
    clase_compacta = " compact" if n > STACKED_FRAC_MAX_N else ""

    columnas_ids = [f"C{j + 1}" for j in range(n)]
    filas_ids = [f"F{i + 1}" for i in range(n)]

    celda_th = 'class="row-label border border-[var(--border-input)] px-2 py-1 text-xs text-sec font-mono text-center"'
    
    # Encabezado superior
    th_cols = [f'<th {cel_th}></th>']
    for cid in columnas_ids:
        th_cols.append(f'<th {cel_th}>{html.escape(cid)}</th>')
    encabezado = f"<tr>{''.join(th_cols)}</tr>"

    filas_html: list[str] = [encabezado]
    for i in range(n):
        td_fila = [f'<th {cel_th}>{html.escape(filas_ids[i])}</th>']
        for j in range(n):
            valor = matriz.get(i, j)
            val_fmt = formatear_val(valor)

            clases_celda = [
                "border",
                "border-[var(--border-input)]",
                "px-3",
                "py-2",
                "text-center",
                "font-mono",
            ]

            if i == fila and j == columna:
                clases_celda.extend(["det-coef", "cell-pivot"])
            elif i == fila or j == columna:
                clases_celda.append("det-cruz")
            else:
                clases_celda.append("det-menor")

            clase_str = " ".join(clases_celda)
            td_fila.append(f'<td class="{clase_str}">{val_fmt}</td>')
        filas_html.append(f"<tr>{''.join(td_fila)}</tr>")

    cuerpo_tabla = "".join(filas_html)
    return (
        f'<div class="inv-scroll w-full overflow-x-auto">'
        f'<table class="inv-table w-full border-collapse{clase_compacta}">'
        f"{cuerpo_tabla}</table></div>"
    )