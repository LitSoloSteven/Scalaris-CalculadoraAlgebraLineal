"""Envoltura estructural de aplicación para vistas de Scalaris."""
from __future__ import annotations

from typing import Any, Callable
from src.frontend.navigation import HUB_ROUTE
from src.frontend.componentes.navbar import create_navbar


def create_app_shell(active_ui: Any = None, active_route: str = "/", active_key: str | None = None,
                     al_alternar_ia: Callable | None = None) -> None:
    """Genera la cabecera de aplicación contextual cuando la ruta no es el Hub."""
    if active_route != HUB_ROUTE:
        create_navbar(active_ui, active_route=active_route, active_key=active_key, al_alternar_ia=al_alternar_ia)
