"""Composicion de la vista de matriz inversa."""
from __future__ import annotations

from nicegui import ui
from src.frontend.controladores.operaciones_inversas.contexto import obtener_contexto_inversa, obtener_senales_inversa

from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.calculadora import PanelCalculadora
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.navegacion import ruta_de
from src.frontend.componentes.panel_matriz_cuadrada import PanelMatrizCuadrada
from src.frontend.componentes.cuadricula_base import ubicar_celda_matriz
from src.frontend.vistas.operaciones_inversas.mixin_historial import MixinHistorialOperacionesInversas
from src.frontend.vistas.operaciones_inversas.mixin_resultados import MixinResultadosOperacionesInversas
from src.frontend.vistas.operaciones_inversas.mixin_pasos import MixinPasosOperacionesInversas



class VistaOperacionesInversas(MixinResultadosOperacionesInversas, MixinPasosOperacionesInversas, MixinHistorialOperacionesInversas):
    """Controlador de vista modular para el cálculo de la Matriz Inversa."""

    def __init__(self):
        self.panel_matriz_cuadrada = PanelMatrizCuadrada()
        self.calculadora = PanelCalculadora()

        self.contenedor_resultados: ui.column | None = None
        self.pestanas_herramientas: ui.tabs | None = None
        self.contenedor_vista_previa: ui.column | None = None
        self.tarea_vista_previa = None
        self.historial: list[dict] = []
        self.contenedor_historial: ui.column | None = None
        self.ultimo_resultado: dict | None = None

        self.reproductor_pasos = None
        self._huella_resultado = None

    def construir(self, token_transferencia: str = ''):
        """Construye la interfaz completa de la vista."""
        self._registrar_desmontaje()
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de('inversa'))

        self.panel_matriz_cuadrada.inyectar_recursos_cliente()
        self.panel_matriz_cuadrada.al_cambiar_datos = self._al_cambiar_matriz
        self.calculadora.inyectar_recursos_cliente()

        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4 vista-raiz sesion-vista'):
            self.contenedor_transferencia = ui.column().classes('w-full')
            self._renderizar_cabecera()

            with ui.element('div').classes('disposicion-dividida mb-8'):
                self._renderizar_columna_captura()
                self._renderizar_columna_herramientas()

            self.contenedor_resultados = ui.column().classes(
                'w-full panel-tarjeta p-6 items-center justify-center min-h-[400px]'
            ).props('id="inversa-resultados"')
            self.restablecer_resultados()

        self.panel_ia.construir()
        self._procesar_transferencia_inicial(token_transferencia)

    def _renderizar_cabecera(self) -> None:
        """Renderiza título y subtítulo de la herramienta."""
        with ui.column().classes('mb-8'):
            ui.label('Matriz inversa').classes('text-2xl font-bold texto-principal')
            ui.label('Gauss-Jordan sobre [A | I]').classes(
                'fuente-pequena texto-secundario uppercase'
            ).classes('sesion-subtitulo')

    def _renderizar_columna_captura(self) -> None:
        """Renderiza la cuadrícula de captura y botones de acción."""
        with ui.column().classes('disposicion-panel'):
            self.panel_matriz_cuadrada.construir_contenedor()
            with ui.row().classes('w-full mt-6 gap-4'):
                ui.button(
                    icon='delete',
                    on_click=self.confirmar_limpieza,
                    color=None,
                ).classes('boton-discreto flex-1 py-3').props(
                    'ripple=false id="boton-limpiar-principal" aria-label="Limpiar"'
                ).tooltip('Limpiar')

                ui.button(
                    'Calcular inversa',
                    on_click=lambda evento: self.calcular(evento.sender),
                    color=None,
                ).classes('boton-principal flex-[2] py-3').props('ripple=false')

    def _procesar_transferencia_inicial(self, token_transferencia: str) -> None:
        """Recupera la matriz desde navegación entrante si existe token."""
        from src.frontend.componentes.transferencia import consumir_matriz, renderizar_aviso_transferencia, limpiar_url_transferencia
        from src.backend.constantes import DIMENSION_MAXIMA_INVERSA
        respuesta = consumir_matriz(token_transferencia, dimension_maxima=DIMENSION_MAXIMA_INVERSA)
        if respuesta is not None:
            with self.contenedor_transferencia:
                dimension = len(respuesta.datos) if respuesta.datos else 0
                renderizar_aviso_transferencia(respuesta, f"Cargamos A ({dimension}×{dimension}) desde {respuesta.nombre_origen}. Presiona Calcular inversa para ver A⁻¹.")
            if respuesta.estado == 'exito':
                self.panel_matriz_cuadrada.cargar_matriz(respuesta.datos)
            limpiar_url_transferencia()

    def obtener_contexto_ia(self):
        """Delega la serializacion de captura y resultado al controlador."""
        return obtener_contexto_inversa(self)

    def obtener_senales_ia(self):
        """Delega las senales y coordenadas invalidas al controlador."""
        return obtener_senales_inversa(self)

    def enfocar_celda(self, coordenada: tuple[int, int]):
        """Enfoca la coordenada indicada para revisar una celda inválida."""
        if coordenada and hasattr(self, 'panel_matriz_cuadrada'):
            ubicar_celda_matriz("A", *coordenada)

    def esta_completamente_vacio(self) -> bool:
        """Consulta la presencia de texto en el panel matricial."""
        return self.panel_matriz_cuadrada.esta_vacio()
