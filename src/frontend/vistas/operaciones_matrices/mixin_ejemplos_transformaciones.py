"""Selección y carga de ejemplos de Transformaciones."""
from src.frontend.componentes.sonido import notificar
from src.frontend.componentes.captura_modelos import construir_ejemplos
from src.frontend.componentes.captura_modelos import llenar_entradas
from src.frontend import textos_transformaciones as textos
from nicegui import ui
from ._ejemplos_transformaciones import EJEMPLOS_TRANSFORMACIONES
from ._ejemplos_aplicacion_transformacion import EJEMPLOS_APLICACION
from .carga_modelos import cargar_captura_modelo


class MixinEjemplosTransformaciones:
    """Carga datos internos de ejemplo en los controles de captura."""

    def _construir_ejemplos(self):
        with ui.column().classes("w-full").bind_visibility_from(
            self.selector_modo, 'value', backward=lambda modo: modo == textos.MODO_ANALISIS
        ):
            construir_ejemplos(EJEMPLOS_TRANSFORMACIONES, self._cargar_ejemplo, "Ejemplos precargados")
        with ui.column().classes("w-full").bind_visibility_from(
            self.selector_modo, 'value', backward=lambda modo: modo == textos.MODO_APLICACION
        ):
            construir_ejemplos(EJEMPLOS_APLICACION, self._cargar_ejemplo, textos.TITULO_EJEMPLOS)

    def _cargar_ejemplo(self, ejemplo: dict):
        aplicacion = "vector_original" in ejemplo
        self.selector_modo.set_value(textos.MODO_APLICACION if aplicacion else textos.MODO_ANALISIS)
        cargar_captura_modelo(self, ejemplo)
        if aplicacion:
            llenar_entradas(self.entradas_vector_original, ejemplo["vector_original"])
            self._restablecer_resultados()
        notificar(f"Ejemplo '{ejemplo['nombre']}' cargado.", type="positive", position="top")
