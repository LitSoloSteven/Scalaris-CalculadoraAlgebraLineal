"""Paginación de trazas con formato aportado por la herramienta consumidora."""
from collections.abc import Callable, Sequence
from typing import Any

from nicegui import ui

FILAS_POR_PAGINA = 15
type PreparadorPagina = Callable[[int, int], tuple[Sequence[tuple[str, str]], list[dict]]]


class PaginacionIteraciones:
    """Recibe tabla, total, preparador de columnas/filas y preferencias para paginar.
    Construir monta navegación y eventos sin interpretar las métricas del método.
    """

    def __init__(
        self, tabla: ui.table, total: int, preparar_pagina: PreparadorPagina,
        preferencias: Sequence[Any] = (),
    ):
        self.tabla, self.total = tabla, total
        self._preparar_pagina = preparar_pagina
        self._preferencias = tuple(preferencias)
        self.pagina = 0

    def construir(self) -> None:
        """Monta botones y estado, enlaza preferencias y muestra la primera página."""
        with ui.row().classes("w-full items-center gap-2"):
            self.anterior = ui.button("Anterior", color=None, on_click=lambda: self._mover(-1)).classes("boton-discreto")
            self.siguiente = ui.button("Siguiente", color=None, on_click=lambda: self._mover(1)).classes("boton-discreto")
            self.estado = ui.label().classes("text-sm texto-secundario").props("role=status")
        for preferencia in self._preferencias:
            preferencia.on_value_change(self._actualizar)
        self._actualizar()

    def _mover(self, direccion: int) -> None:
        ultima = max(0, (self.total - 1) // FILAS_POR_PAGINA)
        self.pagina = min(ultima, max(0, self.pagina + direccion))
        self._actualizar()

    def _actualizar(self) -> None:
        if self.tabla.is_deleted:
            return
        inicio = self.pagina * FILAS_POR_PAGINA
        fin = min(inicio + FILAS_POR_PAGINA, self.total)
        columnas, filas = self._preparar_pagina(inicio, fin)
        self.tabla.columns = [{"name": clave, "label": etiqueta, "field": clave, "align": "left"}
                              for clave, etiqueta in columnas]
        self.tabla.update_rows(filas)
        self.anterior.set_enabled(inicio > 0)
        self.siguiente.set_enabled(fin < self.total)
        self.estado.set_text(f"Filas {inicio + 1 if self.total else 0} a {fin} de {self.total}")
