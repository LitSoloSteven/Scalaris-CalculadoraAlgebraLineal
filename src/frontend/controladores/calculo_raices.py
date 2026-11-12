"""Carga y finalización compartidas de solicitudes individuales de raíces."""
import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente

_registro = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class ConfiguracionCalculoRaices:
    """Define los mensajes de carga, error visible y registro de cada herramienta."""

    mensaje_carga: str
    mensaje_error: str
    mensaje_registro: str


async def resolver_calculo_raices(
    vista: Any, calcular: Callable[[dict], dict], configuracion: ConfiguracionCalculoRaices,
    *, puntero: bool = False,
) -> None:
    """Coordina vista, controlador y mensajes; devuelve None y gestiona errores/cancelación.
    La vista aporta captura, retiro y publicación; solo publica la solicitud vigente.
    """
    if vista.ocupado or vista.contenedor_resultados.is_deleted:
        return
    vista._retirar_resultado()
    tarea = vista.tarea_calculo = asyncio.current_task()
    _mostrar_carga(vista, True)
    vista.estado.set_text(configuracion.mensaje_carga)
    try:
        vigente = await ejecutar_calculo_vigente(vista, vista.capturar, calcular)
        if vigente is not None and vista.tarea_calculo is tarea:
            vista._publicar(*vigente, puntero=puntero)
    except asyncio.CancelledError:
        return
    except Exception:
        _registro.exception(configuracion.mensaje_registro)
        if vista.tarea_calculo is tarea and not vista.estado.is_deleted:
            vista.estado.set_text(configuracion.mensaje_error)
    finally:
        if vista.tarea_calculo is tarea:
            vista.tarea_calculo = None
            _mostrar_carga(vista, False)


def _mostrar_carga(vista: Any, ocupado: bool) -> None:
    vista.ocupado = ocupado
    if not vista.boton_resolver.is_deleted:
        vista.boton_resolver.set_enabled(not ocupado)
        vista.boton_resolver.props("loading" if ocupado else "", remove="" if ocupado else "loading")
