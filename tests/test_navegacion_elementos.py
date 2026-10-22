"""Elementos de navegación, escenas y composición de la barra contextual."""
from unittest.mock import patch

from src.frontend.componentes.iconos import icono_svg
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.barra_navegacion import crear_barra_navegacion
from src.frontend.navegacion import (
    RUTA_INICIO, ESCENAS_VISUALIZADOR, ElementoNavegacion, predeterminado_elemento_clave, enlace_elemento_navegacion, elementos_navegacion,
)
from src.frontend.vistas.geometria.vista_geometria import ESCENAS_VALIDAS


def test_escenas_coinciden_con_vista_geometrica():
    """El registro mantiene exactamente las escenas aceptadas por la vista."""
    claves_escenas = tuple(elemento[0] for elemento in ESCENAS_VISUALIZADOR)
    assert claves_escenas == ESCENAS_VALIDAS, (
        f"Desfase en escenas: registro={claves_escenas}, vista={ESCENAS_VALIDAS}"
    )


def test_elementos_por_pilar_en_orden():
    """Cada pilar ofrece sus herramientas en el orden previsto."""
    elementos_algebra = elementos_navegacion("algebra")
    assert [elemento.clave for elemento in elementos_algebra] == ["sistemas", "vectores", "matrices", "inversa", "determinantes"]
    elementos_visualizador = elementos_navegacion("visualizador")
    assert [elemento.clave for elemento in elementos_visualizador] == ["vis:rectas-planos", "vis:vectores", "vis:combinacion"]
    elementos_utilidades = elementos_navegacion("utilidades")
    assert [elemento.clave for elemento in elementos_utilidades] == ["bases", "romanos"]
    assert elementos_navegacion("desconocido") == ()


def test_claves_unicas_entre_pilares():
    """Los diez elementos tienen claves distintas entre todos los pilares."""
    claves = []
    for pilar in ("algebra", "visualizador", "utilidades"):
        for elemento in elementos_navegacion(pilar):
            claves.append(elemento.clave)
    assert len(claves) == 10
    assert len(set(claves)) == 10


def test_enlaces_validos_y_etiquetas_completas():
    """Cada elemento contiene etiquetas descriptivas y una ruta absoluta."""
    for pilar in ("algebra", "visualizador", "utilidades"):
        for elemento in elementos_navegacion(pilar):
            assert isinstance(elemento, ElementoNavegacion)
            assert elemento.etiqueta_corta.strip() != "", f"Etiqueta breve vacía en {elemento.clave}"
            assert elemento.etiqueta.strip() != "", f"Etiqueta vacía en {elemento.clave}"
            assert elemento.descriptor.strip() != "", f"Descriptor vacío en {elemento.clave}"
            enlace = enlace_elemento_navegacion(elemento)
            assert enlace.startswith("/"), f"Enlace inválido para {elemento.clave}: {enlace}"


def test_clave_predeterminada_por_ruta():
    """Las rutas conocidas tienen clave; las inexistentes carecen de ella."""
    assert predeterminado_elemento_clave("/algebra-lineal/sistemas") == "sistemas"
    assert predeterminado_elemento_clave("/algebra-lineal/vectores") == "vectores"
    assert predeterminado_elemento_clave("/algebra-lineal/matrices") == "matrices"
    assert predeterminado_elemento_clave("/algebra-lineal/inversa") == "inversa"
    assert predeterminado_elemento_clave("/algebra-lineal/determinantes") == "determinantes"
    assert predeterminado_elemento_clave("/algebra-lineal/matrices?operacion=determinante") == "determinantes"
    assert predeterminado_elemento_clave("/utilidades/bases") == "bases"
    assert predeterminado_elemento_clave("/utilidades/romanos") == "romanos"
    assert predeterminado_elemento_clave("/visualizador") == "vis:rectas-planos"
    assert predeterminado_elemento_clave("/ruta/inexistente") is None
    assert predeterminado_elemento_clave("") is None


def test_iconos_generan_svg():
    """Cada icono registrado genera un documento SVG completo."""
    for pilar in ("algebra", "visualizador", "utilidades"):
        for elemento in elementos_navegacion(pilar):
            svg = icono_svg(elemento.icono)
            assert svg.startswith("<svg"), f"Icono inválido o vacío para {elemento.clave}: '{elemento.icono}'"
            assert "</svg>" in svg


def test_contenedor_omite_barra_en_inicio():
    """El inicio omite la barra y una herramienta la crea con su ruta activa."""
    with patch("src.frontend.componentes.estructura_aplicacion.crear_barra_navegacion") as barra_simulada:
        crear_estructura_aplicacion(ruta_activa=RUTA_INICIO)
        barra_simulada.assert_not_called()
        crear_estructura_aplicacion(ruta_activa="/algebra-lineal/sistemas", clave_activa="sistemas")
        barra_simulada.assert_called_once_with(None, ruta_activa="/algebra-lineal/sistemas", clave_activa="sistemas")


def test_barra_con_rutas_conocidas_y_desconocidas(monkeypatch):
    """La barra acepta claves explícitas, inferidas y una ruta desconocida."""
    from nicegui import Client, core, ui
    monkeypatch.setattr(core, "script_mode", False)
    cliente = Client(ui.page("/prueba_barra_contextual"))
    with cliente:
        crear_barra_navegacion(ruta_activa="/algebra-lineal/sistemas")
        crear_barra_navegacion(ruta_activa="/visualizador", clave_activa="vis:vectores")
        crear_barra_navegacion(ruta_activa="/ruta-desconocida")
    cliente.delete()
