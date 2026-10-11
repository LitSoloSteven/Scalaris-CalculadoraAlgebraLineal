"""Controlador para la visualización geométrica de sistemas de rectas y planos."""
import json
import logging
from typing import Any

from src.backend.geometria.clasificacion import (
    clasificar_ecuacion,
    detectar_paralelismo,
)
from src.backend.geometria.conjunto_solucion import (
    construir_conjunto_desde_gauss,
    construir_conjunto_desde_parametros,
    obtener_parametros_solucion,
    validar_solucion_parametrica,
)
from src.backend.geometria.planos import calcular_geometria_plano
from src.backend.geometria.recorte import (
    calcular_rango_automatico,
    recortar_recta_a_caja,
)
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.resolutores.operaciones_vectores.formateadores import (
    formatear_expresion_lineal,
)
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.backend.utilidades.formateadores import formatear_fraccion_str, numero_a_latex
from src.frontend.controladores.geometria.utilidades import (
    a_flotante_seguro,
    ubicar_error_celda,
)
from src.frontend.controladores.sistemas_lineales.compartido import (
    validar_y_construir_aumentada,
)
from src.frontend.controladores.utilidades import parsear_payload

logger = logging.getLogger(__name__)


def _recolectar_interceptos_fila(coeffs: list, bi: Any, n: int) -> list[float]:
    """Calcula los interceptos coordenados de una ecuacion para calcular el rango visual."""
    interceptos = []
    for j in range(n):
        if coeffs[j] != 0:
            val = a_flotante_seguro(bi / coeffs[j])
            if val is not None:
                interceptos.append(val)
    return interceptos


def _construir_ecuaciones(
    m: int, n: int, a_fracs: list, b_fracs: list
) -> tuple[list[dict] | None, list[float]]:
    """Genera la lista estructurada de ecuaciones y recolecta interceptos para el rango."""
    ecuaciones = []
    valores_rango = []
    nombres_vars = ["x", "y", "z"][:n]

    for i in range(m):
        coeffs, bi = a_fracs[i], b_fracs[i]
        kind = clasificar_ecuacion(coeffs, bi, n)
        c_floats = [a_flotante_seguro(c) for c in coeffs]
        b_float = a_flotante_seguro(bi)

        if any(cf is None for cf in c_floats) or b_float is None:
            return None, []

        lhs = formatear_expresion_lineal(coeffs, nombres_vars)
        rhs = numero_a_latex(bi)
        ecuaciones.append({
            "index": i,
            "kind": kind,
            "coeffs": c_floats,
            "coeffs_exact": [str(c) for c in coeffs],
            "b": b_float,
            "b_exact": str(bi),
            "latex": f"{lhs} = {rhs}",
        })
        valores_rango.extend(_recolectar_interceptos_fila(coeffs, bi, n))

    return ecuaciones, valores_rango


def _generar_descripcion_conjunto(n: int, dim: int, p_exact: list | None, d_exact: list) -> str:
    """Genera el texto pedagógico descriptivo para rectas y planos solución."""
    p_str = ", ".join(p_exact) if p_exact else ""
    if dim == 1:
        d_str = ", ".join(d_exact[0])
        return f"Las soluciones forman una recta que pasa por ({p_str}) con dirección ({d_str})."
    if dim == 2 and n == 3:
        d1_str = ", ".join(d_exact[0])
        d2_str = ", ".join(d_exact[1])
        return f"Las soluciones forman un plano que pasa por ({p_str}) generado por ({d1_str}) y ({d2_str})."
    return ""


def _recortar_recta_solucion(set_data: dict, n: int, h: float) -> None:
    """Calcula el segmento visible de una recta recortada a la caja cúbica."""
    d_f = set_data["directions"][0]
    p_f = set_data["point"]
    if not (all(v is not None for v in p_f) and all(v is not None for v in d_f)):
        return
    t_bounds = recortar_recta_a_caja(p_f, d_f, h)
    if not t_bounds:
        set_data["segment_visible"] = False
        return
    t0, t1 = t_bounds
    set_data["segment"] = [
        [p_f[i] + t0 * d_f[i] for i in range(n)],
        [p_f[i] + t1 * d_f[i] for i in range(n)],
    ]
    set_data["segment_visible"] = True


def _calcular_plano_solucion(set_data: dict, sp: dict) -> None:
    """Calcula los coeficientes y vectores normales del plano solución en R3."""
    (nx, ny, nz), offset = calcular_geometria_plano(sp["directions"], sp["particular"])
    set_data["normal_exact"] = [str(nx), str(ny), str(nz)]
    set_data["offset_exact"] = str(offset)
    n_floats = [a_flotante_seguro(nx), a_flotante_seguro(ny), a_flotante_seguro(nz)]
    off_float = a_flotante_seguro(offset)
    if all(v is not None for v in n_floats) and off_float is not None:
        set_data["normal"] = n_floats
        set_data["offset"] = off_float


def _recortar_geometria_solucion(set_data: dict, sol_set: Any, sp: dict | None, n: int, h: float) -> None:
    """Calcula el segmento recortado a la caja o los parámetros analíticos del plano."""
    if set_data.get("whole_space"):
        return
    if sol_set.dimension == 1:
        _recortar_recta_solucion(set_data, n, h)
    elif sol_set.dimension == 2 and n == 3 and sp:
        _calcular_plano_solucion(set_data, sp)


def _construir_set_data(sol_set: Any, sp: dict | None, n: int, h: float) -> dict | None:
    """Construye el payload del conjunto solución con puntos, direcciones y recorte."""
    if sol_set is None:
        return None

    pt_floats = [a_flotante_seguro(p) for p in sol_set.point] if sol_set.point else None
    pt_exact = [str(p) for p in sol_set.point] if sol_set.point else None
    pt_latex = matriz_a_latex(Matriz(n, 1, [[x] for x in sol_set.point])) if sol_set.point else None
    es_todo_espacio = sol_set.dimension == n

    set_data = {
        "kind": sol_set.kind.value,
        "kind_label": "whole_space" if es_todo_espacio else sol_set.kind.value,
        "dimension": sol_set.dimension,
        "whole_space": es_todo_espacio,
        "point": pt_floats,
        "point_exact": pt_exact,
        "point_latex": pt_latex,
    }

    if sp:
        set_data["directions"] = [[a_flotante_seguro(v) for v in d] for d in sp["directions"]]
        set_data["directions_exact"] = [[str(v) for v in d] for d in sp["directions"]]
        set_data["param_names"] = sp["param_names"]
        set_data["free_vars"] = [["x", "y", "z"][c] for c in sp["free_cols"]]

        partes = [matriz_a_latex(Matriz(n, 1, [[x] for x in sp["particular"]]))]
        for i, d in enumerate(sp["directions"]):
            d_latex = matriz_a_latex(Matriz(n, 1, [[x] for x in d]))
            partes.append(f"{sp['param_names'][i]}{d_latex}")
        set_data["param_latex"] = r"\mathbf{x} = " + " + ".join(partes)
        set_data["description"] = _generar_descripcion_conjunto(n, sol_set.dimension, pt_exact, set_data["directions_exact"])
        _recortar_geometria_solucion(set_data, sol_set, sp, n, h)

    return set_data


def _validar_entrada_sistema(
    payload_json: str,
) -> tuple[Matriz | None, list | None, list | None, int, int, dict | None]:
    """Valida el payload y la dimensión del sistema devolviendo error o matrices preparadas."""
    datos, err = parsear_payload(payload_json)
    if err:
        msj = json.loads(err).get("message", "Payload inválido.")
        return None, None, None, 0, 0, {"status": "ERROR", "message": msj, "error_cell": None}

    mat_aug, a_fracs, b_fracs, m, n, err_json = validar_y_construir_aumentada(datos or {})
    if err_json or a_fracs is None or b_fracs is None or mat_aug is None:
        msj = json.loads(err_json).get("message", "") if err_json else ""
        celda_err = ubicar_error_celda((datos or {}).get("matrix_A", []), (datos or {}).get("vector_b", []))
        return None, None, None, 0, 0, {"status": "ERROR", "message": msj, "error_cell": celda_err}

    if n not in (2, 3):
        msj = f"Este visualizador solo grafica sistemas con 2 o 3 variables (el tuyo tiene {n}). Puedes resolverlo en Sistemas de ecuaciones."
        return None, None, None, 0, 0, {"status": "ERROR", "code": "bad_dimension", "message": msj, "error_cell": None, "n": n}

    return mat_aug, a_fracs, b_fracs, m, n, None


def _resolver_y_obtener_solucion(
    mat_aug: Matriz, a_fracs: list, b_fracs: list
) -> tuple[str, Any, dict | None, bool]:
    """Ejecuta Gauss y estructura el conjunto solución si es compatible o indeterminado."""
    resolutor = ResolutorGauss(mat_aug)
    resultado = resolutor.resolver()
    estado_sol = resultado.get("status") or resultado.get("estado")
    sol_set = construir_conjunto_desde_gauss(resultado)
    sp, pendiente_param = None, False
    if estado_sol in ("INFINITE_SOLUTIONS", "SOLUCIONES_INFINITAS"):
        sp = obtener_parametros_solucion(resultado)
        if sp and validar_solucion_parametrica(a_fracs, b_fracs, sp["particular"], sp["directions"]):
            sol_set = construir_conjunto_desde_parametros(sp)
        else:
            pendiente_param, sol_set, sp = True, None, None
    return estado_sol, sol_set, sp, pendiente_param


def _determinar_banderas(n: int, estado_sol: str, a_fracs: list, b_fracs: list) -> list[str]:
    """Evalúa condiciones geométricas especiales como paralelismo estricto en R2."""
    if n == 2 and estado_sol in ("NO_SOLUTION", "SIN_SOLUCION") and detectar_paralelismo(a_fracs, b_fracs):
        return ["parallel"]
    return []


def _acumular_puntos_solucion(sol_set: Any, rango_valores: list[float]) -> None:
    """Añade las coordenadas del punto solución para ajustar el rango de los ejes."""
    if sol_set and sol_set.point:
        for p in sol_set.point:
            pf = a_flotante_seguro(p)
            if pf is not None:
                rango_valores.append(pf)


def procesar_rectas_planos(payload_json: str) -> dict:
    """Procesa un sistema Ax = b para su visualización geométrica interactiva."""
    mat_aug, a_fracs, b_fracs, m, n, error_resp = _validar_entrada_sistema(payload_json)
    if error_resp:
        return error_resp

    ecuaciones, rango_valores = _construir_ecuaciones(m, n, a_fracs, b_fracs)
    if ecuaciones is None:
        msj = "Algún valor es demasiado grande para graficarlo. Usa números más pequeños."
        return {"status": "ERROR", "code": "not_finite", "message": msj, "error_cell": None, "n": n}

    estado_sol, sol_set, sp, pendiente_param = _resolver_y_obtener_solucion(mat_aug, a_fracs, b_fracs)
    _acumular_puntos_solucion(sol_set, rango_valores)

    rango_eje = calcular_rango_automatico([v for v in rango_valores if v is not None])
    set_data = _construir_set_data(sol_set, sp, n, rango_eje[1])
    banderas = _determinar_banderas(n, estado_sol, a_fracs, b_fracs)
    fuera_de_rango = any(abs(v) > rango_eje[1] for v in rango_valores if v is not None)

    return {
        "status": "OK",
        "n": n,
        "m": m,
        "equations": ecuaciones,
        "solution_status": estado_sol,
        "set": set_data,
        "pending_param": pendiente_param,
        "flags": banderas,
        "range": rango_eje,
        "out_of_range": fuera_de_rango,
        "error_cell": None,
        "message": "",
    }
