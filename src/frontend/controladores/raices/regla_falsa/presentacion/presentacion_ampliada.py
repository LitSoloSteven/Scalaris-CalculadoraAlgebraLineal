"""Condición y cumplimiento publicados por la ejecución ampliada."""
from src.frontend.controladores.raices.biseccion.captura.catalogo_criterios import CRITERIOS, condicion_criterio
from src.backend.resolutores.raices.biseccion.contratos.criterios_biseccion import CriterioParada
from src.frontend.controladores.raices.compartido.formato.formato_numerico_raices import numero
from src.frontend.controladores.raices.regla_falsa.presentacion.presentacion import etiqueta_aproximacion, metricas_resumen, titulo_estado

_CUMPLIMIENTOS = {"CUMPLIDO": "Condición cumplida", "NO_CUMPLIDO": "Condición no cumplida",
                  "CONTEO_COMPLETADO": "Conteo completado; no certifica precisión", "NO_APLICA": "No aplica"}
_TITULOS = {
    "criterio_ancho_cumplido": "Ancho posterior menor que el umbral",
    "criterio_decimales_cumplido": "Ancho posterior menor que el umbral decimal",
    "criterio_relativo_cumplido": "Cambio relativo menor que el porcentaje",
    "iteraciones_solicitadas_completadas": "Conteo solicitado completado; precisión no certificada",
}


def titulo_configurado(respuesta: dict, ampliado: dict | None) -> str:
    """Describe el cierre real sin anunciar conteo como precisión alcanzada."""
    if ampliado is None:
        return titulo_estado(respuesta)
    if respuesta["estado"] in ("ESTANCAMIENTO", "LIMITE_ITERACIONES"):
        return "Estancamiento numérico" if respuesta["estado"] == "ESTANCAMIENTO" else "Límite global de iteraciones"
    return _TITULOS.get(respuesta["motivo_parada"], titulo_estado(respuesta))


def datos_criterio(ampliado: dict, respuesta: dict | None = None) -> tuple[tuple[str, str], ...]:
    """Presenta condición, unidad, umbral y métrica de la autoridad de ejecución."""
    criterio = ampliado["criterio"]
    tipo = criterio["tipo"]
    unidad = CriterioParada(**criterio).unidad
    metrica = ampliado["metrica_final"]
    cumplimiento = _texto_cumplimiento(ampliado, respuesta)
    return (("Criterio aplicado", CRITERIOS[tipo][0]),
            ("Condición", condicion_criterio(tipo, criterio["parametro"])),
            ("Unidad de la métrica", unidad), ("Umbral", numero(ampliado["umbral"], True)),
            ("Métrica final", "No aplica: sin dato evaluable en esta fila." if metrica is None else numero(metrica, True)),
            ("Cumplimiento", cumplimiento))


def _texto_cumplimiento(ampliado: dict, respuesta: dict | None) -> str:
    if respuesta is not None and _es_cero_evaluado(respuesta):
        return "Raíz exacta evaluada (residuo 0)"
    return _CUMPLIMIENTOS[ampliado["cumplimiento"]]


def _es_cero_evaluado(respuesta: dict) -> bool:
    return respuesta.get("estado") == "EXITO" and respuesta.get("motivo_parada") in (
        "raiz_en_extremo", "raiz_en_aproximacion", "raiz_exacta",
    )


def metricas_configuradas(respuesta: dict, ampliado: dict | None) -> tuple:
    """Sustituye la etiqueta de residuo por la condición aplicada sin mutar el sobre."""
    datos = metricas_resumen(respuesta)
    if ampliado is None:
        return datos
    return tuple(par for par in datos if par[0] != "Tolerancia de residuo") + datos_criterio(ampliado, respuesta)


def descripcion_captura(captura: dict) -> str:
    """Describe el criterio guardado sin convertir los borradores de una captura histórica."""
    criterio = captura.get("criterio")
    if criterio is None:
        return f"tolerancia {captura['tolerancia']}"
    return condicion_criterio(criterio["tipo"], criterio["parametro"])


def etiqueta_configurada(respuesta: dict, ampliado: dict | None) -> str:
    """Distingue ausencia de valor y conteo provisional sin alterar el estado matemático."""
    if _es_cero_evaluado(respuesta):
        return etiqueta_aproximacion(respuesta)
    if respuesta.get("aproximacion") is not None and ampliado and ampliado["criterio"]["tipo"] == "iteraciones":
        return "Aproximación provisional"
    return etiqueta_aproximacion(respuesta)
