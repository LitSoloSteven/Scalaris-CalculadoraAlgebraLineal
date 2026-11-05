"""Selector angular y restauración compatible de preferencias matemáticas."""
from nicegui import ui

from src.backend.resolutores.raices.unidades_angulares import UNIDADES_ANGULARES, UNIDAD_ANGULAR_DEFECTO


def construir_selector_unidad(vista) -> None:
    """Monta la unidad trigonométrica etiquetada y una guía sin conversiones en la vista."""
    vista.unidad_angular = ui.select({unidad: unidad.capitalize() for unidad in UNIDADES_ANGULARES},
                                    value=UNIDAD_ANGULAR_DEFECTO, label="Unidad trigonométrica").classes("w-full matriz-entrada")
    vista.unidad_angular.set_visibility(False)


def restaurar_unidad(vista, captura: dict) -> None:
    """Restaura unidades explícitas o radianes de capturas completas antiguas; conserva cargas parciales."""
    if "unidad_angular" in captura:
        vista.unidad_angular.set_value(captura["unidad_angular"])
    elif "expresion" in captura and ("criterio" in captura or "decimales" in captura):
        vista.unidad_angular.set_value(UNIDAD_ANGULAR_DEFECTO)
