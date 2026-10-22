"""Cuadricula interactiva de captura para sistemas de ecuaciones lineales."""
from __future__ import annotations
from src.backend.utilidades.estado_captura import captura_vacia

from functools import partial
from typing import Any, Callable
from nicegui import ui

from src.frontend.componentes.cuadricula_base import (
    DIMENSION_MINIMA,
    cache_matriz_desde_datos,
    sincronizar_cache_celdas,
    actualizar_estados_botones_dimension,
    ejecutar_transicion_cuadricula, selectores_cambio_dimension, indice_cambio_dimension,
    purgar_cache_bidimensional,
    purgar_cache_unidimensional,
)
from src.backend.resolutores.sistemas_lineales.exportacion_ecuaciones import exportar_ecuaciones_desde_datos
from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS
from .redimension_ecuaciones import crear_fila_ecuaciones, redimensionar_ecuaciones, actualizar_presentacion


def _renderizar_cabecera_columnas(numero_columnas: int) -> ui.row:
    """Renderiza la cabecera fija de variables xj y termino b."""
    with ui.row().classes(
        "items-center gap-2 mb-2 no-wrap w-full z-10 bg-[var(--bg-panel)] cuadricula-cabecera-fija"
    ) as cabecera:
        for j in range(numero_columnas):
            ui.html(f"x<sub>{j+1}</sub>").classes("cuadricula-celda text-center matematicas-etiqueta")
        ui.label("=").classes("w-8 text-center text-transparent flex-shrink-0")
        ui.label("b").classes("cuadricula-celda text-center matematicas-etiqueta")
    return cabecera


def _construir_botones_tamanos(cuadricula: Any) -> None:
    """Construye los botones de dimension vertical de ecuaciones."""
    with ui.column().classes("gap-2 mt-12 items-center justify-center mr-2"):
        cuadricula.boton_agregar_fila = ui.button(
            icon="add", on_click=partial(cuadricula.ajustar_tamano, incremento_filas=1), color=None
        ).classes("boton-icono w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Añadir Ecuacion"').tooltip("Añadir Ecuacion")
        cuadricula.boton_quitar_fila = ui.button(
            icon="remove", on_click=partial(cuadricula.ajustar_tamano, incremento_filas=-1), color=None
        ).classes("boton-icono w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Quitar Ecuacion"').tooltip("Quitar Ecuacion")


def _construir_botones_variables(cuadricula: Any) -> None:
    """Construye los botones inferiores de anadir o quitar variables xj."""
    with ui.row().classes("w-full justify-center gap-2 mt-4"):
        cuadricula.boton_agregar_columna = ui.button(
            icon="add", on_click=partial(cuadricula.ajustar_tamano, incremento_columnas=1), color=None
        ).classes("boton-icono w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Añadir Variable"').tooltip("Añadir Variable")
        cuadricula.boton_quitar_columna = ui.button(
            icon="remove", on_click=partial(cuadricula.ajustar_tamano, incremento_columnas=-1), color=None
        ).classes("boton-icono w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Quitar Variable"').tooltip("Quitar Variable")


def _renderizar_fila_entradas(cuadricula: CuadriculaEcuaciones, i: int) -> None:
    """Renderiza una fila con entradas de coeficientes y celda de resultado b."""
    crear_fila_ecuaciones(cuadricula, i)


class CuadriculaEcuaciones:
    """Cuadricula de captura de matriz de coeficientes y terminos independientes."""

    def __init__(self, filas_iniciales: int = 3, columnas_iniciales: int = 3) -> None:
        self.filas_interfaz: list[ui.row] = []
        self.entradas_coeficientes: list[list[ui.input]] = []
        self.entradas_independientes: list[ui.input] = []
        self.filas: int = filas_iniciales
        self.columnas: int = columnas_iniciales
        self.modo_homogeneo = False
        self.contenedor_matriz: ui.column | None = None
        self.etiqueta_forma: ui.html | None = None
        self._cache_coeficientes: dict[tuple[int, int], str] = {}
        self._cache_independientes: dict[int, str] = {}
        self.al_cambiar_datos: Callable[[], None] | None = None
        self.boton_quitar_fila: ui.button | None = None
        self.boton_agregar_fila: ui.button | None = None
        self.boton_quitar_columna: ui.button | None = None
        self.boton_agregar_columna: ui.button | None = None

    @staticmethod
    def inyectar_recursos_cliente() -> None:
        """Inyecta el script asociado para animaciones de la cuadricula de ecuaciones."""
        ui.add_head_html('<script src="/assets/js/captura_ecuaciones.js"></script>')

    async def ajustar_tamano(self, incremento_filas: int = 0, incremento_columnas: int = 0) -> None:
        """Ajusta las dimensiones de ecuaciones o variables con animacion."""
        nuevo_m = self.filas + incremento_filas
        nuevo_n = self.columnas + incremento_columnas
        if not (DIMENSION_MINIMA <= nuevo_m <= DIMENSION_MAXIMA_SISTEMAS) or not (
            DIMENSION_MINIMA <= nuevo_n <= DIMENSION_MAXIMA_SISTEMAS
        ):
            return

        incremento = incremento_filas or incremento_columnas
        indice = indice_cambio_dimension(self.filas, nuevo_m) if incremento_filas else indice_cambio_dimension(self.columnas, nuevo_n)
        atributo = "fila" if incremento_filas else "columna"
        selector = f"#{self.contenedor_matriz.html_id} input[data-ecuaciones-{atributo}='{indice}']" if self.contenedor_matriz else ""
        botones = (self.boton_quitar_fila, self.boton_agregar_fila, self.boton_quitar_columna, self.boton_agregar_columna)
        await ejecutar_transicion_cuadricula(
            vars(self), selectores_cambio_dimension(selector, incremento),
            partial(self._aplicar_tamano, nuevo_m, nuevo_n), botones, self._actualizar_botones_dimension,
        )

    def _aplicar_tamano(self, nuevo_m: int, nuevo_n: int) -> None:
        self._sincronizar_cache_desde_entradas()
        anterior = self.filas, self.columnas
        self.filas = nuevo_m
        self.columnas = nuevo_n
        self._cache_coeficientes = purgar_cache_bidimensional(self._cache_coeficientes, self.filas, self.columnas)
        self._cache_independientes = purgar_cache_unidimensional(self._cache_independientes, self.filas)

        if not redimensionar_ecuaciones(self, anterior):
            self.entradas_coeficientes.clear()
            self.entradas_independientes.clear()
            self.generar_cuadricula()
        else:
            actualizar_presentacion(self)
            if anterior[1] != self.columnas:
                self.cabecera_columnas.delete()
                with self.contenedor_matriz:
                    self.cabecera_columnas = _renderizar_cabecera_columnas(self.columnas)
                self.cabecera_columnas.move(target_index=0)
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def _actualizar_botones_dimension(self) -> None:
        actualizar_estados_botones_dimension(self.boton_quitar_fila, self.boton_agregar_fila, self.filas, DIMENSION_MINIMA, DIMENSION_MAXIMA_SISTEMAS)
        actualizar_estados_botones_dimension(self.boton_quitar_columna, self.boton_agregar_columna, self.columnas, DIMENSION_MINIMA, DIMENSION_MAXIMA_SISTEMAS)

    def construir_contenedor_cuadricula(self) -> None:
        """Construye el contenedor principal con indicadores y controles de redimensionado."""
        with ui.row().classes("w-full justify-between items-end mb-4 px-2"):
            self.etiqueta_forma = ui.html().classes("fuente-pequena texto-secundario uppercase etiqueta-dimensiones")

        with ui.row().classes("w-full items-start no-wrap gap-2"):
            self.contenedor_matriz = ui.column().classes(
                "overflow-auto panel-tarjeta p-4 flex-1 cuadricula-area-desplazamiento cuadricula-desplazamiento"
            )
            _construir_botones_tamanos(self)

        _construir_botones_variables(self)
        self.generar_cuadricula()

    def generar_cuadricula(self) -> None:
        """Regenera los widgets de entrada de la matriz a partir del cache actualizado."""
        self._sincronizar_cache_desde_entradas()
        if self.contenedor_matriz:
            self.contenedor_matriz.clear()
        self.entradas_coeficientes.clear()
        self.entradas_independientes.clear()
        self.filas_interfaz.clear()

        actualizar_presentacion(self)
        if self.contenedor_matriz:
            with self.contenedor_matriz:
                self._renderizar_filas_cuadricula()

    def _sincronizar_cache_desde_entradas(self) -> None:
        """Copia valores no vacios desde las celdas UI al diccionario de cache."""
        sincronizar_cache_celdas(self.entradas_coeficientes, self._cache_coeficientes)
        if self.modo_homogeneo:
            return
        for i, celda in enumerate(self.entradas_independientes):
            if celda.value:
                self._cache_independientes[i] = celda.value

    def _renderizar_filas_cuadricula(self) -> None:
        """Renderiza la cabecera fija y las filas de coeficientes y termino independiente."""
        self.cabecera_columnas = _renderizar_cabecera_columnas(self.columnas)
        with ui.column().classes("cuadricula-contenido") as contenido:
            self.contenido_celdas = contenido
            for i in range(self.filas):
                _renderizar_fila_entradas(self, i)

    def _actualizar_celda(self, es_b: bool, r: int, c: int, valor: str) -> None:
        """Actualiza el cache de coeficientes o vector b y notifica el cambio."""
        if es_b and self.modo_homogeneo:
            return
        if es_b:
            self._cache_independientes[r] = valor
        else:
            self._cache_coeficientes[(r, c)] = valor
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def obtener_datos_matriz(self) -> tuple[list[list[str]], list[str]]:
        """Obtiene las matrices numericas A y vector b como cadenas de texto."""
        coeficientes = [
            [(celda.value.strip() if celda.value else "0") for celda in fila]
            for fila in self.entradas_coeficientes
        ]
        independientes = [
            (celda.value.strip() if celda.value else "0") for celda in self.entradas_independientes
        ]
        return coeficientes, ["0"] * self.filas if self.modo_homogeneo else independientes

    def esta_completamente_vacio(self) -> bool:
        """Determina si la totalidad de celdas de la cuadricula estan sin llenar."""
        entradas = [celda for fila in self.entradas_coeficientes for celda in fila]
        entradas.extend(self.entradas_independientes)
        return captura_vacia((celda.value for celda in entradas), considerar_cero=False)

    def limpiar(self) -> None:
        """Limpia el contenido de todas las celdas y purga el cache."""
        self._cache_coeficientes.clear()
        self._cache_independientes.clear()
        for fila in self.entradas_coeficientes:
            for celda in fila:
                celda.value = ""
        for celda in self.entradas_independientes:
            celda.value = "0" if self.modo_homogeneo else ""
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def establecer_modo_homogeneo(self, activo: bool) -> None:
        """Fija b=0 conservando el cache general y notifica el cambio; no interpreta numeros."""
        if self.modo_homogeneo == activo:
            return
        self._sincronizar_cache_desde_entradas()
        self.entradas_independientes.clear()
        self.modo_homogeneo = activo
        self.generar_cuadricula()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def exportar_a_ecuaciones(self, conservar_forma: bool = False) -> list[str]:
        """Genera una lista de cadenas con ecuaciones formateadas algebraicamente."""
        coeficientes, vector_b = self.obtener_datos_matriz()
        return exportar_ecuaciones_desde_datos(coeficientes, vector_b, conservar_forma)

    def importar_desde_analizados(self, matriz_importada: Any) -> None:
        """Reconstruye la cuadricula desde una matriz con datos parseados."""
        if matriz_importada.filas > DIMENSION_MAXIMA_SISTEMAS or (matriz_importada.columnas - 1) > DIMENSION_MAXIMA_SISTEMAS:
            ui.notify(f"El sistema excede el limite permitido ({DIMENSION_MAXIMA_SISTEMAS}x{DIMENSION_MAXIMA_SISTEMAS}).", type="warning")
            return

        coeficientes = [[str(valor) for valor in fila[:-1]] for fila in matriz_importada.datos]
        independientes = [str(fila[-1]) for fila in matriz_importada.datos]
        self.cargar_datos(coeficientes, independientes)

    def cargar_datos(self, coeficientes: list[list[str]], vector_b: list[str]) -> None:
        """Carga datos directamente actualizando dimensiones y cuadricula."""
        self.filas = len(coeficientes)
        self.columnas = len(coeficientes[0]) if self.filas > 0 else 3
        self.modo_homogeneo = False
        self.entradas_coeficientes.clear()
        self.entradas_independientes.clear()
        self._cache_coeficientes.clear()
        self._cache_independientes.clear()
        self._cache_coeficientes.update(cache_matriz_desde_datos(coeficientes))
        for i, valor in enumerate(vector_b):
            texto = str(valor).strip()
            if texto and texto != "0":
                self._cache_independientes[i] = texto
        self.generar_cuadricula()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()
