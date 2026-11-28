"""Paneles de captura de Leontief."""
from nicegui import ui
from src.backend.constantes import DIMENSION_MAXIMA_MODELOS, DIMENSION_MINIMA_LEONTIEF
from functools import partial
from src.frontend.componentes.captura.nucleo.cuadricula_base import (
    crear_entradas_matriz, ejecutar_transicion_cuadricula, selectores_cambio_dimension,
    selector_dimension_matriz, actualizar_estados_botones_dimension,
    indice_cambio_dimension,
)
from src.frontend.componentes.captura.matrices.captura_modelos import crear_entradas_vector, crear_entradas_nombres


class MixinCapturaLeontief:
    """Compone los campos y sus dimensiones sin reglas matemáticas."""

    def _construir_captura_modelo(self):
        """Integra dimensiones, coeficientes C y demanda final d en una sola tarjeta."""
        with ui.column().classes("w-full panel-tarjeta p-5 gap-4"):
            with ui.row().classes("modelos-captura-cabecera w-full"):
                ui.label("Matriz de coeficientes técnicos C").classes("font-bold texto-principal")
                self._construir_selector_tamano()
            ui.html(
                '<p class="text-xs texto-secundario">Cada c<sub>ij</sub> indica la fracción de la producción del sector '
                "<i>i</i> que consume el sector <i>j</i> por unidad producida.</p>"
            )
            self.contenedor_coeficientes = ui.column().classes("modelos-captura")
            self._generar_cuadricula()
            with ui.column().classes("w-full min-w-0 gap-3 modelos-bloque-relacionado"):
                ui.label("Vector de demanda final d").classes("font-bold texto-principal")
                self.contenedor_demanda = ui.column().classes("modelos-captura")
                self._generar_entradas_demanda()

    def _construir_selector_tamano(self):
        with ui.row().classes("items-center gap-2"):
            ui.label("Sectores:").classes("text-sm font-bold texto-secundario")
            self.boton_reducir = ui.button(icon="remove", on_click=partial(self._ajustar_tamano, -1), color=None).classes("boton-icono p-0").props('ripple=false aria-label="Reducir dimensión"')
            self.etiqueta_sectores = ui.label(f"{self.numero_sectores} × {self.numero_sectores}").classes("font-bold text-sm texto-principal etiqueta-dimensiones")
            self.boton_aumentar = ui.button(icon="add", on_click=partial(self._ajustar_tamano, 1), color=None).classes("boton-icono p-0").props('ripple=false aria-label="Aumentar dimensión"')
        self._actualizar_botones_tamano()

    def _construir_panel_sectores(self):
        with ui.expansion("Nombres de sectores (opcional)", icon="label").classes("w-full panel-tarjeta"):
            self.contenedor_sectores = ui.column().classes("w-full pt-2")
            self._generar_entradas_sectores()

    async def _ajustar_tamano(self, delta: int):
        nuevo_tamano = self.numero_sectores + delta
        if not (DIMENSION_MINIMA_LEONTIEF <= nuevo_tamano <= DIMENSION_MAXIMA_MODELOS):
            return
        indice = indice_cambio_dimension(self.numero_sectores, nuevo_tamano)
        selector = ",".join((selector_dimension_matriz("C", indice, ("fila", "columna")),
                             selector_dimension_matriz("d", indice, ("columna",)),
                             selector_dimension_matriz("Sector", indice, ("columna",))))
        await ejecutar_transicion_cuadricula(
            vars(self), selectores_cambio_dimension(selector, delta), partial(self._aplicar_tamano, nuevo_tamano),
            (self.boton_reducir, self.boton_aumentar), self._actualizar_botones_tamano,
        )

    def _actualizar_botones_tamano(self):
        if getattr(self, "etiqueta_sectores", None) is not None:
            self.etiqueta_sectores.set_text(f"{self.numero_sectores} × {self.numero_sectores}")
        actualizar_estados_botones_dimension(self.boton_reducir, self.boton_aumentar, self.numero_sectores,
                                            DIMENSION_MINIMA_LEONTIEF, DIMENSION_MAXIMA_MODELOS)

    def _aplicar_tamano(self, numero: int):
        self.numero_sectores = numero
        self._generar_cuadricula()
        self._generar_entradas_demanda()
        self._generar_entradas_sectores()
        self._restablecer_resultados()

    def _generar_cuadricula(self):
        self.entradas_coeficientes = crear_entradas_matriz(self.contenedor_coeficientes, (self.numero_sectores, self.numero_sectores), "C")
        self._actualizar_botones_tamano()

    def _generar_entradas_demanda(self):
        self.entradas_demanda = crear_entradas_vector(self.contenedor_demanda, self.numero_sectores, "d")

    def _generar_entradas_sectores(self):
        self.entradas_sectores = crear_entradas_nombres(self.contenedor_sectores, self.numero_sectores, "Sector")
