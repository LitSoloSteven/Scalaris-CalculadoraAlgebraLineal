"""Acciones de pegado y redimensión para la captura rectangular."""
from functools import partial
from nicegui import ui

from src.backend.constantes import DIMENSION_MAXIMA_MATRICES, DIMENSION_MINIMA
from src.frontend.componentes.cuadricula_base import (CambioCuadricula, actualizar_estados_botones_dimension,
    ejecutar_transicion_cuadricula, indice_cambio_dimension, purgar_cache_bidimensional,
    selector_dimension_matriz, selectores_cambio_dimension)
from src.frontend.componentes.animacion_matriz import animar_redimension_matriz
from src.frontend.componentes.portapapeles_matricial import parsear_portapapeles_rectangular
from src.frontend.componentes.redimension_rectangular import actualizar_rectangulo
from src.frontend.componentes.tareas import lanzar_tarea
from src.frontend.textos import CAPTURA_PORTAPAPELES_ERROR, CAPTURA_RECTANGULAR_RECORTADA


class AccionesMatrizRectangular:
    """Coordina las acciones de edición de una cuadrícula rectangular."""

    def redimensionar(self, eje: str, delta: int) -> None:
        """Solicita un cambio unitario del eje indicado dentro de los límites."""
        if self._redimensionando:
            return
        self._redimensionando = True
        self._revision_panel += 1
        try:
            lanzar_tarea(ui.context.client, self._redimensionar(eje, delta))
        except Exception:
            self._redimensionando = False
            raise

    async def _redimensionar(self, eje: str, delta: int) -> None:
        try:
            actual = getattr(self, eje)
            nuevo = min(max(actual + delta, DIMENSION_MINIMA), DIMENSION_MAXIMA_MATRICES)
            if nuevo == actual:
                return
            selector = selector_dimension_matriz("A", indice_cambio_dimension(actual, nuevo), ("fila" if eje == "filas" else "columna",))
            botones = tuple(boton for pareja in self.controles.values() for boton in pareja)
            await ejecutar_transicion_cuadricula(vars(self), CambioCuadricula(selectores_cambio_dimension(selector, delta), animar_redimension_matriz),
                partial(self._aplicar_dimension, eje, nuevo), botones, self._actualizar_controles)
        finally:
            self._redimensionando = False

    def _aplicar_dimension(self, eje: str, nuevo: int) -> None:
        anterior = (self.filas, self.columnas)
        setattr(self, eje, nuevo)
        self.cache = purgar_cache_bidimensional(self.cache, self.filas, self.columnas)
        estado = {"entradas": self.celdas, "filas_interfaz": self.filas_interfaz, "contenido": self.contenedor_cuadricula}
        if not actualizar_rectangulo(estado, anterior, (self.filas, self.columnas), self._anadir_fila, self._crear_celda):
            self._renderizar_completa()
        self._publicar(reconstruir=False)

    def _actualizar_controles(self) -> None:
        for eje, botones in self.controles.items():
            actualizar_estados_botones_dimension(*botones, getattr(self, eje), DIMENSION_MINIMA, DIMENSION_MAXIMA_MATRICES)
        if self.etiqueta_dimension_matriz:
            self.etiqueta_dimension_matriz.set_content(f'A <span class="separador-punto">·</span> {self.filas} &times; {self.columnas}')

    def _publicar(self, reconstruir: bool = True) -> None:
        self._actualizar_controles()
        if reconstruir:
            self._renderizar_completa()
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    async def pegar_desde_portapapeles(self) -> None:
        """Lee texto tabular, avisa si excede los límites y carga la matriz."""
        if self._redimensionando:
            return
        self._revision_panel += 1
        revision = self._revision_panel
        try:
            texto = await ui.run_javascript("return navigator.clipboard.readText();")
        except Exception:
            ui.notify(CAPTURA_PORTAPAPELES_ERROR, type="warning")
            return
        if self._redimensionando or revision != self._revision_panel:
            return
        filas, recortado = parsear_portapapeles_rectangular(texto or "", DIMENSION_MAXIMA_MATRICES)
        if recortado:
            ui.notify(CAPTURA_RECTANGULAR_RECORTADA.format(limite=DIMENSION_MAXIMA_MATRICES), type="warning")
        if filas:
            self.cargar_matriz(filas)
