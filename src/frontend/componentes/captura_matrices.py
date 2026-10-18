"""Panel para capturar y manipular multiples matrices con nombres literales (A-Z)."""
from __future__ import annotations

from functools import partial
import string
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
)
from src.backend.constantes import DIMENSION_MAXIMA_MATRICES


def _validar_deltas(matriz: dict[str, Any], incremento_filas: int, incremento_columnas: int) -> tuple[int, int] | None:
    """Valida los nuevos tamanos y devuelve la tupla (nuevo_m, nuevo_n) si es admisible."""
    nuevo_m = matriz["filas"] + incremento_filas
    nuevo_n = matriz["columnas"] + incremento_columnas
    if incremento_filas and not (DIMENSION_MINIMA <= nuevo_m <= DIMENSION_MAXIMA_MATRICES):
        return None
    if incremento_columnas and not (DIMENSION_MINIMA <= nuevo_n <= DIMENSION_MAXIMA_MATRICES):
        return None
    return nuevo_m, nuevo_n


def _construir_cabecera_tarjeta(panel: PanelCapturaMatrices, nombre: str, matriz: dict[str, Any]) -> None:
    """Compone título, distintivo de dimensiones y acciones de la matriz indicada."""
    with ui.row().classes("w-full justify-between items-center mb-2"):
        with ui.row().classes("items-center gap-2"):
            ui.label(f"Matriz {nombre}").classes("font-bold texto-principal text-base")
            matriz["etiqueta_dimension_matriz"] = ui.html(
                f'{nombre} <span class="separador-punto">·</span> {matriz["filas"]} &times; {matriz["columnas"]}'
            ).classes("fuente-pequena texto-secundario uppercase etiqueta-dimensiones")

        with ui.row().classes("items-center gap-2"):
            if panel.al_invertir:
                ui.button("Invertir", on_click=lambda nombre_matriz=nombre: panel.al_invertir(nombre_matriz)).classes(
                    "boton-discreto text-xs"
                ).props('ripple=false aria-label="Invertir Matriz"')
            ui.button(
                icon="delete", on_click=partial(panel.eliminar_matriz, nombre), color=None
            ).classes("boton-discreto w-8 h-8 p-0 ml-1 boton-eliminar-elemento").props(
                'ripple=false aria-label="Eliminar Matriz"'
            ).tooltip("Eliminar Matriz")


def _construir_controles_dimension_interfaz(panel: Any, nombre: str, matriz: dict[str, Any]) -> None:
    """Construye los botones de filas y columnas de la tarjeta."""
    with ui.row().classes("w-full justify-start items-center gap-4 mb-2"):
        with ui.row().classes("items-center gap-1"):
            ui.label("Filas:").classes("text-sm texto-secundario mr-1")
            matriz["boton_quitar_fila"] = ui.button(
                icon="remove", on_click=partial(panel.ajustar_tamano, nombre, incremento_filas=-1), color=None
            ).classes("boton-icono w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Quitar Fila"')
            matriz["etiqueta_filas"] = ui.label(str(matriz["filas"])).classes("font-bold w-4 text-center")
            matriz["boton_agregar_fila"] = ui.button(
                icon="add", on_click=partial(panel.ajustar_tamano, nombre, incremento_filas=1), color=None
            ).classes("boton-icono w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Añadir Fila"')

        with ui.row().classes("items-center gap-1"):
            ui.label("Columnas:").classes("text-sm texto-secundario mr-1")
            matriz["boton_quitar_columna"] = ui.button(
                icon="remove", on_click=partial(panel.ajustar_tamano, nombre, incremento_columnas=-1), color=None
            ).classes("boton-icono w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Quitar Columna"')
            matriz["etiqueta_dimension"] = ui.label(str(matriz["columnas"])).classes("font-bold w-4 text-center")
            matriz["boton_agregar_columna"] = ui.button(
                icon="add", on_click=partial(panel.ajustar_tamano, nombre, incremento_columnas=1), color=None
            ).classes("boton-icono w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Añadir Columna"')


class PanelCapturaMatrices:
    """Panel dinamico de captura para colecciones de matrices con soporte para redimensionado."""

    def __init__(self) -> None:
        self.matrices: dict[str, dict[str, Any]] = {}
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

        self.matrices[nombre] = {
            "filas": 3, "columnas": 3, "entradas": [], "cache": {}, "contenedor": None,
            "etiqueta_filas": None, "etiqueta_dimension": None, "etiqueta_dimension_matriz": None,
            "boton_quitar_fila": None, "boton_agregar_fila": None, "boton_quitar_columna": None, "boton_agregar_columna": None,
        }
        self.renderizar_todas()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def eliminar_matriz(self, nombre: str) -> None:
        """Elimina una matriz identificada por su nombre literal."""
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

        self._deshabilitar_botones_matriz(matriz)
        if incremento_filas < 0 or incremento_columnas < 0:
            selector_destino = f"[data-matriz-fila='{matriz['filas'] - 1}']" if incremento_filas < 0 else f"[data-matriz-columna='{matriz['columnas'] - 1}']"
            await animar_salida_cuadricula(selector_destino, nombre_matriz=nombre)

        matriz["filas"] = nuevo_m
        matriz["columnas"] = nuevo_n
        matriz["cache"] = purgar_cache_bidimensional(matriz["cache"], matriz["filas"], matriz["columnas"])
        self._actualizar_etiquetas_matriz(nombre, matriz)
        self.renderizar_cuadricula(nombre)

        if incremento_filas > 0 or incremento_columnas > 0:
            selector_destino = f"[data-matriz-fila='{matriz['filas'] - 1}']" if incremento_filas > 0 else f"[data-matriz-columna='{matriz['columnas'] - 1}']"
            await animar_entrada_cuadricula(selector_destino, nombre_matriz=nombre)

        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def _sincronizar_cache_matriz(self, matriz: dict[str, Any]) -> None:
        """Copia valores actuales de la UI al cache de celdas."""
        sincronizar_cache_celdas(matriz["entradas"], matriz["cache"])

    def _deshabilitar_botones_matriz(self, matriz: dict[str, Any]) -> None:
        """Deshabilita temporalmente los botones de dimension de la matriz."""
        claves = ("boton_quitar_fila", "boton_agregar_fila",
                  "boton_quitar_columna", "boton_agregar_columna")
        deshabilitar_botones_dimension(tuple(matriz.get(clave) for clave in claves))

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

        actualizar_estados_botones_dimension(matriz["boton_quitar_fila"], matriz["boton_agregar_fila"], matriz["filas"], DIMENSION_MINIMA, DIMENSION_MAXIMA_MATRICES)
        actualizar_estados_botones_dimension(matriz["boton_quitar_columna"], matriz["boton_agregar_columna"], matriz["columnas"], DIMENSION_MINIMA, DIMENSION_MAXIMA_MATRICES)

        with (
            matriz["contenedor"],
            ui.column().classes("cuadricula-contenido"),
        ):
            for i in range(matriz["filas"]):
                self._renderizar_fila_matriz(nombre, matriz, i)

    def _renderizar_fila_matriz(self, nombre: str, matriz: dict[str, Any], i: int) -> None:
        """Construye una fila de entradas para la matriz indicada."""
        with ui.row().classes("items-center gap-2 mb-2 no-wrap").props(f'data-cuadricula-fila="{nombre}_{i}"'):
            fila_ui = []
            for j in range(matriz["columnas"]):
                valor = matriz["cache"].get((i, j), "")
                propiedades = propiedades_celda_accesible(i, j, identificador_matriz=nombre, nombre_campo=f"{nombre}_r{i}c{j}")
                celda = ui.input(
                    value=valor,
                    placeholder="",
                    on_change=lambda evento, r=i, c=j, nombre_matriz=nombre: self._al_cambiar_celda(nombre_matriz, r, c, evento.value),
                ).classes("matriz-entrada cuadricula-celda").props(propiedades)
                fila_ui.append(celda)
            matriz["entradas"].append(fila_ui)

    def _al_cambiar_celda(self, nombre: str, r: int, c: int, valor: str) -> None:
        """Guarda el valor en cache y notifica a observadores."""
        self.matrices[nombre]["cache"][(r, c)] = valor
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def renderizar_todas(self) -> None:
        """Reconstruye todos los paneles de matriz registrados."""
        if not self.contenedor:
            return
        self.contenedor.clear()
        with self.contenedor:
            for nombre in sorted(self.matrices.keys()):
                self._construir_tarjeta_matriz(nombre)

    def _construir_tarjeta_matriz(self, nombre: str) -> None:
        """Genera la tarjeta contenedora y cabecera de control para una matriz."""
        matriz = self.matrices[nombre]
        with ui.column().classes("panel-tarjeta p-4 mb-4 w-full"):
            _construir_cabecera_tarjeta(self, nombre, matriz)
            self._construir_controles_dimension(nombre, matriz)
            matriz["contenedor"] = ui.column().classes(
                "overflow-auto w-full cuadricula-area-desplazamiento cuadricula-desplazamiento"
            )
            self.renderizar_cuadricula(nombre)

    def _construir_controles_dimension(self, nombre: str, matriz: dict[str, Any]) -> None:
        """Construye los botones de filas y columnas de la tarjeta."""
        _construir_controles_dimension_interfaz(self, nombre, matriz)

    def construir(self, contenedor: ui.column) -> None:
        """Asigna el contenedor padre y renderiza la coleccion."""
        self.contenedor = contenedor
        if not self.matrices:
            self.agregar_matriz()
        else:
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
        """Carga un conjunto de matrices reemplazando el contenido existente."""
        self.matrices.clear()
        for nombre, datos in diccionario_matrices.items():
            numero_filas = len(datos)
            numero_columnas = len(datos[0]) if numero_filas > 0 else 3
            self.matrices[nombre] = {
                "filas": numero_filas, "columnas": numero_columnas, "entradas": [], "cache": cache_matriz_desde_datos(datos), "contenedor": None,
                "etiqueta_filas": None, "etiqueta_dimension": None, "etiqueta_dimension_matriz": None,
                "boton_quitar_fila": None, "boton_agregar_fila": None, "boton_quitar_columna": None, "boton_agregar_columna": None,
            }
        self.renderizar_todas()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()
