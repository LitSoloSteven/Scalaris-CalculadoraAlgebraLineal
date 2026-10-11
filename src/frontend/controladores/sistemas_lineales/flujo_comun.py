"""Flujo de ejecución común para controladores de Gauss y Gauss-Jordan."""
import json
from typing import Any

from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.controladores.agrupador_pasos import agrupar_pasos_eliminacion
from src.frontend.controladores.sistemas_lineales.compartido import (
    construir_metadatos_pasos,
    validar_y_construir_aumentada,
)
from src.frontend.controladores.utilidades import (
    construir_vista_pasos,
    parsear_payload,
)


def _verificar_solucion_si_aplica(
    resultado: dict, a_fracciones: list, b_fracciones: list
) -> tuple[Any, list]:
    """Genera pasos de comprobación en LaTeX si el sistema tiene solución única."""
    solucion = resultado.get("solution") or resultado.get("solucion")
    estado = resultado.get("status") or resultado.get("estado")
    if solucion and estado in ("UNIQUE_SOLUTION", "SOLUCION_UNICA"):
        _, pasos_verificacion = ValidadorMatriz.verificar_solucion(
            a_fracciones, solucion, b_fracciones, como_latex=True
        )
        return solucion, pasos_verificacion
    return solucion, []


def _construir_respuesta_payload(
    resultado: dict,
    metodo: str,
    n: int,
    variables: list | None,
    detalles: tuple[list, list, list, list, dict],
) -> dict:
    """Ensambla el diccionario de respuesta para la vista."""
    pasos_latex, metadatos_pasos, comprobacion, vista_pasos, (grupos, stats) = detalles
    solucion = resultado.get("solution") or resultado.get("solucion")
    mensaje = resultado.get("message") or resultado.get("mensaje") or ""
    vars_list = variables if variables is not None else [f"x{i+1}" for i in range(n)]

    if solucion:
        sol_salida = [str(x) for x in solucion]
    else:
        sol_salida = None if metodo == "gauss" else []

    return {
        "status": resultado.get("status") or resultado.get("estado"),
        "classification": mensaje,
        "message": mensaje,
        "solution": sol_salida,
        "solution_param": resultado.get("solution_param") or resultado.get("parametros_solucion"),
        "analisis_sistema": resultado.get("analisis_sistema"),
        "intermediate_steps_latex": pasos_latex,
        "steps_meta": metadatos_pasos,
        "back_substitution_steps": resultado.get("back_substitution_steps", []),
        "verification_steps_latex": comprobacion,
        "variables": vars_list,
        "n_vars": n,
        "steps_view": vista_pasos,
        "groups": grupos,
        "stats": stats,
    }


def ejecutar_flujo_sistema(
    payload_json: str,
    resolutor_cls: type,
    metodo: str,
) -> str:
    """Orquesta la validación, ejecución del resolutor y estructuración pedagógica."""
    datos, err = parsear_payload(
        payload_json,
        "El payload debe ser un objeto JSON con 'matrix_A' y 'vector_b'.",
    )
    if err:
        return err

    matriz, a_fracs, b_fracs, _m, n, err = validar_y_construir_aumentada(datos)
    if err or matriz is None or a_fracs is None or b_fracs is None:
        return err or "{}"

    variables = datos.get("variables")
    resolutor = resolutor_cls(matriz, nombres_variables=variables)
    resultado = resolutor.resolver()

    pasos_crudos = resultado.get("steps") or resultado.get("pasos") or []
    metadatos_pasos = construir_metadatos_pasos(pasos_crudos)
    pasos_latex = [
        {"descripcion": s["description"], "matriz": matriz_a_latex(s["matrix"])}
        for s in pasos_crudos
    ]

    _sol, comprobacion = _verificar_solucion_si_aplica(resultado, a_fracs, b_fracs)

    pasos, grupos, stats = agrupar_pasos_eliminacion(
        pasos_crudos, n, resultado.get("status"), contexto="sistema", metodo=metodo
    )
    vista_pasos = construir_vista_pasos(pasos)

    detalles = (pasos_latex, metadatos_pasos, comprobacion, vista_pasos, (grupos, stats))
    respuesta = _construir_respuesta_payload(resultado, metodo, n, variables, detalles)

    return json.dumps(respuesta, ensure_ascii=False, default=str)
