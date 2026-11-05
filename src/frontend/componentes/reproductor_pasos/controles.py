"""Construcción de controles accesibles del reproductor de pasos."""
from __future__ import annotations

from typing import TYPE_CHECKING
from nicegui import ui

from src.frontend.componentes.reproductor_pasos.catalogo import MULTIPLICADORES_LECTURA

if TYPE_CHECKING:
    from src.frontend.componentes.reproductor_pasos.reproductor import ReproductorPasos


def construir_controles(reproductor: ReproductorPasos) -> None:
    """Dibuja los botones, la velocidad y el deslizador si existen varios pasos."""
    if len(reproductor.pasos) <= 1:
        return
    with ui.row().classes("w-full items-center justify-between gap-4 mt-2 flex-wrap"):
        with ui.row().classes("items-center gap-1"):
            _boton_primero(reproductor)
            _boton_anterior(reproductor)
            _boton_reproducir(reproductor)
            _boton_siguiente(reproductor)
            _boton_ultimo(reproductor)
            ui.select(
                list(MULTIPLICADORES_LECTURA),
                value=reproductor.velocidad,
                on_change=reproductor._cambiar_velocidad,
            ).classes("selector-controles w-28 text-xs").props(
                'dense popup-content-class="selector-menu" aria-label="Velocidad de reproducción"'
            )
        reproductor.deslizador = ui.slider(
            min=0,
            max=len(reproductor.pasos) - 1,
            step=1,
            value=0,
        ).classes("inversa-deslizador flex-1 min-w-[160px]").props('label aria-label="Paso actual"')
        vincular_deslizador = getattr(reproductor, "vincular_deslizador", None)
        if vincular_deslizador is None:
            reproductor.deslizador.on_value_change(reproductor._cambiar_deslizador)
        else:
            vincular_deslizador()


def _boton_primero(reproductor: ReproductorPasos) -> None:
    """Crea el control que navega al primer paso."""
    boton = ui.button(icon="first_page", color=None).classes(
        "boton-icono w-9 h-9 p-0"
    ).props('ripple=false aria-label="Primer paso"').tooltip("Primer paso")
    vincular_accion(reproductor, boton, lambda: reproductor.ir_a(0))


def _boton_anterior(reproductor: ReproductorPasos) -> None:
    """Crea el control que navega al paso anterior."""
    boton = ui.button(icon="chevron_left", color=None).classes(
        "boton-icono w-9 h-9 p-0"
    ).props('ripple=false aria-label="Paso anterior"').tooltip("Paso anterior")
    vincular_accion(reproductor, boton, lambda: _mover(reproductor, -1))


def _boton_reproducir(reproductor: ReproductorPasos) -> None:
    """Crea el control que inicia o pausa la reproducción."""
    reproductor.boton_reproducir = ui.button(
        icon="play_arrow", color=None
    ).classes("boton-icono w-9 h-9 p-0").props(
        'ripple=false aria-label="Reproducción automática"'
    ).tooltip("Reproducción automática")
    vincular_accion(reproductor, reproductor.boton_reproducir, reproductor._alternar_reproduccion)


def _boton_siguiente(reproductor: ReproductorPasos) -> None:
    """Crea el control que navega al paso siguiente."""
    boton = ui.button(icon="chevron_right", color=None).classes(
        "boton-icono w-9 h-9 p-0"
    ).props('ripple=false aria-label="Paso siguiente"').tooltip("Paso siguiente")
    vincular_accion(reproductor, boton, lambda: _mover(reproductor, 1))


def _boton_ultimo(reproductor: ReproductorPasos) -> None:
    """Crea el control que navega al último paso."""
    ultimo = len(reproductor.pasos) - 1
    boton = ui.button(icon="last_page", color=None).classes(
        "boton-icono w-9 h-9 p-0"
    ).props('ripple=false aria-label="Último paso"').tooltip("Último paso")
    vincular_accion(reproductor, boton, lambda: reproductor.ir_a(ultimo))


def vincular_accion(reproductor, boton, accion) -> None:
    """Enlaza una acción y permite que un reproductor especializado capture su modalidad."""
    vincular = getattr(reproductor, "vincular_accion", None)
    if vincular is None:
        boton.on_click(accion)
    else:
        vincular(boton, accion)


def _mover(reproductor, diferencia: int) -> None:
    indice = getattr(reproductor, "indice_solicitado", reproductor.indice_actual)
    reproductor.ir_a(indice + diferencia)
