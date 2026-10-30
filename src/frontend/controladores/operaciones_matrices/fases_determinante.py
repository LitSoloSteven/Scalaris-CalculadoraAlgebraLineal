"""Fases del determinante según eventos y coordenadas de la traza original."""
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from src.frontend import textos
from src.frontend.controladores.agrupacion_trazas import agrupar_traza


def agrupar_determinante(resultado: dict) -> tuple[list[dict], tuple[int, ...]]:
    """Devuelve grupos y posiciones sin alterar pasos ni recalcular determinantes."""
    traza = resultado.get("traza", [])
    grupos, posiciones = agrupar_traza(traza, _identificar)
    for grupo in grupos:
        if grupo["tipo"] == "columna":
            _nombrar_columna(grupo, traza)
    return grupos, posiciones


def _identificar(paso: dict, indice: int) -> tuple:
    tipo = paso["tipo"]
    if tipo == "menor":
        columna = paso.get("menor", {}).get("columna", indice + 1)
        return (tipo, indice), textos.DETERMINANTES_MENOR.format(columna=columna), tipo
    if tipo == "final":
        titulo = textos.DETERMINANTES_DIAGONAL if "diagonal" in paso else textos.DETERMINANTES_FINAL
        return tipo, titulo, tipo
    if tipo in ("planteamiento", "inicial"):
        titulo = textos.DETERMINANTES_PLANTEAMIENTO if tipo == "planteamiento" else textos.DETERMINANTES_INICIAL
        return tipo, titulo, tipo
    columna = paso.get("operacion", {}).get("columna", 0)
    return ("columna", columna), str(columna + 1), "columna"


def _nombrar_columna(grupo: dict, traza: list[dict]) -> None:
    pasos = [traza[indice] for indice in grupo["indices_pasos"]]
    pivote = next((paso for paso in pasos if paso["tipo"] == "pivote"), pasos[0])
    operacion = pivote.get("operacion", {})
    intercambio = any(paso["tipo"] == "intercambio" for paso in pasos)
    grupo["titulo"] = textos.DETERMINANTES_COLUMNA.format(
        columna=operacion.get("columna", 0) + 1,
        valor=formatear_fraccion_texto(operacion.get("valor", 0)),
        intercambio=textos.DETERMINANTES_INTERCAMBIO if intercambio else "",
    )
