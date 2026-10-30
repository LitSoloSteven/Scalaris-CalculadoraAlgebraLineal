"""Captura de matrices cuadradas con caché de celdas y controles de dimensión."""
from __future__ import annotations

import logging
from functools import partial
from typing import Callable

from nicegui import ui

from src.frontend.componentes.cuadricula_base import (
    DIMENSION_MINIMA,
    actualizar_estados_botones_dimension,
    cache_matriz_desde_datos,
    propiedades_celda_accesible,
    purgar_cache_bidimensional,
    ejecutar_transicion_cuadricula, selectores_cambio_dimension, selector_dimension_matriz,
    CambioCuadricula, indice_cambio_dimension,
)
from .redimension_matriz_cuadrada import redimensionar_celdas, actualizar_etiqueta_dimension, DIMENSION_MAXIMA_CELDA_NORMAL
from .tareas import lanzar_tarea
from .animacion_matriz import animar_redimension_matriz
from .portapapeles_matricial import parsear_texto_portapapeles
from src.backend.constantes import DIMENSION_MAXIMA_INVERSA

registro = logging.getLogger(__name__)

IDENTIFICADOR_MATRIZ = "A"
DIMENSION_INICIAL = 3


class PanelMatrizCuadrada:
    """Panel de captura de matriz cuadrada con un único control bidimensional (n×n)."""

    def __init__(self, dimension_inicial: int = DIMENSION_INICIAL) -> None:
        self.dimension: int = min(max(dimension_inicial, DIMENSION_MINIMA), DIMENSION_MAXIMA_INVERSA)
        self.cache: dict[tuple[int, int], str] = {}
        self.filas_interfaz: list[ui.row] = []
        self.celdas: list[list[ui.input]] = []
        self.al_cambiar_datos: Callable[[], None] | None = None
        self._suspender_eventos: bool = False
        self._redimensionando: bool = False
        self.contenedor: ui.column | None = None
        self.contenedor_cuadricula: ui.column | None = None
        self.etiqueta_dimension: ui.label | None = None
        self.etiqueta_dimension_matriz: ui.html | None = None
        self.boton_reducir: ui.button | None = None
        self.boton_aumentar: ui.button | None = None

    @staticmethod
    def inyectar_recursos_cliente() -> None:
        """Inyecta los scripts necesarios para navegación y animación de matriz cuadrada."""
        ui.add_head_html('<script src="/assets/js/captura_matrices.js"></script>')
        ui.add_head_html('<script src="/assets/js/matriz_cuadrada.js"></script>')

    def construir_contenedor(self) -> ui.column:
        """Construye el contenedor UI completo del panel."""
        self.contenedor = ui.column().classes("w-full panel-tarjeta p-4")
        with self.contenedor:
            with ui.row().classes("w-full justify-between items-center mb-4 flex-wrap gap-2"):
                with ui.row().classes("items-center gap-2"):
                    ui.label("Matriz A").classes("text-lg font-bold texto-principal")
                    self.etiqueta_dimension_matriz = ui.html(
                        f'{IDENTIFICADOR_MATRIZ} <span class="separador-punto">·</span> {self.dimension} &times; {self.dimension}'
                    ).classes("fuente-pequena texto-secundario uppercase etiqueta-dimensiones")

                with ui.row().classes("items-center gap-3 flex-wrap"):
                    self._construir_controles_tamano()
                    ui.button("Pegar", icon="content_paste", color=None, on_click=self.pegar_desde_portapapeles).props(
                        "ripple=false"
                    ).classes("boton-discreto").tooltip("Pegar matriz desde el portapapeles")

            with ui.column().classes("overflow-auto w-full cuadricula-area-desplazamiento cuadricula-desplazamiento"):
                self.contenedor_cuadricula = ui.column().classes("cuadricula-contenido")
                self._renderizar_completa()

            ui.label(
                f"Pega desde Excel o un bloc de notas (tabuladores o comas). Máx. {DIMENSION_MAXIMA_INVERSA}×{DIMENSION_MAXIMA_INVERSA}."
            ).classes("text-xs texto-secundario mt-2")

        return self.contenedor

    def _construir_controles_tamano(self) -> None:
        """Construye los botones de decremento e incremento de dimensión."""
        with ui.row().classes("items-center gap-1"):
            ui.label("Tamaño:").classes("text-sm texto-secundario mr-1")
            self.boton_reducir = ui.button(
                icon="remove", color=None, on_click=lambda: self.redimensionar(-1)
            ).props('ripple=false aria-label="Quitar fila y columna"').classes(
                "boton-icono w-8 h-8 p-0 flex-shrink-0"
            ).tooltip("Quitar fila y columna")
            self.etiqueta_dimension = ui.label(str(self.dimension)).classes("font-bold w-6 text-center texto-principal")
            self.boton_aumentar = ui.button(
                icon="add", color=None, on_click=lambda: self.redimensionar(+1)
            ).props('ripple=false aria-label="Añadir fila y columna"').classes(
                "boton-icono w-8 h-8 p-0 flex-shrink-0"
            ).tooltip("Añadir fila y columna")
            self._actualizar_botones()

    def _renderizar_completa(self) -> None:
        """Renderiza la cuadrícula completa desde cero usando las filas DOM almacenadas."""
        if not self.contenedor_cuadricula:
            return
        self.contenedor_cuadricula.clear()
        self.filas_interfaz.clear()
        self.celdas.clear()
        with self.contenedor_cuadricula:
            for r in range(self.dimension):
                self._anadir_fila_dom(r)

    def _anadir_fila_dom(self, r: int) -> None:
        """Crea una fila DOM y sus celdas de entrada asociadas."""
        with ui.row().classes("items-center gap-2 mb-2 no-wrap").props(f'data-matriz-fila="{r}"') as fila_interfaz:
            celdas_fila: list[ui.input] = []
            for c in range(self.dimension):
                celda = self._crear_celda_ui(r, c)
                celdas_fila.append(celda)
            self.filas_interfaz.append(fila_interfaz)
            self.celdas.append(celdas_fila)

    def _crear_celda_ui(self, r: int, c: int) -> ui.input:
        """Construye una celda de entrada individual con propiedades accesibles."""
        valor = self.cache.get((r, c), "")
        clase_tam = "cuadricula-celda-compacta" if self.dimension > DIMENSION_MAXIMA_CELDA_NORMAL else "cuadricula-celda"
        propiedades = propiedades_celda_accesible(r, c, identificador_matriz=IDENTIFICADOR_MATRIZ, nombre_campo=f"{IDENTIFICADOR_MATRIZ}_r{r}c{c}")
        return ui.input(
            value=valor,
            placeholder="",
            on_change=lambda evento, fil=r, columna=c: self._al_cambiar_celda(fil, columna, evento.value),
        ).classes(f"matriz-entrada {clase_tam}").props(propiedades)

    def _al_cambiar_celda(self, r: int, c: int, valor: str) -> None:
        """Actualiza el caché ante cambios en una celda y notifica observadores."""
        if self._suspender_eventos:
            return
        if valor:
            self.cache[(r, c)] = valor
        else:
            self.cache.pop((r, c), None)
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def redimensionar(self, delta: int) -> None:
        """Dispara el redimensionamiento asíncrono con paso de delta."""
        if self._redimensionando:
            return
        self._redimensionando = True
        try:
            lanzar_tarea(ui.context.client, self._redimensionar_asincrono(delta))
        except Exception:
            self._redimensionando = False
            raise

    async def _redimensionar_asincrono(self, delta: int) -> None:
        """Aplica la modificación de tamaño con animación DOM."""
        nuevo_n = min(max(self.dimension + delta, DIMENSION_MINIMA), DIMENSION_MAXIMA_INVERSA)
        try:
            if nuevo_n == self.dimension:
                return
            indice = indice_cambio_dimension(self.dimension, nuevo_n)
            selector = selector_dimension_matriz(IDENTIFICADOR_MATRIZ, indice, ("fila", "columna"))
            await ejecutar_transicion_cuadricula(
                vars(self), CambioCuadricula(selectores_cambio_dimension(selector, delta), animar_redimension_matriz),
                partial(self._aplicar_dimension, nuevo_n), (self.boton_reducir, self.boton_aumentar), self._actualizar_botones,
            )
        finally:
            self._redimensionando = False

    def _aplicar_dimension(self, dimension: int) -> None:
        anterior = self.dimension
        self.dimension = dimension
        self.cache = purgar_cache_bidimensional(self.cache, dimension, dimension)
        redimensionar_celdas(self, anterior)
        self._publicar_matriz(reconstruir=False)

    def _actualizar_botones(self) -> None:
        """Actualiza la disponibilidad de los botones de incremento y decremento."""
        actualizar_estados_botones_dimension(self.boton_reducir, self.boton_aumentar, self.dimension, DIMENSION_MINIMA, DIMENSION_MAXIMA_INVERSA)

    def obtener_datos_matriz(self) -> list[list[str]]:
        """Extrae la matriz actual como lista bidimensional de cadenas."""
        return [
            [(self.cache.get((r, c), "0") or "0") for c in range(self.dimension)]
            for r in range(self.dimension)
        ]

    def cargar_matriz(self, datos: list[list[str]]) -> None:
        """Carga una matriz externa adaptando la dimensión n."""
        if not datos or not datos[0]:
            return
        nuevo_n = min(max(len(datos), DIMENSION_MINIMA), DIMENSION_MAXIMA_INVERSA)
        self.cache.clear()
        datos_recortados = [fila[:nuevo_n] for fila in datos[:nuevo_n]]
        self.cache.update(cache_matriz_desde_datos(datos_recortados))
        self.dimension = nuevo_n
        self._publicar_matriz()

    def _publicar_matriz(self, reconstruir: bool = True) -> None:
        actualizar_etiqueta_dimension(self, IDENTIFICADOR_MATRIZ)
        self._actualizar_botones()
        if reconstruir:
            self._renderizar_completa()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    async def pegar_desde_portapapeles(self) -> None:
        """Lee el contenido textual del portapapeles y lo parsea hacia la matriz."""
        try:
            texto = await ui.run_javascript("return navigator.clipboard.readText();")
        except Exception as error:
            registro.warning("No se pudo leer el portapapeles: %s", error)
            ui.notify("No se pudo acceder al portapapeles.", type="warning")
            return
        if not texto:
            return
        filas = parsear_texto_portapapeles(texto)
        if filas:
            self.cargar_matriz(filas)

    def esta_vacio(self) -> bool:
        """Comprueba si todas las celdas están vacías."""
        return not bool(self.cache)

    def limpiar(self) -> None:
        """Vacía las entradas de la matriz conservando su dimensión."""
        self.cache.clear()
        self._renderizar_completa()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()
