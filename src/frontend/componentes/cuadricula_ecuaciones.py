"""Cuadricula interactiva de captura para sistemas de ecuaciones lineales."""
from __future__ import annotations

from functools import partial
from typing import Any, Callable
from nicegui import ui

from src.frontend.componentes.cuadricula_base import (
    DIMENSION_MINIMA,
    cache_matriz_desde_datos,
    deshabilitar_botones_dimension,
    sincronizar_cache_celdas,
    actualizar_estados_botones_dimension,
    animar_entrada_cuadricula,
    animar_salida_cuadricula,
    propiedades_celda_accesible,
    purgar_cache_bidimensional,
    purgar_cache_unidimensional,
)
from src.backend.resolutores.sistemas_lineales.exportacion_ecuaciones import exportar_ecuaciones_desde_datos
from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS


def _renderizar_cabecera_columnas(numero_columnas: int) -> None:
    """Renderiza la cabecera fija de variables xj y termino b."""
    with ui.row().classes(
        "items-center gap-2 mb-2 no-wrap w-full z-10 bg-[var(--bg-panel)] cuadricula-cabecera-fija"
    ):
        for j in range(numero_columnas):
            ui.html(f"x<sub>{j+1}</sub>").classes("cuadricula-celda text-center matematicas-etiqueta")
        ui.label("=").classes("w-8 text-center text-transparent flex-shrink-0")
        ui.label("b").classes("cuadricula-celda text-center matematicas-etiqueta")


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
    with ui.row().classes("items-center gap-2 mb-2 no-wrap").props(f'data-cuadricula-fila="{i}"'):
        fila_coeficientes = []
        for j in range(cuadricula.columnas):
            valor = cuadricula._cache_coeficientes.get((i, j), "")
            propiedades = propiedades_celda_accesible(i, j, nombre_campo=f"r{i}c{j}")
            celda = ui.input(
                value=valor,
                placeholder="",
                on_change=lambda evento, r=i, c=j: cuadricula._actualizar_celda(False, r, c, evento.value),
            ).classes("matriz-entrada cuadricula-celda").props(propiedades)
            fila_coeficientes.append(celda)
        cuadricula.entradas_coeficientes.append(fila_coeficientes)

        ui.label("=").classes("w-8 text-center matematicas-etiqueta text-xl flex-shrink-0")
        valor_independiente = cuadricula._cache_independientes.get(i, "")
        propiedades_independiente = propiedades_celda_accesible(i, cuadricula.columnas, nombre_campo=f"r{i}cb")
        celda_b = ui.input(
            value=valor_independiente,
            placeholder="",
            on_change=lambda evento, r=i: cuadricula._actualizar_celda(True, r, 0, evento.value),
        ).classes("matriz-entrada cuadricula-celda").props(propiedades_independiente)
        cuadricula.entradas_independientes.append(celda_b)


class CuadriculaEcuaciones:
    """Cuadricula de captura de matriz de coeficientes y terminos independientes."""

    def __init__(self, filas_iniciales: int = 3, columnas_iniciales: int = 3) -> None:
        self.entradas_coeficientes: list[list[ui.input]] = []
        self.entradas_independientes: list[ui.input] = []
        self.filas: int = filas_iniciales
        self.columnas: int = columnas_iniciales
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

        self._deshabilitar_botones_redimension()
        if incremento_filas < 0 or incremento_columnas < 0:
            selector_destino = f"[data-ecuaciones-fila='{self.filas - 1}']" if incremento_filas < 0 else f"[data-ecuaciones-columna='{self.columnas - 1}']"
            await animar_salida_cuadricula(selector_destino)

        self.filas = nuevo_m
        self.columnas = nuevo_n
        self._cache_coeficientes = purgar_cache_bidimensional(self._cache_coeficientes, self.filas, self.columnas)
        self._cache_independientes = purgar_cache_unidimensional(self._cache_independientes, self.filas)

        self.generar_cuadricula()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

        if incremento_filas > 0 or incremento_columnas > 0:
            selector_destino = f"[data-ecuaciones-fila='{self.filas - 1}']" if incremento_filas > 0 else f"[data-ecuaciones-columna='{self.columnas - 1}']"
            await animar_entrada_cuadricula(selector_destino)

    def _deshabilitar_botones_redimension(self) -> None:
        """Deshabilita temporalmente los botones de tamano durante la animacion."""
        deshabilitar_botones_dimension((
            self.boton_quitar_fila, self.boton_agregar_fila,
            self.boton_quitar_columna, self.boton_agregar_columna,
        ))

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

        texto_forma = "Sistema Cuadrado" if self.filas == self.columnas else "Sistema Rectangular"
        if self.etiqueta_forma:
            self.etiqueta_forma.content = (
                f'{texto_forma} <span class="separador-punto">·</span> {self.filas} &times; {self.columnas}'
            )

        actualizar_estados_botones_dimension(self.boton_quitar_fila, self.boton_agregar_fila, self.filas, DIMENSION_MINIMA, DIMENSION_MAXIMA_SISTEMAS)
        actualizar_estados_botones_dimension(self.boton_quitar_columna, self.boton_agregar_columna, self.columnas, DIMENSION_MINIMA, DIMENSION_MAXIMA_SISTEMAS)

        if self.contenedor_matriz:
            with self.contenedor_matriz:
                self._renderizar_filas_cuadricula()

    def _sincronizar_cache_desde_entradas(self) -> None:
        """Copia valores no vacios desde las celdas UI al diccionario de cache."""
        sincronizar_cache_celdas(self.entradas_coeficientes, self._cache_coeficientes)
        for i, celda in enumerate(self.entradas_independientes):
            if celda.value:
                self._cache_independientes[i] = celda.value

    def _renderizar_filas_cuadricula(self) -> None:
        """Renderiza la cabecera fija y las filas de coeficientes y termino independiente."""
        _renderizar_cabecera_columnas(self.columnas)
        with ui.column().classes("cuadricula-contenido"):
            for i in range(self.filas):
                _renderizar_fila_entradas(self, i)

    def _actualizar_celda(self, es_b: bool, r: int, c: int, valor: str) -> None:
        """Actualiza el cache de coeficientes o vector b y notifica el cambio."""
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
        return coeficientes, independientes

    def esta_completamente_vacio(self) -> bool:
        """Determina si la totalidad de celdas de la cuadricula estan sin llenar."""
        for fila in self.entradas_coeficientes:
            for celda in fila:
                if celda.value and str(celda.value).strip() != "":
                    return False
        for celda in self.entradas_independientes:
            if celda.value and str(celda.value).strip() != "":
                return False
        return True

    def limpiar(self) -> None:
        """Limpia el contenido de todas las celdas y purga el cache."""
        self._cache_coeficientes.clear()
        self._cache_independientes.clear()
        for fila in self.entradas_coeficientes:
            for celda in fila:
                celda.value = ""
        for celda in self.entradas_independientes:
            celda.value = ""
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

        self.filas = matriz_importada.filas
        self.columnas = matriz_importada.columnas - 1
        self._cache_coeficientes.clear()
        self._cache_independientes.clear()

        for i in range(self.filas):
            for j in range(self.columnas):
                valor_texto = str(matriz_importada.datos[i][j])
                if valor_texto != "0":
                    self._cache_coeficientes[(i, j)] = valor_texto
            valor_independiente = str(matriz_importada.datos[i][-1])
            if valor_independiente != "0":
                self._cache_independientes[i] = valor_independiente

        self.generar_cuadricula()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def cargar_datos(self, coeficientes: list[list[str]], vector_b: list[str]) -> None:
        """Carga datos directamente actualizando dimensiones y cuadricula."""
        self.filas = len(coeficientes)
        self.columnas = len(coeficientes[0]) if self.filas > 0 else 3
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
