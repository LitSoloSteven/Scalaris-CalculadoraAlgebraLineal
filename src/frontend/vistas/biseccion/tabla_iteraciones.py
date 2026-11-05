"""Paginación en servidor y formato de la página visible de la traza."""
from nicegui import ui

from src.frontend.controladores.biseccion.presentacion import COLUMNAS, filas_tabla
from src.frontend.controladores.biseccion.salidas_biseccion import COLUMNAS_EXAMEN, datos_examen

_FILAS_POR_PAGINA = 15


def mostrar_tabla(respuesta: dict, examen: ui.switch | ui.checkbox | None = None) -> None:
    """Monta una tabla desplazable que solo recibe las filas de la página actual."""
    with ui.column().classes("panel-tarjeta p-5 w-full min-w-0"):
        ui.label("Tabla de iteraciones").classes("text-xl font-bold")
        ui.label("Ancho: b−a. Cota: (b−a)/2 en x, si f es continua. Residuo: |f(c)|. Error relativo: |(cᵢ−cᵢ₋₁)/cᵢ|·100%; no aplica en la primera fila o si cᵢ=0.").classes("text-sm texto-secundario")
        precision = ui.switch("Inspeccionar valores internos (hasta 17 cifras)")
        with ui.element("div").classes("biseccion-tabla w-full").props('tabindex=0 role=region aria-label="Tabla de iteraciones con desplazamiento horizontal"'):
            tabla = ui.table(columns=[], rows=[], row_key="i", pagination=0).classes("w-full").props("hide-bottom")
        paginacion = _Paginacion(tabla, respuesta, precision, examen)
        paginacion.construir()


class _Paginacion:
    def __init__(self, tabla, respuesta: dict, precision, examen):
        self.tabla, self.respuesta = tabla, respuesta
        self.precision, self.examen = precision, examen
        self.pagina = 0
        self.total = len(respuesta["iteraciones"])

    def construir(self) -> None:
        """Monta el navegador de páginas y enlaza las preferencias de la tabla."""
        with ui.row().classes("w-full items-center gap-2"):
            self.anterior = ui.button("Anterior", color=None, on_click=lambda: self._mover(-1)).classes("boton-discreto")
            self.siguiente = ui.button("Siguiente", color=None, on_click=lambda: self._mover(1)).classes("boton-discreto")
            self.estado = ui.label().classes("text-sm texto-secundario").props("role=status")
        self.precision.on_value_change(self._actualizar)
        if self.examen is not None:
            self.examen.on_value_change(self._actualizar)
        self._actualizar()

    def _mover(self, direccion: int) -> None:
        ultima = max(0, (self.total - 1) // _FILAS_POR_PAGINA)
        self.pagina = min(ultima, max(0, self.pagina + direccion))
        self._actualizar()

    def _actualizar(self) -> None:
        if self.tabla.is_deleted:
            return
        inicio = self.pagina * _FILAS_POR_PAGINA
        fin = min(inicio + _FILAS_POR_PAGINA, self.total)
        originales = self.respuesta["iteraciones"][inicio:fin]
        examen = self.examen is not None and self.examen.value
        self.tabla.columns = [{"name": clave, "label": etiqueta, "field": clave, "align": "left"}
                              for clave, etiqueta in (COLUMNAS + COLUMNAS_EXAMEN if examen else COLUMNAS)]
        filas = filas_tabla({"iteraciones": originales}, self.precision.value)
        if examen:
            for fila, original in zip(filas, originales):
                fila.update(datos_examen(original, self.respuesta["estado"]))
        self.tabla.update_rows(filas)
        self.anterior.set_enabled(inicio > 0)
        self.siguiente.set_enabled(fin < self.total)
        self.estado.set_text(f"Filas {inicio + 1 if self.total else 0} a {fin} de {self.total}")
