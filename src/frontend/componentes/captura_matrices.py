"""Panel para capturar y manipular multiples matrices con nombres literales (A-Z)."""
from __future__ import annotations

from functools import partial
import string
from typing import Any, Callable
from nicegui import ui

from src.frontend.componentes.cuadricula_base import (
    DIMENSION_MINIMA,
    actualizar_estados_botones_dimension,
    ejecutar_transicion_cuadricula, selectores_cambio_dimension, selector_dimension_matriz, indice_cambio_dimension,
    purgar_cache_bidimensional,
)
from src.backend.constantes import DIMENSION_MAXIMA_MATRICES
from .estado_captura_matrices import (
    MATRICES_PERMANENTES, crear_registro_matriz, asegurar_matrices_permanentes,
)
from .redimension_rectangular import actualizar_rectangulo
from .redimension_captura_matrices import crear_celda_matriz, crear_fila_matriz


def _validar_deltas(matriz: dict[str, Any], incremento_filas: int, incremento_columnas: int) -> tuple[int, int] | None:
    """Valida los nuevos tamanos y devuelve la tupla (nuevo_m, nuevo_n) si es admisible."""
    nuevo_m = matriz["filas"] + incremento_filas
    nuevo_n = matriz["columnas"] + incremento_columnas
    if incremento_filas and not (DIMENSION_MINIMA <= nuevo_m <= DIMENSION_MAXIMA_MATRICES):
        return None
    if incremento_columnas and not (DIMENSION_MINIMA <= nuevo_n <= DIMENSION_MAXIMA_MATRICES):
        return None
    return nuevo_m, nuevo_n


def _construir_cabecera_tarjeta(nombre: str, matriz: dict[str, Any]) -> None:
    """Compone título, distintivo de dimensiones y acciones de la matriz indicada."""
    with ui.element("header").classes("captura-matriz-cabecera"):
        ui.label(f"Matriz {nombre}").classes("captura-matriz-titulo texto-principal").props(f'id="matriz-titulo-{nombre}"')
        matriz["etiqueta_dimension_matriz"] = ui.html(
            f'{nombre} <span class="separador-punto">·</span> {matriz["filas"]} &times; {matriz["columnas"]}'
        ).classes("texto-secundario etiqueta-dimensiones")


def _construir_acciones_tarjeta(panel: PanelCapturaMatrices, nombre: str) -> None:
    """Ofrece la transferencia a inversa y la eliminación junto a las dimensiones."""
    with ui.row().classes("captura-matriz-acciones"):
        if panel.al_invertir:
            ui.button(icon="arrow_forward", color=None, on_click=lambda: panel.al_invertir(nombre)).classes(
                "boton-discreto captura-matriz-accion"
            ).props(f'ripple=false aria-label="Abrir matriz {nombre} en Matriz inversa"').tooltip(
                f"Envía una copia de la matriz {nombre} a Matriz inversa para calcular su inversa."
            )
        boton = ui.button(icon="delete", on_click=partial(panel.eliminar_matriz, nombre), color=None).classes(
            "boton-discreto captura-matriz-accion boton-eliminar-elemento"
        ).props(f'ripple=false aria-label="Eliminar matriz {nombre}"').tooltip(f"Eliminar matriz {nombre}")
        boton.set_enabled(nombre not in MATRICES_PERMANENTES)


def _construir_controles_dimension_interfaz(panel: Any, nombre: str, matriz: dict[str, Any]) -> None:
    """Construye los botones de filas y columnas de la tarjeta."""
    with ui.element("div").classes("captura-matriz-herramientas"):
        with ui.row().classes("captura-matriz-dimension").props(f'role="group" aria-label="Filas de la matriz {nombre}"'):
            ui.label("Filas:").classes("text-sm texto-secundario mr-1")
            matriz["boton_quitar_fila"] = ui.button(
                icon="remove", on_click=partial(panel.ajustar_tamano, nombre, incremento_filas=-1), color=None
            ).classes("boton-icono captura-matriz-accion").props(f'ripple=false aria-label="Quitar fila de matriz {nombre}"')
            matriz["etiqueta_filas"] = ui.label(str(matriz["filas"])).classes("font-bold w-4 text-center")
            matriz["boton_agregar_fila"] = ui.button(
                icon="add", on_click=partial(panel.ajustar_tamano, nombre, incremento_filas=1), color=None
            ).classes("boton-icono captura-matriz-accion").props(f'ripple=false aria-label="Añadir fila a matriz {nombre}"')

        with ui.row().classes("captura-matriz-dimension").props(f'role="group" aria-label="Columnas de la matriz {nombre}"'):
            ui.label("Columnas:").classes("text-sm texto-secundario mr-1")
            matriz["boton_quitar_columna"] = ui.button(
                icon="remove", on_click=partial(panel.ajustar_tamano, nombre, incremento_columnas=-1), color=None
            ).classes("boton-icono captura-matriz-accion").props(f'ripple=false aria-label="Quitar columna de matriz {nombre}"')
            matriz["etiqueta_dimension"] = ui.label(str(matriz["columnas"])).classes("font-bold w-4 text-center")
            matriz["boton_agregar_columna"] = ui.button(
                icon="add", on_click=partial(panel.ajustar_tamano, nombre, incremento_columnas=1), color=None
            ).classes("boton-icono captura-matriz-accion").props(f'ripple=false aria-label="Añadir columna a matriz {nombre}"')
        _construir_acciones_tarjeta(panel, nombre)


class PanelCapturaMatrices:
    """Panel dinamico de captura para colecciones de matrices con soporte para redimensionado."""

    clases_celda = 'matriz-entrada cuadricula-celda'

    def __init__(self) -> None:
        self.matrices: dict[str, dict[str, Any]] = {}
        asegurar_matrices_permanentes(self.matrices)
        self.contenedor: ui.column | None = None
        self.al_invertir: Callable[[str], None] | None = None
        self.al_cambiar_datos: Callable[[], None] | None = None

    @staticmethod
    def inyectar_recursos_cliente() -> None:
        """Inyecta el script asociado para animaciones de celdas matriciales."""
        ui.add_head_html('<script src="/assets/js/captura_matrices.js"></script>')

    def obtener_siguiente_nombre_disponible(self) -> str | None:
        """Obtiene la primera letra disponible del abecedario para nombrar una nueva matriz."""
        for letra in string.ascii_uppercase:
            if letra not in self.matrices:
                return letra
        return None

    def agregar_matriz(self) -> None:
        """Agrega una nueva matriz 3x3 si no se ha alcanzado el limite alfabetico."""
        nombre = self.obtener_siguiente_nombre_disponible()
        if not nombre:
            ui.notify("Limite de matrices alcanzado (Z)", type="warning")
            return

        self.matrices[nombre] = crear_registro_matriz()
        self.renderizar_todas()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def eliminar_matriz(self, nombre: str) -> None:
        """Elimina una matriz adicional; los nombres A y B son permanentes."""
        if nombre in MATRICES_PERMANENTES:
            return
        if nombre in self.matrices:
            del self.matrices[nombre]
            self.renderizar_todas()
            if self.al_cambiar_datos:
                self.al_cambiar_datos()

    async def ajustar_tamano(self, nombre: str, incremento_filas: int = 0, incremento_columnas: int = 0) -> None:
        """Ajusta las filas o columnas de una matriz especifica aplicando animacion."""
        if nombre not in self.matrices:
            return
        matriz = self.matrices[nombre]
        self._sincronizar_cache_matriz(matriz)
        dimensiones = _validar_deltas(matriz, incremento_filas, incremento_columnas)
        if not dimensiones:
            return
        nuevo_m, nuevo_n = dimensiones

        incremento = incremento_filas or incremento_columnas
        atributo = "fila" if incremento_filas else "columna"
        indice = indice_cambio_dimension(matriz["filas"], nuevo_m) if incremento_filas else indice_cambio_dimension(matriz["columnas"], nuevo_n)
        selector = selector_dimension_matriz(nombre, indice, (atributo,))
        botones = tuple(matriz.get(clave) for clave in ("boton_quitar_fila", "boton_agregar_fila", "boton_quitar_columna", "boton_agregar_columna"))
        await ejecutar_transicion_cuadricula(
            matriz, selectores_cambio_dimension(selector, incremento),
            partial(self._aplicar_tamano, nombre, dimensiones), botones, partial(self._actualizar_botones_matriz, matriz),
        )

    def _aplicar_tamano(self, nombre: str, dimensiones: tuple[int, int]) -> None:
        matriz = self.matrices[nombre]
        anterior = matriz['filas'], matriz['columnas']
        nuevo_m, nuevo_n = dimensiones
        matriz["filas"] = nuevo_m
        matriz["columnas"] = nuevo_n
        matriz["cache"] = purgar_cache_bidimensional(matriz["cache"], matriz["filas"], matriz["columnas"])
        self._actualizar_etiquetas_matriz(nombre, matriz)
        if not actualizar_rectangulo(matriz, anterior, dimensiones,
                                    partial(crear_fila_matriz, self, nombre),
                                    lambda fila, columna: crear_celda_matriz(self, nombre, (fila, columna))):
            self.renderizar_cuadricula(nombre)
        self._actualizar_botones_matriz(matriz)

        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def _sincronizar_cache_matriz(self, matriz: dict[str, Any]) -> None:
        """Copia valores actuales de la UI al cache de celdas."""
        matriz["cache"].update({
            (r, c): celda.value
            for r, fila in enumerate(matriz["entradas"]) for c, celda in enumerate(fila)
        })

    def _actualizar_botones_matriz(self, matriz: dict[str, Any]) -> None:
        actualizar_estados_botones_dimension(matriz["boton_quitar_fila"], matriz["boton_agregar_fila"], matriz["filas"], DIMENSION_MINIMA, DIMENSION_MAXIMA_MATRICES)
        actualizar_estados_botones_dimension(matriz["boton_quitar_columna"], matriz["boton_agregar_columna"], matriz["columnas"], DIMENSION_MINIMA, DIMENSION_MAXIMA_MATRICES)

    def _actualizar_etiquetas_matriz(self, nombre: str, matriz: dict[str, Any]) -> None:
        """Actualiza el conteo y el distintivo de dimensiones de la matriz indicada."""
        if matriz["etiqueta_filas"]:
            matriz["etiqueta_filas"].set_text(str(matriz["filas"]))
        if matriz["etiqueta_dimension"]:
            matriz["etiqueta_dimension"].set_text(str(matriz["columnas"]))
        if matriz["etiqueta_dimension_matriz"]:
            matriz["etiqueta_dimension_matriz"].content = f'{nombre} <span class="separador-punto">·</span> {matriz["filas"]} &times; {matriz["columnas"]}'

    def renderizar_cuadricula(self, nombre: str) -> None:
        """Renderiza las celdas de una matriz concreta con nombres accesibles."""
        matriz = self.matrices[nombre]
        if not matriz["contenedor"]:
            return
        matriz["contenedor"].clear()
        matriz["entradas"].clear()
        matriz['filas_interfaz'] = []

        self._actualizar_botones_matriz(matriz)

        with matriz['contenedor'], ui.column().classes('cuadricula-contenido') as contenido:
            matriz['contenido'] = contenido
            for i in range(matriz["filas"]):
                self._renderizar_fila_matriz(nombre, matriz, i)

    def _renderizar_fila_matriz(self, nombre: str, matriz: dict[str, Any], i: int) -> None:
        """Construye una fila de entradas para la matriz indicada."""
        crear_fila_matriz(self, nombre, i)

    def _al_cambiar_celda(self, nombre: str, r: int, c: int, valor: str) -> None:
        """Guarda el valor en cache y notifica a observadores."""
        self.matrices[nombre]["cache"][(r, c)] = valor
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def renderizar_todas(self) -> None:
        """Reconstruye todos los paneles de matriz registrados."""
        asegurar_matrices_permanentes(self.matrices)
        if not self.contenedor:
            return
        for matriz in self.matrices.values():
            self._sincronizar_cache_matriz(matriz)
        self.contenedor.clear()
        with self.contenedor:
            for nombre in sorted(self.matrices.keys()):
                self._construir_tarjeta_matriz(nombre)

    def _construir_tarjeta_matriz(self, nombre: str) -> None:
        """Genera la tarjeta contenedora y cabecera de control para una matriz."""
        matriz = self.matrices[nombre]
        with ui.column().classes("panel-tarjeta captura-matriz").props(f'role="group" aria-labelledby="matriz-titulo-{nombre}"'):
            _construir_cabecera_tarjeta(nombre, matriz)
            self._construir_controles_dimension(nombre, matriz)
            matriz["contenedor"] = ui.column().classes(
                "overflow-auto w-full cuadricula-area-desplazamiento cuadricula-desplazamiento captura-matriz-cuadricula"
            )
            self.renderizar_cuadricula(nombre)

    def _construir_controles_dimension(self, nombre: str, matriz: dict[str, Any]) -> None:
        """Construye los botones de filas y columnas de la tarjeta."""
        _construir_controles_dimension_interfaz(self, nombre, matriz)

    def construir(self, contenedor: ui.column) -> None:
        """Asigna el contenedor padre y renderiza la coleccion."""
        self.contenedor = contenedor
        self.renderizar_todas()

    def obtener_datos_crudos(self) -> dict[str, dict]:
        """Recoge texto de las celdas y dimensiones, preservando los nombres de matrices."""
        return {
            nombre: {
                "filas": matriz["filas"], "columnas": matriz["columnas"],
                "datos": [[celda.value for celda in fila] for fila in matriz["entradas"]],
            }
            for nombre, matriz in self.matrices.items()
        }

    def cargar_datos(self, diccionario_matrices: dict[str, list[list[str]]]) -> None:
        """Reemplaza la captura y completa A y B sin renombrar las matrices cargadas."""
        self.matrices.clear()
        for nombre, datos in diccionario_matrices.items():
            self.matrices[nombre] = crear_registro_matriz(datos)
        self.renderizar_todas()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def limpiar(self) -> None:
        """Vacia todas las celdas conservando nombres, dimensiones y matrices permanentes."""
        asegurar_matrices_permanentes(self.matrices)
        for matriz in self.matrices.values():
            matriz["cache"].clear()
            for fila in matriz["entradas"]:
                for celda in fila:
                    celda.value = ""
        self.renderizar_todas()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()
