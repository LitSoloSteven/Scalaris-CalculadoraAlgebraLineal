"""Condición y cumplimiento publicados por la ejecución ampliada."""
from src.frontend.controladores.biseccion.catalogo_criterios import CRITERIOS, condicion_criterio
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada
from src.frontend.controladores.formato_numerico_raices import numero
from .presentacion import metricas_resumen, titulo_estado

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


def datos_criterio(ampliado: dict) -> tuple[tuple[str, str], ...]:
    """Presenta condición, unidad, umbral y métrica de la autoridad de ejecución."""
    criterio = ampliado["criterio"]
    tipo = criterio["tipo"]
    unidad = CriterioParada(**criterio).unidad
    metrica = ampliado["metrica_final"]
    return (("Criterio aplicado", CRITERIOS[tipo][0]),
            ("Condición", condicion_criterio(tipo, criterio["parametro"])),
            ("Unidad de la métrica", unidad), ("Umbral", numero(ampliado["umbral"], True)),
            ("Métrica final", "No aplica: sin dato evaluable en esta fila." if metrica is None else numero(metrica, True)),
            ("Cumplimiento", _CUMPLIMIENTOS[ampliado["cumplimiento"]]))


def metricas_configuradas(respuesta: dict, ampliado: dict | None) -> tuple:
    """Sustituye la etiqueta de residuo por la condición aplicada sin mutar el sobre."""
    datos = metricas_resumen(respuesta)
    if ampliado is None:
        return datos
    return tuple(par for par in datos if par[0] != "Tolerancia de residuo") + datos_criterio(ampliado)


def descripcion_captura(captura: dict) -> str:
    """Describe el criterio guardado sin convertir los borradores de una captura histórica."""
    criterio = captura.get("criterio")
    if criterio is None:
        return f"tolerancia {captura['tolerancia']}"
    return condicion_criterio(criterio["tipo"], criterio["parametro"])
