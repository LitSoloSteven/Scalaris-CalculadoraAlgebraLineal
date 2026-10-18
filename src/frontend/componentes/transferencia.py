"""Almacén temporal volátil para transferencias de datos entre herramientas."""
from __future__ import annotations

from dataclasses import dataclass
import secrets
import threading
import time
from typing import Any, Callable

from nicegui import ui

from src.backend.utilidades import transferencias
from src.frontend.constantes import MAXIMO_ENTRADAS_TRANSFERENCIA, TIEMPO_VIDA_TRANSFERENCIA_SEGUNDOS
from src.frontend.navegacion import herramienta_por_identificador

_ALMACEN: dict[str, tuple[float, dict[str, Any]]] = {}
_BLOQUEO = threading.Lock()


def _ahora() -> float:
    """Devuelve la marca temporal monotona actual."""
    return time.monotonic()


def _guardar_en_almacen(tipo: str, origen: str, datos: Any, **extra: Any) -> str:
    """Registra una carga de datos en el almacen volatil y purga entradas expiradas."""
    token = secrets.token_urlsafe(16)
    carga = {"version": 1, "tipo": tipo, "origen": origen, "datos": datos, **extra}
    with _BLOQUEO:
        ahora = _ahora()
        expiradas = [clave for clave, (marca_tiempo, _) in _ALMACEN.items() if ahora - marca_tiempo > TIEMPO_VIDA_TRANSFERENCIA_SEGUNDOS]
        for clave in expiradas:
            del _ALMACEN[clave]
        if len(_ALMACEN) >= MAXIMO_ENTRADAS_TRANSFERENCIA:
            mas_antigua = min(_ALMACEN.keys(), key=lambda clave: _ALMACEN[clave][0])
            del _ALMACEN[mas_antigua]
        _ALMACEN[token] = (ahora, carga)
    return token


def guardar_matriz(identificador_origen: str, datos: list[list[str]]) -> str:
    """Almacena una matriz A cuadrada o rectangular para transferirla a otra vista."""
    return _guardar_en_almacen("matriz_a", identificador_origen, datos)


def guardar_sistema(identificador_origen: str, coeficientes: list[list[str]], independientes: list[str]) -> str:
    """Almacena un sistema completo Ax = b para su visualizacion o resolucion."""
    return _guardar_en_almacen("sistema", identificador_origen, {"matriz_a": coeficientes, "vector_b": independientes})


def guardar_vectores(identificador_origen: str, escena: str, datos: list[list[str]]) -> str:
    """Almacena un conjunto de vectores y su escena destino."""
    return _guardar_en_almacen("vectores", identificador_origen, datos, escena=escena)


def url_transferencia(ruta: str, token: str) -> str:
    """Genera la URL con parametro de consulta para transferencia."""
    return f"{ruta}?handoff={token}"


def limpiar_url_transferencia() -> None:
    """Remueve el parametro handoff de la barra de direcciones del navegador."""
    codigo_cliente = (
        "(()=>{const direccion=new URL(location.href);direccion.searchParams.delete('handoff');"
        "history.replaceState(null,'',direccion.pathname+direccion.search+direccion.hash);})()"
    )
    ui.timer(0.2, lambda: ui.run_javascript(codigo_cliente), once=True)


@dataclass(frozen=True)
class ResultadoTransferencia:
    """Estructura inmutable que describe el resultado de consumir una transferencia."""

    estado: str
    datos: Any
    nombre_origen: str
    mensaje: str


def _extraer_entrada(token: str) -> tuple[dict[str, Any] | None, ResultadoTransferencia | None]:
    """Extrae la carga util verificando existencia y frescura temporal."""
    with _BLOQUEO:
        entrada = _ALMACEN.pop(token, None)
    if entrada is None:
        return None, ResultadoTransferencia(
            estado="ausente", datos=None, nombre_origen="",
            mensaje="No encontramos los datos que ibas a traer. Ya los usaste o el enlace es antiguo. Puedes capturarlos aquí.",
        )
    marca_tiempo, carga = entrada
    if _ahora() - marca_tiempo > TIEMPO_VIDA_TRANSFERENCIA_SEGUNDOS:
        return None, ResultadoTransferencia(
            estado="expirada", datos=None, nombre_origen="",
            mensaje="Los datos tardaron demasiado en llegar y expiraron. Vuelve a la herramienta de origen y repite la acción.",
        )
    return carga, None


def _obtener_nombre_origen(identificador_origen: Any) -> str:
    """Obtiene el nombre accesible de la herramienta origen."""
    try:
        return herramienta_por_identificador(str(identificador_origen)).nombre
    except KeyError:
        return "otra herramienta"


def _consumir_transferencia(
    token: str, validar_carga: Callable[[dict[str, Any]], tuple[Any, str | None]]
) -> ResultadoTransferencia | None:
    """Flujo parametrizado unico para extraer, validar y limpiar transferencias."""
    if not token:
        return None

    carga, resultado_fallido = _extraer_entrada(token)
    if resultado_fallido is not None:
        return resultado_fallido

    nombre_origen = _obtener_nombre_origen(carga.get("origen"))
    datos, mensaje_error = validar_carga(carga)
    if mensaje_error is not None:
        return ResultadoTransferencia(estado="invalida", datos=None, nombre_origen=nombre_origen, mensaje=mensaje_error)

    return ResultadoTransferencia(estado="exito", datos=datos, nombre_origen=nombre_origen, mensaje="")


def consumir_matriz(token: str, *, dimension_maxima: int) -> ResultadoTransferencia | None:
    """Extrae y valida una matriz transferida por token."""
    return _consumir_transferencia(token, lambda carga: transferencias.validar_carga_matriz(carga, dimension_maxima=dimension_maxima))


def consumir_sistema(token: str, *, maximo_ecuaciones: int, dimensiones_permitidas: set[int]) -> ResultadoTransferencia | None:
    """Extrae y valida un sistema lineal transferido por token."""
    return _consumir_transferencia(token, lambda carga: transferencias.validar_carga_sistema(carga, maximo_ecuaciones=maximo_ecuaciones, dimensiones_permitidas=dimensiones_permitidas))


def consumir_vectores(token: str, *, dimensiones_permitidas: set[int]) -> ResultadoTransferencia | None:
    """Extrae y valida una familia de vectores transferida por token."""
    return _consumir_transferencia(token, lambda carga: transferencias.validar_carga_vectores(carga, dimensiones_permitidas=dimensiones_permitidas))


def renderizar_aviso_transferencia(resultado: ResultadoTransferencia, mensaje_exito: str) -> None:
    """Muestra un aviso accesible de estado al recibir datos de transferencia."""
    if resultado.estado == "exito":
        with ui.row().classes("transferencia-aviso").props("role=status"):
            ui.icon("check_circle").classes("texto-acento")
            ui.label(mensaje_exito)
    else:
        with ui.row().classes("items-center gap-2 px-4 py-2 distintivo-advertencia w-fit").props("role=status"):
            ui.icon("warning_amber")
            ui.label(resultado.mensaje)
