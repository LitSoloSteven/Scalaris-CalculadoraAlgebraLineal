"""Envoltura estructural de aplicación para vistas de Scalaris."""
from __future__ import annotations

from typing import Any, Callable
from src.frontend.navegacion import RUTA_INICIO
from src.frontend.componentes.barra_navegacion import crear_barra_navegacion


def crear_estructura_aplicacion(interfaz_activa: Any = None, ruta_activa: str = "/", clave_activa: str | None = None,
                     al_alternar_ia: Callable | None = None) -> None:
    """Genera la cabecera contextual de las herramientas fuera de la página de inicio."""
    if ruta_activa != RUTA_INICIO:
        opciones = {"ruta_activa": ruta_activa, "clave_activa": clave_activa}
        if al_alternar_ia is not None:
            opciones["al_alternar_ia"] = al_alternar_ia
        crear_barra_navegacion(interfaz_activa, **opciones)
