"""Paneles de captura de Transformaciones."""
from nicegui import ui
from src.backend.constantes import DIMENSION_MINIMA, DIMENSION_MAXIMA_MODELOS
from functools import partial
from src.frontend.componentes.captura.nucleo.cuadricula_base import (
    crear_entradas_matriz, ejecutar_transicion_cuadricula, selectores_cambio_dimension,
    selector_dimension_matriz, actualizar_estados_botones_dimension,
    indice_cambio_dimension,
)
from src.frontend.componentes.captura.matrices.captura_modelos import crear_entradas_nombres


class MixinCapturaTransformaciones:
    """Compone los campos y sus dimensiones sin reglas matemáticas."""

    def _construir_selector_tamano(self):
        with ui.row().classes("items-center gap-3 flex-wrap"):
            with ui.row().classes("gap-1 items-center"):
                ui.label("m (ℝᵐ):").classes("text-sm font-bold texto-secundario")
                self.boton_quitar_fila = ui.button(icon="remove", on_click=partial(self._ajustar_filas, -1), color=None).classes("boton-icono p-0").props('ripple=false aria-label="Reducir filas m"')
                self.etiqueta_filas = ui.label(str(self.filas)).classes("font-bold text-sm w-5 text-center texto-principal etiqueta-dimensiones")
                self.boton_agregar_fila = ui.button(icon="add", on_click=partial(self._ajustar_filas, 1), color=None).classes("boton-icono p-0").props('ripple=false aria-label="Aumentar filas m"')
            with ui.row().classes("gap-1 items-center"):
                ui.label("n (ℝⁿ):").classes("text-sm font-bold texto-secundario")
                self.boton_quitar_columna = ui.button(icon="remove", on_click=partial(self._ajustar_columnas, -1), color=None).classes("boton-icono p-0").props('ripple=false aria-label="Reducir columnas n"')
                self.etiqueta_columnas = ui.label(str(self.columnas)).classes("font-bold text-sm w-5 text-center texto-principal etiqueta-dimensiones")
                self.boton_agregar_columna = ui.button(icon="add", on_click=partial(self._ajustar_columnas, 1), color=None).classes("boton-icono p-0").props('ripple=false aria-label="Aumentar columnas n"')
        self._actualizar_botones_tamano()

    def _construir_panel_a(self):
        with ui.column().classes("w-full panel-tarjeta p-5 gap-3 mb-4"):
            with ui.row().classes("modelos-captura-cabecera w-full"):
                ui.label("Matriz A de la transformación").classes("font-bold texto-principal")
                self._construir_selector_tamano()
            ui.html(
                '<p class="text-xs texto-secundario">'
                "Ingresa la matriz A tal que T(x) = Ax. "
                "Filas m = dimensión del codominio ℝ<sup>m</sup>, "
                "columnas n = dimensión del dominio ℝ<sup>n</sup>.</p>"
            )
            self.contenedor_coeficientes = ui.column().classes("modelos-captura")
            self._generar_cuadricula()

    def _construir_panel_variables(self):
        with ui.expansion("Nombres de variables (opcional)", icon="label").classes("w-full panel-tarjeta"):
            self.contenedor_variables = ui.column().classes("w-full pt-2")
            self._generar_entradas_variables()


    async def _ajustar_filas(self, delta: int):
        await self._ajustar_dimension("filas", delta)

    async def _ajustar_columnas(self, delta: int):
        await self._ajustar_dimension("columnas", delta)

    async def _ajustar_dimension(self, eje: str, delta: int):
        actual = getattr(self, eje)
        nuevo = actual + delta
        if not (DIMENSION_MINIMA <= nuevo <= DIMENSION_MAXIMA_MODELOS):
            return
        indice = indice_cambio_dimension(actual, nuevo)
        selector = selector_dimension_matriz("A", indice, ("fila" if eje == "filas" else "columna",))
        if eje == "columnas":
            selector += "," + selector_dimension_matriz("Variable", indice, ("columna",))
            selector += "," + selector_dimension_matriz("v", indice, ("fila",))
        botones = (self.boton_quitar_fila, self.boton_agregar_fila, self.boton_quitar_columna, self.boton_agregar_columna)
        await ejecutar_transicion_cuadricula(
            vars(self), selectores_cambio_dimension(selector, delta), partial(self._aplicar_dimension, eje, nuevo),
            botones, self._actualizar_botones_tamano,
        )

    def _actualizar_botones_tamano(self):
        if getattr(self, "etiqueta_filas", None) is not None:
            self.etiqueta_filas.set_text(str(self.filas))
        if getattr(self, "etiqueta_columnas", None) is not None:
            self.etiqueta_columnas.set_text(str(self.columnas))
        actualizar_estados_botones_dimension(self.boton_quitar_fila, self.boton_agregar_fila, self.filas, DIMENSION_MINIMA, DIMENSION_MAXIMA_MODELOS)
        actualizar_estados_botones_dimension(self.boton_quitar_columna, self.boton_agregar_columna, self.columnas, DIMENSION_MINIMA, DIMENSION_MAXIMA_MODELOS)

    def _aplicar_dimension(self, eje: str, numero: int):
        setattr(self, eje, numero)
        self._generar_cuadricula()
        if eje == "columnas":
            self._generar_entradas_variables()
        self._restablecer_resultados()

    def _generar_cuadricula(self):
        self.entradas_coeficientes = crear_entradas_matriz(self.contenedor_coeficientes, (self.filas, self.columnas), "A")
        self._actualizar_botones_tamano()

    def _generar_entradas_variables(self):
        self.entradas_variables = crear_entradas_nombres(self.contenedor_variables, self.columnas, "Variable")
        if getattr(self, "contenedor_vector_original", None) is not None:
            self._generar_vector_original()
