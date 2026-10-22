"""Vista principal de inicio: matriz de areas con dialogos por pilar."""
from __future__ import annotations

import html
from nicegui import ui

from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.iconos import icono_svg
from src.frontend.navegacion import RUTA_INICIO
from src.frontend.controladores.inicio._modelo import (
    ModeloTarjeta, formatear_cantidad_elementos, pilares_inicio, seleccion_inicial,
)

_CLASES_ORDEN = ('inicio-orden-0', 'inicio-orden-1', 'inicio-orden-2', 'inicio-orden-3')


def _elemento_texto(etiqueta: str, texto: str, clases: str, titulo: str | None = None) -> ui.html:
    """Crea un elemento semantico con texto escapado para prevenir inyecciones."""
    elemento = ui.html(html.escape(texto), tag=etiqueta, sanitize=False).classes(clases)
    if titulo:
        elemento.props(f'title="{html.escape(titulo)}"')
    return elemento


class VistaInicio:
    """Compone las áreas y herramientas de la página de inicio."""

    def __init__(self, glosa_abierta: bool = False):
        self.glosa_abierta = glosa_abierta
        self.panel_ia = None
        self.tarjetas: dict[str, ui.element] = {}
        self.marcas: dict[str, ui.html] = {}
        self.filas: dict[str, ui.element] = {}
        self.marcas_filas: dict[str, ui.html] = {}

    def _construir_tarjeta(self, modelo_tarjeta: ModeloTarjeta):
        """Compone una tarjeta de herramienta como enlace accesible."""
        with ui.element('a').classes('inicio-tarjeta').props(f'href="{modelo_tarjeta.enlace}" data-clave="{modelo_tarjeta.clave}"') as tarjeta:
            with ui.element('span').classes('inicio-tarjeta-icono').props('aria-hidden="true"'):
                ui.html(icono_svg(modelo_tarjeta.icono))
            _elemento_texto('span', modelo_tarjeta.nombre, 'inicio-tarjeta-nombre')
            _elemento_texto('span', modelo_tarjeta.descripcion, 'inicio-tarjeta-descripcion')
            marca = _elemento_texto('span', '', 'inicio-tarjeta-marca')

        self.tarjetas[modelo_tarjeta.clave] = tarjeta
        self.marcas[modelo_tarjeta.clave] = marca
        return tarjeta

    async def _aplicar_destacada(self, cliente):
        """Marca la tarjeta reciente y su fila, o Sistemas de ecuaciones como inicio."""
        identificadores = None
        try:
            await cliente.connected()
            respuesta = await cliente.run_javascript(
                "return (window.scalaris && window.scalaris.recientes) ? window.scalaris.recientes.leer() : {valido: false, identificadores: []};",
                timeout=3.0,
            )
            if isinstance(respuesta, dict) and respuesta.get('valido'):
                identificadores = respuesta.get('identificadores')
        except Exception:
            identificadores = None

        if getattr(cliente, 'is_deleted', False):
            return

        seleccion = seleccion_inicial(identificadores)
        self._marcar_seleccion(seleccion)

    def _marcar_seleccion(self, seleccion) -> None:
        """Aplica las clases y textos correspondientes a la seleccion destacada."""
        tarjeta = self.tarjetas.get(seleccion.clave_tarjeta)
        marca = self.marcas.get(seleccion.clave_tarjeta)
        fila = self.filas.get(seleccion.identificador_pilar)
        marca_fila = self.marcas_filas.get(seleccion.identificador_pilar)
        texto_marca = 'Sigue aquí' if seleccion.hay_historial else 'Empieza aquí'

        if tarjeta is not None:
            tarjeta.classes(add='esta-destacada')
        if marca is not None:
            marca.set_content(html.escape(texto_marca))
        if fila is not None:
            fila.classes(add='esta-destacada')
        if marca_fila is not None:
            marca_fila.set_content(html.escape(texto_marca))

    async def construir(self, cliente):
        """Construye la matriz, los dialogos nativos y activa Glosa si corresponde."""
        ui.query('body').classes('inicio-pagina')
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=RUTA_INICIO)

        pilares = pilares_inicio()

        with ui.element('main').classes('inicio-raiz vista-raiz'):
            self._renderizar_cabecera()
            self._renderizar_matriz(pilares)
            self._renderizar_dialogos(pilares)

        self.panel_ia.construir()
        await self._aplicar_destacada(cliente)
        if self.glosa_abierta:
            ui.query('body').classes(add='inicio-glosa-disponible')
            self.panel_ia.abrir()

    def _renderizar_cabecera(self) -> None:
        """Renderiza el encabezado y logo de Scalaris."""
        with ui.element('header').classes('inicio-cabecera'):
            with ui.element('div').classes('inicio-marca'):
                with ui.element('div').classes('inicio-logotipo marca-contenedor-logotipo'):
                    ui.html('''
                        <img src="/assets/LogoOscuro.png" alt="" class="marca-logotipo marca-logotipo-oscuro" />
                        <img src="/assets/LogoClaro.png" alt="" class="marca-logotipo marca-logotipo-claro" />
                    ''')
                _elemento_texto('h1', 'Scalaris', 'inicio-titulo')
            _elemento_texto('p', 'Álgebra lineal y utilidades numéricas, con cada paso a la vista.', 'inicio-descripcion')

    def _renderizar_matriz(self, pilares: list) -> None:
        """Renderiza los botones de áreas en la matriz de inicio."""
        with ui.element('div').classes('inicio-matriz').props('role="group" aria-label="Áreas de Scalaris"'):
            indice_fila = 0
            for indice_fila, pilar in enumerate(pilares):
                self._renderizar_fila(pilar, indice_fila)


    def _renderizar_fila(self, pilar, indice_fila):
        """Compone las herramientas de un área en el orden del catálogo."""
        atributos_fila = (
            f'type="button" id="inicio-fila-{pilar.identificador}" '
            f'aria-haspopup="dialog" aria-expanded="false" '
            f'aria-controls="inicio-dialogo-{pilar.identificador}"'
        )
        with (
            ui.element('button').classes('inicio-fila ' + _CLASES_ORDEN[indice_fila]).props(atributos_fila) as fila,
            ui.element('span').classes('inicio-cuerpo-fila'),
        ):
            with ui.element('span').classes('inicio-capa-destacada').props('aria-hidden="true"'):
                ui.element('span').classes('inicio-destacada')
            with ui.element('span').classes('inicio-celda inicio-icono-celda').props('aria-hidden="true"'):
                ui.html(icono_svg(pilar.icono))
            with ui.element('span').classes('inicio-celda inicio-nombre-celda'):
                _elemento_texto('span', pilar.nombre_corto, 'inicio-titulo-fila', titulo=pilar.nombre_corto)
                _elemento_texto('span', pilar.descripcion, 'inicio-descripcion-fila', titulo=pilar.descripcion)
            with ui.element('span').classes('inicio-celda inicio-detalle-celda'):
                texto_conteo = formatear_cantidad_elementos(len(pilar.tarjetas), pilar.unidad_singular, pilar.unidad_plural)
                _elemento_texto('span', texto_conteo, 'inicio-conteo-fila')
                marca_fila = _elemento_texto('span', '', 'inicio-marca-fila')
                with ui.element('span').classes('inicio-indicador-fila').props('aria-hidden="true"'):
                    ui.html(icono_svg('abrir'))
        self.filas[pilar.identificador] = fila
        self.marcas_filas[pilar.identificador] = marca_fila

    def _renderizar_dialogos(self, pilares: list) -> None:
        """Renderiza los modales popovers para cada area."""
        for pilar in pilares:
            atributos_dialogo = (
                f'id="inicio-dialogo-{pilar.identificador}" '
                f'aria-labelledby="inicio-dialogo-titulo-{pilar.identificador}"'
            )
            with (
                ui.element('dialog').classes('inicio-dialogo').props(atributos_dialogo),
                ui.element('div').classes('inicio-dialogo-tarjeta'),
            ):
                self._renderizar_cabecera_dialogo(pilar)
                self._renderizar_cuerpo_dialogo(pilar)

    def _renderizar_cabecera_dialogo(self, pilar) -> None:
        """Encabezado de la tarjeta popover."""
        with ui.element('header').classes('inicio-dialogo-cabecera'):
            with ui.element('span').classes('inicio-dialogo-icono').props('aria-hidden="true"'):
                ui.html(icono_svg(pilar.icono))
            titulo = _elemento_texto('h2', pilar.nombre_corto, 'inicio-dialogo-titulo', titulo=pilar.nombre_corto)
            titulo.props(f'id="inicio-dialogo-titulo-{pilar.identificador}"')
            texto_conteo = formatear_cantidad_elementos(len(pilar.tarjetas), pilar.unidad_singular, pilar.unidad_plural)
            _elemento_texto('span', texto_conteo, 'inicio-dialogo-conteo')
            with (
                ui.element('button').classes('inicio-dialogo-cerrar').props('type="button" aria-label="Cerrar"'),
                ui.element('span').classes('inicio-dialogo-icono-cerrar').props('aria-hidden="true"'),
            ):
                ui.html(icono_svg('cerrar'))

    def _renderizar_cuerpo_dialogo(self, pilar) -> None:
        """Lista de herramientas del area."""
        if len(pilar.tarjetas) == 0:
            with ui.element('div').classes('inicio-area-vacia'):
                _elemento_texto('p', 'Esta área aún no tiene herramientas.', 'inicio-mensaje-vacio')
            return
        with ui.element('ul').classes('inicio-lista-herramientas'):
            indice_tarjeta = 0
            for modelo_tarjeta in pilar.tarjetas:
                with ui.element('li').classes(_CLASES_ORDEN[min(indice_tarjeta, 3)]):
                    self._construir_tarjeta(modelo_tarjeta)
                indice_tarjeta += 1
