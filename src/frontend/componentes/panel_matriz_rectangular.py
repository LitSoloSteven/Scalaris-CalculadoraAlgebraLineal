"""Captura de una matriz rectangular con controles independientes por eje."""
from collections.abc import Callable
from functools import partial
from nicegui import ui

from src.backend.constantes import DIMENSION_MAXIMA_MATRICES, DIMENSION_MINIMA
from src.frontend.componentes.cuadricula_base import propiedades_celda_accesible
from src.frontend.componentes.panel_matriz_rectangular_acciones import AccionesMatrizRectangular
from src.frontend.textos import (CAPTURA_RECTANGULAR_AYUDA, CAPTURA_RECTANGULAR_MATRIZ,
    CAPTURA_RECTANGULAR_PEGAR, CAPTURA_RECTANGULAR_TOOLTIP, CAPTURA_RECTANGULAR_EJES,
    CAPTURA_RECTANGULAR_ACCIONES)

DIMENSION_INICIAL = 3


class PanelMatrizRectangular(AccionesMatrizRectangular):
    """Captura filas y columnas de una matriz A, conservando su caché."""

    def __init__(self) -> None:
        self.filas = self.columnas = DIMENSION_INICIAL
        self.cache: dict[tuple[int, int], str] = {}
        self.celdas = []
        self.filas_interfaz = []
        self.al_cambiar_datos: Callable[[], None] | None = None
        self.contenedor = self.contenedor_cuadricula = None
        self.etiqueta_dimension_matriz = None
        self.controles = {}
        self._redimensionando = False
        self._revision_panel = 0

    @property
    def dimension(self) -> int:
        """Devuelve la mayor dimensión para los límites de presentación."""
        return max(self.filas, self.columnas)

    @staticmethod
    def inyectar_recursos_cliente() -> None:
        """Carga los recursos existentes de navegación y transición matricial."""
        ui.add_head_html('<script src="/assets/js/captura_matrices.js"></script>')
        ui.add_head_html('<script src="/assets/js/matriz_cuadrada.js"></script>')

    def construir_contenedor(self) -> ui.column:
        """Construye el panel, sus controles y la cuadrícula de captura."""
        self.contenedor = ui.column().classes("w-full panel-tarjeta p-4 min-w-0")
        with self.contenedor:
            with ui.row().classes("w-full justify-between items-center flex-wrap gap-2"):
                ui.label(CAPTURA_RECTANGULAR_MATRIZ).classes("text-lg font-bold texto-principal")
                self.etiqueta_dimension_matriz = ui.html().classes("etiqueta-dimensiones sesion-numero")
                self._crear_controles()
                ui.button(CAPTURA_RECTANGULAR_PEGAR, icon="content_paste", color=None, on_click=self.pegar_desde_portapapeles).props(
                    f'ripple=false aria-label="{CAPTURA_RECTANGULAR_TOOLTIP}"').classes("boton-discreto flex-shrink-0").tooltip(CAPTURA_RECTANGULAR_TOOLTIP)
            with ui.column().classes("overflow-auto w-full cuadricula-area-desplazamiento cuadricula-desplazamiento"):
                self.contenedor_cuadricula = ui.column().classes("cuadricula-contenido")
                self._renderizar_completa()
            ui.label(CAPTURA_RECTANGULAR_AYUDA.format(limite=DIMENSION_MAXIMA_MATRICES)).classes("text-xs texto-secundario mt-2")
        self._actualizar_controles()
        return self.contenedor

    def _crear_controles(self) -> None:
        for eje, etiqueta in CAPTURA_RECTANGULAR_EJES:
            with ui.row().classes("items-center gap-1"):
                ui.label(etiqueta).classes("text-sm texto-secundario")
                botones = []
                for delta, icono, accion in CAPTURA_RECTANGULAR_ACCIONES:
                    nombre = f"{accion} {etiqueta.lower()}"
                    boton = ui.button(icon=icono, color=None, on_click=partial(self.redimensionar, eje, delta)).props(
                        f'ripple=false aria-label="{nombre}"').classes("boton-icono w-8 h-8 p-0 flex-shrink-0").tooltip(nombre)
                    botones.append(boton)
                self.controles[eje] = botones

    def _renderizar_completa(self) -> None:
        if self.contenedor_cuadricula is None:
            return
        self.contenedor_cuadricula.clear()
        self.celdas.clear()
        self.filas_interfaz.clear()
        with self.contenedor_cuadricula:
            for fila in range(self.filas):
                self._anadir_fila(fila)

    def _anadir_fila(self, fila: int) -> None:
        with ui.row().classes("items-center gap-2 mb-2 no-wrap").props(f'data-matriz-fila="{fila}"') as contenedor:
            self.filas_interfaz.append(contenedor)
            self.celdas.append([self._crear_celda(fila, columna) for columna in range(self.columnas)])

    def _crear_celda(self, fila: int, columna: int) -> ui.input:
        propiedades = propiedades_celda_accesible(fila, columna, identificador_matriz="A", nombre_campo=f"A_r{fila}c{columna}")
        return ui.input(value=self.cache.get((fila, columna), ""), on_change=lambda evento: self._cambiar_celda(fila, columna, evento.value)).classes(
            "matriz-entrada cuadricula-celda min-w-0").props(propiedades)

    def _cambiar_celda(self, fila: int, columna: int, valor: str) -> None:
        self._revision_panel += 1
        if valor:
            self.cache[(fila, columna)] = valor
        else:
            self.cache.pop((fila, columna), None)
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def obtener_datos_matriz(self) -> list[list[str]]:
        """Devuelve las celdas actuales, interpretando las vacías como cero."""
        return [[self.cache.get((fila, columna), "0") or "0" for columna in range(self.columnas)] for fila in range(self.filas)]

    def cargar_matriz(self, datos: list[list[str]]) -> None:
        """Carga datos rectangulares, rellenando huecos y limitando sus dimensiones."""
        if not datos or not any(datos):
            return
        self._revision_panel += 1
        self.filas = min(len(datos), DIMENSION_MAXIMA_MATRICES)
        self.columnas = min(max(len(fila) for fila in datos[:self.filas]), DIMENSION_MAXIMA_MATRICES)
        recortados = [fila[:self.columnas] + ["0"] * max(0, self.columnas - len(fila)) for fila in datos[:self.filas]]
        self.cache = {(fila, columna): str(valor).strip() for fila, valores in enumerate(recortados)
                      for columna, valor in enumerate(valores) if str(valor).strip()}
        self._publicar()

    def esta_vacio(self) -> bool:
        """Indica si no hay valores escritos en la captura."""
        return not bool(self.cache)

    def limpiar(self) -> None:
        """Vacía la captura conservando sus dimensiones."""
        self._revision_panel += 1
        self.cache.clear()
        self._publicar()
