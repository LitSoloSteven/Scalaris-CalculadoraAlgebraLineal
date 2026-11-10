"""Errores junto al campo y foco de la primera corrección pendiente."""
from nicegui import ui

from src.frontend.controladores.regla_falsa.validacion_contextual import errores_captura
from .estado_captura import CAMPOS


class EstadosEntrada:
    """Conserva validación contextual en controles existentes sin publicar HTML de usuario."""

    def __init__(self, vista):
        self.vista = vista
        self.revisados = set()
        self.mensajes = {}

    def construir(self) -> None:
        """Enlaza salida de cada campo con revisión y un mensaje accesible local."""
        for clave, atributo in CAMPOS.items():
            campo = getattr(self.vista, atributo)
            with campo:
                self.mensajes[clave] = ui.label().classes("text-sm texto-advertencia break-all").props(
                    "role=alert")
            campo.on("blur", lambda evento, clave=clave: self.revisar(clave))

    def revisar(self, clave: str) -> None:
        """Revisa un campo visitado sin enfocar ni enviar un cálculo."""
        self.revisados.add(clave)
        self.actualizar()

    def actualizar(self) -> None:
        """Actualiza solo campos visitados tras una edición de la captura."""
        if self.revisados:
            self._mostrar(errores_captura(self.vista.capturar()))

    def validar(self) -> bool:
        """Valida todos los campos y enfoca el primero inválido; devuelve si se puede enviar."""
        self.revisados.update(CAMPOS)
        errores = errores_captura(self.vista.capturar())
        self._mostrar(errores)
        if errores:
            clave = next(clave for clave in CAMPOS if clave in errores)
            getattr(self.vista, CAMPOS[clave]).run_method("focus")
            self.vista.estado.set_text("Revisa el campo señalado antes de calcular.")
        return not errores

    def limpiar(self) -> None:
        """Retira los errores visitados al vaciar el ejercicio."""
        self.revisados.clear()
        self._mostrar({})

    def _mostrar(self, errores: dict) -> None:
        for clave, mensaje in self.mensajes.items():
            texto = errores.get(clave, "") if clave in self.revisados else ""
            mensaje.set_text(texto)
            mensaje.set_visibility(bool(texto))
            campo = getattr(self.vista, CAMPOS[clave])
            campo.props(f'aria-invalid={str(bool(texto)).lower()} aria-describedby={mensaje.html_id}')
