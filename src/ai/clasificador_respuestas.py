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
from src.ai.presupuesto.presupuesto_mensajes import validar_longitud_mensaje

registro = logging.getLogger(__name__)


def procesar_respuesta_exitosa(
    respuesta: requests.Response, modelo: str
) -> ResultadoIA:
    """Parsea el JSON de una respuesta HTTP 200 y extrae el texto generado."""
    return _procesar_contenido(_leer_json(respuesta), modelo)


def _leer_json(respuesta: requests.Response) -> dict | None:
    try:
        datos = respuesta.json()
    except ValueError:
        return None
    return datos if isinstance(datos, dict) else None


def _primera_opcion(datos: dict) -> dict:
    opciones = datos.get("choices")
    if isinstance(opciones, list) and opciones and isinstance(opciones[0], dict):
        return opciones[0]
    return {}


def _procesar_contenido(datos: dict | None, modelo: str) -> ResultadoIA:
    if datos is None:
        registro.error("La respuesta de IA no contiene un JSON válido")
        return ResultadoIA(False, ERROR_SERVICIO, TipoErrorIA.SERVICIO)
    try:
        contenido = (_primera_opcion(datos).get("message") or {}).get("content")
        if contenido is not None and not isinstance(contenido, str):
            return ResultadoIA(False, ERROR_SERVICIO, TipoErrorIA.SERVICIO)
        if contenido and contenido.strip():
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
    except (AttributeError, IndexError, KeyError, TypeError):
        registro.error("La respuesta de IA tiene una estructura inesperada")
        return ResultadoIA(False, ERROR_SERVICIO, TipoErrorIA.SERVICIO)


@dataclass
class ContextoIntento:
    """Metadatos de la iteración actual en la cascada de llamadas a modelos."""

    intento: int
    indice_modelo: int
    tiempo_restante: float
    total_modelos: int


def clasificar_respuesta(
    respuesta: requests.Response, modelo: str, contexto: ContextoIntento,
) -> tuple[ResultadoIA | None, str]:
    """Distingue rechazos HTTP, errores dentro de HTTP 200 y texto aprovechable."""
    codigo = respuesta.status_code
    if codigo not in (200, 403):
        return clasificar_error_http(codigo, modelo, contexto)
    datos = _leer_json(respuesta)
    if codigo == 200:
        return _clasificar_generacion(datos, modelo, contexto)
    error = _extraer_error(datos or {}) or {}
    return clasificar_error_http(codigo, modelo, contexto, error.get("metadata"), error.get("message"))


def _clasificar_generacion(
    datos: dict | None, modelo: str, contexto: ContextoIntento,
) -> tuple[ResultadoIA | None, str]:
    finalizacion = _primera_opcion(datos or {}).get("finish_reason")
    if finalizacion == "content_filter":
        return clasificar_error_http(403, modelo, contexto)
    error = _extraer_error(datos or {})
    if error is not None:
        codigo = error.get("code")
        estado = codigo if type(codigo) is int and 400 <= codigo <= 599 else 502
        return clasificar_error_http(estado, modelo, contexto, error.get("metadata"), error.get("message"))
    if finalizacion == "error":
        return None, "reserva"
    resultado = _procesar_contenido(datos, modelo)
    return resultado, "exito" if resultado.exito else "reserva"


def _extraer_error(datos: dict) -> dict | None:
    error = datos.get("error")
    if isinstance(error, dict):
        return error
    error = _primera_opcion(datos).get("error")
    return error if isinstance(error, dict) else None


def _rechazo_del_proveedor(metadatos: object, mensaje: object) -> bool:
    datos = metadatos if isinstance(metadatos, dict) else {}
    if datos.keys() & {"limit_source", "patterns", "flagged_input", "reasons"}:
        return False
    tipo = datos.get("error_type")
    if tipo in ("content_policy_violation", "refusal"):
        return False
    if tipo in ("provider_unavailable", "not_found") or (
        tipo == "permission_denied" and bool(datos.get("provider_code"))
    ):
        return True
    texto = mensaje.casefold() if isinstance(mensaje, str) else ""
    return (
        "only available on agentic harnesses" in texto
        or "only available for use with agentic harnesses" in texto
    )


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
    if contexto.indice_modelo + 1 < contexto.total_modelos:
        return None, "reserva"
    resultado = ResultadoIA(
        False,
        "Glosa está recibiendo muchas consultas ahora. Espera unos segundos y vuelve a intentarlo.",
        TipoErrorIA.LIMITE_PETICIONES,
    )
    return resultado, "terminar"


def clasificar_error_http(
    codigo: int, modelo: str, contexto: ContextoIntento, metadatos: object = None,
    mensaje_proveedor: object = None,
) -> tuple[ResultadoIA | None, str]:
    """Clasifica el estado HTTP en reintento, reserva o resultado definitivo."""
    if codigo == 401:
        registro.error("Error de autenticación con OpenRouter: estado %s", codigo)
        resultado = ResultadoIA(
            False,
            "Glosa no pudo autenticarse con el servicio de IA. Avisa a quien administra Scalaris.",
            TipoErrorIA.AUTENTICACION,
        )
        return resultado, "terminar"

    if codigo in (402, 403):
        registro.warning("OpenRouter rechazó la consulta: estado %s", codigo)
        if codigo == 403 and _rechazo_del_proveedor(metadatos, mensaje_proveedor):
            return None, "reserva"
        return ResultadoIA(
            False, "El servicio de IA rechazó la consulta. Avisa a quien administra Scalaris.",
            TipoErrorIA.SERVICIO,
        ), "terminar"

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
        if indice_modelo + 1 < total_modelos:
            return None, False
        mensaje = "Glosa tardó demasiado en responder. Vuelve a intentarlo en unos segundos."
        return ResultadoIA(False, mensaje, TipoErrorIA.TIEMPO_AGOTADO), True
    if isinstance(error, requests.exceptions.ConnectionError):
        registro.error("Error de conexión al contactar %s", modelo)
        mensaje = "No hay conexión con el servicio de IA. Revisa tu red y vuelve a intentarlo."
        return ResultadoIA(False, mensaje, TipoErrorIA.RED), True
    registro.error("Fallo de red no clasificado al contactar el servicio de IA")
    return None, False
