"""Controles de modo y coordenadas para aplicar transformaciones lineales."""
from nicegui import ui

from src.frontend import textos_transformaciones as textos
from src.frontend.componentes.cuadricula_base import crear_entradas_matriz
from src.frontend.componentes.selector_opciones import SelectorOpciones
from src.frontend.controladores.limpieza_captura import vaciar_campos
from src.frontend.sugerencias import Senales
from .procedimiento_aplicacion_transformacion import detener_procedimiento_aplicacion


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
        self.boton_calcular.props["aria-label"] = self.boton_calcular.text
        self._restablecer_resultados()

    def _cambiar_tipo_objeto(self, evento) -> None:
        self.tipo_objeto = evento.value
        self._restablecer_resultados()

    def _construir_herramientas_modelo(self) -> None:
        super()._construir_herramientas_modelo()
        self.contenedor_historial.parent_slot.parent.bind_visibility_from(
            self.selector_modo, 'value', backward=lambda modo: modo == textos.MODO_ANALISIS)

    def obtener_contexto_ia(self):
        """Devuelve el contexto del análisis; omite contratos de aplicación aún no disponibles."""
        return None if self.modo_transformacion == textos.MODO_APLICACION else super().obtener_contexto_ia()

    def obtener_senales_ia(self):
        """Conserva señales del análisis sin atribuir sus propiedades a una aplicación."""
        if self.modo_transformacion == textos.MODO_APLICACION:
            return Senales(self.herramienta_modelo, "sin_resultado")
        return super().obtener_senales_ia()

    def _sincronizar_captura_modelo(self) -> None:
        detener_procedimiento_aplicacion(self)
        super()._sincronizar_captura_modelo()

    def _desmontar_modelo(self) -> None:
        detener_procedimiento_aplicacion(self)
        super()._desmontar_modelo()

    def limpiar_todo(self) -> None:
        """Limpia también las coordenadas y nombres ocultos para que no reaparezcan."""
        vaciar_campos(self.entradas_variables + self.entradas_vector_original)
        super().limpiar_todo()
