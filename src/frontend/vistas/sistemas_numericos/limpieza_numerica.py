"""Retiro de capturas, mensajes y procedimientos en las herramientas numéricas."""
from nicegui import ui
from src.frontend.controladores.limpieza_captura import (
    campos_vacios, vaciar_campos, retirar_estado_calculado,
)
from src.frontend.textos import LIMPIEZA_ESTADO_BASES, LIMPIEZA_ESTADO_ROMANOS


class MixinLimpiezaBases:
    """Retira toda presentación calculada por el conversor de bases."""

    def esta_completamente_vacio(self) -> bool:
        """Consulta el valor de entrada independientemente de su longitud."""
        return campos_vacios([self.entrada_valor])

    def limpiar_todo(self) -> None:
        """Cancela la espera y vacía entrada, resultados, bits, errores y pasos."""
        tarea = self.tarea_espera
        if tarea is not None and not tarea.done():
            tarea.cancel()
        self.tarea_espera = None
        self.entrada_valor.set_value('')
        self.etiqueta_error.set_text('')
        self._limpiar_resultados()
        self.resultados.update({base: '' for base in self.resultados})
        self.resultados_completos = {}
        self.contenedor_pasos.clear()
        self._publicar_estado(LIMPIEZA_ESTADO_BASES)
        retirar_estado_calculado(self)


class MixinLimpiezaRomanos:
    """Retira operandos, validación y procedimiento de la calculadora romana."""

    def esta_completamente_vacio(self) -> bool:
        """Consulta ambos operandos sin interpretarlos como números."""
        return campos_vacios([self.entrada_a, self.entrada_b])

    def limpiar_todo(self) -> None:
        """Vacía operandos y errores y vuelve a la orientación inicial."""
        vaciar_campos([self.entrada_a, self.entrada_b])
        self.etiqueta_error.set_text('')
        self.ultimo_error = None
        self._orientar_error_operandos()
        self.contenedor_sugerencias.clear()
        self.contenedor_resultado.clear()
        with self.contenedor_resultado:
            ui.label(LIMPIEZA_ESTADO_ROMANOS).props('role="status"')
        retirar_estado_calculado(self)
