"""Paridad entre el directorio y la barra contextual para los quince destinos."""
from unittest.mock import Mock

from nicegui import Client, core, ui
import pytest

from src.frontend.componentes.barra_navegacion import crear_barra_navegacion
from src.frontend.componentes.iconos import icono_svg
from src.frontend.navegacion import enlace_elemento_navegacion
from src.frontend.navegacion.secciones_inicio import seccion_por_clave


_GRUPOS = (
    ("sistemas-lineales", "Sistemas lineales", ("sistemas", "leontief")),
    ("matrices", "Matrices", ("matrices", "inversa", "determinantes", "factorizacion_lu")),
    ("vectores-geometria", "Vectores y geometría",
     ("vectores", "transformaciones", "vis:rectas-planos", "vis:vectores", "vis:combinacion")),
    ("metodos-numericos", "Métodos numéricos", ("metodos_cerrados", "metodos_abiertos")),
    ("sistemas-numeracion", "Sistemas de numeración", ("bases", "romanos")),
)


def _enlaces(cliente):
    """Devuelve los enlaces en el orden que recibe el navegador."""
    return [elemento for elemento in cliente.elements.values() if "navegacion-elemento" in elemento.classes]


def _comprobar_titulo_e_icono(cliente, identificador, titulo):
    """Comprueba el rótulo del grupo, el símbolo y el nombre de la lista."""
    cabecera, = (elemento for elemento in cliente.elements.values() if "navegacion-seccion" in elemento.classes)
    assert [hijo.content for hijo in cabecera.descendants()] == [icono_svg(f"seccion-{identificador}"), titulo]
    lista, = (elemento for elemento in cliente.elements.values() if "navegacion-elementos" in elemento.classes)
    assert lista._props["aria-label"] == f"Herramientas de {titulo}"


def _svg_del_enlace(enlace):
    """Recupera el SVG que se monta dentro del enlace."""
    return next(hijo.content for hijo in enlace.descendants() if hijo.content.startswith("<svg"))


def _comprobar_enlaces(cliente, seccion, activo):
    """Comprueba destinos, símbolos y selección de la lista renderizada."""
    enlaces = _enlaces(cliente)
    assert [enlace._props["href"] for enlace in enlaces] == [enlace_elemento_navegacion(acceso) for acceso in seccion.accesos]
    assert [enlace._props["href"] for enlace in enlaces if enlace._props.get("aria-current") == "page"] == [
        enlace_elemento_navegacion(activo)
    ]
    assert [_svg_del_enlace(enlace) for enlace in enlaces] == [icono_svg(acceso.icono) for acceso in seccion.accesos]


@pytest.fixture
def cliente_contextual(monkeypatch):
    """Prepara una barra contextual y registra las acciones de conexión."""
    monkeypatch.setenv("SCALARIS_NAV", "1")
    monkeypatch.setattr(core, "script_mode", False)
    cliente = Client(ui.page("/prueba-barra-secciones"))
    enviar = Mock()
    monkeypatch.setattr(cliente, "run_javascript", enviar)
    try:
        yield cliente, enviar
    finally:
        cliente.delete()


@pytest.mark.parametrize("identificador,titulo,claves,clave", [
    (identificador, titulo, claves, clave)
    for identificador, titulo, claves in _GRUPOS for clave in claves
])
def test_cada_acceso_activa_su_seccion_del_directorio(cliente_contextual, identificador, titulo, claves, clave):
    """El grupo y su orden coinciden para herramientas y escenas, con un único activo."""
    cliente, enviar = cliente_contextual
    seccion = seccion_por_clave(clave)
    assert seccion.identificador == identificador
    assert tuple(acceso.clave for acceso in seccion.accesos) == claves
    activo = next(acceso for acceso in seccion.accesos if acceso.clave == clave)
    with cliente:
        crear_barra_navegacion(ruta_activa=activo.ruta, clave_activa=clave)

    _comprobar_titulo_e_icono(cliente, identificador, titulo)
    _comprobar_enlaces(cliente, seccion, activo)
    cliente.connect_handlers[0]()
    enviar.assert_any_call(f'window.scalaris?.recientes?.registrar?.("{clave}");')
    enviar.assert_any_call("window.scalaris?.navegacion?.centrarActivo?.();")


def test_vectores_y_su_escena_tienen_etiquetas_distintas(cliente_contextual):
    """La herramienta y la escena se distinguen visualmente y en su nombre accesible."""
    cliente, _ = cliente_contextual
    with cliente:
        crear_barra_navegacion(ruta_activa="/visualizador", clave_activa="vis:vectores")
    etiquetas = {enlace._props["href"]: enlace for enlace in _enlaces(cliente)}
    for destino, nombre in [("/algebra-lineal/vectores", "Vectores"),
                            ("/visualizador?escena=vectores", "Vectores del Visualizador")]:
        enlace = etiquetas[destino]
        assert enlace._props["aria-label"] == nombre
        assert any(hijo.content == nombre for hijo in enlace.descendants())


def test_seccion_ignora_claves_ausentes_o_ajenas():
    """Una clave ajena al directorio no inventa un grupo contextual."""
    for clave in (None, "", "no-registrada", "vis:desconocida"):
        assert seccion_por_clave(clave) is None
