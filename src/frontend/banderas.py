"""Configuración de navegación, panel lateral y sugerencias mediante variables de entorno."""
from __future__ import annotations

import os

_VALORES_VERDADEROS: frozenset[str] = frozenset({"1", "true", "on", "yes"})
_VALORES_FALSOS: frozenset[str] = frozenset({"0", "false", "off", "no"})


def _interpretar_booleano_entorno(nombre_variable: str, predeterminado: bool) -> bool:
    """Interpreta 1/0, true/false, on/off y yes/no sin distinguir mayúsculas.
    Devuelve predeterminado cuando la variable falta o su contenido es inválido."""
    valor = os.getenv(nombre_variable)
    if valor is None:
        return predeterminado
    normalizado = valor.strip().lower()
    if normalizado in _VALORES_VERDADEROS:
        return True
    if normalizado in _VALORES_FALSOS:
        return False
    return predeterminado


def navegacion_actualizada() -> bool:
    """Indica si la barra de navegación y taxonomía v2 están activas (por defecto: True)."""
    return _interpretar_booleano_entorno("SCALARIS_NAV", predeterminado=True)


def panel_lateral_habilitado() -> bool:
    """Indica si el panel lateral de Glosa está habilitado (por defecto: True)."""
    return _interpretar_booleano_entorno("SCALARIS_DOCK", predeterminado=True)


def proactivo_habilitado() -> bool:
    """Indica si el modo proactivo de sugerencias está habilitado (por defecto: True)."""
    return _interpretar_booleano_entorno("SCALARIS_PROACTIVE", predeterminado=True)
