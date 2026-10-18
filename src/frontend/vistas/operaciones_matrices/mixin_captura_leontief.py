"""Paneles de captura de Leontief."""
from nicegui import ui
from src.backend.constantes import DIMENSION_MAXIMA_MODELOS, DIMENSION_MINIMA_LEONTIEF
from functools import partial
from src.frontend.componentes.cuadricula_base import crear_entradas_matriz
from src.frontend.componentes.captura_modelos import crear_entradas_vector, crear_entradas_nombres


class MixinCapturaLeontief:
    """Compone los campos y sus dimensiones sin reglas matemáticas."""

    def _construir_selector_tamano(self):
        with ui.row().classes("w-full items-center gap-3 mb-2"):
            ui.label("Tamaño n×n:").classes("text-sm font-bold texto-secundario")
            ui.button(icon="remove", on_click=partial(self._ajustar_tamano, -1), color=None).classes("boton-icono w-7 h-7 p-0").props('ripple=false aria-label="Reducir dimension"')
            ui.button(icon="add", on_click=partial(self._ajustar_tamano, 1), color=None).classes("boton-icono w-7 h-7 p-0").props('ripple=false aria-label="Aumentar dimension"')

    def _construir_panel_c(self):
        with ui.column().classes("w-full panel-tarjeta p-4 mb-4"):
            ui.label("Matriz de coeficientes técnicos C").classes("font-bold texto-principal mb-3")
            ui.html(
                '<p class="text-xs texto-secundario mb-2">Cada c<sub>ij</sub> indica la fracción de la producción del sector '
                "<i>i</i> que consume el sector <i>j</i> por unidad producida.</p>"
            )
            self.contenedor_coeficientes = ui.column().classes("modelos-captura")
            self._generar_cuadricula()

    def _construir_panel_d(self):
        with ui.column().classes("w-full panel-tarjeta p-4 mb-4"):
            ui.label("Vector de demanda final d").classes("font-bold texto-principal mb-3")
            self.contenedor_demanda = ui.column().classes("modelos-captura")
            self._generar_entradas_demanda()

    def _construir_panel_sectores(self):
        with ui.column().classes("w-full panel-tarjeta p-4"):
            ui.label("Nombres de sectores (opcional)").classes("font-bold texto-principal mb-3 text-sm")
            self.contenedor_sectores = ui.column().classes("w-full")
            self._generar_entradas_sectores()

    def _ajustar_tamano(self, delta: int):
        nuevo_tamano = self.numero_sectores + delta
        if not (DIMENSION_MINIMA_LEONTIEF <= nuevo_tamano <= DIMENSION_MAXIMA_MODELOS):
            return
        self.numero_sectores = nuevo_tamano
        self._generar_cuadricula()
        self._generar_entradas_demanda()
        self._generar_entradas_sectores()
        self._restablecer_resultados()

    def _generar_cuadricula(self):
        self.entradas_coeficientes = crear_entradas_matriz(self.contenedor_coeficientes, (self.numero_sectores, self.numero_sectores), "C")

    def _generar_entradas_demanda(self):
        self.entradas_demanda = crear_entradas_vector(self.contenedor_demanda, self.numero_sectores, "d")

    def _generar_entradas_sectores(self):
        self.entradas_sectores = crear_entradas_nombres(self.contenedor_sectores, self.numero_sectores, "Sector")
