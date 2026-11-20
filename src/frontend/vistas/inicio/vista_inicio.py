"""Portada y directorio de herramientas de Scalaris."""
import asyncio
import html

from nicegui import Client, ui

from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.iconos import icono_svg
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.selector_tema import renderizar_boton_tema
from src.frontend.controladores.inicio._modelo import EstadoPortada, estado_portada
from src.frontend.navegacion import ElementoNavegacion, RUTA_INICIO, enlace_elemento_navegacion
from src.frontend.navegacion.secciones_inicio import GrupoInicio, SeccionInicio, secciones_inicio
from .panel_ejemplo import construir_html_ejemplo, renderizar_panel_ejemplo


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
    gesto = seccion.icono
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
        self._enlace_destacado = None
        self._texto_destacado = None
        self._panel_ejemplo = None

    def _renderizar_presentacion(self, estado: EstadoPortada) -> None:
        enlace = html.escape(estado.enlace, quote=True)
        with ui.element("section").classes("inicio-presentacion").props('aria-labelledby="inicio-titulo"'):
            with ui.element("div"):
                ui.html("Álgebra lineal,<br><em>paso a paso.</em>", tag="h1").classes("inicio-titulo").props(
                    'id="inicio-titulo"'
                )
                _texto("p", "Resuelve ejercicios y visualiza qué ocurre en cada paso.", "inicio-descripcion")
                with ui.element("a").classes("inicio-destacado").props(f'href="{enlace}"') as enlace_destacado:
                    self._texto_destacado = _texto("span", estado.texto_destacado)
                    _flecha()
                self._enlace_destacado = enlace_destacado
            self._panel_ejemplo = renderizar_panel_ejemplo(estado.enlace, estado)

    async def _leer_recientes_cliente(self, cliente: Client):
        try:
            await asyncio.wait_for(cliente.connected(timeout=3.0), timeout=3.0)
            if getattr(cliente, "is_deleted", False):
                return None
            respuesta = await cliente.run_javascript(
                "return window.scalaris?.recientes?.leer?.() ?? { valido: false, identificadores: [] };",
                timeout=3.0,
            )
            if not isinstance(respuesta, dict) or respuesta.get("valido") is not True:
                return None
            identificadores = respuesta.get("identificadores")
            return identificadores if isinstance(identificadores, list) else None
        except Exception:
            return None

    def _actualizar_destacado(self, estado_inicial: EstadoPortada, estado: EstadoPortada) -> None:
        if self._enlace_destacado is not None:
            atributos = []
            if estado.hay_historial:
                atributos.append(f'data-acceso-reciente="{html.escape(estado.clave, quote=True)}"')
            if estado.enlace != estado_inicial.enlace:
                atributos.append(f'href="{html.escape(estado.enlace, quote=True)}"')
            if atributos:
                self._enlace_destacado.props(" ".join(atributos))
        if self._texto_destacado is not None and estado.texto_destacado != estado_inicial.texto_destacado:
            self._texto_destacado.set_content(html.escape(estado.texto_destacado))

    async def _aplicar_ultimo_acceso(self, cliente: Client, estado_inicial: EstadoPortada) -> None:
        identificadores = await self._leer_recientes_cliente(cliente)
        if (
            getattr(cliente, "is_deleted", False)
            or getattr(self._panel_ejemplo, "is_deleted", False)
            or not identificadores
        ):
            return
        estado = estado_portada(identificadores)
        if estado == estado_inicial:
            return
        self._actualizar_destacado(estado_inicial, estado)
        if self._panel_ejemplo is None:
            return
        if estado.clave == estado_inicial.clave and estado.enlace == estado_inicial.enlace:
            return
        self._panel_ejemplo.set_content(construir_html_ejemplo(estado))
        cliente.run_javascript("window.scalaris?.ejemplosInicio?.preparar?.();")

    async def construir(self, cliente: Client) -> None:
        """Monta la portada en el cliente y actualiza el último acceso al conectar."""
        ui.query("body").classes("inicio-pagina")
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=RUTA_INICIO)
        estado_inicial = estado_portada()
        with ui.element("main").classes("inicio-raiz vista-raiz"):
            _renderizar_cabecera()
            self._renderizar_presentacion(estado_inicial)
            _renderizar_directorio()
        self.panel_ia.construir()
        if self.glosa_abierta:
            ui.query("body").classes(add="inicio-glosa-disponible")
            self.panel_ia.abrir()
        await self._aplicar_ultimo_acceso(cliente, estado_inicial)
