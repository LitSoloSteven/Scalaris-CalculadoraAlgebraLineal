"""Vista previa textual e historial de capturas de varias entradas."""
from nicegui import ui

from src.frontend import textos
from src.frontend.controladores.sesion_matricial import registrar_calculo


def renderizar_registro_captura(registro: dict, cargar) -> None:
    """Presenta un registro con restauración explícita y sin repetir el cálculo."""
    with ui.column().classes("w-full panel-tarjeta p-3"):
        ui.label(registro["hora"]).classes("texto-secundario")
        ui.label(registro["mensaje"]).classes("texto-principal")
        ui.button(textos.MODELOS_RESTAURAR, color=None, on_click=lambda evento: cargar(
            registro["captura"])).classes("boton-discreto").props("ripple=false")


def renderizar_historial_capturas(contenedor, registros: list[dict], cargar) -> None:
    """Actualiza el historial con su estado vacío y acciones de restauración."""
    contenedor.clear()
    with contenedor:
        if not registros:
            ui.label(textos.MODELOS_HISTORIAL_VACIO).classes("texto-secundario")
        for registro in registros:
            renderizar_registro_captura(registro, cargar)


class SesionCapturas:
    """Retiene cinco capturas y una vista textual sin depender de una herramienta concreta."""

    def __init__(self, cargar) -> None:
        self.cargar = cargar
        self.registros = []
        with ui.expansion(textos.MODELOS_VISTA_PREVIA, icon="visibility").classes("w-full panel-tarjeta"):
            self.previa = ui.label("").classes("w-full min-w-0 whitespace-pre font-mono overflow-x-auto texto-principal").props(
                'tabindex="0" role="region"')
            self.previa._props["aria-label"] = textos.MODELOS_VISTA_PREVIA
        with ui.expansion(textos.MODELOS_HISTORIAL, icon="history").classes("w-full panel-tarjeta"):
            self.contenedor = ui.column().classes("w-full min-w-0")
        self._renderizar()

    def actualizar_previa(self, texto: str) -> None:
        """Sustituye la vista textual con los valores actuales escapados por ui.label."""
        if not self.previa.is_deleted:
            self.previa.set_text(texto)

    def registrar(self, captura: dict, mensaje: str) -> None:
        """Guarda una copia independiente de la captura exitosa y actualiza el historial."""
        registrar_calculo(self.registros, {"captura": captura, "mensaje": mensaje})
        self._renderizar()

    def _renderizar(self) -> None:
        renderizar_historial_capturas(self.contenedor, self.registros, self.cargar)
