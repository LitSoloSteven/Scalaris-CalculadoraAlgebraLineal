"""Flujo de ejecución común para controladores de Gauss y Gauss-Jordan."""
import json
from typing import Any

from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.controladores.agrupador_pasos import agrupar_pasos_eliminacion
from src.backend.resolutores.sistemas_lineales.captura import validar_y_construir_aumentada
from src.frontend.controladores.sistemas_lineales.compartido import (
    construir_metadatos_pasos,
)
from src.frontend.controladores.utilidades import (
    construir_vista_pasos,
    parsear_carga_json,
)


def _verificar_solucion_si_aplica(
    resultado: dict, a_fracciones: list, b_fracciones: list
) -> tuple[Any, list]:
    """Genera pasos de comprobación en LaTeX si el sistema tiene solución única."""
    solucion = resultado.get("solucion")
    estado = resultado.get("estado")
    if solucion and estado == "SOLUCION_UNICA":
        _, pasos_verificacion = ValidadorMatriz.verificar_solucion(
            a_fracciones, solucion, b_fracciones, como_latex=True
        )
        return solucion, pasos_verificacion
    return solucion, []


def _construir_respuesta_carga(
    resultado: dict,
    metodo: str,
    numero_variables: int,
    variables: list | None,
    detalles: tuple[list, list, list, list, dict],
) -> dict:
    """Ensambla el diccionario de respuesta para la vista."""
    pasos_latex, metadatos_pasos, comprobacion, vista_pasos, (grupos, estadisticas) = detalles
    solucion = resultado.get("solucion")
    mensaje = resultado.get("mensaje") or ""
    lista_variables = variables if variables is not None else [f"x{i+1}" for i in range(numero_variables)]

    if solucion:
        sol_salida = [str(valor_solucion) for valor_solucion in solucion]
    else:
        sol_salida = None if metodo == "gauss" else []

    return {
        "estado": resultado.get("estado"),
        "clasificacion": mensaje,
        "mensaje": mensaje,
        "solucion": sol_salida,
        "parametros_solucion": resultado.get("parametros_solucion"),
        "analisis_sistema": resultado.get("analisis_sistema"),
        "pasos_intermedios_latex": pasos_latex,
        "metadatos_pasos": metadatos_pasos,
        "pasos_sustitucion_regresiva": resultado.get("pasos_sustitucion_regresiva", []),
        "pasos_verificacion_latex": comprobacion,
        "variables": lista_variables,
        "numero_variables": numero_variables,
        "vista_pasos": vista_pasos,
        "grupos": grupos,
        "estadisticas": estadisticas,
    }


def ejecutar_flujo_sistema(
    carga_json: str,
    resolutor_cls: type,
    metodo: str,
) -> str:
    """Orquesta la validación, ejecución del resolutor y estructuración pedagógica."""
    datos, error = parsear_carga_json(
        carga_json,
        "La carga debe ser un objeto JSON con 'matriz_a' y 'vector_b'. Revisa esos campos.",
    )
    if error:
        return error

    matriz, a_fracs, b_fracs, _m, numero_variables, error = validar_y_construir_aumentada(datos)
    if error or matriz is None or a_fracs is None or b_fracs is None:
        return error or "{}"

    variables = datos.get("variables")
    resolutor = resolutor_cls(matriz, nombres_variables=variables)
    resultado = resolutor.resolver()

    pasos_crudos = resultado.get("pasos") or []
    metadatos_pasos = construir_metadatos_pasos(pasos_crudos)
    pasos_latex = [
        {"descripcion": paso["descripcion"], "matriz": matriz_a_latex(paso["matriz"])}
        for paso in pasos_crudos
    ]

    _sol, comprobacion = _verificar_solucion_si_aplica(resultado, a_fracs, b_fracs)

    pasos, grupos, estadisticas = agrupar_pasos_eliminacion(
        pasos_crudos, numero_variables, resultado.get("estado"), contexto="sistema", metodo=metodo
    )
    vista_pasos = construir_vista_pasos(pasos)

    detalles = (pasos_latex, metadatos_pasos, comprobacion, vista_pasos, (grupos, estadisticas))
    respuesta = _construir_respuesta_carga(resultado, metodo, numero_variables, variables, detalles)

    return json.dumps(respuesta, ensure_ascii=False, default=str)
