"""Presentacion economica del balance de produccion calculado por Leontief."""
from src.backend.constantes import ERROR, EXITO, SIN_SOLUCION
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from .comprobacion_productos import crear_paso_analisis


def _conclusion_viabilidad(es_viable: bool, menores: list[dict]) -> str:
    if es_viable:
        return ("✓ Se satisface la condición de Hawkins-Simon: todos los menores "
                "principales de (I − C) son positivos. La economía puede producir "
                "cualquier vector de demanda final positivo.")
    fallidos = [menor["orden"] for menor in menores if not menor["es_positivo"]]
    return ("✗ No se satisface la condición de Hawkins-Simon: los menores de "
            f"orden {fallidos} no son positivos. El modelo puede ser inviable "
            "para ciertos vectores de demanda.")


def _presentar_menores(menores: list[tuple], viable: bool, aplicable: bool) -> dict:
    datos = [{"orden": orden, "determinante": formatear_fraccion_texto(valor), "es_positivo": positivo}
             for orden, valor, positivo in menores]
    conclusion = (_conclusion_viabilidad(viable, datos) if aplicable else
                  "Hay coeficientes tecnicos negativos. El criterio de Hawkins-Simon no certifica la viabilidad de este modelo; el balance algebraico se comprueba por separado.")
    return {"es_economicamente_viable": viable if aplicable else None, "menores_principales": datos,
            "criterio_aplicable": aplicable, "conclusion": conclusion}


def _presentar_sectores(calculo: dict, demanda: list, sectores: list[str]) -> list[dict]:
    return [{"sector": sector, "produccion_total": formatear_fraccion_texto(produccion),
             "demanda_final": formatear_fraccion_texto(demanda_sector),
             "consumo_intermedio": formatear_fraccion_texto(consumo),
             "valor_anadido": formatear_fraccion_texto(balance)}
            for sector, produccion, demanda_sector, consumo, balance in zip(
                sectores, calculo["produccion"], demanda, calculo["consumos"], calculo["balances"],
            )]


def presentar_leontief(calculo: dict, demanda: list, sectores: list[str]) -> dict:
    """Devuelve el contrato economico desde calculo exacto, demanda y etiquetas de sectores."""
    determinante, multiplicador = calculo["determinante"], calculo["multiplicador"]
    dimension = len(demanda)
    condicion = _presentar_menores(calculo["menores"], calculo["es_viable"], calculo["coeficientes_no_negativos"])
    if determinante == 0:
        return _presentar_balance_singular(calculo, sectores, condicion)
    if multiplicador is None:
        mensaje = f"La matriz es singular (rango {calculo['rango']} < {dimension}). No tiene inversa."
        return {"estado": ERROR, "mensaje": f"No se pudo invertir (I − C): {mensaje}."}
    return {
        "estado": EXITO, "mensaje": f"Modelo de Leontief resuelto correctamente ({dimension} sectores).",
        "traza_comprobacion": calculo["traza_comprobacion"],
        "numero_sectores": dimension, "nombres_sectores": sectores,
        "determinante_leontief": formatear_fraccion_texto(determinante),
        "matriz_leontief_latex": matriz_a_latex(calculo["matriz_leontief"]),
        "matriz_multiplicador_latex": matriz_a_latex(multiplicador),
        "matriz_identidad_latex": matriz_a_latex(calculo["identidad"]),
        "vector_produccion": [formatear_fraccion_texto(valor) for valor in calculo["produccion"]],
        "vector_demanda": [formatear_fraccion_texto(valor) for valor in demanda],
        "hawkins_simon": condicion, "analisis_sectorial": _presentar_sectores(calculo, demanda, sectores), "pasos": [],
    }


def _presentar_balance_singular(calculo: dict, sectores: list[str], condicion: dict) -> dict:
    """Presenta consistencia y parámetros sin afirmar que existe un multiplicador."""
    balance = calculo["balance_singular"]
    mensaje = ("El sistema de Leontief es singular y la demanda es incompatible: no hay solución."
               if balance["estado"] == SIN_SOLUCION else
               "El sistema de Leontief es singular y admite infinitas soluciones para esta demanda.")
    analisis = balance["analisis_sistema"]
    detalle = (rf"\operatorname{{rg}}(I-C)={analisis['rango_a']},\quad "
               rf"\operatorname{{rg}}([I-C\mid d])={analisis['rango_aumentada']}")
    traza = calculo["traza_comprobacion"] + [crear_paso_analisis(
        analisis["clasificacion_rouche"], detalle, analisis["explicacion_rouche"], "verificacion")]
    return {"estado": balance["estado"], "mensaje": mensaje,
            "numero_sectores": len(sectores), "nombres_sectores": sectores,
            "traza_comprobacion": traza,
            "determinante_leontief": formatear_fraccion_texto(calculo["determinante"]),
            "hawkins_simon": condicion, "pasos": balance["pasos"],
            "analisis_sistema": balance["analisis_sistema"],
            "parametros_solucion": balance["parametros_solucion"]}
