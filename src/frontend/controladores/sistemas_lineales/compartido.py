"""Utilidades compartidas para validación y metadatos de sistemas lineales."""
from fractions import Fraction
import json
from typing import Any

from src.backend.excepciones import ErrorDatosMatriz
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.controladores.clasificador_pasos import clasificar_paso


def _validar_dimensiones_aumentada(
    matriz_a_cruda: list, vector_b_crudo: list
) -> tuple[int, int, str | None]:
    """Valida la consistencia de forma y dimensiones entre matriz y vector."""
    m = len(matriz_a_cruda)
    if m == 0:
        return 0, 0, json.dumps({"status": "ERROR", "message": "La matriz A está vacía."})
    if not isinstance(matriz_a_cruda[0], list):
        return 0, 0, json.dumps({"status": "ERROR", "message": "La matriz A debe ser una lista de filas."})
    n = len(matriz_a_cruda[0])
    if n == 0:
        return 0, 0, json.dumps({"status": "ERROR", "message": "La matriz A no puede tener 0 columnas."})

    valido, mensaje = ValidadorMatriz.validar_datos_matriz(matriz_a_cruda, m, n)
    if not valido:
        return 0, 0, json.dumps({"status": "ERROR", "message": mensaje})
    if len(vector_b_crudo) != m:
        msg = f"El vector b tiene {len(vector_b_crudo)} valores; se esperaban {m} (uno por fila de A)."
        return 0, 0, json.dumps({"status": "ERROR", "message": msg})
    return m, n, None


def _parsear_celdas_a_fracciones(
    matriz_a_cruda: list, vector_b_crudo: list
) -> tuple[list[list[Fraction]] | None, list[Fraction] | None, str | None]:
    """Convierte celdas de matriz y vector a fracciones exactas con coordenadas."""
    a_fracciones: list[list[Fraction]] = []
    for i, fila in enumerate(matriz_a_cruda):
        fila_frac: list[Fraction] = []
        for j, celda in enumerate(fila):
            texto = str(celda).strip() if celda is not None and str(celda).strip() else "0"
            ok, val, err = ValidadorMatriz.parsear_numero_exacto(texto)
            if not ok:
                return None, None, json.dumps({"status": "ERROR", "message": f"Error en A[{i+1},{j+1}]: {err}"})
            fila_frac.append(val)
        a_fracciones.append(fila_frac)

    b_fracciones: list[Fraction] = []
    for i, celda in enumerate(vector_b_crudo):
        texto = str(celda).strip() if celda is not None and str(celda).strip() else "0"
        ok, val, err = ValidadorMatriz.parsear_numero_exacto(texto)
        if not ok:
            return None, None, json.dumps({"status": "ERROR", "message": f"Error en b[{i+1}]: {err}"})
        b_fracciones.append(val)
    return a_fracciones, b_fracciones, None


def validar_y_construir_aumentada(
    datos: dict,
) -> tuple[Matriz | None, list[list[Fraction]] | None, list[Fraction] | None, int, int, str | None]:
    """Valida el payload y construye la matriz aumentada [A | b]."""
    matriz_a_cruda = datos.get("matrix_A", [])
    vector_b_crudo = datos.get("vector_b", [])

    m, n, error_dim = _validar_dimensiones_aumentada(matriz_a_cruda, vector_b_crudo)
    if error_dim is not None:
        return None, None, None, 0, 0, error_dim

    a_fracciones, b_fracciones, error_parse = _parsear_celdas_a_fracciones(matriz_a_cruda, vector_b_crudo)
    if error_parse is not None or a_fracciones is None or b_fracciones is None:
        return None, None, None, 0, 0, error_parse

    try:
        datos_aumentados = [a_fracciones[i] + [b_fracciones[i]] for i in range(m)]
        matriz = Matriz(m, n + 1, datos_aumentados)
    except ErrorDatosMatriz as error:
        return None, None, None, 0, 0, json.dumps({"status": "ERROR", "message": f"Datos inválidos: {error}"})

    return matriz, a_fracciones, b_fracciones, m, n, None


def _determinar_filas_objetivo(
    kind: str, r1: int | None, r2: int | None
) -> tuple[list[int], list[int], int | None]:
    """Retorna las listas de índices de filas antes, después y fila del pivote."""
    if r1 is None:
        return [], [], None
    if kind == "intercambio" and r2 is not None:
        return [r1, r2], [r1, r2], r1
    if kind == "eliminacion" and r2 is not None:
        return [r1, r2], [r1], r2
    if kind == "normalizacion":
        return [r1], [r1], r1
    return [], [], None


def _extraer_detalles_paso(
    kind: str,
    parsed: dict,
    col_pivote_actual: int,
    filas_previas: list,
    filas_actuales: list,
) -> tuple[list[int] | None, dict, dict, list | None, int]:
    """Calcula pivote y extractos de filas antes y después según la operación."""
    from src.ai.contexto import extraer_filas

    r1, r2 = parsed.get("row1"), parsed.get("row2")
    if kind == "pivote" and r1 is not None and parsed.get("col") is not None:
        col = parsed["col"]
        return [r1, col], {}, {}, None, col

    filas_ant, filas_desp, fila_pivote = _determinar_filas_objetivo(kind, r1, r2)
    if not filas_ant or fila_pivote is None:
        return None, {}, {}, None, col_pivote_actual

    filas_antes, rango_columnas = extraer_filas(filas_previas, filas_ant, col_pivote_actual)
    filas_despues, _ = extraer_filas(filas_actuales, filas_desp, col_pivote_actual)
    return [fila_pivote, col_pivote_actual], filas_antes, filas_despues, rango_columnas, col_pivote_actual


def _obtener_filas_matriz(matriz: Any) -> list[list]:
    """Extrae las filas de una matriz como listas de valores."""
    columnas = getattr(matriz, "columnas", getattr(matriz, "cols", 0))
    filas = getattr(matriz, "filas", getattr(matriz, "rows", 0))
    return [
        [matriz.obtener(r, c) if hasattr(matriz, "obtener") else matriz.get(r, c) for c in range(columnas)]
        for r in range(filas)
    ]


def construir_metadatos_pasos(pasos_crudos: list[dict], matriz_inicial: Any = None) -> list[dict]:
    """Genera metadatos estructurados de pasos para renderizado y explicaciones."""
    meta = []
    total = len(pasos_crudos)
    col_pivote_actual = 0

    for i, paso in enumerate(pasos_crudos):
        desc = paso.get("description", paso.get("descripcion", ""))
        mat = paso.get("matrix", paso.get("matriz"))
        filas_actuales = _obtener_filas_matriz(mat) if mat else []
        parsed = clasificar_paso(desc)
        kind = parsed["kind"]

        if i > 0:
            mat_previa = pasos_crudos[i - 1].get("matrix", pasos_crudos[i - 1].get("matriz"))
        else:
            mat_previa = matriz_inicial if matriz_inicial is not None else mat
        filas_previas = _obtener_filas_matriz(mat_previa) if mat_previa else filas_actuales

        pivote, antes, despues, columnas_rango, col_pivote_actual = _extraer_detalles_paso(
            kind, parsed, col_pivote_actual, filas_previas, filas_actuales
        )
        meta.append({
            "index": i + 1,
            "total": total,
            "kind": kind,
            "op": desc,
            "pivot": pivote,
            "rows_before": antes,
            "rows_after": despues,
            "cols": list(columnas_rango) if columnas_rango else None,
        })
    return meta
