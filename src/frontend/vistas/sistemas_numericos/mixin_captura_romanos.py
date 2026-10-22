"""Operandos, operación y ejemplos de la calculadora romana."""
from nicegui import ui
from src.frontend.controladores.sesion_matricial import actualizar_contexto


class MixinCapturaRomanos:
    """Compone y actualiza los controles de captura romana."""

    def _construir_ejemplos_rapidos(self) -> None:
        """Construye los botones de ejemplos rápidos preconfigurados."""
        with ui.row().classes("w-full items-center gap-3 flex-wrap"):
            with ui.row().classes("items-center gap-1.5 texto-secundario"):
                ui.icon("bolt", size="xs").classes("texto-acento")
                ui.label("Ejemplos rápidos:").classes("text-xs font-semibold tracking-wider uppercase")

            with ui.row().classes("gap-2.5 flex-wrap"):
                self.sugerencia_ejemplo("XIV + IX", "XIV", "IX", "suma")
                self.sugerencia_ejemplo("XX − VIII", "XX", "VIII", "resta")
                self.sugerencia_ejemplo("III × IV", "III", "IV", "multiplicacion")

    def _construir_campos_entrada(self) -> None:
        """Construye los campos de operandos y la etiqueta de operación."""
        with ui.column().classes("w-full gap-1"):
            with ui.row().classes("w-full items-center gap-3 flex-nowrap"):
                self.entrada_a = ui.input(placeholder="Operando A (ej: XIV)").classes(
                    "flex-1 matriz-entrada numericos-entrada text-center"
                ).classes("numericos-operando")
                self.entrada_a.props('autocomplete="off" spellcheck="false"')

                self.etiqueta_signo = ui.label("+").classes("text-2xl font-bold texto-secundario flex-shrink-0")

                self.entrada_b = ui.input(placeholder="Operando B (ej: IX)").classes(
                    "flex-1 matriz-entrada numericos-entrada text-center"
                ).classes("numericos-operando")
                self.entrada_b.props('autocomplete="off" spellcheck="false"')

            self.etiqueta_error = ui.label("").classes("fuente-pequena").classes("numericos-error").props('role="alert"')

    def sugerencia_ejemplo(self, etiqueta: str, operando_a: str, operando_b: str, operacion: str):
        """Crea un botón estilizado de ejemplo rápido."""
        return ui.button(
            etiqueta, on_click=lambda: self.cargar_ejemplo(operando_a, operando_b, operacion), color=None
        ).classes(
            "px-3.5 py-1.5 rounded-lg border texto-principal font-mono text-xs font-bold tracking-wide cursor-pointer"
        ).classes("numericos-ejemplo").props("no-caps flat ripple=false")

    def cargar_ejemplo(self, operando_a: str, operando_b: str, operacion: str) -> None:
        """Carga los operandos y la operación del ejemplo seleccionado."""
        self.entrada_a.value = operando_a
        self.entrada_b.value = operando_b
        self.pestanas_operacion.set_value(operacion)
        self.etiqueta_error.text = ""

    def actualizar_signo(self, evento) -> None:
        """Actualiza el glifo del operador visual."""
        signos = {"suma": "+", "resta": "−", "multiplicacion": "×"}
        self.etiqueta_signo.text = signos.get(evento.value, "+")
        self.etiqueta_error.text = ""
        self._notificar_cambio()

    def copiar(self, texto: str) -> None:
        """Copia el texto al portapapeles y notifica al usuario."""
        ui.clipboard.write(texto)
        ui.notify(f"Copiado: {texto}", type="positive", position="top")

    def _notificar_cambio(self) -> None:
        """Notifica al panel de Glosa para recalcular contexto."""
        actualizar_contexto(self)

    def _orientar_error_operandos(self, error=None, mensaje: str = "") -> None:
        """Señala operandos mediante los metadatos de error del backend, sin repetir validación."""
        token = getattr(error, "token_invalido", None)
        for entrada in (self.entrada_a, self.entrada_b):
            if not hasattr(entrada, "props"):
                continue
            valor = (entrada.value or "").strip().upper()
            invalida = bool(mensaje and ((token is not None and valor == token) or (getattr(error, "codigo", None) == "ENTRADA_VACIA" and not valor)))
            if invalida:
                entrada._props["error-message"] = mensaje
                entrada.props("error")
            else:
                entrada.props(remove="error error-message")
