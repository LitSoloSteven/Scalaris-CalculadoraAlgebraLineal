"""Controles de modo y coordenadas para aplicar transformaciones lineales."""
from nicegui import ui

from src.frontend import textos_transformaciones as textos
from src.frontend.componentes.cuadricula_base import crear_entradas_matriz
from src.frontend.componentes.selector_opciones import SelectorOpciones


class MixinAplicacionTransformacion:
    """Compone selectores y un vector columna con la cuadrícula compartida."""

    def _construir_selector_modo(self) -> None:
        self.selector_modo = SelectorOpciones(textos.OPCIONES_MODO, self.modo_transformacion,
                                              self._cambiar_modo, "Operación de transformaciones")

    def _construir_panel_aplicacion(self) -> None:
        region = ui.column().classes("w-full min-w-0 gap-3")
        with self.selector_modo.asociar_contenido(textos.MODO_APLICACION, region):
            self.selector_tipo_objeto = SelectorOpciones(textos.OPCIONES_OBJETO, self.tipo_objeto,
                                                        self._cambiar_tipo_objeto, "Objeto que se transforma")
            ui.label(textos.CONVENCION).classes("texto-secundario text-sm")
            with ui.column().classes("w-full panel-tarjeta p-4 min-w-0"):
                ui.label(textos.TITULO_CAPTURA).classes("font-bold texto-principal")
                ui.label(textos.AYUDA_CAPTURA).classes("texto-secundario text-sm")
                self.contenedor_vector_original = ui.column().classes("modelos-captura min-w-0")
                self._generar_vector_original()

    def _generar_vector_original(self) -> None:
        self.entradas_vector_original = [fila[0] for fila in crear_entradas_matriz(
            self.contenedor_vector_original, (self.columnas, 1), "v")]
        for indice, entrada in enumerate(self.entradas_vector_original):
            entrada.props["aria-label"] = f"Componente original {indice + 1}"

    def _cambiar_modo(self, evento) -> None:
        self.modo_transformacion = evento.value
        self.boton_calcular.set_text(textos.APLICAR if evento.value == textos.MODO_APLICACION else textos.ANALIZAR)
        self._restablecer_resultados()

    def _cambiar_tipo_objeto(self, evento) -> None:
        self.tipo_objeto = evento.value
        self._restablecer_resultados()
