"""Clasifica respuestas y fallos HTTP de OpenRouter para reintentar, usar reserva o terminar."""

from dataclasses import dataclass
import logging
import requests

from src.ai.constantes import (
    CODIGOS_ESTADO_TRANSITORIOS,
    TIEMPO_RESTANTE_MINIMO_PARA_REINTENTO,
)

from src.ai.respuestas import ResultadoIA, TipoErrorIA
from src.ai.textos import ERROR_SERVICIO, RESPUESTA_DEMASIADO_EXTENSA
from src.ai.presupuesto_mensajes import validar_longitud_mensaje

registro = logging.getLogger(__name__)


def procesar_respuesta_exitosa(
    respuesta: requests.Response, modelo: str
) -> ResultadoIA:
    """Parsea el JSON de una respuesta HTTP 200 y extrae el texto generado."""
    try:
        datos = respuesta.json()
        opciones = datos.get("choices") or []
        contenido = (
            (opciones[0].get("message") or {}).get("content")
            if opciones
            else None
        )
        if contenido is not None and not isinstance(contenido, str):
            return ResultadoIA(False, ERROR_SERVICIO, TipoErrorIA.SERVICIO)
        if contenido:
            try:
                validar_longitud_mensaje(contenido)
            except ValueError:
                return ResultadoIA(False, RESPUESTA_DEMASIADO_EXTENSA, TipoErrorIA.SERVICIO)
            return ResultadoIA(True, contenido, modelo=modelo)
        registro.error("Respuesta de IA vacía con estado 200. Modelo: %s", modelo)
        return ResultadoIA(
            False,
            "Glosa no devolvió una respuesta. Reformula la pregunta o inténtalo de nuevo.",
            TipoErrorIA.VACIO,
        )
    except Exception:
        registro.error("La respuesta de IA no contiene un JSON válido")
        return ResultadoIA(False, ERROR_SERVICIO, TipoErrorIA.SERVICIO)


@dataclass
class ContextoIntento:
    """Metadatos de la iteración actual en la cascada de llamadas a modelos."""

    intento: int
    indice_modelo: int
    tiempo_restante: float
    total_modelos: int


def _puede_reintentar(contexto: ContextoIntento) -> bool:
    return (
        contexto.intento == 0
        and contexto.indice_modelo == 0
        and contexto.tiempo_restante > TIEMPO_RESTANTE_MINIMO_PARA_REINTENTO
    )


def _manejar_limite_tasa(
    contexto: ContextoIntento,
) -> tuple[ResultadoIA | None, str]:
    """Determina si el límite permite reintentar, usar la reserva o terminar."""
    if _puede_reintentar(contexto):
        return None, "reintentar"
    if contexto.indice_modelo == 0 and contexto.total_modelos > 1:
        return None, "reserva"
    resultado = ResultadoIA(
        False,
        "Glosa está recibiendo muchas consultas ahora. Espera unos segundos y vuelve a intentarlo.",
        TipoErrorIA.LIMITE_PETICIONES,
    )
    return resultado, "terminar"


def clasificar_error_http(
    codigo: int, modelo: str, contexto: ContextoIntento,
) -> tuple[ResultadoIA | None, str]:
    """Clasifica el estado HTTP en reintento, reserva o resultado definitivo."""
    if codigo in (401, 403):
        registro.error("Error de autenticación con OpenRouter: estado %s", codigo)
        resultado = ResultadoIA(
            False,
            "Glosa no pudo autenticarse con el servicio de IA. Avisa a quien administra Scalaris.",
            TipoErrorIA.AUTENTICACION,
        )
        return resultado, "terminar"

    if codigo == 429:
        registro.warning("Límite de tasa en %s", modelo)
        return _manejar_limite_tasa(contexto)

    if codigo in CODIGOS_ESTADO_TRANSITORIOS:
        registro.warning("Error transitorio de OpenRouter: estado %s", codigo)
        if _puede_reintentar(contexto):
            return None, "reintentar"
        return None, "reserva"

    registro.error("Error no manejado de OpenRouter: estado %s", codigo)
    return None, "reserva"


def clasificar_excepcion_red(
    error: Exception, modelo: str, indice_modelo: int, total_modelos: int,
) -> tuple[ResultadoIA | None, bool]:
    """Clasifica fallos de transporte sin copiar detalles privados al registro."""
    if isinstance(error, requests.exceptions.Timeout):
        registro.warning("Tiempo de espera agotado al contactar %s", modelo)
        if indice_modelo == 0 and total_modelos > 1:
            return None, False
        mensaje = "Glosa tardó demasiado en responder. Vuelve a intentarlo en unos segundos."
        return ResultadoIA(False, mensaje, TipoErrorIA.TIEMPO_AGOTADO), True
    if isinstance(error, requests.exceptions.ConnectionError):
        registro.error("Error de conexión al contactar %s", modelo)
        mensaje = "No hay conexión con el servicio de IA. Revisa tu red y vuelve a intentarlo."
        return ResultadoIA(False, mensaje, TipoErrorIA.RED), True
    registro.error("Fallo de red no clasificado al contactar el servicio de IA")
    return None, False
