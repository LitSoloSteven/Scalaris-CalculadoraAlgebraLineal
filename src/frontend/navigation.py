"""Registro central de taxonomía, navegación y redirecciones de Scalaris.

Módulo puro de Python (solo stdlib) que actúa como única fuente de verdad
para la jerarquía de pilares, herramientas, metadatos de rutas y redirecciones legacy.
Los modelos viven en `_nav_modelos` y los datos en `_nav_catalogo`; aquí se
reexportan para conservar la API pública.
"""
from __future__ import annotations

import urllib.parse

from src.frontend._nav_catalogo import (
    ALIAS_PILARES,
    NAV_FLAT_ORDER,
    ORDEN_ITEMS_POR_PILAR,
    PILLARS,
    SHORT_LABELS,
    TOOLS,
    VISUALIZER_SCENES,
)
from src.frontend._nav_modelos import LegacyRedirect, NavItem, Pillar, Tool

__all__ = [
    "HUB_ENABLED",
    "HUB_PAGE_TITLE",
    "HUB_ROUTE",
    "LegacyRedirect",
    "NAV_FLAT_ORDER",
    "NavItem",
    "PILLARS",
    "Pillar",
    "TOOLS",
    "Tool",
    "VISUALIZER_SCENES",
    "breadcrumb",
    "default_item_key",
    "legacy_redirects",
    "nav_groups",
    "nav_item_href",
    "nav_items",
    "pillar_for_route",
    "pillar_of",
    "redirect_location",
    "route_of",
    "tool_by_id",
    "tool_by_route",
    "visible_tools",
]

HUB_ENABLED: bool = True
HUB_ROUTE: str = "/"
HUB_PAGE_TITLE: str = "Inicio | Scalaris"

_SHORT_LABELS: dict[str, str] = SHORT_LABELS
_PILLARS_BY_ID: dict[str, Pillar] = {p.id: p for p in PILLARS}
_TOOLS_BY_ID: dict[str, Tool] = {t.id: t for t in TOOLS}


def tool_by_id(tool_id: str) -> Tool:
    """Devuelve la Tool correspondiente al id dado.

    Raises:
        KeyError: si el id no existe en el registro.
    """
    if tool_id not in _TOOLS_BY_ID:
        raise KeyError(f"Herramienta no encontrada en el registro: '{tool_id}'")
    return _TOOLS_BY_ID[tool_id]


def route_of(tool_id: str) -> str:
    """Devuelve la ruta canónica asociada a la herramienta."""
    return tool_by_id(tool_id).route


def tool_by_route(path: str) -> Tool | None:
    """Busca y devuelve la Tool activa asociada a la ruta dada.

    Ignora cadenas de consulta (?query) y barras finales.
    Devuelve None si no coincide con ninguna ruta actual.
    """
    clean_path = path.split("?")[0].rstrip("/")
    if not clean_path:
        clean_path = "/"
    for tool in TOOLS:
        if tool.route.rstrip("/") == clean_path:
            return tool
    return None


def pillar_of(tool_id: str) -> Pillar:
    """Devuelve el Pillar al que pertenece la herramienta."""
    tool = tool_by_id(tool_id)
    return _PILLARS_BY_ID[tool.pillar_id]


def visible_tools(pillar_id: str | None = None) -> tuple[Tool, ...]:
    """Devuelve las herramientas habilitadas (enabled=True) en orden de taxonomía."""
    if pillar_id is None:
        return tuple(t for t in TOOLS if t.enabled)
    return tuple(t for t in TOOLS if t.enabled and t.pillar_id == pillar_id)


def nav_groups() -> tuple[tuple[Pillar, tuple[Tool, ...]], ...]:
    """Devuelve en el orden de PILLARS cada pilar con al menos una herramienta."""
    groups = []
    for p in PILLARS:
        tools = visible_tools(p.id)
        if tools:
            groups.append((p, tools))
    return tuple(groups)


def pillar_for_route(path: str) -> Pillar | None:
    """Encuentra el pilar al que pertenece una ruta base."""
    clean_path = path.split("?")[0].rstrip("/")
    if not clean_path:
        clean_path = "/"
    for p in PILLARS:
        if clean_path == p.prefix or clean_path.startswith(p.prefix + "/"):
            return p
    return None


def breadcrumb(route: str) -> tuple[tuple[str, str | None], ...]:
    """Genera la estructura de migas de pan para una ruta dada.

    Ejemplo: (("Álgebra lineal", None), ("Matriz inversa", "/algebra-lineal/inversa"))
    Devuelve tupla vacía si la ruta no existe en el registro.
    """
    tool = tool_by_route(route)
    if tool is None:
        return ()
    pillar = _PILLARS_BY_ID[tool.pillar_id]
    return ((pillar.name, None), (tool.name, tool.route))


def legacy_redirects() -> tuple[LegacyRedirect, ...]:
    """Devuelve la tupla de redirecciones legacy activas según el estado de HUB_ENABLED."""
    # Lectura dinámica en tiempo de llamada para permitir monkeypatching en tests
    import src.frontend.navigation as nav_mod
    hub_active = getattr(nav_mod, "HUB_ENABLED", False)

    redirects: list[LegacyRedirect] = []

    if not hub_active:
        redirects.append(LegacyRedirect(path="/", target_route="/algebra-lineal/sistemas", permanent=False))
        redirects.append(LegacyRedirect(path="/ia", target_route="/algebra-lineal/sistemas", permanent=False))
    else:
        redirects.append(LegacyRedirect(path="/ia", target_route="/", fixed_query=(("glosa", "1"),), permanent=True))

    redirects.extend([
        LegacyRedirect(path="/sistemas-lineales", target_route="/algebra-lineal/sistemas"),
        LegacyRedirect(path="/gauss", target_route="/algebra-lineal/sistemas", fixed_query=(("method", "gauss"),)),
        LegacyRedirect(path="/gauss-jordan", target_route="/algebra-lineal/sistemas", fixed_query=(("method", "gauss-jordan"),)),
        LegacyRedirect(path="/operaciones-matrices", target_route="/algebra-lineal/matrices"),
        LegacyRedirect(path="/matriz-inversa", target_route="/algebra-lineal/inversa"),
        LegacyRedirect(path="/vectores", target_route="/algebra-lineal/vectores"),
        LegacyRedirect(path="/conversor", target_route="/utilidades/bases"),
        LegacyRedirect(path="/romanos", target_route="/utilidades/romanos"),
    ])

    return tuple(redirects)


def redirect_location(redirect: LegacyRedirect, incoming_items: list[tuple[str, str]]) -> str:
    """Calcula la URL de destino final para una redirección legacy.

    Reglas de precedencia:
      1. Empieza por los pares de la query fija.
      2. Añade los pares entrantes cuya clave no esté entre las fijas.
      3. Conserva duplicados y valores vacíos.
      4. Codifica con urlencode; si no hay pares no añade '?'.
    """
    fixed_pairs: list[tuple[str, str]] = list(redirect.fixed_query)
    fixed_keys = {k for k, _ in fixed_pairs}

    for k, v in incoming_items:
        if k not in fixed_keys:
            fixed_pairs.append((k, v))

    if fixed_pairs:
        encoded_query = urllib.parse.urlencode(fixed_pairs)
        return f"{redirect.target_route}?{encoded_query}"
    return redirect.target_route


def _item_de_herramienta(tool: Tool) -> NavItem:
    """Convierte una herramienta en su item de navegación contextual."""
    return NavItem(
        key=tool.id,
        label=tool.name,
        short_label=_SHORT_LABELS[tool.id],
        descriptor=tool.descriptor,
        icon=tool.icon,
        route=tool.route,
        query=(),
        tool_id=tool.id,
    )


def _items_visualizador() -> tuple[NavItem, ...]:
    """Construye un item por cada escena del visualizador geométrico."""
    ruta = tool_by_id("visualizador").route
    return tuple(
        NavItem(
            key=f"vis:{escena}",
            label=label,
            short_label=short_label,
            descriptor=descriptor,
            icon=icon,
            route=ruta,
            query=(("escena", escena),),
            tool_id="visualizador",
        )
        for escena, label, short_label, descriptor, icon in VISUALIZER_SCENES
    )


def nav_items(pillar_id: str) -> tuple[NavItem, ...]:
    """Devuelve los items de navegacion contextual asociados a un pilar."""
    pilar = ALIAS_PILARES.get(pillar_id, pillar_id)
    if pilar == "visualizador":
        return _items_visualizador()
    orden = ORDEN_ITEMS_POR_PILAR.get(pilar)
    if orden is None:
        return ()
    return tuple(_item_de_herramienta(tool_by_id(tool_id)) for tool_id in orden)


def nav_item_href(item: NavItem) -> str:
    """Calcula la URL de destino del item con query string codificada si existe."""
    if item.query:
        return f"{item.route}?{urllib.parse.urlencode(item.query)}"
    return item.route


def default_item_key(route: str) -> str | None:
    """Obtiene la clave del item de navegacion predeterminado para una ruta."""
    tool = tool_by_route(route)
    if tool is None:
        return None
    if tool.id == "visualizador":
        return "vis:rectas-planos"
    return tool.id