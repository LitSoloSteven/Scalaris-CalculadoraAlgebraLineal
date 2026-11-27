"""Composicion de la vista de sistemas lineales."""
from nicegui import ui
from src.frontend.componentes.aplicacion.controles.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.navegacion import ruta_de
from src.frontend.componentes.captura.ecuaciones.cuadricula_ecuaciones import CuadriculaEcuaciones
from src.frontend.componentes.captura.ecuaciones.filas_ecuaciones import crear_cabecera_ecuaciones
from src.frontend.componentes.captura.paneles.calculadora import PanelCalculadora
from src.frontend.componentes.glosa.panel.panel_ia import PanelIA
from src.frontend.vistas.algebra.sistemas_lineales.captura.mixin_sincronizacion import MixinSincronizacionSistemasLineales
from .mixin_historial import MixinHistorialSistemasLineales
from src.frontend.vistas.algebra.sistemas_lineales.resultados.mixin_pasos import MixinPasosSistemasLineales
from src.frontend.vistas.algebra.sistemas_lineales.resultados.mixin_resultados import MixinResultadosSistemasLineales
from src.frontend.vistas.algebra.sistemas_lineales.captura.mixin_vista_previa import MixinVistaPreviaSistemasLineales
from src.frontend.vistas.algebra.sistemas_lineales.captura._transferencia_sistemas import procesar_transferencia_matriz
from src.frontend.controladores.algebra.sistemas_lineales.resolucion.contexto import (
    obtener_contexto_sistema, obtener_senales_sistema,
)
from src.frontend.controladores.algebra.sistemas_lineales.nucleo.estado_captura import cambiar_modo
from src.frontend.vistas.algebra.sistemas_lineales.captura.modo_homogeneo import cambiar_modo_homogeneo


class VistaSistemasLineales(
    MixinSincronizacionSistemasLineales,
    MixinHistorialSistemasLineales,
    MixinVistaPreviaSistemasLineales,
    MixinPasosSistemasLineales,
    MixinResultadosSistemasLineales
):
    """Controlador de vista modular para Sistemas Lineales."""

    def __init__(self, metodo_inicial='gauss'):
        self.cuadricula = CuadriculaEcuaciones()
        self.calculadora = PanelCalculadora()
        self.contenedor_resultados = None
        self.pestanas_modo = None
        self.pestanas_metodo = None
        self.metodo_inicial = metodo_inicial
        self.reproductor_pasos = None
        self.ultimo_resultado = None
        self._huella_resultado = None

        self.num_ecuaciones = 3
        self.entradas_ecuaciones = []
        self.contenedor_ecuaciones_lista = None

        self.historial = []
        self.tarea_vista_previa = None
        self.contenedor_vista_previa = None
        self.contenedor_historial = None

    def construir(self, token_transferencia: str = ''):
        """Construye la interfaz completa de la vista."""
        self._registrar_desmontaje()
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de('sistemas'))
        self.cuadricula.inyectar_recursos_cliente()
        self.cuadricula.al_cambiar_datos = self._al_cambiar_cuadricula
        self.calculadora.inyectar_recursos_cliente()

        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4 vista-raiz sesion-vista disposicion-herramienta'):
            self.contenedor_transferencia = ui.column().classes('w-full empty:hidden')
            self._renderizar_selectores()

            with ui.element('div').classes('disposicion-captura-fila mb-2'):
                self._renderizar_columna_edicion()
                self._renderizar_columna_herramientas()

            self.contenedor_resultados = ui.column().classes(
                'disposicion-resultados panel-tarjeta p-6 items-center justify-center min-h-[400px]'
            ).props('id="sistemas-resultados"')
            self.restablecer_resultados()
            self.actualizar_botones_sincronizacion()

        self.panel_ia.construir()
        self._procesar_transferencia_sistemas(token_transferencia)

    def _renderizar_selectores(self) -> None:
        """Renderiza tabs de modo (Matriz/Ecuaciones) y método (Gauss/Gauss-Jordan)."""
        with ui.row().classes('w-full justify-between items-center mb-2 gap-4 flex-wrap'):
            with ui.tabs().classes('pestanas-controles sistemas-pestanas-modo').props('dense no-caps') as self.pestanas_modo:
                ui.tab('Matriz', icon='grid_4x4')
                ui.tab('Ecuaciones', icon='functions')

            with ui.tabs().classes('pestanas-controles pestanas-metodo').props('dense no-caps') as self.pestanas_metodo:
                ui.tab('gauss', label='Gauss')
                ui.tab('gauss-jordan', label='Gauss-Jordan')
            self.pestanas_metodo.value = self.metodo_inicial
            self.pestanas_metodo.on_value_change(self.cambiar_metodo)

            self.pestanas_modo.on_value_change(lambda evento: cambiar_modo(self, evento.value))

    def _renderizar_columna_edicion(self) -> None:
        """Renderiza paneles para edición en Matriz o Ecuaciones y botones de acción."""
        with ui.column().classes('disposicion-panel'):
            with ui.tab_panels(self.pestanas_modo, value='Matriz').classes(
                'w-full p-0 overflow-hidden panel-tarjeta sistemas-panel-captura'
            ):
                with ui.tab_panel('Matriz').classes('p-6'):
                    self.casilla_homogeneo = ui.checkbox("Sistema homogéneo Ax = 0", value=False,
                                                       on_change=lambda evento: cambiar_modo_homogeneo(self, evento.value))
                    self._crear_sincronizacion_ecuaciones()
                    self.cuadricula.construir_contenedor_cuadricula()

                with ui.tab_panel('Ecuaciones').classes('p-6'):
                    self._renderizar_panel_ecuaciones()

            with ui.row().classes('w-full mt-6 gap-4'):
                self._construir_boton_limpieza()
                ui.button(
                    'Resolver', on_click=lambda evento: self.resolver_sistema(evento.sender), color=None
                ).classes('boton-principal flex-[2] py-3').props('ripple=false')


    def _crear_sincronizacion_ecuaciones(self):
        """Construye crear sincronizacion ecuaciones conservando el orden de los elementos."""
        with ui.row().classes('w-full justify-end mb-4'):
            self.boton_desde_ecuaciones = ui.button(
                'Sincronizar desde Ecuaciones', icon='sync',
                on_click=self.sincronizar_desde_ecuaciones, color=None
            ).classes('boton-discreto text-xs py-1 px-3').props('ripple=false')

    def _renderizar_panel_ecuaciones(self) -> None:
        """Renderiza la lista de ecuaciones editables y botones agregar/quitar."""
        self.boton_quitar_ecuacion, self.boton_agregar_ecuacion = crear_cabecera_ecuaciones(
            self._cambiar_ecuaciones_animadas, self._crear_sincronizacion_matriz,
        )
        self.contenedor_ecuaciones_lista = ui.column().classes('w-full')
        self.renderizar_ecuaciones()

    def _crear_sincronizacion_matriz(self) -> None:
        self.boton_desde_matriz = ui.button(
            'Sincronizar desde Matriz', icon='sync',
            on_click=self.sincronizar_desde_matriz, color=None,
        ).classes('boton-discreto text-xs py-1 px-3').props('ripple=false')

    def _procesar_transferencia_sistemas(self, token_transferencia: str) -> None:
        """Aplica la matriz del token de handoff entrante si existe."""
        procesar_transferencia_matriz(self, token_transferencia)

    def _campos_visuales_limpieza(self) -> list:
        return [self.cuadricula.contenedor_matriz, *self.entradas_ecuaciones]

    def obtener_contexto_ia(self):
        """Devuelve el contexto pedagógico del sistema y su resultado vigente."""
        return obtener_contexto_sistema(self)

    def obtener_senales_ia(self):
        """Delega las senales de captura y resultado al controlador."""
        return obtener_senales_sistema(self)
