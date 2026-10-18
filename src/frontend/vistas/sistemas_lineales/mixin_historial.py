"""Tarjetas y restauracion del historial de sistemas lineales."""
from nicegui import ui
from src.frontend.vistas.mixin_sesion_matricial import MixinSesionMatricial


class MixinHistorialSistemasLineales(MixinSesionMatricial):
    """Maneja el registro, visualización y restauración del historial de sistemas resueltos."""

    def _restaurar_historial(self, datos: dict) -> None:
        """Restaura la captura de coeficientes y terminos del registro de sesion."""
        if self.pestanas_modo.value == 'Ecuaciones':
            self.pestanas_modo.set_value('Matriz')
        self.cuadricula.limpiar()
        self.cuadricula.cargar_datos(datos['matriz_a'], datos['vector_b'])
        self._al_cambiar_cuadricula()
        ui.notify('Matriz restaurada', type='positive')
