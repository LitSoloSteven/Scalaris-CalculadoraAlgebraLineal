"""Vaciado de los campos de modelos matriciales sin modificar dimensiones."""
from src.frontend.controladores.limpieza_captura import (
    campos_vacios, vaciar_campos, retirar_estado_calculado,
)


class MixinLimpiezaModelos:
    """Comparte presencia y vaciado sobre los campos declarados por cada modelo."""

    def esta_completamente_vacio(self) -> bool:
        """Comprueba coeficientes y campos auxiliares del modelo activo."""
        return campos_vacios(self._campos_captura())

    def limpiar_todo(self) -> None:
        """Vacía coeficientes y nombres y restablece el resultado y su contexto."""
        vaciar_campos(self._campos_captura())
        self._restablecer_resultados()
        retirar_estado_calculado(self)
