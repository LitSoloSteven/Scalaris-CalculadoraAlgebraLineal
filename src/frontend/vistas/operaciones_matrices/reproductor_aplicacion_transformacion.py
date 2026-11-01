"""Navegación de aplicación que evita repetir la entrada visual del mismo paso."""
from src.frontend.componentes.reproductor_pasos import ReproductorPasos


class ReproductorAplicacion(ReproductorPasos):
    """Conserva los controles compartidos y omite selecciones consecutivas idénticas."""

    def construir(self) -> None:
        """Restablece el paso presentado al reconstruir los controles."""
        self._indice_visible = None
        super().construir()

    def ir_a(self, indice: int, *, autoreproduccion: bool = False) -> None:
        """Navega una sola vez por destino, sin reiniciar animaciones del paso vigente."""
        if not self.pasos:
            return
        destino = max(0, min(indice, len(self.pasos) - 1))
        if getattr(self, "_indice_visible", None) == destino:
            return
        super().ir_a(destino, autoreproduccion=autoreproduccion)
        self._indice_visible = self.indice_actual
