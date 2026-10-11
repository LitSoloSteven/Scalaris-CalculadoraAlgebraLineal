"""Integración del visualizador en el registro de navegación."""
from src.frontend.navigation import (
    nav_groups,
    route_of,
    breadcrumb,
    tool_by_id,
    visible_tools,
    TOOLS,
    NAV_FLAT_ORDER,
)
from src.frontend.vistas.hub._recent import normalize_recent


def test_visualizador_presente_en_grupos_navegacion():
    """El visualizador aparece entre los grupos de navegación."""
    all_tool_ids = set()
    for pillar, tools in nav_groups():
        for tool in tools:
            all_tool_ids.add(tool.id)
    assert "visualizador" in all_tool_ids


def test_ruta_visualizador():
    """El registro devuelve la ruta del visualizador."""
    assert route_of("visualizador") == "/visualizador"


def test_visualizador_breadcrumb():
    """La miga del visualizador conserva su nombre y área."""
    bc = breadcrumb("/visualizador")
    assert len(bc) == 2
    assert bc[0][0] == "Visualizador geométrico"  # pillar name
    assert bc[1][0] == "Rectas, planos y vectores"  # tool name
    assert bc[1][1] == "/visualizador"


def test_historial_reciente_admite_visualizador():
    """El normalizador acepta el identificador del visualizador."""
    result = normalize_recent(["visualizador", "sistemas", "bases"])
    tool_ids = [t.id for t in result]
    assert "visualizador" in tool_ids


def test_registro_conserva_rutas_unicas():
    """Las rutas del registro no se repiten."""
    routes = [t.route for t in TOOLS]
    assert len(routes) == len(set(routes))


def test_registro_conserva_identificadores_unicos():
    """Los identificadores del registro no se repiten."""
    ids = [t.id for t in TOOLS]
    assert len(ids) == len(set(ids))


def test_orden_navegacion_incluye_visualizador():
    """El orden de navegación incluye el visualizador."""
    assert "visualizador" in NAV_FLAT_ORDER


def test_visualizador_habilitado():
    """La herramienta de visualización está habilitada."""
    vis = tool_by_id("visualizador")
    assert vis.enabled
