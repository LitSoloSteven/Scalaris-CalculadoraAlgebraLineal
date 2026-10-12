"""Elementos de navegación, escenas y composición de la barra contextual."""
from unittest.mock import patch

from src.frontend.componentes.icons import icon_svg
from src.frontend.componentes.app_shell import create_app_shell
from src.frontend.componentes.navbar import create_navbar
from src.frontend.navigation import (
    HUB_ROUTE, VISUALIZER_SCENES, NavItem, default_item_key, nav_item_href, nav_items,
)
from src.frontend.vistas.geometria.vista_geometria import ESCENAS_VALIDAS


def test_escenas_coinciden_con_vista_geometrica():
    """El registro mantiene exactamente las escenas aceptadas por la vista."""
    claves_escenas = tuple(elemento[0] for elemento in VISUALIZER_SCENES)
    assert claves_escenas == ESCENAS_VALIDAS, (
        f"Desfase en escenas: registro={claves_escenas}, vista={ESCENAS_VALIDAS}"
    )


def test_elementos_por_pilar_en_orden():
    """Cada pilar ofrece sus herramientas en el orden previsto."""
    elementos_algebra = nav_items("algebra")
    assert [elemento.key for elemento in elementos_algebra] == ["sistemas", "vectores", "matrices", "inversa"]
    elementos_visualizador = nav_items("visualizador")
    assert [elemento.key for elemento in elementos_visualizador] == ["vis:rectas-planos", "vis:vectores", "vis:combinacion"]
    elementos_utilidades = nav_items("utilidades")
    assert [elemento.key for elemento in elementos_utilidades] == ["bases", "romanos"]
    assert nav_items("desconocido") == ()


def test_claves_unicas_entre_pilares():
    """Los nueve elementos tienen claves distintas entre todos los pilares."""
    claves = []
    for pilar in ("algebra", "visualizador", "utilidades"):
        for elemento in nav_items(pilar):
            claves.append(elemento.key)
    assert len(claves) == 9
    assert len(set(claves)) == 9


def test_enlaces_validos_y_etiquetas_completas():
    """Cada elemento contiene etiquetas descriptivas y una ruta absoluta."""
    for pilar in ("algebra", "visualizador", "utilidades"):
        for elemento in nav_items(pilar):
            assert isinstance(elemento, NavItem)
            assert elemento.short_label.strip() != "", f"Etiqueta breve vacía en {elemento.key}"
            assert elemento.label.strip() != "", f"Etiqueta vacía en {elemento.key}"
            assert elemento.descriptor.strip() != "", f"Descriptor vacío en {elemento.key}"
            enlace = nav_item_href(elemento)
            assert enlace.startswith("/"), f"Enlace inválido para {elemento.key}: {enlace}"


def test_clave_predeterminada_por_ruta():
    """Las rutas conocidas tienen clave; las inexistentes carecen de ella."""
    assert default_item_key("/algebra-lineal/sistemas") == "sistemas"
    assert default_item_key("/algebra-lineal/vectores") == "vectores"
    assert default_item_key("/algebra-lineal/matrices") == "matrices"
    assert default_item_key("/algebra-lineal/inversa") == "inversa"
    assert default_item_key("/utilidades/bases") == "bases"
    assert default_item_key("/utilidades/romanos") == "romanos"
    assert default_item_key("/visualizador") == "vis:rectas-planos"
    assert default_item_key("/ruta/inexistente") is None
    assert default_item_key("") is None


def test_iconos_generan_svg():
    """Cada icono registrado genera un documento SVG completo."""
    for pilar in ("algebra", "visualizador", "utilidades"):
        for elemento in nav_items(pilar):
            svg = icon_svg(elemento.icon)
            assert svg.startswith("<svg"), f"Icono inválido o vacío para {elemento.key}: '{elemento.icon}'"
            assert "</svg>" in svg


def test_contenedor_omite_barra_en_hub():
    """El Hub omite la barra y una herramienta la crea con su ruta activa."""
    with patch("src.frontend.componentes.app_shell.create_navbar") as barra_simulada:
        create_app_shell(active_route=HUB_ROUTE)
        barra_simulada.assert_not_called()
        create_app_shell(active_route="/algebra-lineal/sistemas", active_key="sistemas")
        barra_simulada.assert_called_once_with(None, active_route="/algebra-lineal/sistemas", active_key="sistemas")


def test_barra_con_rutas_conocidas_y_desconocidas():
    """La barra acepta claves explícitas, inferidas y una ruta desconocida."""
    create_navbar(active_route="/algebra-lineal/sistemas")
    create_navbar(active_route="/visualizador", active_key="vis:vectores")
    create_navbar(active_route="/ruta-desconocida")
