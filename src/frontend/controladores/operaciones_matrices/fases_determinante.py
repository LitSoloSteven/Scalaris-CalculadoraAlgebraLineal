"""Fases del determinante según eventos y coordenadas de la traza original."""
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from src.frontend import textos
from src.frontend.controladores.agrupacion_trazas import agrupar_traza


def agrupar_determinante(resultado: dict) -> tuple[list[dict], tuple[int, ...]]:
    """Devuelve grupos y posiciones sin alterar pasos ni recalcular determinantes."""
    traza = resultado.get("traza", [])
    grupos, posiciones = agrupar_traza(traza, lambda paso, indice: _identificar(paso, indice, traza))
    for grupo in grupos:
        if grupo["tipo"] == "columna":
            _nombrar_columna(grupo, traza)
    return grupos, posiciones


def _identificar(paso: dict, indice: int, traza: list[dict]) -> tuple:
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
    columna = columna_determinante(traza, indice)
    return ("columna", columna), str(columna + 1), "columna"


def columna_determinante(traza: list[dict], indice: int) -> int:
    """Relaciona intercambios sin columna explícita con el pivote siguiente de la traza."""
    paso = traza[indice]
    if paso["tipo"] == "intercambio":
        paso = next((siguiente for siguiente in traza[indice + 1:] if siguiente["tipo"] == "pivote"), paso)
    return paso.get("operacion", {}).get("columna", 0)


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
