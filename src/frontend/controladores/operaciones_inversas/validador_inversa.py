"""Validación y formateo de comprobaciones formales para cálculo de inversa."""
from fractions import Fraction
from typing import Any

from src.backend.constantes import (
    DIMENSION_MAXIMA_INVERSA,
    DIMENSION_MAXIMA_LATEX_INVERSA,
)
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.utilidades.formateadores import formatear_fraccion_str
from src.backend.utilidades.validadores import ValidadorMatriz


def construir_resultado_vacio(
    estado: str,
    mensaje: str,
    *,
    n: int = 0,
    tiempo_s: float = 0.0,
    determinante: Fraction | None = None,
    matriz_a: Matriz | None = None,
    error_cell: list[int] | None = None,
) -> dict:
    """Construye un resultado vacío homogéneo para errores y matrices singulares."""
    latex_a = (
        matriz_a_latex(matriz_a)
        if (matriz_a is not None and n <= DIMENSION_MAXIMA_LATEX_INVERSA)
        else None
    )
    return {
        "status": estado,
        "message": mensaje,
        "n": n,
        "elapsed_s": round(tiempo_s, 4),
        "determinant": determinante,
        "determinant_str": formatear_fraccion_str(determinante) if determinante is not None else None,
        "matrix_a": matriz_a,
        "matrix_a_latex": latex_a,
        "inverse": None,
        "inverse_latex": None,
        "steps": [],
        "groups": [],
        "stats": {
            "total": 0,
            "pivotes": 0,
            "intercambios": 0,
            "eliminaciones": 0,
            "normalizaciones": 0,
        },
        "verifications": [],
        "error_cell": error_cell,
    }


def _parsear_celdas_inversa(datos: list, n: int) -> tuple[list[list[Fraction]] | None, list[int] | None, str | None]:
    """Parsea cada celda a fracción exacta y reporta coordenadas del primer fallo."""
    matriz_parseada = []
    for i in range(n):
        fila = datos[i]
        if not isinstance(fila, list) or len(fila) != n:
            return None, None, f"La fila {i + 1} debe contener {n} columnas."
        fila_parseada = []
        for j in range(n):
            texto = str(fila[j]).strip() if fila[j] is not None and str(fila[j]).strip() else "0"
            ok, val, err_msg = ValidadorMatriz.parsear_numero_exacto(texto)
            if not ok:
                return None, [i, j], f"Error en A[{i + 1},{j + 1}]: {err_msg}"
            fila_parseada.append(val)
        matriz_parseada.append(fila_parseada)
    return matriz_parseada, None, None


def validar_y_parsear_matriz_cuadrada(datos_crudos: dict) -> tuple[Matriz | None, int, dict | None]:
    """Valida dimensión, estructura y contenido numérico de la matriz cuadrada."""
    n = datos_crudos.get("n")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1 or n > DIMENSION_MAXIMA_INVERSA:
        dim = n if (isinstance(n, int) and not isinstance(n, bool)) else 0
        msj = f"La dimensión n debe ser un entero entre 1 y {DIMENSION_MAXIMA_INVERSA}."
        return None, dim, construir_resultado_vacio("ERROR", msj, n=dim)

    datos = datos_crudos.get("data")
    if not isinstance(datos, list) or len(datos) != n:
        return None, n, construir_resultado_vacio("ERROR", f"Se esperaban {n} filas en la matriz.", n=n)

    matriz_parseada, celda_err, msj_err = _parsear_celdas_inversa(datos, n)
    if msj_err is not None:
        return None, n, construir_resultado_vacio("ERROR", msj_err, n=n, error_cell=celda_err)

    matriz_a = Matriz(n, n, matriz_parseada)
    return matriz_a, n, None


def extraer_comprobaciones_inversa(resultado: dict, n: int) -> list[dict]:
    """Extrae las tres propiedades de verificación formal para matrices invertibles."""
    verificaciones = []
    paso_der = resultado.get("verification_step")
    if paso_der:
        latex_der = paso_der.get("detail_latex") if n <= DIMENSION_MAXIMA_LATEX_INVERSA else None
        verificaciones.append({"key": "right", "title": "A · A⁻¹ = I", "coincide": bool(paso_der.get("coincide")), "detail_latex": latex_der})

    paso_izq = resultado.get("verification_reverse_step")
    if paso_izq:
        latex_izq = paso_izq.get("detail_latex") if n <= DIMENSION_MAXIMA_LATEX_INVERSA else None
        verificaciones.append({"key": "left", "title": "A⁻¹ · A = I", "coincide": bool(paso_izq.get("coincide")), "detail_latex": latex_izq})

    paso_trans = resultado.get("transpose_property_step")
    if paso_trans:
        latex_trans = paso_trans.get("detail_latex") if n <= DIMENSION_MAXIMA_LATEX_INVERSA else None
        verificaciones.append({"key": "transpose", "title": "(Aᵀ)⁻¹ = (A⁻¹)ᵀ", "coincide": bool(paso_trans.get("coincide")), "detail_latex": latex_trans})

    return verificaciones
