"""Presentación del paso automático o manual de un panel exploratorio."""
from src.frontend.controladores.exploracion_raices import sugerir_paso


class PasoExploracion:
    """Comparte la captura del paso entre paneles con rango y estado propios."""

    def restablecer_paso(self) -> None:
        """Recupera el paso automático e invalida los candidatos anteriores."""
        self._paso_automatico = True
        self.actualizar_paso()
        self.invalidar()

    def actualizar_paso(self) -> None:
        """Muestra el paso efectivo o el motivo por el que no puede representarse."""
        if not self._paso_automatico:
            self.etiqueta_paso.set_text("Paso manual.")
            return
        try:
            valor = sugerir_paso({"x_min": self.minimo.value, "x_max": self.maximo.value})
            texto = f"Paso automático efectivo · {valor:.9g}"
        except ValueError as error:
            texto = str(error)
        self.etiqueta_paso.set_text(texto)

    def _capturar_paso(self):
        if not self._paso_automatico:
            return self.paso.value
        try:
            return sugerir_paso({"x_min": self.minimo.value, "x_max": self.maximo.value})
        except ValueError:
            return None
