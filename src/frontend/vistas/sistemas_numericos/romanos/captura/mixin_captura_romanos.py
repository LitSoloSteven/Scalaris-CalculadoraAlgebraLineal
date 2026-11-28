"""Operandos y operación de la calculadora romana."""
from nicegui import ui
from src.frontend.componentes.aplicacion.base.simbolos import habilitar_simbolos
from src.frontend.componentes.aplicacion.base.sonido import notificar
from src.frontend.controladores.compartido.sesion.sesion_matricial import actualizar_contexto, notificar_edicion


class MixinCapturaRomanos:
    """Compone y actualiza los controles de captura romana."""

    def _construir_campos_entrada(self) -> None:
        """Construye los campos de operandos con rótulos persistentes y la etiqueta de operación."""
        with ui.column().classes("w-full gap-1"):
            with ui.row().classes("w-full items-end gap-3 numericos-operandos-fila flex-wrap sm:flex-nowrap"):
                with ui.column().classes("flex-1 min-w-0 gap-1"):
                    ui.label("Operando A").classes("text-sm font-semibold texto-secundario").props(
                        'id="romanos-etiqueta-a"'
                    )
                    self.entrada_a = ui.input().classes(
                        "w-full matriz-entrada numericos-entrada text-center numericos-operando"
                    )
                    self.entrada_a.props(
                        'autocomplete="off" spellcheck="false" aria-label="Operando A" '
                        'aria-labelledby="romanos-etiqueta-a"'
                    )
                    habilitar_simbolos(self.entrada_a, "romano")

                self.etiqueta_signo = ui.label("+").classes(
                    "text-2xl font-bold texto-secundario flex-shrink-0 self-end mb-3"
                )

                with ui.column().classes("flex-1 min-w-0 gap-1"):
                    ui.label("Operando B").classes("text-sm font-semibold texto-secundario").props(
                        'id="romanos-etiqueta-b"'
                    )
                    self.entrada_b = ui.input().classes(
                        "w-full matriz-entrada numericos-entrada text-center numericos-operando"
                    )
                    self.entrada_b.props(
                        'autocomplete="off" spellcheck="false" aria-label="Operando B" '
                        'aria-labelledby="romanos-etiqueta-b"'
                    )
                    habilitar_simbolos(self.entrada_b, "romano")

            self.etiqueta_error = ui.label("").classes("fuente-pequena numericos-error").props('role="alert"')

    def cargar_ejemplo(self, operando_a: str, operando_b: str, operacion: str) -> None:
        """Carga los operandos y la operación recibidos en la captura."""
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
        notificar(f"Copiado: {texto}", type="positive", position="top")

    def _notificar_cambio(self) -> None:
        """Notifica al panel de Glosa para recalcular contexto."""
        notificar_edicion(self)
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
                entrada.props(
                    f'error hide-bottom-space aria-invalid=true aria-describedby={self.etiqueta_error.html_id}',
                    remove="error-message",
                )
            else:
                entrada.props(
                    "aria-invalid=false",
                    remove="error error-message hide-bottom-space aria-describedby",
                )
