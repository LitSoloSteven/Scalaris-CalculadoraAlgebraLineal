"""Construcción y sincronización de la tabla de iteraciones."""
from collections.abc import Callable

from nicegui import ui

from src.frontend.controladores.formato_numerico_raices import numero


class TablaIteraciones:
    """Presenta filas numéricas y sincroniza su selección con el reproductor."""

    def __init__(self, al_seleccionar: Callable[[dict | None, int | None], None]):
        self._al_seleccionar = al_seleccionar
        self.tabla = None
        self._filas_grafica = {}
        self._indices_paso = {}

    def mostrar(self, filas: tuple, metodo: str) -> None:
        """Construye la tabla para la traza que devolvió el motor."""
        if not filas:
            return
        etiquetas = _etiquetas_columnas(metodo)
        filas_visibles = _preparar_filas_visibles(filas, metodo, etiquetas)
        filas_tabla = self._preparar_filas_tabla(filas_visibles, etiquetas)
        self._crear_tabla(etiquetas, filas_tabla)

    def _preparar_filas_tabla(self, filas_visibles, etiquetas) -> list[dict]:
        filas_tabla = []
        for clave, fila, fila_grafica, indice_paso in filas_visibles:
            visible = _formatear_fila(fila, etiquetas)
            visible["clave"] = clave
            filas_tabla.append(visible)
            self._filas_grafica[clave] = fila_grafica
            self._indices_paso[clave] = indice_paso
        return filas_tabla

    def _crear_tabla(self, etiquetas, filas_tabla) -> None:
        columnas = [{"name": campo, "label": texto, "field": campo, "align": "left"}
                    for campo, texto in etiquetas]
        ui.label("Selecciona una fila para ver sus puntos en la gráfica.").classes(
            "text-sm texto-secundario")
        self.tabla = ui.table(
            columns=columnas, rows=filas_tabla, row_key="clave", pagination=15,
            selection="single", on_select=self._seleccionar,
        ).classes("metodos-abiertos-tabla w-full")
        self.tabla.add_slot("body", _PLANTILLA_CUERPO)

    def _seleccionar(self, evento) -> None:
        if not evento.selection:
            self._al_seleccionar(None, None)
            return
        clave = str(evento.selection[0].get("clave", ""))
        self._al_seleccionar(self._filas_grafica.get(clave), self._indices_paso.get(clave))

    def sincronizar(self, fila: dict | None) -> None:
        """Marca la fila asociada al paso y cambia de página cuando hace falta."""
        if self.tabla is None or self.tabla.is_deleted:
            return
        seleccion = self._fila_seleccionada(fila)
        actual = [str(registro.get("clave")) for registro in self.tabla.selected]
        deseada = [] if not seleccion else [str(seleccion[0]["clave"])]
        self._cambiar_pagina(seleccion, deseada)
        if actual != deseada:
            self.tabla.selected = seleccion
            self.tabla.update()

    def _fila_seleccionada(self, fila: dict | None) -> list[dict]:
        if fila is None:
            return []
        fila_tabla = next((registro for registro in self.tabla.rows
                           if str(registro.get("i")) == str(fila.get("i"))), None)
        return [] if fila_tabla is None else [fila_tabla]

    def _cambiar_pagina(self, seleccion, deseada) -> None:
        if not seleccion:
            return
        indice = next((posicion for posicion, registro in enumerate(self.tabla.rows)
                       if str(registro.get("clave")) == deseada[0]), None)
        paginacion = self.tabla.pagination
        por_pagina = paginacion.get("rowsPerPage", 15)
        if indice is not None and por_pagina:
            pagina = indice // por_pagina + 1
            if paginacion.get("page", 1) != pagina:
                self.tabla.pagination = {**paginacion, "page": pagina}

    def limpiar(self) -> None:
        """Olvida las referencias a la tabla que ya salió de la interfaz."""
        self.tabla = None
        self._filas_grafica.clear()
        self._indices_paso.clear()


def _etiquetas_columnas(metodo: str) -> tuple[tuple[str, str], ...]:
    if metodo == "secante":
        return (("i", "i"), ("x_anterior", "xₙ₋₁"), ("x_n", "xₙ"),
                ("f_x_anterior", "f(xₙ₋₁)"), ("f_x_n", "f(xₙ)"),
                ("x_siguiente", "xₙ₊₁"), ("f_x_siguiente", "f(xₙ₊₁)"),
                ("residuo", "Residuo"), ("error_absoluto", "|Δx|"),
                ("error_relativo_porcentual", "Error rel. %"), ("criterio", "Criterio"))
    return (("i", "i"), ("x_n", "xₙ"), ("f_x_n", "f(xₙ)"),
            ("derivada", "f'(xₙ)"), ("x_siguiente", "xₙ₊₁"),
            ("f_x_siguiente", "f(xₙ₊₁)"), ("residuo", "Residuo"),
            ("error_absoluto", "|Δx|"), ("error_relativo_porcentual", "Error rel. %"),
            ("criterio", "Criterio"))


def _preparar_filas_visibles(filas, metodo, etiquetas) -> list[tuple]:
    visibles = []
    if metodo == "newton" and filas:
        primera = filas[0]
        inicial = {campo: None for campo, _ in etiquetas}
        inicial.update(i="0 (inicial)", x_n=primera["x_n"], f_x_n=primera["f_x_n"])
        visibles.append(("inicial", inicial, primera, 1))
    visibles.extend((str(fila["i"]), fila, fila, indice)
                    for indice, fila in enumerate(filas, 1))
    return visibles


def _formatear_fila(fila: dict, etiquetas) -> dict:
    return {campo: ("-" if fila.get(campo) is None else
                    str(fila[campo]) if campo == "i" else numero(fila[campo]))
            for campo, _ in etiquetas}


_PLANTILLA_CUERPO = """
    <q-tr :props="props" class="metodos-abiertos-fila" tabindex="0"
        :aria-label="'Mostrar iteración ' + props.row.i"
        @click="props.selected = !props.selected"
        @keydown.enter.prevent.stop="props.selected = !props.selected"
        @keydown.space.prevent.stop="props.selected = !props.selected">
        <q-td auto-width>
            <q-checkbox v-model="props.selected" dense @click.stop />
        </q-td>
        <q-td v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.value }}
        </q-td>
    </q-tr>
"""
