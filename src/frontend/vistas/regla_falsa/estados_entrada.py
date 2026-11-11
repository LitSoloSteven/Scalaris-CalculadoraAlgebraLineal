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
            self._vincular(getattr(self.vista, atributo), clave)
        for tipo, campo in self.vista.parametros_criterio.items():
            if tipo != "residuo":
                self._vincular(campo, "criterio")

    def _vincular(self, campo, clave: str) -> None:
        campo.without_auto_validation()
        campo.on("blur", lambda: self.revisar(clave))
        with campo.add_slot("error"):
            self.mensajes[campo] = ui.label().props("role=alert")

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
        self.revisados.update((*CAMPOS, "criterio"))
        errores = errores_captura(self.vista.capturar())
        self._mostrar(errores)
        if errores:
            clave = next(iter(errores))
            self._campo(clave).run_method("focus")
            self.vista.estado.set_text("Revisa el campo señalado antes de calcular.")
        return not errores

    def limpiar(self) -> None:
        """Retira los errores visitados al vaciar el ejercicio."""
        self.revisados.clear()
        self._mostrar({})

    def _mostrar(self, errores: dict) -> None:
        activo = self.vista.criterio.value
        claves = (*CAMPOS, "criterio") if activo != "residuo" else tuple(CAMPOS)
        for tipo, campo in self.vista.parametros_criterio.items():
            if tipo != activo:
                self._mostrar_campo(campo, "")
        for clave in claves:
            texto = errores.get(clave, "") if clave in self.revisados else ""
            self._mostrar_campo(self._campo(clave), texto)

    def _mostrar_campo(self, campo, texto: str) -> None:
        mensaje = self.mensajes[campo]
        mensaje.set_text(texto)
        campo.error = texto or None
        if texto:
            # Quasar da prioridad a error-message sobre la ranura con el ID accesible.
            campo.props(f"aria-invalid=true aria-describedby={mensaje.html_id}", remove="error-message")
        else:
            campo.props("aria-invalid=false", remove="aria-describedby")

    def _campo(self, clave: str):
        if clave == "criterio":
            return self.vista.parametros_criterio[self.vista.criterio.value]
        return getattr(self.vista, CAMPOS[clave])
