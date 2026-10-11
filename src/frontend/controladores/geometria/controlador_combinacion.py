"""Controlador para la visualización geométrica interactiva de combinaciones lineales."""
from fractions import Fraction
import json
import logging
from typing import Any

from src.backend.excepciones import AlgebraLinealError
from src.backend.geometria.recorte import calcular_rango_automatico
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import (
    ResolutorCombinacionLineal,
)
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.controladores.geometria.utilidades import a_flotante_seguro
from src.frontend.controladores.operaciones_vectores.controlador_operaciones_vectores import (
    construir_vector_desde_dict,
)
from src.frontend.controladores.utilidades import parsear_payload

logger = logging.getLogger(__name__)


def _ubicar_celda_invalida_vector(nombre_vec: str, datos_vec: list) -> dict | None:
    """Busca el índice de la primera celda con contenido numérico no parseable."""
    for ci, celda in enumerate(datos_vec):
        ok, _, _ = ValidadorMatriz.parsear_numero_exacto(str(celda).strip() or "0")
        if not ok:
            return {"kind": "vec", "name": nombre_vec, "index": ci}
    return None


def _parsear_vector_b(b_raw: dict) -> tuple[Matriz | None, dict | None]:
    """Valida y parsea el vector objetivo b reportando la celda en caso de error."""
    try:
        return construir_vector_desde_dict(b_raw), None
    except ValueError as e:
        celda_err = _ubicar_celda_invalida_vector("b", b_raw.get("data", []))
        return None, {"status": "ERROR", "message": str(e), "error_cell": celda_err}


def _parsear_vectores_columnas(vectors_raw: list, n: int) -> tuple[list[Matriz] | None, dict | None]:
    """Valida y parsea los vectores generadores asegurando igual dimensión."""
    matrices_columnas = []
    vec_names = [f"v_{i+1}" for i in range(len(vectors_raw))]
    for vi, v_raw in enumerate(vectors_raw):
        try:
            v_mat = construir_vector_desde_dict(v_raw)
        except ValueError as e:
            celda_err = _ubicar_celda_invalida_vector(vec_names[vi], v_raw.get("data", []))
            return None, {"status": "ERROR", "message": str(e), "error_cell": celda_err}

        if v_mat.filas != n:
            msj = f"El vector {vec_names[vi]} tiene dimensión {v_mat.filas}, pero b tiene {n}."
            return None, {"status": "ERROR", "message": msj, "error_cell": None}
        matrices_columnas.append(v_mat)
    return matrices_columnas, None


def _construir_cadena_acumulada(resultado: dict, matrices_columnas: list[Matriz], n: int) -> tuple[list[dict], list[float]]:
    """Calcula los puntos parciales de la cadena vectorial c1*v1 + ... + ck*vk."""
    coeffs_exact = resultado.get("coeficientes") or []
    if not coeffs_exact:
        coeffs_str = resultado.get("coeficientes_str", [])
        coeffs_exact = []
        for cs in coeffs_str:
            ok, val, _ = ValidadorMatriz.parsear_numero_exacto(cs)
            coeffs_exact.append(val if ok else Fraction(0))

    cadena = []
    acumulado = [Fraction(0)] * n
    valores_rango = []

    for vi, c in enumerate(coeffs_exact):
        c_frac = Fraction(c) if not isinstance(c, Fraction) else c
        for dim in range(n):
            acumulado[dim] += c_frac * Fraction(matrices_columnas[vi].obtener(dim, 0))
        pt_floats = [a_flotante_seguro(x) for x in acumulado]
        cadena.append({
            "float": pt_floats,
            "exact": [str(x) for x in acumulado],
            "label": f"c_{vi+1}·v_{vi+1}" if vi == 0 else f"+ c_{vi+1}·v_{vi+1}",
        })
        valores_rango.extend([x for x in pt_floats if x is not None])

    return cadena, valores_rango


def _validar_lista_vectores_raw(vectors_raw: Any) -> str | None:
    """Verifica que la lista de vectores columna tenga entre 1 y 4 elementos."""
    if not isinstance(vectors_raw, list) or not (1 <= len(vectors_raw) <= 4):
        return "Se necesitan entre 1 y 4 vectores columna."
    return None


def _validar_entrada_combinacion(
    payload_json: str,
) -> tuple[Matriz | None, list[Matriz] | None, int, dict | None]:
    """Valida la entrada de vectores y dimensión para la combinación lineal."""
    datos, err = parsear_payload(payload_json)
    if err:
        return None, None, 0, {"status": "ERROR", "message": json.loads(err).get("message", ""), "error_cell": None}

    vectors_raw = (datos or {}).get("vectors", [])
    err_len = _validar_lista_vectores_raw(vectors_raw)
    if err_len:
        return None, None, 0, {"status": "ERROR", "message": err_len, "error_cell": None}

    b_mat, err_b = _parsear_vector_b((datos or {}).get("b", {}))
    if err_b or b_mat is None:
        return None, None, 0, err_b

    n = b_mat.filas
    if n not in (2, 3):
        return None, None, 0, {"status": "ERROR", "code": "bad_dimension", "message": f"Solo se grafican vectores de dimensión 2 o 3 (b tiene {n}).", "error_cell": None}

    matrices_columnas, err_columnas = _parsear_vectores_columnas(vectors_raw, n)
    if err_columnas:
        return None, None, 0, err_columnas

    return b_mat, matrices_columnas, n, None


def _evaluar_estado_solucion(
    sol_status: str,
    resultado: dict,
    matrices_columnas: list[Matriz],
    n: int,
) -> tuple[list[dict] | None, str | None, bool, list[float]]:
    """Genera la cadena vectorial o banderas de representación según compatibilidad."""
    if sol_status == "UNIQUE":
        cadena, extras = _construir_cadena_acumulada(resultado, matrices_columnas, n)
        return cadena, None, False, extras
    if sol_status == "INFINITE":
        return None, "non_unique", False, []
    if sol_status == "NO_SOLUTION":
        return None, None, True, []
    return None, None, False, []


def _extraer_coordenadas_flotantes(
    b_mat: Matriz, matrices_columnas: list[Matriz], n: int
) -> tuple[list[float | None], list[list[float | None]]]:
    """Convierte las componentes exactas de b y de las columnas a flotantes seguros."""
    b_float = [a_flotante_seguro(Fraction(b_mat.obtener(i, 0))) for i in range(n)]
    vecs_float = [[a_flotante_seguro(Fraction(v.obtener(i, 0))) for i in range(n)] for v in matrices_columnas]
    return b_float, vecs_float


def procesar_combinacion(payload_json: str) -> dict:
    """Procesa el vector objetivo y los vectores generadores para graficar la combinación."""
    b_mat, matrices_columnas, n, err_resp = _validar_entrada_combinacion(payload_json)
    if err_resp or b_mat is None or matrices_columnas is None:
        return err_resp or {}

    try:
        resolutor = ResolutorCombinacionLineal()
        resultado = resolutor.resolver(b_mat, matrices_columnas)
    except (AlgebraLinealError, ValueError) as e:
        return {"status": "ERROR", "message": str(e), "error_cell": None}

    sol_status = resultado.get("status", "ERROR")
    b_float, vecs_float = _extraer_coordenadas_flotantes(b_mat, matrices_columnas, n)
    if any(x is None for x in b_float) or any(any(x is None for x in vf) for vf in vecs_float):
        msj = "Algún valor es demasiado grande para graficarlo. Usa números más pequeños."
        return {"status": "ERROR", "code": "not_finite", "message": msj, "error_cell": None, "n": n}

    rango_valores = [v for v in b_float if v is not None] + [v for vf in vecs_float for v in vf if v is not None]
    cadena, repres, b_fuera, extras = _evaluar_estado_solucion(sol_status, resultado, matrices_columnas, n)
    rango_valores.extend(extras)

    rango_eje = calcular_rango_automatico(rango_valores)
    fuera_de_rango = any(abs(v) > rango_eje[1] for v in rango_valores if v is not None)

    return {
        "status": "OK",
        "n": n,
        "b": {"float": b_float, "exact": [str(b_mat.obtener(i, 0)) for i in range(n)]},
        "vectors": [{"float": vf, "exact": [str(matrices_columnas[idx].obtener(i, 0)) for i in range(n)]} for idx, vf in enumerate(vecs_float)],
        "chain": cadena,
        "representation": repres,
        "b_outside_span": b_fuera,
        "solution_status": sol_status,
        "range": rango_eje,
        "out_of_range": fuera_de_rango,
        "error_cell": None,
        "message": resultado.get("message", ""),
    }
