"""Taxonomía, rutas y referencias del registro de navegación."""
from src.frontend.componentes.icons import icon_svg
from src.frontend.navigation import (
    NAV_FLAT_ORDER, PILLARS, TOOLS, breadcrumb, legacy_redirects, pillar_of,
    tool_by_id, tool_by_route, visible_tools,
)


def test_identificadores_y_rutas_unicos():
    """Pilares, herramientas y redirecciones tienen identificadores únicos."""
    identificadores_pilares = [pilar.id for pilar in PILLARS]
    assert len(identificadores_pilares) == len(set(identificadores_pilares)), "Identificadores de pilares duplicados"
    identificadores_herramientas = [herramienta.id for herramienta in TOOLS]
    assert len(identificadores_herramientas) == len(set(identificadores_herramientas)), "Identificadores de herramientas duplicados"
    rutas_herramientas = [herramienta.route for herramienta in TOOLS]
    assert len(rutas_herramientas) == len(set(rutas_herramientas)), "Rutas canónicas duplicadas"
    rutas_anteriores = [redireccion.path for redireccion in legacy_redirects()]
    assert len(rutas_anteriores) == len(set(rutas_anteriores)), "Rutas de redirección duplicadas"


def test_formato_de_rutas():
    """Las rutas son absolutas y carecen de barra final salvo la raíz."""
    for herramienta in TOOLS:
        assert herramienta.route.startswith("/"), f"La ruta {herramienta.route} debe empezar con '/'"
        if herramienta.route != "/":
            assert not herramienta.route.endswith("/"), f"La ruta {herramienta.route} no debe terminar con '/'"
    for redireccion in legacy_redirects():
        assert redireccion.path.startswith("/"), f"La ruta anterior {redireccion.path} debe empezar con '/'"
        if redireccion.path != "/":
            assert not redireccion.path.endswith("/"), f"La ruta anterior {redireccion.path} no debe terminar con '/'"
        assert redireccion.target_route.startswith("/"), f"El destino {redireccion.target_route} debe empezar con '/'"
        if redireccion.target_route != "/":
            assert not redireccion.target_route.endswith("/"), f"El destino {redireccion.target_route} no debe terminar con '/'"


def test_redirecciones_sin_colision_con_rutas_actuales():
    """Las rutas anteriores no sustituyen ninguna ruta canónica actual."""
    rutas_actuales = {herramienta.route for herramienta in TOOLS}
    rutas_anteriores = {redireccion.path for redireccion in legacy_redirects()}
    coincidencias = rutas_actuales.intersection(rutas_anteriores)
    assert not coincidencias, f"Colisión entre rutas canónicas y anteriores: {coincidencias}"


def test_pilares_referenciados_existen():
    """Cada herramienta referencia un pilar registrado y resoluble."""
    pilares_por_identificador = {pilar.id: pilar for pilar in PILLARS}
    for herramienta in TOOLS:
        assert herramienta.pillar_id in pilares_por_identificador, f"La herramienta '{herramienta.id}' referencia un pilar inexistente '{herramienta.pillar_id}'"
        pilar_resuelto = pillar_of(herramienta.id)
        assert pilar_resuelto.id == herramienta.pillar_id


def test_herramientas_habilitadas_con_iconos():
    """Cada herramienta visible tiene un icono SVG no vacío."""
    for herramienta in visible_tools():
        svg = icon_svg(herramienta.icon)
        assert isinstance(svg, str) and svg.strip().startswith("<svg"), (
            f"La herramienta '{herramienta.id}' con icono '{herramienta.icon}' no genera un SVG válido"
        )


def test_titulos_con_sufijo_oficial():
    """Los títulos de todas las páginas incluyen la marca oficial."""
    for herramienta in TOOLS:
        assert herramienta.page_title.endswith("| Scalaris"), (
            f"El título de '{herramienta.id}' ('{herramienta.page_title}') carece de '| Scalaris'"
        )


def test_busqueda_por_ruta_normaliza_consulta_y_barra():
    """La búsqueda ignora consultas y barras finales, y rechaza rutas ajenas."""
    sistemas = tool_by_route("/algebra-lineal/sistemas/?method=gauss-jordan&x=1")
    assert sistemas is not None and sistemas.id == "sistemas"
    inversa = tool_by_route("/algebra-lineal/inversa/")
    assert inversa is not None and inversa.id == "inversa"
    assert tool_by_route("/ruta-completamente-inexistente") is None
    assert tool_by_route("/algebra-lineal/inexistente") is None


def test_visualizador_habilitado_y_visible():
    """El visualizador geométrico está habilitado y aparece entre herramientas."""
    visualizador = tool_by_id("visualizador")
    assert visualizador.enabled, "El visualizador debe estar habilitado"
    identificadores_visibles = {herramienta.id for herramienta in visible_tools()}
    assert "visualizador" in identificadores_visibles, "El visualizador debe figurar entre herramientas visibles"


def test_orden_cubre_todas_las_herramientas_visibles():
    """El orden plano contiene exactamente las herramientas habilitadas."""
    identificadores_visibles = {herramienta.id for herramienta in visible_tools()}
    assert set(NAV_FLAT_ORDER) == identificadores_visibles, (
        f"El orden {set(NAV_FLAT_ORDER)} difiere de las herramientas visibles {identificadores_visibles}"
    )


def test_migas_de_pan_por_ruta():
    """Las rutas conocidas generan migas y las inexistentes devuelven vacío."""
    migas = breadcrumb("/algebra-lineal/inversa")
    assert migas == (("Álgebra lineal", None), ("Matriz inversa", "/algebra-lineal/inversa"))
    migas_consulta = breadcrumb("/algebra-lineal/sistemas?method=gauss")
    assert migas_consulta == (("Álgebra lineal", None), ("Sistemas de ecuaciones", "/algebra-lineal/sistemas"))
    migas_inexistentes = breadcrumb("/ruta/falsa/123")
    assert migas_inexistentes == ()
