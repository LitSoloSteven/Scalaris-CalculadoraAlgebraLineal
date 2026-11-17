"""Tabla paginada con selección explícita vinculada al paso del procedimiento."""
import json
from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from src.frontend.componentes.tabla_iteraciones import PaginacionIteraciones


@dataclass(frozen=True)
class FormatoTablaRaices:
    """Define las columnas, los textos y el formateo de una página de iteraciones."""

    descripcion: str
    nombre_region: str
    clase_region: str
    preparar_filas: Callable[[tuple, bool], tuple]


class TablaRaicesSeleccionable:
    """Pagina la traza y enlaza la fila seleccionada con el procedimiento."""

    def __init__(self, filas: tuple, al_elegir, formato: FormatoTablaRaices, *, preferencias: tuple = ()):
        self.filas, self.al_elegir = filas, al_elegir
        self.formato = formato
        self._preferencias = preferencias
        self.fila_activa = None
        self._indices = {str(fila["i"]): indice for indice, fila in enumerate(filas, 1)}

    def construir(self) -> None:
        """Monta tabla, inspección y navegación con nombres accesibles y desplazamiento local."""
        ui.label("Tabla de iteraciones").classes("text-xl font-bold texto-principal")
        ui.label(self.formato.descripcion).classes("text-sm texto-secundario")
        self.precision = ui.switch("Mostrar 17 cifras")
        with ui.element("div").classes(f"{self.formato.clase_region} w-full").props(
                f'tabindex=0 role=region aria-label="{self.formato.nombre_region}"'):
            self.tabla = ui.table(columns=[], rows=[], row_key="i", pagination=0, selection="single",
                                  on_select=self._elegir).classes("w-full").props("hide-bottom")
            with self.tabla.add_slot("body-selection"):
                ui.element("q-checkbox").props(
                    ':model-value="props.selected" :aria-label="\'Ver iteración \' + props.row.i" '
                    f':id="\'{self.tabla.html_id}-fila-\' + props.row.i"',
                ).on("update:model-value", js_handler="valor => { props.selected = valor }")
        self.paginacion = PaginacionIteraciones(
            self.tabla, len(self.filas), self._preparar, (self.precision, *self._preferencias),
        )
        self.paginacion.construir()

    def seleccionar(self, fila: dict | None) -> None:
        """Sigue la fila del paso activo sin disparar un nuevo cálculo matemático."""
        self.fila_activa = None if fila is None else str(fila["i"])
        visibles = [registro for registro in self.tabla.rows if registro["i"] == self.fila_activa]
        if fila is None or visibles:
            claves = [str(registro.get("i")) for registro in self.tabla.selected if isinstance(registro, dict)]
            if claves != [registro["i"] for registro in visibles]:
                self.tabla.selected = visibles
                self.tabla.update()
        else:
            self.paginacion.mostrar_indice(self._indices[self.fila_activa] - 1)

    def _preparar(self, inicio: int, fin: int) -> tuple:
        columnas, filas = self.formato.preparar_filas(self.filas[inicio:fin], self.precision.value)
        self.tabla.selected = [fila for fila in filas if fila["i"] == self.fila_activa]
        return columnas, filas

    def _elegir(self, evento) -> None:
        if not evento.selection:
            anterior = self.fila_activa
            self.al_elegir(0)
            self._devolver_foco(anterior)
            return
        if not isinstance(evento.selection[0], dict):
            return
        indice = self._indices.get(str(evento.selection[0].get("i")))
        if indice is not None:
            self.al_elegir(indice)
            self._devolver_foco(str(evento.selection[0]["i"]))

    def _devolver_foco(self, clave: str | None) -> None:
        if clave is None or self.tabla.is_deleted:
            return
        selector = json.dumps(f'[aria-label="Ver iteración {clave}"]')
        identificador = json.dumps(self.tabla.html_id)
        ui.run_javascript(
            f"requestAnimationFrame(() => document.getElementById({identificador})?.querySelector({selector})?.focus({{preventScroll:true}}))"
        )
