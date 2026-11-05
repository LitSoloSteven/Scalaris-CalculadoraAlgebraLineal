"""Vigencia y estados de la solicitud del cálculo individual."""
import asyncio
import logging

from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente

registro = logging.getLogger(__name__)


async def resolver_calculo(vista, calcular, *, puntero: bool = False) -> None:
    """Admite un trabajador por vista y publica únicamente la captura vigente."""
    if vista.ocupado or vista.contenedor_resultados.is_deleted:
        return
    vista._retirar_resultado()
    tarea = vista.tarea_calculo = asyncio.current_task()
    _mostrar_carga(vista, True)
    vista.estado.set_text("Calculando la raíz en el intervalo…")
    try:
        vigente = await ejecutar_calculo_vigente(vista, vista.capturar, calcular)
        if vigente is not None and vista.tarea_calculo is tarea:
            vista._publicar(*vigente, puntero=puntero)
    except asyncio.CancelledError:
        return
    except Exception:
        registro.exception("No se pudo presentar el cálculo de bisección")
        if vista.tarea_calculo is tarea and not vista.estado.is_deleted:
            vista.estado.set_text("No se pudo completar el cálculo. Revisa la función y vuelve a intentarlo.")
    finally:
        if vista.tarea_calculo is tarea:
            vista.tarea_calculo = None
            _mostrar_carga(vista, False)


def _mostrar_carga(vista, ocupado: bool) -> None:
    vista.ocupado = ocupado
    if not vista.boton_resolver.is_deleted:
        vista.boton_resolver.set_enabled(not ocupado)
        vista.boton_resolver.props("loading" if ocupado else "", remove="" if ocupado else "loading")
