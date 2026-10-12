"""Panel interactivo de captura para familias de vectores con orientacion conmutable."""
from __future__ import annotations

from functools import partial
from typing import Any, Callable
from nicegui import ui

from src.frontend.componentes.cuadricula_base import (
    DIMENSION_MINIMA,
    actualizar_estados_botones_dimension,
    animar_salida_cuadricula,
    props_vector_accesible,
    purgar_cache_unidimensional,
)

DIMENSION_MAXIMA_VECTORES = 10


def _construir_acciones_vector(instancia: VectorCapturePanel, name: str) -> None:
    """Construye los botones de alternar orientacion y eliminar vector."""
    with ui.row().classes("items-center gap-1"):
        if instancia.allow_orientation_toggle:
            ui.button(
                icon="swap_horiz", on_click=partial(instancia.alternar_orientacion, name), color=None
            ).classes("btn-neo-icon w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Cambiar orientacion"').tooltip("Cambiar orientacion")
        if name != instancia.first_vector_fixed_label:
            ui.button(
                icon="delete", on_click=partial(instancia.remove_vector, name), color=None
            ).classes("btn-ghost w-8 h-8 p-0 ml-2 btn-eliminar-elemento").props('ripple=false aria-label="Eliminar Vector"').tooltip("Eliminar Vector")


def _construir_tarjeta_vector(instancia: VectorCapturePanel, name: str) -> None:
    """Construye la tarjeta contenedora y cabecera de un vector individual."""
    v = instancia.vectors[name]
    name_html = f"{name[0]}<sub>{name[2:]}</sub>" if "_" in name else name
    with ui.column().classes("panel-card p-4 min-w-[140px] items-center"):
        with ui.row().classes("w-full justify-between items-center mb-2 no-wrap"):
            v["lbl_badge"] = ui.html(
                f'{name_html} <span class="separador-punto">·</span> {instancia.dim}&times;1'
            ).classes("fs-small text-sec uppercase etiqueta-dimensiones")
            _construir_acciones_vector(instancia, name)

        v["ui_container"] = ui.column().classes("items-center")
        instancia.render_vector_grid(name)


def _cargar_datos_vectores(
    instancia: VectorCapturePanel, vectors_dict: dict[str, list[str]], orientation: str
) -> None:
    """Reemplaza los vectores activos por las listas provistas."""
    if not vectors_dict:
        return
    instancia.vectors.clear()
    first_vec = next(iter(vectors_dict.values()))
    instancia.dim = len(first_vec)
    for name, vals in vectors_dict.items():
        cache = {i: str(v).strip() for i, v in enumerate(vals) if str(v).strip() != "0"}
        instancia.vectors[name] = {
            "orientation": orientation if instancia.allow_orientation_toggle else "column",
            "cache": cache,
            "ui_container": None,
            "lbl_badge": None,
            "btn_toggle": None,
        }
    instancia.render_all_vectors()
    if instancia.on_data_change:
        instancia.on_data_change()


class VectorCapturePanel:
    """Panel de captura de vectores en dimension n compartida con orientacion fila/columna."""

    def __init__(
        self,
        panel_id: str,
        *,
        min_vectors: int = 1,
        max_vectors: int = 8,
        allow_orientation_toggle: bool = True,
        default_orientation: str = "column",
        first_vector_fixed_label: str | None = None,
    ) -> None:
        self.panel_id = panel_id
        self.min_vectors = min_vectors
        self.max_vectors = max_vectors
        self.allow_orientation_toggle = allow_orientation_toggle
        self.first_vector_fixed_label = first_vector_fixed_label
        self.vectors: dict[str, dict[str, Any]] = {}
        self.dim = 3
        self.container: ui.column | None = None
        self.header_container: ui.row | None = None
        self.on_data_change: Callable[[], None] | None = None
        self.default_orientation = "column" if not allow_orientation_toggle else default_orientation
        self.btn_dim_dec: ui.button | None = None
        self.btn_dim_inc: ui.button | None = None
        self.lbl_dim: ui.label | None = None

    @staticmethod
    def inject_scripts() -> None:
        """Inyecta los scripts para animaciones vectoriales."""
        ui.add_head_html('<script src="/assets/js/captura_vectores.js"></script>')
        ui.add_head_html('<script src="/assets/js/square_matrix.js"></script>')

    def get_next_available_name(self) -> str:
        """Determina la siguiente etiqueta alfabetica o subindicada para un vector."""
        if self.first_vector_fixed_label and self.first_vector_fixed_label not in self.vectors:
            return self.first_vector_fixed_label
        if self.max_vectors <= 3:
            for ltr in ("u", "v", "w"):
                if ltr not in self.vectors and ltr != self.first_vector_fixed_label:
                    return ltr
        for i in range(1, 10):
            name = f"v_{i}"
            if name not in self.vectors and name != self.first_vector_fixed_label:
                return name
        return "x"

    def add_vector(self) -> None:
        """Agrega un nuevo vector si la cantidad no sobrepasa el limite establecido."""
        if len(self.vectors) >= self.max_vectors:
            ui.notify(f"Limite de vectores alcanzado ({self.max_vectors})", type="warning")
            return
        name = self.get_next_available_name()
        self.vectors[name] = {
            "orientation": self.default_orientation,
            "cache": {},
            "ui_container": None,
            "lbl_badge": None,
            "btn_toggle": None,
        }
        self.render_all_vectors()
        if self.on_data_change:
            self.on_data_change()

    def remove_vector(self, name: str) -> None:
        """Elimina el vector indicado respetando el minimo permitido."""
        if len(self.vectors) <= self.min_vectors:
            ui.notify(f"Se requiere al menos {self.min_vectors} vector(es)", type="warning")
            return
        if name == self.first_vector_fixed_label:
            return
        if name in self.vectors:
            del self.vectors[name]
            self.render_all_vectors()
            if self.on_data_change:
                self.on_data_change()

    async def adjust_dimension(self, delta: int = 0) -> None:
        """Modifica la dimension compartida 'dim' de todos los vectores registrados."""
        nueva_dim = self.dim + delta
        if not (DIMENSION_MINIMA <= nueva_dim <= DIMENSION_MAXIMA_VECTORES):
            return

        if self.btn_dim_dec:
            self.btn_dim_dec.disable()
        if self.btn_dim_inc:
            self.btn_dim_inc.disable()

        if delta < 0 and self.container is not None:
            await animar_salida_cuadricula(
                f"#{self.container.html_id} input[data-geometria-indice='{self.dim - 1}']"
            )

        self.dim = nueva_dim
        for v in self.vectors.values():
            v["cache"] = purgar_cache_unidimensional(v["cache"], self.dim)

        if self.lbl_dim:
            self.lbl_dim.set_text(str(self.dim))
        actualizar_estados_botones_dimension(
            self.btn_dim_dec, self.btn_dim_inc, self.dim, DIMENSION_MINIMA, DIMENSION_MAXIMA_VECTORES
        )

        for name in self.vectors:
            self.render_vector_grid(name)
        if self.on_data_change:
            self.on_data_change()

    def alternar_orientacion(self, nombre: str) -> None:
        """Alterna entre disposicion vertical (columna) y horizontal (fila)."""
        if not self.allow_orientation_toggle or nombre not in self.vectors:
            return
        vector = self.vectors[nombre]
        vector["orientation"] = "row" if vector["orientation"] == "column" else "column"
        self.render_vector_grid(nombre)
        if self.on_data_change:
            self.on_data_change()

    def render_vector_grid(self, name: str) -> None:
        """Renderiza los componentes de entrada del vector indicado."""
        v = self.vectors[name]
        if not v["ui_container"]:
            return
        v["ui_container"].clear()
        name_html = f"{name[0]}<sub>{name[2:]}</sub>" if "_" in name else name
        badge_text = f"{self.dim}&times;1" if v["orientation"] == "column" else f"1&times;{self.dim}"
        if v["lbl_badge"]:
            v["lbl_badge"].content = f'{name_html} <span class="separador-punto">·</span> {badge_text}'

        with v["ui_container"]:
            clase_fila = "cuadricula-fila-sin-ajuste" if v["orientation"] == "row" else ""
            with ui.row().classes(f"items-center gap-2 p-2 {clase_fila}"):
                for i in range(self.dim):
                    val = v["cache"].get(i, "")
                    props = props_vector_accesible(
                        i, v["orientation"], nombre_vector=name, identificador_panel=self.panel_id,
                    )
                    ui.input(
                        value=val,
                        placeholder="",
                        on_change=lambda e, idx=i, nm=name: self._al_cambiar_celda_vector(nm, idx, e.value),
                    ).classes("matrix-input grid-cell").props(props)

    def _al_cambiar_celda_vector(self, name: str, idx: int, valor: str) -> None:
        """Actualiza el cache de la celda modificada."""
        self.vectors[name]["cache"][idx] = valor
        if self.on_data_change:
            self.on_data_change()

    def render_all_vectors(self) -> None:
        """Reconstruye todos los paneles vectoriales en el contenedor asignado."""
        if not self.container:
            return
        self.container.clear()
        with self.container:
            with ui.row().classes("w-full flex-wrap gap-4 items-start"):
                for name in sorted(self.vectors.keys()):
                    _construir_tarjeta_vector(self, name)

    def build(self, container: ui.column) -> None:
        """Ensambla el panel completo incluyendo la cabecera de dimension."""
        self.container = container
        with ui.row().classes("w-full justify-between items-center mb-4 px-2"):
            ui.label("Familia de Vectores").classes("text-lg font-bold text-main")
            with ui.row().classes("items-center gap-3"):
                self.btn_dim_dec = ui.button(
                    icon="remove", on_click=partial(self.adjust_dimension, delta=-1), color=None
                ).classes("btn-neo-icon w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Reducir dimension"').tooltip("Reducir dimension")
                self.lbl_dim = ui.label(str(self.dim)).classes("font-bold w-6 text-center text-main")
                self.btn_dim_inc = ui.button(
                    icon="add", on_click=partial(self.adjust_dimension, delta=1), color=None
                ).classes("btn-neo-icon w-8 h-8 p-0 flex-shrink-0").props('ripple=false aria-label="Aumentar dimension"').tooltip("Aumentar dimension")
                ui.button("Añadir Vector", icon="add", on_click=self.add_vector, color=None).classes("btn-ghost").props("ripple=false")

        actualizar_estados_botones_dimension(
            self.btn_dim_dec, self.btn_dim_inc, self.dim, DIMENSION_MINIMA, DIMENSION_MAXIMA_VECTORES
        )
        if not self.vectors:
            self.add_vector()
        else:
            self.render_all_vectors()

    def load_data(self, vectors_dict: dict[str, list[str]], orientation: str = "column") -> None:
        """Carga vectores desde un diccionario reemplazando las entradas activas."""
        _cargar_datos_vectores(self, vectors_dict, orientation)
