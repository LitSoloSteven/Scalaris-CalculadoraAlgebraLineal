"""Montaje del enlace anterior de Regla falsa."""
from src.frontend.controladores.raices.metodos_cerrados.adaptadores import REGLA_FALSA
from src.frontend.vistas.metodos_cerrados.vista_metodos_cerrados import VistaMetodosCerrados, montar_pagina


class VistaReglaFalsa(VistaMetodosCerrados):
    """Conserva el acceso al procedimiento para integraciones del enlace anterior."""

    def __init__(self):
        super().__init__(REGLA_FALSA)

    @property
    def reproductor_pasos(self):
        """Devuelve el reproductor del procedimiento visible."""
        return self.salida.reproductor

    @property
    def detalle_procedimiento(self):
        """Expone la traza compartida mientras hay un procedimiento vigente."""
        return self.salida if self.reproductor_pasos is not None else None


def construir_pagina_regla_falsa() -> VistaReglaFalsa:
    """Monta Métodos cerrados con Regla falsa y devuelve la instancia del cliente."""
    vista = VistaReglaFalsa()
    montar_pagina(vista)
    return vista
