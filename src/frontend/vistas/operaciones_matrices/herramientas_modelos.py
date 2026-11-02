"""Vista previa e historial de capturas completas de modelos matriciales."""
from nicegui import ui

from src.frontend import textos
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.controladores.operaciones_matrices.contexto_modelos import capturar_modelo
from src.frontend.controladores.operaciones_matrices.vista_previa_modelos import preparar_vista_previa_modelo
from src.frontend.controladores.sesion_matricial import registrar_calculo, programar_vista_previa
from .carga_modelos import cargar_captura_modelo
from src.frontend.componentes.sesion_capturas import renderizar_historial_capturas


class MixinHerramientasModelos:
    """Comparte presentación y restauración de la captura de cada sesión."""

    def _construir_herramientas_modelo(self) -> None:
        self.historial = []
        self.tarea_vista_previa = None
        with self.contenedor_resultados.parent_slot.parent:
            with ui.expansion(textos.MODELOS_VISTA_PREVIA, icon="visibility").classes("w-full panel-tarjeta"):
                self.contenedor_vista_previa = ui.column().classes("w-full min-w-0")
            with ui.expansion(textos.MODELOS_HISTORIAL, icon="history").classes("w-full panel-tarjeta"):
                self.contenedor_historial = ui.column().classes("w-full min-w-0")
        self._renderizar_historial_modelo()
        programar_vista_previa(self)

    async def _actualizar_vista_previa(self) -> None:
        contenedor = self.contenedor_vista_previa
        if contenedor.is_deleted:
            return
        contenedor.clear()
        with contenedor:
            try:
                renderizar_latex(preparar_vista_previa_modelo(self))
            except ValueError:
                ui.label(textos.VISTA_PREVIA_ERROR).classes("texto-secundario").props('role="status"')

    def _registrar_modelo(self) -> None:
        if self.ultimo_resultado.get("estado") == "ERROR":
            return
        registrar_calculo(self.historial, {"captura": capturar_modelo(self), "mensaje": self.ultimo_resultado.get("mensaje", "")})
        self._renderizar_historial_modelo()

    def _renderizar_historial_modelo(self) -> None:
        renderizar_historial_capturas(self.contenedor_historial, self.historial,
                                     lambda captura: cargar_captura_modelo(self, captura))
