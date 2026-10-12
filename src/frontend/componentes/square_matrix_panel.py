"""Componente para la captura e interacción con matrices cuadradas (SquareMatrixPanel).

Optimizado para redimensionado incremental sin regenerar la cuadrícula completa,
con soporte para animación fluida de hasta 50×50 elementos.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from nicegui import ui

from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.componentes.cuadricula_base import (
    DIMENSION_MINIMA,
    actualizar_estados_botones_dimension,
    props_celda_accesible,
    purgar_cache_bidimensional,
)
from src.frontend.constantes import DIMENSION_MAXIMA_INVERSA

logger = logging.getLogger(__name__)

ID_MATRIZ = "A"
MIN_N = DIMENSION_MINIMA
MAX_N = DIMENSION_MAXIMA_INVERSA
DEFAULT_N = 3


class SquareMatrixPanel:
    """Panel de captura de matriz cuadrada con un único control bidimensional (n×n)."""

    def __init__(self, initial_n: int = DEFAULT_N) -> None:
        self.n: int = min(max(initial_n, MIN_N), MAX_N)
        self.cache: dict[tuple[int, int], str] = {}
        self.rows_ui: list[ui.row] = []
        self.cells: list[list[ui.input]] = []
        self.on_data_change: Callable[[], None] | None = None
        self._suspend_events: bool = False
        self._resizing: bool = False
        self.container: ui.column | None = None
        self.grid_container: ui.column | None = None
        self.lbl_n: ui.label | None = None
        self.lbl_badge: ui.html | None = None
        self.btn_dec: ui.button | None = None
        self.btn_inc: ui.button | None = None

    @staticmethod
    def inject_scripts() -> None:
        """Inyecta los scripts necesarios para navegación y animación de matriz cuadrada."""
        ui.add_head_html('<script src="/assets/js/captura_matrices.js"></script>')
        ui.add_head_html('<script src="/assets/js/square_matrix.js"></script>')

    def build_container(self) -> ui.column:
        """Construye el contenedor UI completo del panel."""
        self.container = ui.column().classes("w-full panel-card p-4")
        with self.container:
            with ui.row().classes("w-full justify-between items-center mb-4 flex-wrap gap-2"):
                with ui.row().classes("items-center gap-2"):
                    ui.label("Matriz A").classes("text-lg font-bold text-main")
                    self.lbl_badge = ui.html(
                        f'{ID_MATRIZ} <span class="separador-punto">·</span> {self.n} &times; {self.n}'
                    ).classes("fs-small text-sec uppercase etiqueta-dimensiones")

                with ui.row().classes("items-center gap-3 flex-wrap"):
                    self._construir_controles_tamano()
                    ui.button("Pegar", icon="content_paste", color=None, on_click=self.paste_from_clipboard).props(
                        "ripple=false"
                    ).classes("btn-ghost").tooltip("Pegar matriz desde el portapapeles")

            with ui.column().classes("overflow-auto w-full grid-scroll cuadricula-desplazamiento"):
                self.grid_container = ui.column().classes("cuadricula-contenido")
                self._render_full()

            ui.label(
                f"Pega desde Excel o un bloc de notas (tabuladores o comas). Máx. {MAX_N}×{MAX_N}."
            ).classes("text-xs text-sec mt-2")

        return self.container

    def _construir_controles_tamano(self) -> None:
        """Construye los botones de decremento e incremento de dimensión."""
        with ui.row().classes("items-center gap-1"):
            ui.label("Tamaño:").classes("text-sm text-sec mr-1")
            self.btn_dec = ui.button(
                icon="remove", color=None, on_click=lambda: self.resize(-1)
            ).props('ripple=false aria-label="Quitar fila y columna"').classes(
                "btn-neo-icon w-8 h-8 p-0 flex-shrink-0"
            ).tooltip("Quitar fila y columna")
            self.lbl_n = ui.label(str(self.n)).classes("font-bold w-6 text-center text-main")
            self.btn_inc = ui.button(
                icon="add", color=None, on_click=lambda: self.resize(+1)
            ).props('ripple=false aria-label="Añadir fila y columna"').classes(
                "btn-neo-icon w-8 h-8 p-0 flex-shrink-0"
            ).tooltip("Añadir fila y columna")
            self._update_buttons()

    def _render_full(self) -> None:
        """Renderiza la cuadrícula completa desde cero usando las filas DOM almacenadas."""
        if not self.grid_container:
            return
        self.grid_container.clear()
        self.rows_ui.clear()
        self.cells.clear()
        with self.grid_container:
            for r in range(self.n):
                self._anadir_fila_dom(r)

    def _anadir_fila_dom(self, r: int) -> None:
        """Crea una fila DOM y sus celdas de entrada asociadas."""
        with ui.row().classes("items-center gap-2 mb-2 no-wrap").props(f'data-matriz-fila="{r}"') as row_ui:
            row_cells: list[ui.input] = []
            for c in range(self.n):
                celda = self._crear_celda_ui(r, c)
                row_cells.append(celda)
            self.rows_ui.append(row_ui)
            self.cells.append(row_cells)

    def _crear_celda_ui(self, r: int, c: int) -> ui.input:
        """Construye una celda de entrada individual con props accesibles."""
        val = self.cache.get((r, c), "")
        clase_tam = "grid-cell-compact" if self.n > 8 else "grid-cell"
        props = props_celda_accesible(r, c, id_matriz=ID_MATRIZ, nombre_campo=f"{ID_MATRIZ}_r{r}c{c}")
        return ui.input(
            value=val,
            placeholder="",
            on_change=lambda e, fil=r, col=c: self._on_change(fil, col, e.value),
        ).classes(f"matrix-input {clase_tam}").props(props)

    def _on_change(self, r: int, c: int, val: str) -> None:
        """Actualiza el caché ante cambios en una celda y notifica observadores."""
        if self._suspend_events:
            return
        if val:
            self.cache[(r, c)] = val
        else:
            self.cache.pop((r, c), None)
        if self.on_data_change:
            self.on_data_change()

    def resize(self, delta: int) -> None:
        """Dispara el redimensionamiento asíncrono con paso de delta."""
        if self._resizing:
            return
        asyncio.create_task(self._resize_async(delta))

    async def _resize_async(self, delta: int) -> None:
        """Aplica la modificación de tamaño con animación DOM."""
        nuevo_n = min(max(self.n + delta, MIN_N), MAX_N)
        if nuevo_n == self.n:
            return
        self._resizing = True
        try:
            viejo_n = self.n
            self.n = nuevo_n
            self.cache = purgar_cache_bidimensional(self.cache, self.n, self.n)
            self._update_badge()
            self._update_buttons()
            self._render_full()
            if self.on_data_change:
                self.on_data_change()
        finally:
            self._resizing = False

    def _update_badge(self) -> None:
        """Actualiza el texto descriptivo del badge y contador."""
        if self.lbl_n:
            self.lbl_n.set_text(str(self.n))
        if self.lbl_badge:
            self.lbl_badge.content = f'{ID_MATRIZ} <span class="separador-punto">·</span> {self.n} &times; {self.n}'

    def _update_buttons(self) -> None:
        """Actualiza la disponibilidad de los botones de incremento y decremento."""
        actualizar_estados_botones_dimension(self.btn_dec, self.btn_inc, self.n, MIN_N, MAX_N)

    def obtener_matriz(self) -> list[list[str]]:
        """Extrae la matriz actual como lista bidimensional de cadenas."""
        return [
            [(self.cache.get((r, c), "0") or "0") for c in range(self.n)]
            for r in range(self.n)
        ]

    def cargar_matriz(self, data: list[list[str]]) -> None:
        """Carga una matriz externa adaptando la dimensión n."""
        if not data or not data[0]:
            return
        nuevo_n = min(max(len(data), MIN_N), MAX_N)
        self.cache.clear()
        for r in range(min(len(data), nuevo_n)):
            for c in range(min(len(data[r]), nuevo_n)):
                txt = str(data[r][c]).strip()
                if txt and txt != "0":
                    self.cache[(r, c)] = txt
        self.n = nuevo_n
        self._update_badge()
        self._update_buttons()
        self._render_full()
        if self.on_data_change:
            self.on_data_change()

    async def paste_from_clipboard(self) -> None:
        """Lee el contenido textual del portapapeles y lo parsea hacia la matriz."""
        try:
            texto = await ui.run_javascript("return navigator.clipboard.readText();")
        except Exception as error:
            logger.warning("No se pudo leer el portapapeles: %s", error)
            ui.notify("No se pudo acceder al portapapeles.", type="warning")
            return
        if not texto:
            return
        filas = _parsear_texto_portapapeles(texto)
        if filas:
            self.cargar_matriz(filas)

    def is_empty(self) -> bool:
        """Comprueba si todas las celdas están vacías."""
        return not bool(self.cache)

    def obtener_datos_matriz(self) -> list[list[str]]:
        """Devuelve los datos matriciales almacenados en el panel."""
        return self.obtener_matriz()

    def clear(self) -> None:
        """Vacía las entradas de la matriz conservando su dimensión."""
        self.cache.clear()
        self._render_full()
        if self.on_data_change:
            self.on_data_change()


def _parsear_texto_portapapeles(texto: str) -> list[list[str]]:
    """Parsea una cadena con filas separadas por saltos de línea y celdas por coma o tab."""
    lineas = [lin.strip() for lin in texto.strip().splitlines() if lin.strip()]
    resultado: list[list[str]] = []
    for lin in lineas:
        delimitador = "\t" if "\t" in lin else "," if "," in lin else " "
        celdas = [c.strip() for c in lin.split(delimitador) if c.strip()]
        if celdas:
            resultado.append(celdas)
    return resultado
