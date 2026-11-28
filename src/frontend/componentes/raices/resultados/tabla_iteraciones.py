"""Paginación de trazas con formato aportado por la herramienta consumidora."""
from collections.abc import Callable, Sequence
from typing import Any

from nicegui import ui

FILAS_POR_PAGINA = 15
type PreparadorPagina = Callable[[int, int], tuple[Sequence[tuple[str, str]], list[dict]]]
_COLUMNAS_TEXTO = frozenset({"criterio", "signo_producto", "accion", "signo_examen", "accion_examen"})


def columnas_iteraciones(etiquetas: Sequence[tuple[str, str]]) -> list[dict]:
    """Transforma pares de campo y título en columnas alineadas según su contenido."""
    return [
        {"name": campo, "label": titulo, "field": campo,
         "align": "left" if campo in _COLUMNAS_TEXTO else "right"}
        for campo, titulo in etiquetas
    ]


def presentar_tabla_iteraciones(tabla: ui.table, *, paginacion_propia: bool = False) -> None:
    """Aplica estilo y rótulos a una tabla NiceGUI, con paginación externa opcional."""
    tabla.classes("tabla-resultados w-full").props(
        'rows-per-page-label="Filas por página:" '
        'no-data-label="El cálculo no generó iteraciones." '
        ':pagination-label="(inicio, fin, total) => inicio + \'–\' + fin + \' de \' + total" '
        ':selected-rows-label="n => n === 1 ? \'1 fila seleccionada\' : n + \' filas seleccionadas\'"'
    )
    if paginacion_propia:
        tabla.props("hide-pagination hide-selected-banner")


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

    def mostrar_indice(self, indice: int) -> None:
        """Muestra la página que contiene el índice de fila indicado, acotándolo al total."""
        self.pagina = max(0, min(indice, self.total - 1)) // FILAS_POR_PAGINA
        self._actualizar()

    def _actualizar(self) -> None:
        if self.tabla.is_deleted:
            return
        inicio = self.pagina * FILAS_POR_PAGINA
        fin = min(inicio + FILAS_POR_PAGINA, self.total)
        columnas, filas = self._preparar_pagina(inicio, fin)
        self.tabla.columns = columnas_iteraciones(columnas)
        self.tabla.update_rows(filas, clear_selection=False)
        self.anterior.set_enabled(inicio > 0)
        self.siguiente.set_enabled(fin < self.total)
        self.estado.set_text(f"Filas {inicio + 1 if self.total else 0} a {fin} de {self.total}")
