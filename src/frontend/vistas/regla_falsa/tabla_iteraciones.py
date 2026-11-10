"""Tabla paginada con selección explícita vinculada al paso del procedimiento."""
from nicegui import ui

from src.frontend.componentes.tabla_iteraciones import PaginacionIteraciones
from src.frontend.controladores.regla_falsa.tabla import COLUMNAS, filas_tabla


class TablaReglaFalsa:
    """Conserva la fila activa y presenta solo quince filas de la traza en cada página."""

    def __init__(self, filas: tuple, al_elegir):
        self.filas, self.al_elegir = filas, al_elegir
        self.fila_activa = None
        self._indices = {str(fila["i"]): indice for indice, fila in enumerate(filas, 1)}

    def construir(self) -> None:
        """Monta tabla, inspección y navegación con nombres accesibles y desplazamiento local."""
        ui.label("Tabla de iteraciones").classes("text-xl font-bold texto-principal")
        ui.label("Selecciona una fila para ver su secante. El error relativo no está disponible en la primera fila o si c = 0.").classes(
            "text-sm texto-secundario")
        self.precision = ui.switch("Mostrar 17 cifras")
        with ui.element("div").classes("regla-falsa-tabla w-full").props(
                'tabindex=0 role=region aria-label="Tabla de regla falsa con desplazamiento horizontal"'):
            self.tabla = ui.table(columns=[], rows=[], row_key="i", pagination=0, selection="single",
                                  on_select=self._elegir).classes("w-full").props("hide-bottom")
            self.tabla.add_slot("body-selection", '<q-checkbox v-model="props.selected" :aria-label="\'Ver iteración \' + props.row.i" />')
        self.paginacion = PaginacionIteraciones(self.tabla, len(self.filas), self._preparar, (self.precision,))
        self.paginacion.construir()

    def seleccionar(self, fila: dict | None) -> None:
        """Sigue la fila del paso activo sin disparar un nuevo cálculo matemático."""
        self.fila_activa = None if fila is None else str(fila["i"])
        if fila is None:
            self.tabla.selected = []
        else:
            self.paginacion.mostrar_indice(self._indices[self.fila_activa] - 1)
        self.tabla.update()

    def _preparar(self, inicio: int, fin: int) -> tuple:
        filas = filas_tabla(self.filas[inicio:fin], self.precision.value)
        self.tabla.selected = [fila for fila in filas if fila["i"] == self.fila_activa]
        return COLUMNAS, filas

    def _elegir(self, evento) -> None:
        if not evento.selection:
            self.al_elegir(0)
            return
        if not isinstance(evento.selection[0], dict):
            return
        indice = self._indices.get(str(evento.selection[0].get("i")))
        if indice is not None:
            self.al_elegir(indice)
