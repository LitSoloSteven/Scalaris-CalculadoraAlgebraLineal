"""Historial reutilizable de los cálculos recientes de la sesión."""
from __future__ import annotations

import copy
import time
from collections.abc import Callable
from typing import Any

from nicegui import ui

MAXIMO_POR_DEFECTO = 5
CLASES_TONO: dict[str, str] = {
    "exito": "text-accent",
    "alerta": "text-warn",
    "error": "text-err",
}


class HistorialCalculos:
    """Guarda los últimos cálculos y permite restaurar sus datos de entrada."""

    def __init__(
        self,
        al_restaurar: Callable[[Any], None],
        vacio: str,
        maximo: int = MAXIMO_POR_DEFECTO,
    ) -> None:
        """Configura el historial.

        Args:
            al_restaurar: Función que recibe una copia de los datos de la entrada elegida.
            vacio: Mensaje orientativo cuando todavía no hay cálculos.
            maximo: Cantidad máxima de entradas conservadas.

        Raises:
            ValueError: Si maximo es menor que 1.
        """
        if maximo < 1:
            raise ValueError("El historial debe conservar al menos una entrada.")
        self._al_restaurar = al_restaurar
        self._vacio = vacio
        self._maximo = maximo
        self._entradas: list[dict[str, Any]] = []
        self._contenedor: ui.column | None = None

    def construir(self) -> None:
        """Crea el contenedor del historial y pinta las entradas existentes."""
        self._contenedor = ui.column().classes("w-full")
        self._pintar()

    def agregar(
        self,
        datos: Any,
        *,
        titulo: str,
        estado: str,
        tono: str = "exito",
        detalle: str | None = None,
    ) -> None:
        """Agrega un cálculo al inicio del historial y repinta la lista.

        Args:
            datos: Datos de entrada que se devolverán al restaurar.
            titulo: Texto corto de la insignia, por ejemplo la dimensión.
            estado: Resultado legible del cálculo.
            tono: "exito", "alerta" o "error", según el estado.
            detalle: Línea secundaria opcional, por ejemplo un valor calculado.
        """
        self._entradas.insert(0, {
            "datos": copy.deepcopy(datos),
            "titulo": titulo,
            "estado": estado,
            "tono": tono,
            "detalle": detalle,
            "hora": time.strftime("%H:%M"),
        })
        del self._entradas[self._maximo:]
        self._pintar()

    def _contenedor_vivo(self) -> bool:
        """Indica si el contenedor existe y no fue destruido con la página."""
        return self._contenedor is not None and not self._contenedor.is_deleted

    def _pintar(self) -> None:
        """Redibuja todas las entradas o el mensaje de historial vacío."""
        if not self._contenedor_vivo():
            return
        self._contenedor.clear()
        with self._contenedor:
            if not self._entradas:
                ui.label(self._vacio).classes("text-sec italic text-sm mt-4 text-center")
                return
            for entrada in self._entradas:
                self._pintar_entrada(entrada)

    def _pintar_entrada(self, entrada: dict[str, Any]) -> None:
        """Dibuja la tarjeta de una entrada con su botón de restauración."""
        clase_estado = CLASES_TONO.get(entrada["tono"], CLASES_TONO["exito"])
        with ui.column().classes(
            "panel-card p-4 w-full mb-3 gap-2 border border-[var(--border-input)]"
        ):
            with ui.row().classes("w-full justify-between items-center no-wrap"):
                ui.badge(entrada["titulo"], color=None).classes("badge-success font-mono")
                ui.label(entrada["hora"]).classes("text-xs text-sec flex-shrink-0")
            ui.label(entrada["estado"]).classes(f"text-xs font-bold {clase_estado}")
            if entrada["detalle"]:
                ui.label(entrada["detalle"]).classes("text-xs font-mono text-sec").style(
                    "overflow-wrap: anywhere; min-width: 0;"
                )
            ui.button(
                "Restaurar",
                on_click=lambda _, datos=entrada["datos"]: self._restaurar(datos),
                color=None,
            ).classes("btn-ghost text-xs w-full mt-2").props("ripple=false")

    def _restaurar(self, datos: Any) -> None:
        """Entrega una copia de los datos guardados a la función de restauración."""
        self._al_restaurar(copy.deepcopy(datos))
