"""Indicadores de espera y cancelación de la consulta activa de Glosa."""
from dataclasses import dataclass
import threading
from typing import Any

from nicegui import ui


ESPERA_CANCELAR_SEGUNDOS = 5


@dataclass
class IndicadoresEnvio:
    """Conserva referencias a los elementos que aparecen durante una consulta."""

    escritura: Any = None
    boton_cancelar: Any = None
    temporizador: Any = None


def _consulta_vigente(instancia, identificador, cancelar):
    return (instancia._contador_solicitudes == identificador
            and getattr(instancia, "_esta_enviando", False) and not cancelar.is_set())


def iniciar_temporizador_cancelar(
    instancia: Any, identificador: int, cancelar: threading.Event, escritura: Any,
) -> IndicadoresEnvio:
    """Programa el botón de cancelación y conserva su referencia hasta finalizar."""
    indicadores = IndicadoresEnvio(escritura)

    def cancelar_consulta():
        """Cancela únicamente la consulta que creó estos indicadores."""
        if _consulta_vigente(instancia, identificador, cancelar):
            cancelar.set()
            instancia._contador_solicitudes += 1
            finalizar_envio(instancia, indicadores)
            instancia._ultimo_envio = 0.0

    def mostrar_cancelacion():
        """Monta el botón cuando la petición sigue activa al vencer la espera."""
        if not _consulta_vigente(instancia, identificador, cancelar):
            return
        with instancia.area_chat:
            indicadores.boton_cancelar = ui.row().classes("w-full justify-center mt-2")
        with indicadores.boton_cancelar:
            ui.button("Cancelar", on_click=cancelar_consulta).classes("boton-discreto text-xs texto-secundario")
        instancia._desplazar_al_final()

    with instancia.area_chat:
        indicadores.temporizador = ui.timer(ESPERA_CANCELAR_SEGUNDOS, mostrar_cancelacion, once=True)
    return indicadores


def finalizar_envio(instancia: Any, indicadores: IndicadoresEnvio) -> None:
    """Retira los indicadores y restablece los controles al terminar o cancelar."""
    if indicadores.temporizador:
        indicadores.temporizador.cancel()
    for elemento in (indicadores.escritura, indicadores.boton_cancelar):
        if elemento is not None and not elemento.is_deleted:
            elemento.delete()
    instancia._esta_enviando = False
    campo = getattr(instancia, "campo_entrada", None)
    if campo:
        campo.enable()
    instancia._forzar_sugerencias = True
    instancia._renderizar_sugerencias_laterales()
