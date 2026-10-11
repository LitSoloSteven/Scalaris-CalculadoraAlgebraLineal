"""Controlador para la visualización geométrica interactiva de pares de vectores."""
from fractions import Fraction
import json

from src.backend.geometria.recorte import calcular_rango_automatico
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.controladores.geometria.utilidades import (
    a_flotante_seguro,
    ubicar_error_vector,
)
from src.frontend.controladores.utilidades import parsear_payload


def _parsear_vectores_entrada(vectores_crudos: list) -> tuple[list[list[Fraction]] | None, dict | None]:
    """Valida y parsea las componentes de los dos vectores de entrada."""
    nombres = ["u", "v"]
    vectores_parseados = []

    for vi, vec_data in enumerate(vectores_crudos):
        raw = vec_data if isinstance(vec_data, list) else vec_data.get("data", [])
        if not isinstance(raw, list):
            return None, {"status": "ERROR", "message": "Datos de vector inválidos.", "error_cell": None}
        componentes = []
        for ci, celda in enumerate(raw):
            texto = str(celda).strip() if celda is not None else "0"
            ok, val, msg = ValidadorMatriz.parsear_numero_exacto(texto or "0")
            if not ok:
                celda_err = {"kind": "vec", "name": nombres[vi], "index": ci}
                return None, {"status": "ERROR", "message": f"Error en {nombres[vi]}[{ci + 1}]: {msg}", "error_cell": celda_err}
            componentes.append(val)
        vectores_parseados.append(componentes)

    return vectores_parseados, None


def _generar_cuadros_y_rango(
    u_frac: list[Fraction], v_frac: list[Fraction], estaticos: list[float]
) -> tuple[list[dict], list[float]]:
    """Calcula los 25 fotogramas de la combinación ku + v para k en [-3, 3]."""
    cuadros = []
    todos_los_valores = list(estaticos)

    for j in range(-12, 13):
        k_frac = Fraction(j, 4)
        ku = [a_flotante_seguro(k_frac * c) for c in u_frac]
        ku_plus_v = [a_flotante_seguro(k_frac * a + b) for a, b in zip(u_frac, v_frac)]
        cuadros.append({
            "k": float(k_frac),
            "k_exact": str(k_frac),
            "ku": ku,
            "ku_plus_v": ku_plus_v,
        })
        todos_los_valores.extend([x for x in ku if x is not None])
        todos_los_valores.extend([x for x in ku_plus_v if x is not None])

    return cuadros, todos_los_valores


def _validar_y_extraer_par_vectores(
    payload_json: str,
) -> tuple[list | None, list | None, int, dict | None]:
    """Valida el payload y la dimensión de los dos vectores devolviendo error o fracciones."""
    datos, err = parsear_payload(payload_json)
    if err:
        return None, None, 0, {"status": "ERROR", "message": json.loads(err).get("message", ""), "error_cell": None}

    vectores_raw = (datos or {}).get("vectors", [])
    if not isinstance(vectores_raw, list) or len(vectores_raw) != 2:
        return None, None, 0, {"status": "ERROR", "message": "Se necesitan exactamente 2 vectores.", "error_cell": None}

    vectores, err_dict = _parsear_vectores_entrada(vectores_raw)
    if err_dict or vectores is None:
        return None, None, 0, err_dict or {}

    n = len(vectores[0])
    if n != len(vectores[1]):
        return None, None, 0, {"status": "ERROR", "message": "Los vectores deben tener la misma dimensión.", "error_cell": None}
    if n not in (2, 3):
        msj = f"Solo se grafican vectores de dimensión 2 o 3 (los tuyos tienen {n})."
        return None, None, 0, {"status": "ERROR", "code": "bad_dimension", "message": msj, "error_cell": None}

    return vectores[0], vectores[1], n, None


def procesar_vectores(payload_json: str) -> dict:
    """Procesa dos vectores u y v generando los estados estáticos y de animación."""
    u_frac, v_frac, n, err_resp = _validar_y_extraer_par_vectores(payload_json)
    if err_resp or u_frac is None or v_frac is None:
        return err_resp or {}

    u_float = [a_flotante_seguro(c) for c in u_frac]
    v_float = [a_flotante_seguro(c) for c in v_frac]
    u_plus_v = [a_flotante_seguro(a + b) for a, b in zip(u_frac, v_frac)]
    estaticos = u_float + v_float + u_plus_v

    if any(v is None for v in estaticos):
        return {"status": "ERROR", "code": "not_finite", "message": "Las coordenadas generan valores no finitos.", "error_cell": None}

    cuadros, todos_los_valores = _generar_cuadros_y_rango(u_frac, v_frac, estaticos)
    rango_eje = calcular_rango_automatico(todos_los_valores)
    fuera_de_rango = any(abs(v) > rango_eje[1] for v in todos_los_valores if v is not None)

    return {
        "status": "OK",
        "n": n,
        "u": {"float": u_float, "exact": [str(c) for c in u_frac]},
        "v": {"float": v_float, "exact": [str(c) for c in v_frac]},
        "static": {"u": u_float, "v": v_float, "u_plus_v": u_plus_v},
        "frames": cuadros,
        "default_frame": 16,
        "range": rango_eje,
        "out_of_range": fuera_de_rango,
        "error_cell": None,
        "message": "",
    }
