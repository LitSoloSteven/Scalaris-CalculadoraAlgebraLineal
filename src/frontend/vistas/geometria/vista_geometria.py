"""Composición de controles, estados y figuras del visualizador geométrico."""
from __future__ import annotations

import asyncio
import logging
from nicegui import ui

from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.tareas import lanzar_tarea
from src.frontend.constantes import ANTIRREBOTE_GEOMETRIA_SEGUNDOS
from src.frontend.navegacion import ruta_de
from src.frontend.controladores.sesion_matricial import actualizar_contexto
from .mixin_controles import MixinControlesGeometria
from .limpieza_geometria import MixinLimpiezaGeometria
from .mixin_escenas import MixinEscenasGeometria
from ._actualizacion_geometria import actualizar_figura
from ._contexto_ia_geometria import obtener_contexto_ia, obtener_senales_ia
from ._estados_geometria import mostrar_estado_vacio, renderizar_error
from ._transferencia_geometria import procesar_transferencia_rectas, procesar_transferencia_vectores

registro = logging.getLogger(__name__)
ESCENAS_VALIDAS = ('rectas-planos', 'vectores', 'combinacion')


class VistaGeometria(MixinLimpiezaGeometria, MixinControlesGeometria, MixinEscenasGeometria):
    """Orquesta la visualización y el contexto de IA sin resolver matemáticas."""

    def __init__(self):
        self._cliente = None
        self.panel_ia = None
        self.escena = 'rectas-planos'
        self.ultimo_resultado = None
        self.ultimo_hash_entrada = None
        self._tarea_previa = None
        self._primer_dibujo = True
        self._elemento_plotly = None
        self._clave_figura = None
        self._huella_resultado = None
        self.contenedor_controles = None
        self.contenedor_figura = None
        self.contenedor_resumen = None
        self.contenedor_deslizador = None
        self.contenedor_estado = None
        self.cuadricula = None
        self.panel_vectores = None
        self.panel_combinacion = None

    def _ejecutar_javascript(self, codigo: str) -> None:
        cliente = self._cliente
        if cliente is None or cliente.is_deleted:
            return
        cliente.run_javascript(codigo)

    def _lanzar_tarea(self, corrutina) -> asyncio.Task:
        return lanzar_tarea(self._cliente, corrutina)

    def construir(self, escena: str = 'rectas-planos', token_transferencia: str = ''):
        """Compone la escena indicada y carga una transferencia opcional."""
        self._cliente = ui.context.client
        self._cliente.on_disconnect(self._cancelar_actualizacion)
        self.escena = self.normalizar_escena(escena)
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de('visualizador'), clave_activa=f"vis:{self.escena}")
        ui.add_head_html('<script src="/assets/js/geometria.js"></script>')
        self._construir_contenedores()
        self.panel_ia.construir()
        self._construir_controles(self.escena)
        self._mostrar_estado_vacio()
        self._procesar_transferencia(token_transferencia)

    def _construir_contenedores(self):
        with (
            ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4 vista-raiz geometria-raiz'),
            ui.element('div').classes('disposicion-dividida'),
        ):
            self._construir_panel_entrada()
            self._construir_panel_salida()

    def _construir_panel_entrada(self):
        with ui.column().classes('disposicion-panel p-6 bg-[var(--bg-page)] geometria-panel'):
            self.contenedor_controles = ui.column().classes('geometria-contenedor')

    def _construir_panel_salida(self):
        with ui.column().classes('disposicion-panel p-6 bg-[var(--bg-page)] geometria-panel'):
            self.contenedor_estado = ui.column().classes('geometria-contenedor')
            self.contenedor_figura = ui.column().classes('geometria-contenedor')
            self.contenedor_deslizador = ui.column().classes('geometria-contenedor')
            self.contenedor_resumen = ui.column().classes('geometria-contenedor')

    @staticmethod
    def normalizar_escena(escena: str) -> str:
        """Devuelve la escena solicitada o rectas y planos cuando es desconocida."""
        return escena if escena in ESCENAS_VALIDAS else 'rectas-planos'

    def _procesar_transferencia(self, token: str):
        if not token:
            return
        procesar = procesar_transferencia_rectas if self.escena == 'rectas-planos' else procesar_transferencia_vectores
        procesar(self, token)

    def _mostrar_estado_vacio(self):
        mostrar_estado_vacio(self)

    def _notificar_cambio_datos(self):
        self._programar_actualizacion()
        actualizar_contexto(self)

    def _cancelar_actualizacion(self):
        if self._tarea_previa and not self._tarea_previa.done():
            self._tarea_previa.cancel()

    def _programar_actualizacion(self):
        self._cancelar_actualizacion()
        self._tarea_previa = self._lanzar_tarea(self._actualizar_con_antirrebote())

    async def _actualizar_con_antirrebote(self):
        try:
            await asyncio.sleep(ANTIRREBOTE_GEOMETRIA_SEGUNDOS)
            await self._actualizar_figura()
        except asyncio.CancelledError:
            raise
        except Exception:
            registro.exception("No se pudo actualizar la vista geométrica")

    async def _actualizar_figura(self):
        await actualizar_figura(self)

    def _construir_carga(self) -> dict | None:
        return self._extraer_carga_controles()

    def _renderizar_error(self, resultado: dict):
        self._ejecutar_javascript('window.scalaris?.geometria?.marcarInvalido(null);')
        renderizar_error(self, resultado)

    def obtener_contexto_ia(self):
        """Devuelve el contexto de entrada y resultado para el asistente."""
        return obtener_contexto_ia(self)

    def obtener_senales_ia(self):
        """Devuelve señales de la escena para las sugerencias del asistente."""
        return obtener_senales_ia(self)

    def renderizar_sugerencias_en_linea(self):
        """Muestra las sugerencias disponibles junto al resultado."""
        if self.panel_ia:
            self.panel_ia.renderizar_sugerencias_en_linea()
