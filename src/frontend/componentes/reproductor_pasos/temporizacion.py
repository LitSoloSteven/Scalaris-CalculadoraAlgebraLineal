"""Reinicio de la espera de lectura cuando cambia una acción de reproducción."""
from nicegui import ui


def reiniciar_espera(reproductor) -> None:
    """Sustituye el temporizador vigente por una espera completa, activa y no inmediata."""
    anterior = reproductor.temporizador
    if anterior is None or anterior.is_deleted or reproductor.tarjeta.is_deleted:
        return
    intervalo = anterior.interval
    anterior.active = False
    anterior.delete()
    with reproductor.tarjeta:
        reproductor.temporizador = ui.timer(
            intervalo, reproductor._avanzar, active=True, immediate=False
        )
