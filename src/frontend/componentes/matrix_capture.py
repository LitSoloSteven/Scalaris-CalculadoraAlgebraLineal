"""Panel para capturar y manipular multiples matrices con nombres literales (A-Z)."""
from __future__ import annotations

from functools import partial
import string
from typing import Any, Callable
from nicegui import ui

from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.componentes.cuadricula_base import (
    DIMENSION_MINIMA,
    actualizar_estados_botones_dimension,
    animar_entrada_cuadricula,
    animar_salida_cuadricula,
    props_celda_accesible,
    purgar_cache_bidimensional,
)
from src.frontend.constantes import DIMENSION_MAXIMA_MATRICES


def _validar_deltas(mat: dict[str, Any], delta_m: int, delta_n: int) -> tuple[int, int] | None:
    """Valida los nuevos tamanos y devuelve la tupla (nuevo_m, nuevo_n) si es admisible."""
    nuevo_m = mat["m"] + delta_m
    nuevo_n = mat["n"] + delta_n
    if delta_m and not (DIMENSION_MINIMA <= nuevo_m <= DIMENSION_MAXIMA_MATRICES):
        return None
    if delta_n and not (DIMENSION_MINIMA <= nuevo_n <= DIMENSION_MAXIMA_MATRICES):
        return None
    return nuevo_m, nuevo_n


def _construir_cabecera_tarjeta(panel: MatrixCapturePanel, name: str, mat: dict[str, Any]) -> None:
    """Genera la fila superior con titulo, badge y boton de eliminacion."""
    with ui.row().classes("w-full justify-between items-center mb-2"):
        with ui.row().classes("items-center gap-2"):
            ui.label(f"Matriz {name}").classes("font-bold text-main text-base")
            mat["lbl_badge"] = ui.html(
                f'{name} <span class="separador-punto">·</span> {mat["m"]} &times; {mat["n"]}'
            ).classes("fs-small text-sec uppercase etiqueta-dimensiones")

        with ui.row().classes("items-center gap-2"):
            if panel.on_invert:
                ui.button("Invertir", on_click=lambda nm=name: panel.on_invert(nm)).classes(
                    "btn-ghost text-xs"
                ).props('ripple=false aria-label="Invertir Matriz"')
            ui.button(
                icon="delete", on_click=partial(panel.eliminar_matriz, name), color=None
            ).classes("btn-ghost w-8 h-8 p-0 ml-1 btn-eliminar-elemento").props(
                'ripple=false aria-label="Eliminar Matriz"'
            ).tooltip("Eliminar Matriz")


def _extraer_matriz_exacta(mat: dict[str, Any]) -> Matriz:
    """Extrae valores numericos exactos de las celdas UI de una matriz."""
    filas_datos = []
    for fila_ui in mat["entradas"]:
        fila_vals = []
        for celda in fila_ui:
            txt = celda.value.strip() if celda.value else "0"
            valida, frac, _ = ValidadorMatriz.parse_number_exact(txt)
            fila_vals.append(frac if valida else 0)
        filas_datos.append(fila_vals)
    return Matriz(filas_datos)


def _crear_cache_desde_filas(data: list[list[str]]) -> dict[tuple[int, int], str]:
    """Genera un mapa de coordenadas a cadenas omitiendo los ceros vacios."""
    cache = {}
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            s = str(val).strip()
            if s and s != "0":
                cache[(r, c)] = s
    return cache


def _construir_controles_dimension_ui(panel: Any, name: str, mat: dict[str, Any]) -> None:
    """Construye los botones de filas y columnas de la tarjeta."""
    with ui.row().classes("w-full justify-start items-center gap-4 mb-2"):
        with ui.row().classes("items-center gap-1"):
            ui.label("Filas:").classes("text-sm text-sec mr-1")
            mat["btn_m_dec"] = ui.button(
                icon="remove", on_click=partial(panel.adjust_size, name, delta_m=-1), color=None
            ).classes("btn-neo-icon w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Quitar Fila"')
            mat["lbl_m"] = ui.label(str(mat["m"])).classes("font-bold w-4 text-center")
            mat["btn_m_inc"] = ui.button(
                icon="add", on_click=partial(panel.adjust_size, name, delta_m=1), color=None
            ).classes("btn-neo-icon w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Añadir Fila"')

        with ui.row().classes("items-center gap-1"):
            ui.label("Columnas:").classes("text-sm text-sec mr-1")
            mat["btn_n_dec"] = ui.button(
                icon="remove", on_click=partial(panel.adjust_size, name, delta_n=-1), color=None
            ).classes("btn-neo-icon w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Quitar Columna"')
            mat["lbl_n"] = ui.label(str(mat["n"])).classes("font-bold w-4 text-center")
            mat["btn_n_inc"] = ui.button(
                icon="add", on_click=partial(panel.adjust_size, name, delta_n=1), color=None
            ).classes("btn-neo-icon w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Añadir Columna"')


class MatrixCapturePanel:
    """Panel dinamico de captura para colecciones de matrices con soporte para redimensionado."""

    def __init__(self) -> None:
        self.matrices: dict[str, dict[str, Any]] = {}
        self.container: ui.column | None = None
        self.on_invert: Callable[[str], None] | None = None
        self.on_data_change: Callable[[], None] | None = None

    @staticmethod
    def inject_scripts() -> None:
        """Inyecta el script asociado para animaciones de celdas matriciales."""
        ui.add_head_html('<script src="/assets/js/matrix_capture.js"></script>')

    def get_next_available_name(self) -> str | None:
        """Obtiene la primera letra disponible del abecedario para nombrar una nueva matriz."""
        for letra in string.ascii_uppercase:
            if letra not in self.matrices:
                return letra
        return None

    def agregar_matriz(self) -> None:
        """Agrega una nueva matriz 3x3 si no se ha alcanzado el limite alfabetico."""
        name = self.get_next_available_name()
        if not name:
            ui.notify("Limite de matrices alcanzado (Z)", type="warning")
            return

        self.matrices[name] = {
            "m": 3, "n": 3, "entradas": [], "cache": {}, "ui_container": None,
            "lbl_m": None, "lbl_n": None, "lbl_badge": None,
            "btn_m_dec": None, "btn_m_inc": None, "btn_n_dec": None, "btn_n_inc": None,
        }
        self.renderizar_todas()
        if self.on_data_change:
            self.on_data_change()

    def eliminar_matriz(self, name: str) -> None:
        """Elimina una matriz identificada por su nombre literal."""
        if name in self.matrices:
            del self.matrices[name]
            self.renderizar_todas()
            if self.on_data_change:
                self.on_data_change()

    async def adjust_size(self, name: str, delta_m: int = 0, delta_n: int = 0) -> None:
        """Ajusta las filas o columnas de una matriz especifica aplicando animacion."""
        if name not in self.matrices:
            return
        mat = self.matrices[name]
        self._sincronizar_cache_matriz(mat)
        res_val = _validar_deltas(mat, delta_m, delta_n)
        if not res_val:
            return
        nuevo_m, nuevo_n = res_val

        self._deshabilitar_botones_matriz(mat)
        if delta_m < 0 or delta_n < 0:
            target = f"[data-matrix-row='{mat['m'] - 1}']" if delta_m < 0 else f"[data-matrix-col='{mat['n'] - 1}']"
            await animar_salida_cuadricula(target, es_fila=(delta_m < 0), indice=mat["m"] - 1, nombre_matriz=name)

        if delta_m:
            mat["m"] = nuevo_m
        if delta_n:
            mat["n"] = nuevo_n
        mat["cache"] = purgar_cache_bidimensional(mat["cache"], mat["m"], mat["n"])
        self._actualizar_etiquetas_matriz(name, mat)
        self.renderizar_cuadricula(name)

        if delta_m > 0 or delta_n > 0:
            target = f"[data-matrix-row='{mat['m'] - 1}']" if delta_m > 0 else f"[data-matrix-col='{mat['n'] - 1}']"
            await animar_entrada_cuadricula(target, nombre_matriz=name)

        if self.on_data_change:
            self.on_data_change()

    def _sincronizar_cache_matriz(self, mat: dict[str, Any]) -> None:
        """Copia valores actuales de la UI al cache de celdas."""
        for r, fila in enumerate(mat["entradas"]):
            for c, celda in enumerate(fila):
                if celda.value:
                    mat["cache"][(r, c)] = celda.value

    def _deshabilitar_botones_matriz(self, mat: dict[str, Any]) -> None:
        """Deshabilita temporalmente los botones de dimension de la matriz."""
        for clave in ("btn_m_dec", "btn_m_inc", "btn_n_dec", "btn_n_inc"):
            btn = mat.get(clave)
            if btn:
                btn.disable()

    def _actualizar_etiquetas_matriz(self, name: str, mat: dict[str, Any]) -> None:
        """Actualiza los textos de conteo y badge de dimensiones."""
        if mat["lbl_m"]:
            mat["lbl_m"].set_text(str(mat["m"]))
        if mat["lbl_n"]:
            mat["lbl_n"].set_text(str(mat["n"]))
        if mat["lbl_badge"]:
            mat["lbl_badge"].content = f'{name} <span class="separador-punto">·</span> {mat["m"]} &times; {mat["n"]}'

    def renderizar_cuadricula(self, name: str) -> None:
        """Renderiza las celdas de una matriz concreta con nombres accesibles."""
        mat = self.matrices[name]
        if not mat["ui_container"]:
            return
        mat["ui_container"].clear()
        mat["entradas"].clear()

        actualizar_estados_botones_dimension(mat["btn_m_dec"], mat["btn_m_inc"], mat["m"], DIMENSION_MINIMA, DIMENSION_MAXIMA_MATRICES)
        actualizar_estados_botones_dimension(mat["btn_n_dec"], mat["btn_n_inc"], mat["n"], DIMENSION_MINIMA, DIMENSION_MAXIMA_MATRICES)

        with mat["ui_container"]:
            with ui.column().classes("cuadricula-contenido"):
                for i in range(mat["m"]):
                    self._renderizar_fila_matriz(name, mat, i)

    def _renderizar_fila_matriz(self, name: str, mat: dict[str, Any], i: int) -> None:
        """Construye una fila de entradas para la matriz indicada."""
        with ui.row().classes("items-center gap-2 mb-2 no-wrap").props(f'data-grid-row="{name}_{i}"'):
            fila_ui = []
            for j in range(mat["n"]):
                val = mat["cache"].get((i, j), "")
                props = props_celda_accesible(i, j, id_matriz=name, nombre_campo=f"{name}_r{i}c{j}")
                celda = ui.input(
                    value=val,
                    placeholder="",
                    on_change=lambda e, r=i, c=j, nm=name: self._al_cambiar_celda(nm, r, c, e.value),
                ).classes("matrix-input grid-cell").props(props)
                fila_ui.append(celda)
            mat["entradas"].append(fila_ui)

    def _al_cambiar_celda(self, name: str, r: int, c: int, val: str) -> None:
        """Guarda el valor en cache y notifica a observadores."""
        self.matrices[name]["cache"][(r, c)] = val
        if self.on_data_change:
            self.on_data_change()

    def renderizar_todas(self) -> None:
        """Reconstruye todos los paneles de matriz registrados."""
        if not self.container:
            return
        self.container.clear()
        with self.container:
            for name in sorted(self.matrices.keys()):
                self._construir_tarjeta_matriz(name)

    def _construir_tarjeta_matriz(self, name: str) -> None:
        """Genera la tarjeta contenedora y cabecera de control para una matriz."""
        mat = self.matrices[name]
        with ui.column().classes("panel-card p-4 mb-4 w-full"):
            _construir_cabecera_tarjeta(self, name, mat)
            self._construir_controles_dimension(name, mat)
            mat["ui_container"] = ui.column().classes(
                "overflow-auto w-full grid-scroll cuadricula-desplazamiento"
            )
            self.renderizar_cuadricula(name)

    def _construir_controles_dimension(self, name: str, mat: dict[str, Any]) -> None:
        """Construye los botones de filas y columnas de la tarjeta."""
        _construir_controles_dimension_ui(self, name, mat)

    def build(self, container: ui.column) -> None:
        """Asigna el contenedor padre y renderiza la coleccion."""
        self.container = container
        if not self.matrices:
            self.agregar_matriz()
        else:
            self.renderizar_todas()

    def obtener_diccionario_matrices(self) -> dict[str, Matriz]:
        """Extrae el diccionario de matrices construidas con aritmetica exacta."""
        return {name: _extraer_matriz_exacta(mat) for name, mat in self.matrices.items()}

    def cargar_datos(self, matrices_dict: dict[str, list[list[str]]]) -> None:
        """Carga un conjunto de matrices reemplazando el contenido existente."""
        self.matrices.clear()
        for name, data in matrices_dict.items():
            m = len(data)
            n = len(data[0]) if m > 0 else 3
            self.matrices[name] = {
                "m": m, "n": n, "entradas": [], "cache": _crear_cache_desde_filas(data), "ui_container": None,
                "lbl_m": None, "lbl_n": None, "lbl_badge": None,
                "btn_m_dec": None, "btn_m_inc": None, "btn_n_dec": None, "btn_n_inc": None,
            }
        self.renderizar_todas()
        if self.on_data_change:
            self.on_data_change()
