"""Cuadricula interactiva de captura para sistemas de ecuaciones lineales."""
from __future__ import annotations

from functools import partial
from typing import Any, Callable
from nicegui import ui

from src.frontend.componentes.cuadricula_base import (
    DIMENSION_MINIMA,
    actualizar_estados_botones_dimension,
    animar_entrada_cuadricula,
    animar_salida_cuadricula,
    props_celda_accesible,
    purgar_cache_bidimensional,
    purgar_cache_unidimensional,
)
from src.frontend.componentes.exportador_ecuaciones import exportar_ecuaciones_desde_datos
from src.frontend.constantes import DIMENSION_MAXIMA_SISTEMAS


def _renderizar_cabecera_columnas(n: int) -> None:
    """Renderiza la cabecera fija de variables xj y termino b."""
    with ui.row().classes(
        "items-center gap-2 mb-2 no-wrap w-full z-10 bg-[var(--bg-panel)] cuadricula-cabecera-fija"
    ):
        for j in range(n):
            ui.html(f"x<sub>{j+1}</sub>").classes("grid-cell text-center math-label")
        ui.label("=").classes("w-8 text-center text-transparent flex-shrink-0")
        ui.label("b").classes("grid-cell text-center math-label")


def _construir_botones_tamanos(grid: Any) -> None:
    """Construye los botones de dimension vertical de ecuaciones."""
    with ui.column().classes("gap-2 mt-12 items-center justify-center mr-2"):
        grid.btn_m_inc = ui.button(
            icon="add", on_click=partial(grid.adjust_size, delta_m=1), color=None
        ).classes("btn-neo-icon w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Añadir Ecuacion"').tooltip("Añadir Ecuacion")
        grid.btn_m_dec = ui.button(
            icon="remove", on_click=partial(grid.adjust_size, delta_m=-1), color=None
        ).classes("btn-neo-icon w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Quitar Ecuacion"').tooltip("Quitar Ecuacion")


def _construir_botones_variables(grid: Any) -> None:
    """Construye los botones inferiores de anadir o quitar variables xj."""
    with ui.row().classes("w-full justify-center gap-2 mt-4"):
        grid.btn_n_inc = ui.button(
            icon="add", on_click=partial(grid.adjust_size, delta_n=1), color=None
        ).classes("btn-neo-icon w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Añadir Variable"').tooltip("Añadir Variable")
        grid.btn_n_dec = ui.button(
            icon="remove", on_click=partial(grid.adjust_size, delta_n=-1), color=None
        ).classes("btn-neo-icon w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Quitar Variable"').tooltip("Quitar Variable")


def _renderizar_fila_entradas(grid: EquationGrid, i: int) -> None:
    """Renderiza una fila con entradas de coeficientes y celda de resultado b."""
    with ui.row().classes("items-center gap-2 mb-2 no-wrap").props(f'data-grid-row="{i}"'):
        fila_A = []
        for j in range(grid.n):
            val = grid._cache_A.get((i, j), "")
            props = props_celda_accesible(i, j, nombre_campo=f"r{i}c{j}")
            celda = ui.input(
                value=val,
                placeholder="",
                on_change=lambda e, r=i, c=j: grid._actualizar_celda(False, r, c, e.value),
            ).classes("matrix-input grid-cell").props(props)
            fila_A.append(celda)
        grid.entradas_A.append(fila_A)

        ui.label("=").classes("w-8 text-center math-label text-xl flex-shrink-0")
        val_b = grid._cache_b.get(i, "")
        props_b = props_celda_accesible(i, grid.n, nombre_campo=f"r{i}cb")
        celda_b = ui.input(
            value=val_b,
            placeholder="",
            on_change=lambda e, r=i: grid._actualizar_celda(True, r, 0, e.value),
        ).classes("matrix-input grid-cell").props(props_b)
        grid.entradas_b.append(celda_b)


class EquationGrid:
    """Cuadricula de captura de matriz de coeficientes y terminos independientes."""

    def __init__(self, default_m: int = 3, default_n: int = 3) -> None:
        self.entradas_A: list[list[ui.input]] = []
        self.entradas_b: list[ui.input] = []
        self.m: int = default_m
        self.n: int = default_n
        self.contenedor_matriz: ui.column | None = None
        self.shape_label: ui.html | None = None
        self._cache_A: dict[tuple[int, int], str] = {}
        self._cache_b: dict[int, str] = {}
        self.on_data_change: Callable[[], None] | None = None
        self.btn_m_dec: ui.button | None = None
        self.btn_m_inc: ui.button | None = None
        self.btn_n_dec: ui.button | None = None
        self.btn_n_inc: ui.button | None = None

    @staticmethod
    def inject_scripts() -> None:
        """Inyecta el script asociado para animaciones de la cuadricula de ecuaciones."""
        ui.add_head_html('<script src="/assets/js/equation_grid.js"></script>')

    async def adjust_size(self, delta_m: int = 0, delta_n: int = 0) -> None:
        """Ajusta las dimensiones de ecuaciones o variables con animacion."""
        nuevo_m = self.m + delta_m
        nuevo_n = self.n + delta_n
        if not (DIMENSION_MINIMA <= nuevo_m <= DIMENSION_MAXIMA_SISTEMAS) or not (
            DIMENSION_MINIMA <= nuevo_n <= DIMENSION_MAXIMA_SISTEMAS
        ):
            return

        self._deshabilitar_botones_redimension()
        if delta_m < 0 or delta_n < 0:
            target = f"[data-row='{self.m - 1}']" if delta_m < 0 else f"[data-col='{self.n - 1}']"
            await animar_salida_cuadricula(target, es_fila=(delta_m < 0), indice=self.m - 1)

        self.m = nuevo_m
        self.n = nuevo_n
        self._cache_A = purgar_cache_bidimensional(self._cache_A, self.m, self.n)
        self._cache_b = purgar_cache_unidimensional(self._cache_b, self.m)

        self.generar_cuadricula()
        if self.on_data_change:
            self.on_data_change()

        if delta_m > 0 or delta_n > 0:
            target = f"[data-row='{self.m - 1}']" if delta_m > 0 else f"[data-col='{self.n - 1}']"
            await animar_entrada_cuadricula(target)

    def _deshabilitar_botones_redimension(self) -> None:
        """Deshabilita temporalmente los botones de tamano durante la animacion."""
        for btn in (self.btn_m_dec, self.btn_m_inc, self.btn_n_dec, self.btn_n_inc):
            if btn:
                btn.disable()

    def build_grid_container(self) -> None:
        """Construye el contenedor principal con indicadores y controles de redimensionado."""
        with ui.row().classes("w-full justify-between items-end mb-4 px-2"):
            self.shape_label = ui.html().classes("fs-small text-sec uppercase etiqueta-dimensiones")

        with ui.row().classes("w-full items-start no-wrap gap-2"):
            self.contenedor_matriz = ui.column().classes(
                "overflow-auto panel-card p-4 flex-1 grid-scroll cuadricula-desplazamiento"
            )
            _construir_botones_tamanos(self)

        _construir_botones_variables(self)
        self.generar_cuadricula()

    def generar_cuadricula(self) -> None:
        """Regenera los widgets de entrada de la matriz a partir del cache actualizado."""
        self._sincronizar_cache_desde_entradas()
        if self.contenedor_matriz:
            self.contenedor_matriz.clear()
        self.entradas_A.clear()
        self.entradas_b.clear()

        shape_text = "Sistema Cuadrado" if self.m == self.n else "Sistema Rectangular"
        if self.shape_label:
            self.shape_label.content = (
                f'{shape_text} <span class="separador-punto">·</span> {self.m} &times; {self.n}'
            )

        actualizar_estados_botones_dimension(self.btn_m_dec, self.btn_m_inc, self.m, DIMENSION_MINIMA, DIMENSION_MAXIMA_SISTEMAS)
        actualizar_estados_botones_dimension(self.btn_n_dec, self.btn_n_inc, self.n, DIMENSION_MINIMA, DIMENSION_MAXIMA_SISTEMAS)

        if self.contenedor_matriz:
            with self.contenedor_matriz:
                self._renderizar_filas_cuadricula()

    def _sincronizar_cache_desde_entradas(self) -> None:
        """Copia valores no vacios desde las celdas UI al diccionario de cache."""
        for i, fila in enumerate(self.entradas_A):
            for j, celda in enumerate(fila):
                if celda.value:
                    self._cache_A[(i, j)] = celda.value
        for i, celda in enumerate(self.entradas_b):
            if celda.value:
                self._cache_b[i] = celda.value

    def _renderizar_filas_cuadricula(self) -> None:
        """Renderiza la cabecera fija y las filas de coeficientes y termino independiente."""
        _renderizar_cabecera_columnas(self.n)
        with ui.column().classes("cuadricula-contenido"):
            for i in range(self.m):
                _renderizar_fila_entradas(self, i)

    def _actualizar_celda(self, es_b: bool, r: int, c: int, valor: str) -> None:
        """Actualiza el cache de coeficientes o vector b y notifica el cambio."""
        if es_b:
            self._cache_b[r] = valor
        else:
            self._cache_A[(r, c)] = valor
        if self.on_data_change:
            self.on_data_change()

    def obtener_datos_matriz(self) -> tuple[list[list[str]], list[str]]:
        """Obtiene las matrices numericas A y vector b como cadenas de texto."""
        matriz_A_vals = [
            [(celda.value.strip() if celda.value else "0") for celda in fila]
            for fila in self.entradas_A
        ]
        vector_b_vals = [
            (celda.value.strip() if celda.value else "0") for celda in self.entradas_b
        ]
        return matriz_A_vals, vector_b_vals

    def is_strictly_empty(self) -> bool:
        """Determina si la totalidad de celdas de la cuadricula estan sin llenar."""
        for fila in self.entradas_A:
            for celda in fila:
                if celda.value and str(celda.value).strip() != "":
                    return False
        for celda in self.entradas_b:
            if celda.value and str(celda.value).strip() != "":
                return False
        return True

    def clear(self) -> None:
        """Limpia el contenido de todas las celdas y purga el cache."""
        self._cache_A.clear()
        self._cache_b.clear()
        for fila in self.entradas_A:
            for celda in fila:
                celda.value = ""
        for celda in self.entradas_b:
            celda.value = ""
        if self.on_data_change:
            self.on_data_change()

    def export_to_equations(self, preserve_shape: bool = False) -> list[str]:
        """Genera una lista de cadenas con ecuaciones formateadas algebraicamente."""
        matriz_A, vector_b = self.obtener_datos_matriz()
        return exportar_ecuaciones_desde_datos(matriz_A, vector_b, preserve_shape)

    def import_from_parsed(self, matriz_importada: Any) -> None:
        """Reconstruye la cuadricula desde una matriz con datos parseados."""
        if matriz_importada.filas > DIMENSION_MAXIMA_SISTEMAS or (matriz_importada.columnas - 1) > DIMENSION_MAXIMA_SISTEMAS:
            ui.notify(f"El sistema excede el limite permitido ({DIMENSION_MAXIMA_SISTEMAS}x{DIMENSION_MAXIMA_SISTEMAS}).", type="warning")
            return

        self.m = matriz_importada.filas
        self.n = matriz_importada.columnas - 1
        self._cache_A.clear()
        self._cache_b.clear()

        for i in range(self.m):
            for j in range(self.n):
                val_s = str(matriz_importada.datos[i][j])
                if val_s != "0":
                    self._cache_A[(i, j)] = val_s
            val_b = str(matriz_importada.datos[i][-1])
            if val_b != "0":
                self._cache_b[i] = val_b

        self.generar_cuadricula()
        if self.on_data_change:
            self.on_data_change()

    def cargar_datos(self, matriz_A: list[list[str]], vector_b: list[str]) -> None:
        """Carga datos directamente actualizando dimensiones y cuadricula."""
        self.m = len(matriz_A)
        self.n = len(matriz_A[0]) if self.m > 0 else 3
        self._cache_A.clear()
        self._cache_b.clear()
        for i, row in enumerate(matriz_A):
            for j, val in enumerate(row):
                s = str(val).strip()
                if s and s != "0":
                    self._cache_A[(i, j)] = s
        for i, val in enumerate(vector_b):
            s = str(val).strip()
            if s and s != "0":
                self._cache_b[i] = s
        self.generar_cuadricula()
        if self.on_data_change:
            self.on_data_change()
