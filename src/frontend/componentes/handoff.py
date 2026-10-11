"""Almacen temporal volatil para transferencias de datos entre herramientas (handoff)."""
from __future__ import annotations

from dataclasses import dataclass
import secrets
import threading
import time
from typing import Any, Callable

from nicegui import ui

from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.constantes import MAX_ENTRADAS_HANDOFF, TTL_HANDOFF_SEGUNDOS
from src.frontend.navigation import tool_by_id
from src.frontend.textos import MSJ_HANDOFF_DATOS_INVALIDOS

TTL_SEGUNDOS = TTL_HANDOFF_SEGUNDOS
_MAX_ENTRADAS = MAX_ENTRADAS_HANDOFF
_ALMACEN: dict[str, tuple[float, dict[str, Any]]] = {}
_BLOQUEO = threading.Lock()


def _ahora() -> float:
    """Devuelve la marca temporal monotona actual."""
    return time.monotonic()


def _guardar_en_almacen(tipo: str, origen: str, datos: Any, **extra: Any) -> str:
    """Registra una carga de datos en el almacen volatil y purga entradas expiradas."""
    token = secrets.token_urlsafe(16)
    payload = {"v": 1, "kind": tipo, "source": origen, "data": datos, **extra}
    with _BLOQUEO:
        ahora = _ahora()
        expiradas = [k for k, (ts, _) in _ALMACEN.items() if ahora - ts > TTL_SEGUNDOS]
        for k in expiradas:
            del _ALMACEN[k]
        if len(_ALMACEN) >= _MAX_ENTRADAS:
            mas_antigua = min(_ALMACEN.keys(), key=lambda k: _ALMACEN[k][0])
            del _ALMACEN[mas_antigua]
        _ALMACEN[token] = (ahora, payload)
    return token


def guardar_matriz(id_origen: str, datos: list[list[str]]) -> str:
    """Almacena una matriz A cuadrada o rectangular para transferirla a otra vista."""
    return _guardar_en_almacen("matrix_A", id_origen, datos)


def guardar_sistema(id_origen: str, a_mat: list[list[str]], b_vec: list[str]) -> str:
    """Almacena un sistema completo Ax = b para su visualizacion o resolucion."""
    return _guardar_en_almacen("system", id_origen, {"matrix_A": a_mat, "vector_b": b_vec})


def guardar_vectores(id_origen: str, escena: str, datos: list[list[str]]) -> str:
    """Almacena un conjunto de vectores y su escena destino."""
    return _guardar_en_almacen("vectors", id_origen, datos, scene=escena)


def url_handoff(ruta: str, token: str) -> str:
    """Genera la URL con parametro de consulta para handoff."""
    return f"{ruta}?handoff={token}"


def limpiar_url_handoff() -> None:
    """Remueve el parametro handoff de la barra de direcciones del navegador."""
    js = (
        "(()=>{const u=new URL(location.href);u.searchParams.delete('handoff');"
        "history.replaceState(null,'',u.pathname+u.search+u.hash);})()"
    )
    ui.timer(0.2, lambda: ui.run_javascript(js), once=True)


@dataclass(frozen=True)
class ResultadoHandoff:
    """Estructura inmutable que describe el resultado de consumir una transferencia."""

    status: str
    data: Any
    source_name: str
    message: str


def _extraer_entrada(token: str) -> tuple[dict[str, Any] | None, ResultadoHandoff | None]:
    """Extrae la carga util verificando existencia y frescura temporal."""
    with _BLOQUEO:
        entrada = _ALMACEN.pop(token, None)
    if entrada is None:
        return None, ResultadoHandoff(
            status="missing", data=None, source_name="",
            message="No encontramos los datos que ibas a traer. Ya los usaste o el enlace es antiguo. Puedes capturarlos aquí.",
        )
    marca_tiempo, payload = entrada
    if _ahora() - marca_tiempo > TTL_SEGUNDOS:
        return None, ResultadoHandoff(
            status="expired", data=None, source_name="",
            message="Los datos tardaron demasiado en llegar y expiraron. Vuelve a la herramienta de origen y repite la acción.",
        )
    return payload, None


def _obtener_nombre_origen(source_id: Any) -> str:
    """Obtiene el nombre accesible de la herramienta origen."""
    try:
        return tool_by_id(str(source_id)).name
    except KeyError:
        return "otra herramienta"


def _consumir_transferencia(
    token: str, validador_fn: Callable[[dict[str, Any]], tuple[Any, str | None]]
) -> ResultadoHandoff | None:
    """Flujo parametrizado unico para extraer, validar y limpiar transferencias."""
    if not token:
        return None

    payload, resultado_fallido = _extraer_entrada(token)
    if resultado_fallido is not None:
        return resultado_fallido

    nombre_origen = _obtener_nombre_origen(payload.get("source"))
    datos, error_msg = validador_fn(payload)
    if error_msg is not None:
        return ResultadoHandoff(status="invalid", data=None, source_name=nombre_origen, message=error_msg)

    return ResultadoHandoff(status="ok", data=datos, source_name=nombre_origen, message="")


def _validar_celdas_matriz(datos: list[list[str]], max_n: int) -> str | None:
    """Valida dimensiones cuadradas y valores numericos exactos de una matriz."""
    n = len(datos)
    for fila in datos:
        if not isinstance(fila, list) or len(fila) != n:
            return MSJ_HANDOFF_DATOS_INVALIDOS
    if n > max_n:
        return f"La matriz es de {n}×{n} y esta herramienta admite hasta {max_n}×{max_n}. Empezamos con la herramienta vacía."
    for fila in datos:
        for celda in fila:
            if not ValidadorMatriz.validar_celda(celda):
                return MSJ_HANDOFF_DATOS_INVALIDOS
    return None


def validar_payload_matriz(payload: Any, *, max_n: int) -> tuple[list[list[str]] | None, str | None]:
    """Valida la estructura, dimensiones y formato numerico de una matriz transferida."""
    if not isinstance(payload, dict) or payload.get("v") != 1 or payload.get("kind") != "matrix_A":
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    if not isinstance(payload.get("source"), str):
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    datos = payload.get("data")
    if not isinstance(datos, list) or not datos:
        return None, MSJ_HANDOFF_DATOS_INVALIDOS

    error = _validar_celdas_matriz(datos, max_n)
    if error:
        return None, error
    return datos, None


def _validar_dims_sistema(m: int, n: int, max_m: int, allowed_n: set[int]) -> str | None:
    """Comprueba que m y n esten dentro de los limites permitidos por el visualizador."""
    if m == 0 or m > max_m:
        return f"El sistema debe tener entre 1 y {max_m} ecuaciones. Empezamos con la herramienta vacía."
    if n not in allowed_n:
        opciones = ", o ".join(map(str, sorted(allowed_n)))
        return f"El sistema tiene {n} variables. Esta herramienta solo grafica sistemas con {opciones} variables. Empezamos con la herramienta vacía."
    return None


def _validar_celdas_sistema(a_mat: list[list[str]], b_vec: list[str], n: int) -> bool:
    """Verifica que todas las celdas de A y b contengan numeros exactos."""
    for i, fila in enumerate(a_mat):
        if not isinstance(fila, list) or len(fila) != n:
            return False
        for celda in fila:
            if not ValidadorMatriz.validar_celda(celda):
                return False
        if not ValidadorMatriz.validar_celda(b_vec[i]):
            return False
    return True


def validar_payload_sistema(payload: Any, *, max_m: int, allowed_n: set[int]) -> tuple[dict[str, Any] | None, str | None]:
    """Valida los coeficientes A y termino b de un sistema de ecuaciones transferido."""
    if not isinstance(payload, dict) or payload.get("v") != 1 or payload.get("kind") != "system":
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    datos = payload.get("data")
    if not isinstance(datos, dict):
        return None, MSJ_HANDOFF_DATOS_INVALIDOS

    a_mat = datos.get("matrix_A")
    b_vec = datos.get("vector_b")
    if not isinstance(a_mat, list) or not isinstance(b_vec, list) or len(b_vec) != len(a_mat):
        return None, MSJ_HANDOFF_DATOS_INVALIDOS

    m = len(a_mat)
    n = len(a_mat[0]) if m > 0 else 0
    err_dim = _validar_dims_sistema(m, n, max_m, allowed_n)
    if err_dim:
        return None, err_dim

    if not _validar_celdas_sistema(a_mat, b_vec, n):
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    return datos, None


def _validar_celdas_vectores(datos: list[list[str]], n: int) -> bool:
    """Verifica que los vectores tengan dimension homogenea n y celdas validas."""
    for vec in datos:
        if not isinstance(vec, list) or len(vec) != n:
            return False
        for celda in vec:
            if not ValidadorMatriz.validar_celda(celda):
                return False
    return True


def validar_payload_vectores(payload: Any, *, allowed_n: set[int]) -> tuple[dict[str, Any] | None, str | None]:
    """Valida las dimensiones y datos de una familia de vectores transferida."""
    if not isinstance(payload, dict) or payload.get("v") != 1 or payload.get("kind") != "vectors":
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    datos = payload.get("data")
    escena = payload.get("scene", "vectores")
    if not isinstance(datos, list) or not datos:
        return None, MSJ_HANDOFF_DATOS_INVALIDOS

    n = len(datos[0])
    if n not in allowed_n:
        opciones_txt = ", o ".join(map(str, sorted(allowed_n)))
        return None, f"Los vectores tienen dimensión {n}. Esta herramienta solo grafica en {opciones_txt}D. Empezamos con la herramienta vacía."

    if not _validar_celdas_vectores(datos, n):
        return None, MSJ_HANDOFF_DATOS_INVALIDOS
    return {"scene": escena, "data": datos}, None


def consumir_matriz(token: str, *, max_n: int) -> ResultadoHandoff | None:
    """Extrae y valida una matriz transferida por token."""
    return _consumir_transferencia(token, lambda p: validar_payload_matriz(p, max_n=max_n))


def consumir_sistema(token: str, *, max_m: int, allowed_n: set[int]) -> ResultadoHandoff | None:
    """Extrae y valida un sistema lineal transferido por token."""
    return _consumir_transferencia(token, lambda p: validar_payload_sistema(p, max_m=max_m, allowed_n=allowed_n))


def consumir_vectores(token: str, *, allowed_n: set[int]) -> ResultadoHandoff | None:
    """Extrae y valida una familia de vectores transferida por token."""
    return _consumir_transferencia(token, lambda p: validar_payload_vectores(p, allowed_n=allowed_n))


def renderizar_aviso_handoff(resultado: ResultadoHandoff, mensaje_exito: str) -> None:
    """Muestra un aviso accesible de estado al recibir datos de handoff."""
    if resultado.status == "ok":
        with ui.row().classes("handoff-note").props("role=status"):
            ui.icon("check_circle").classes("text-accent")
            ui.label(mensaje_exito)
    else:
        with ui.row().classes("items-center gap-2 px-4 py-2 badge-warning w-fit").props("role=status"):
            ui.icon("warning_amber")
            ui.label(resultado.message)
