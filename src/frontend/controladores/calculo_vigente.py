"""Ejecución en trabajador con comprobación de la captura antes de publicar."""
import asyncio
from collections.abc import Callable
from typing import Any
from nicegui import run
from src.ai.huellas import calcular_huella
from src.frontend.controladores.sesion_matricial import notificar_edicion


def _campos(vista: Any) -> tuple:
    obtener = getattr(vista, '_campos_captura', None)
    return tuple(obtener()) if obtener else ()


def _revision(vista: Any) -> tuple:
    return (getattr(vista, '_revision_captura', 0),
            getattr(vista, '_version_solicitud', 0),
            getattr(vista, '_identificador_calculo', 0),
            tuple(id(campo) for campo in _campos(vista)))


def _vigilar_campos(vista: Any) -> None:
    for campo in _campos(vista):
        if not getattr(campo, '_vigila_calculo', False):
            campo.on_value_change(lambda: notificar_edicion(vista))
            campo._vigila_calculo = True


async def ejecutar_calculo_vigente(
    vista: Any, capturar: Callable[[], dict], calcular: Callable[[dict], Any],
) -> tuple[Any, str] | None:
    """Recibe vista, captura y controlador; devuelve respuesta y huella si siguen vigentes.
    Ejecuta en trabajador y propaga los errores vigentes y la cancelación."""
    _vigilar_campos(vista)
    contenedor = vista.contenedor_resultados
    revision = _revision(vista)
    captura = capturar()
    huella = calcular_huella(captura)
    try:
        respuesta = await run.io_bound(calcular, captura)
    except Exception:
        if not _sigue_vigente(vista, contenedor, revision, huella, capturar):
            return None
        raise
    if respuesta is None and asyncio.current_task().cancelling():
        raise asyncio.CancelledError
    if respuesta is None or not _sigue_vigente(vista, contenedor, revision, huella, capturar):
        return None
    return respuesta, huella


def _sigue_vigente(vista, contenedor, revision, huella, capturar) -> bool:
    if contenedor.is_deleted or contenedor is not vista.contenedor_resultados:
        return False
    return revision == _revision(vista) and huella == calcular_huella(capturar())
