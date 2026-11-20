"""Portada y directorio de herramientas de Scalaris."""
import html

from nicegui import Client, ui

from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.iconos import icono_svg
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.selector_tema import renderizar_boton_tema
from src.frontend.controladores.inicio._modelo import acceso_destacado
from src.frontend.navegacion import ElementoNavegacion, RUTA_INICIO, enlace_elemento_navegacion
from src.frontend.navegacion.secciones_inicio import GrupoInicio, SeccionInicio, secciones_inicio
from .panel_ejemplo import renderizar_panel_ejemplo


def _texto(etiqueta: str, texto: str, clases: str = "") -> ui.html:
    return ui.html(html.escape(texto), tag=etiqueta).classes(clases)


def _simbolo(nombre: str) -> None:
    ui.html(icono_svg(nombre), tag="span").classes("inicio-simbolo").props('aria-hidden="true"')


def _flecha() -> None:
    _texto("span", "→", "inicio-flecha").props('aria-hidden="true"')


def _renderizar_cabecera() -> None:
    with ui.element("header").classes("inicio-cabecera"):
        with ui.element("div").classes("inicio-marca"):
            with ui.element("span").classes("inicio-logotipo marca-contenedor-logotipo"):
                ui.element("img").classes("marca-logotipo marca-logotipo-oscuro").props(
                    'src="/assets/LogoOscuro.png" alt="" width=40 height=40'
                )
                ui.element("img").classes("marca-logotipo marca-logotipo-claro").props(
                    'src="/assets/LogoClaro.png" alt="" width=40 height=40'
                )
            _texto("span", "Scalaris")
            _texto("abbr", "UAM", "inicio-universidad").props('title="Universidad Americana"')
        with ui.element("div").classes("inicio-tema"):
            renderizar_boton_tema(mostrar_nombre=True)


def _renderizar_presentacion() -> None:
    enlace = acceso_destacado().ruta
    with ui.element("section").classes("inicio-presentacion").props('aria-labelledby="inicio-titulo"'):
        with ui.element("div"):
            ui.html("Álgebra lineal,<br><em>paso a paso.</em>", tag="h1").classes("inicio-titulo").props(
                'id="inicio-titulo"'
            )
            _texto("p", "Resuelve ejercicios y visualiza qué ocurre en cada paso.", "inicio-descripcion")
            with ui.element("a").classes("inicio-destacado").props(f'href="{enlace}"'):
                _texto("span", "Resolver un sistema")
                _flecha()
        renderizar_panel_ejemplo(enlace)


def _renderizar_acceso(acceso: ElementoNavegacion) -> None:
    enlace = enlace_elemento_navegacion(acceso)
    with ui.element("a").classes("inicio-enlace").props(
        f'href="{enlace}" data-clave="{acceso.clave}" data-gesto-inicio="{acceso.clave}"'
    ):
        _simbolo(acceso.icono)
        _texto("span", acceso.etiqueta)
        _flecha()


def _renderizar_grupo(grupo: GrupoInicio) -> None:
    if grupo.subtitulo:
        _texto("h4", grupo.subtitulo, "inicio-subtitulo")
    clases = "inicio-lista inicio-lista-escenas" if grupo.accesos[0].identificador_herramienta == "visualizador" else "inicio-lista"
    with ui.element("ul").classes(clases):
        for acceso in grupo.accesos:
            with ui.element("li"):
                _renderizar_acceso(acceso)


def _renderizar_seccion(seccion: SeccionInicio, indice: int) -> None:
    identificador_titulo = f"inicio-titulo-{seccion.identificador}"
    gesto = f"seccion-{seccion.identificador}"
    with ui.element("section").classes("inicio-seccion").classes(
        add="inicio-seccion-numeracion" if seccion.identificador == "sistemas-numeracion" else ""
    ).props(f'aria-labelledby="{identificador_titulo}"').style(f"--inicio-indice: {indice}"):
        with ui.element("header").classes("inicio-seccion-cabecera").props(f'data-gesto-inicio="{gesto}"'):
            _simbolo(gesto)
            _texto("h3", seccion.titulo, "inicio-seccion-titulo").props(f'id="{identificador_titulo}"')
        for grupo in seccion.grupos:
            _renderizar_grupo(grupo)


def _renderizar_directorio() -> None:
    with ui.element("nav").classes("inicio-directorio").props('aria-labelledby="inicio-herramientas"') as directorio:
        _texto("h2", "Herramientas", "inicio-directorio-titulo").props('id="inicio-herramientas"')
        with ui.element("div").classes("inicio-secciones"):
            for indice, seccion in enumerate(secciones_inicio()):
                _renderizar_seccion(seccion, indice)
    directorio.props("data-directorio-listo")


class VistaInicio:
    """Compone la portada y conserva el acceso directo a Glosa."""

    def __init__(self, glosa_abierta: bool = False):
        self.glosa_abierta = glosa_abierta
        self.panel_ia = None

    async def construir(self, cliente: Client) -> None:
        """Monta la portada en el cliente y abre Glosa cuando lo pide la ruta."""
        ui.query("body").classes("inicio-pagina")
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=RUTA_INICIO)
        with ui.element("main").classes("inicio-raiz vista-raiz"):
            _renderizar_cabecera()
            _renderizar_presentacion()
            _renderizar_directorio()
        self.panel_ia.construir()
        if self.glosa_abierta:
            ui.query("body").classes(add="inicio-glosa-disponible")
            self.panel_ia.abrir()
