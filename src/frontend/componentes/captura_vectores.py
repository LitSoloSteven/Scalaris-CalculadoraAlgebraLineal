"""Panel interactivo de captura para familias de vectores con orientacion conmutable."""
from __future__ import annotations

from functools import partial
import html
from typing import Any, Callable
from nicegui import ui
from .opciones_captura_vectores import OpcionesCapturaVectores
from .transicion_vectores import MixinTransicionVectores
from src.backend.constantes import DIMENSION_MAXIMA_VECTORES

from src.frontend.componentes.cuadricula_base import (
    DIMENSION_MINIMA,
    actualizar_estados_botones_dimension,
    propiedades_vector_accesible,
)



def _formatear_nombre_vector(nombre: str) -> str:
    """Escapa la etiqueta y su subíndice antes de incluirlos en la cabecera HTML."""
    if "_" in nombre:
        return f"{html.escape(nombre[0])}<sub>{html.escape(nombre[2:])}</sub>"
    return html.escape(nombre)


def _construir_acciones_vector(instancia: PanelCapturaVectores, nombre: str) -> None:
    """Construye los botones de alternar orientacion y eliminar vector."""
    with ui.row().classes("vectores-captura-acciones items-center gap-1"):
        if instancia.permitir_alternar_orientacion:
            instancia.vectores[nombre]["boton_orientacion"] = ui.button(
                icon="swap_horiz", on_click=partial(instancia.alternar_orientacion, nombre), color=None
            ).classes("boton-icono w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Cambiar orientacion"').tooltip("Cambiar orientacion")
        if instancia.permite_variar_cantidad and nombre != instancia.etiqueta_fija_primer_vector:
            instancia._botones_eliminar_vectores[nombre] = ui.button(
                icon="delete", on_click=partial(instancia._eliminar_vector_animado, nombre), color=None
            ).classes("boton-discreto w-8 h-8 p-0 ml-2 boton-eliminar-elemento").props('ripple=false aria-label="Eliminar Vector"').tooltip("Eliminar Vector")


def _construir_tarjeta_vector(instancia: PanelCapturaVectores, nombre: str) -> None:
    """Construye la tarjeta contenedora y cabecera de un vector individual."""
    vector = instancia.vectores[nombre]
    nombre_html = _formatear_nombre_vector(nombre)
    with ui.column().classes("panel-tarjeta p-4 min-w-[140px] items-center vectores-captura-tarjeta"):
        with ui.row().classes("w-full justify-between items-center mb-2 no-wrap vectores-captura-cabecera"):
            vector["etiqueta_dimension"] = ui.html(
                f'{nombre_html} <span class="separador-punto">·</span> {instancia.dimension}&times;1'
            ).classes("fuente-pequena texto-secundario uppercase etiqueta-dimensiones")
            _construir_acciones_vector(instancia, nombre)

        vector["contenedor"] = ui.column().classes("items-center vectores-captura-desplazamiento")
        instancia.renderizar_cuadricula_vector(nombre)


def _cargar_datos_vectores(
    instancia: PanelCapturaVectores, datos_vectores: dict[str, list[str]], orientacion: str
) -> None:
    """Reemplaza los vectores activos por las listas provistas."""
    if not datos_vectores:
        return
    instancia.vectores.clear()
    primer_vector = next(iter(datos_vectores.values()))
    instancia.dimension = len(primer_vector)
    for nombre, valores in datos_vectores.items():
        cache = {i: str(valor).strip() for i, valor in enumerate(valores) if str(valor).strip() != "0"}
        instancia.vectores[nombre] = {
            "orientacion": orientacion if instancia.permitir_alternar_orientacion else "columna",
            "celdas": cache,
            "contenedor": None,
            "etiqueta_dimension": None,
            "boton_orientacion": None,
        }
    instancia.renderizar_todos_vectores()
    if instancia.al_cambiar_datos:
        instancia.al_cambiar_datos()


class PanelCapturaVectores(MixinTransicionVectores):
    """Panel de captura de vectores en dimension n compartida con orientacion fila/columna."""

    def __init__(self, identificador_panel: str, opciones: OpcionesCapturaVectores | None = None) -> None:
        self.identificador_panel = identificador_panel
        configuracion = opciones if opciones is not None else {}
        minimo_vectores = configuracion.get('minimo_vectores', 1)
        maximo_vectores = configuracion.get('maximo_vectores', 8)
        permitir_alternar_orientacion = configuracion.get('permitir_orientacion', True)
        orientacion_inicial = configuracion.get('orientacion_inicial', "columna")
        etiqueta_fija_primer_vector = configuracion.get('etiqueta_primer_vector', None)
        self.minimo_vectores = minimo_vectores
        self.maximo_vectores = maximo_vectores
        self.permitir_alternar_orientacion = permitir_alternar_orientacion
        self.etiqueta_fija_primer_vector = etiqueta_fija_primer_vector
        self.vectores: dict[str, dict[str, Any]] = {}
        self._botones_eliminar_vectores: dict[str, Any] = {}
        self.dimension = 3
        self.contenedor: ui.column | None = None
        self.contenedor_cabecera: ui.row | None = None
        self.al_cambiar_datos: Callable[[], None] | None = None
        self.orientacion_inicial = "columna" if not permitir_alternar_orientacion else orientacion_inicial
        self.boton_reducir_dimension: ui.button | None = None
        self.boton_aumentar_dimension: ui.button | None = None
        self.etiqueta_dimension: ui.label | None = None

    @property
    def permite_variar_cantidad(self) -> bool:
        """Indica si los limites permiten anadir o eliminar vectores de la familia."""
        return self.maximo_vectores > self.minimo_vectores

    @staticmethod
    def inyectar_recursos_cliente() -> None:
        """Inyecta los scripts para animaciones vectoriales."""
        ui.add_head_html('<script src="/assets/js/captura_vectores.js"></script>')

    def obtener_siguiente_nombre_disponible(self) -> str:
        """Determina la siguiente etiqueta alfabetica o subindicada para un vector."""
        if self.etiqueta_fija_primer_vector and self.etiqueta_fija_primer_vector not in self.vectores:
            return self.etiqueta_fija_primer_vector
        if self.maximo_vectores <= 3:
            for letra in ("u", "v", "w"):
                if letra not in self.vectores and letra != self.etiqueta_fija_primer_vector:
                    return letra
        for i in range(1, 10):
            nombre = f"v_{i}"
            if nombre not in self.vectores and nombre != self.etiqueta_fija_primer_vector:
                return nombre
        return "x"

    def agregar_vector(self) -> None:
        """Agrega un nuevo vector si la cantidad no sobrepasa el limite establecido."""
        if len(self.vectores) >= self.maximo_vectores:
            ui.notify(f"Limite de vectores alcanzado ({self.maximo_vectores})", type="warning")
            return
        nombre = self.obtener_siguiente_nombre_disponible()
        self.vectores[nombre] = {
            "orientacion": self.orientacion_inicial,
            "celdas": {},
            "contenedor": None,
            "etiqueta_dimension": None,
            "boton_orientacion": None,
        }
        self.renderizar_todos_vectores()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def eliminar_vector(self, nombre: str) -> None:
        """Elimina el vector indicado respetando el minimo permitido."""
        if len(self.vectores) <= self.minimo_vectores:
            ui.notify(f"Se requiere al menos {self.minimo_vectores} vector(es)", type="warning")
            return
        if nombre == self.etiqueta_fija_primer_vector:
            return
        if nombre in self.vectores:
            del self.vectores[nombre]
            self.renderizar_todos_vectores()
            if self.al_cambiar_datos:
                self.al_cambiar_datos()

    def alternar_orientacion(self, nombre: str) -> None:
        """Alterna entre disposicion vertical (columna) y horizontal (fila)."""
        if not self.permitir_alternar_orientacion or nombre not in self.vectores:
            return
        vector = self.vectores[nombre]
        vector["orientacion"] = "fila" if vector["orientacion"] == "columna" else "columna"
        self.renderizar_cuadricula_vector(nombre)
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def renderizar_cuadricula_vector(self, nombre: str) -> None:
        """Renderiza los componentes de entrada del vector indicado."""
        vector = self.vectores[nombre]
        if not vector["contenedor"]:
            return
        vector["contenedor"].clear()
        nombre_html = _formatear_nombre_vector(nombre)
        texto_dimension = f"{self.dimension}&times;1" if vector["orientacion"] == "columna" else f"1&times;{self.dimension}"
        if vector["etiqueta_dimension"]:
            vector["etiqueta_dimension"].content = f'{nombre_html} <span class="separador-punto">·</span> {texto_dimension}'

        with vector["contenedor"]:
            clase_fila = "cuadricula-fila-sin-ajuste vectores-captura-fila" if vector["orientacion"] == "fila" else "vectores-captura-columna"
            with ui.row().classes(f"items-center gap-2 p-2 vectores-captura-celdas {clase_fila}"):
                for i in range(self.dimension):
                    valor = vector["celdas"].get(i, "")
                    propiedades = propiedades_vector_accesible(
                        i, vector["orientacion"], nombre_vector=nombre, identificador_panel=self.identificador_panel,
                    )
                    ui.input(
                        value=valor,
                        placeholder="",
                        on_change=lambda evento, indice=i, nombre_matriz=nombre: self._al_cambiar_celda_vector(nombre_matriz, indice, evento.value),
                    ).classes("matriz-entrada cuadricula-celda").props(propiedades)

    def _al_cambiar_celda_vector(self, nombre: str, indice: int, valor: str) -> None:
        """Actualiza el cache de la celda modificada."""
        self.vectores[nombre]["celdas"][indice] = valor
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    def renderizar_todos_vectores(self) -> None:
        """Reconstruye todos los paneles vectoriales en el contenedor asignado."""
        if not self.contenedor:
            return
        self.contenedor.clear()
        self._botones_eliminar_vectores.clear()
        with (
            self.contenedor,
            ui.row().classes("w-full flex-wrap gap-4 items-start vectores-captura-lista"),
        ):
            for nombre in sorted(self.vectores.keys()):
                _construir_tarjeta_vector(self, nombre)
        self._actualizar_botones_vectores()

    def construir(self, contenedor: ui.column) -> None:
        """Ensambla el panel completo incluyendo la cabecera de dimension."""
        with contenedor:
            with ui.row().classes("w-full justify-between items-center px-2 vectores-captura-dimension") as self.contenedor_cabecera:
                ui.label("Familia de Vectores").classes("text-lg font-bold texto-principal")
                with ui.row().classes("items-center gap-3"):
                    self.boton_reducir_dimension = ui.button(
                        icon="remove", on_click=partial(self.ajustar_dimension, delta=-1), color=None
                    ).classes("boton-icono w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Reducir dimension"').tooltip("Reducir dimension")
                    self.etiqueta_dimension = ui.label(str(self.dimension)).classes("font-bold w-6 text-center texto-principal")
                    self.boton_aumentar_dimension = ui.button(
                        icon="add", on_click=partial(self.ajustar_dimension, delta=1), color=None
                    ).classes("boton-icono w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Aumentar dimension"').tooltip("Aumentar dimension")
                    self._construir_boton_agregar_vector()
            self.contenedor = ui.column().classes("w-full")

        actualizar_estados_botones_dimension(
            self.boton_reducir_dimension, self.boton_aumentar_dimension, self.dimension, DIMENSION_MINIMA, DIMENSION_MAXIMA_VECTORES
        )
        if not self.vectores:
            self.agregar_vector()
        else:
            self.renderizar_todos_vectores()

    def _construir_boton_agregar_vector(self) -> None:
        """Ofrece ampliar la familia solo cuando su cantidad puede variar."""
        if self.permite_variar_cantidad:
            self.boton_agregar_vector = ui.button("Añadir Vector", icon="add", on_click=self._agregar_vector_animado, color=None).classes("boton-discreto").props("ripple=false")

    def cargar_datos(self, datos_vectores: dict[str, list[str]], orientacion: str = "columna") -> None:
        """Carga vectores desde un diccionario reemplazando las entradas activas."""
        _cargar_datos_vectores(self, datos_vectores, orientacion)
