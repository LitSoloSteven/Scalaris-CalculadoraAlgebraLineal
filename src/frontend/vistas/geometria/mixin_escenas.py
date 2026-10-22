"""Construcción y montaje de figuras Plotly para las escenas geométricas."""
from __future__ import annotations

import json
import logging
from nicegui import ui
from ._escenas import construir_figura_rectas_planos, construir_figura_vectores, construir_figura_combinacion
from ._resumen_geometria import renderizar_resumen

registro = logging.getLogger(__name__)


class MixinEscenasGeometria:
    """Delega figuras y resúmenes y registra cuadros del deslizador en el cliente."""

    async def _tema_actual(self) -> str:
        cliente = self._cliente
        if cliente is None or cliente.is_deleted:
            return 'papel'
        try:
            return await cliente.run_javascript(
                "document.documentElement.getAttribute('data-tema') || 'papel'", timeout=3.0,
            ) or 'papel'
        except TimeoutError:
            return 'papel'

    async def _obtener_solo_figura(self, resultado: dict, escena: str):
        constructores = {
            'rectas-planos': construir_figura_rectas_planos,
            'vectores': construir_figura_vectores,
            'combinacion': construir_figura_combinacion,
        }
        constructor = constructores.get(escena)
        if constructor is None:
            return None
        return constructor(resultado, tema=await self._tema_actual())

    def _registrar_cuadros(self, resultado: dict):
        if self.escena == 'vectores' and resultado.get('cuadros'):
            identificador = f'geometria-figura-{id(self)}'
            cuadros = json.dumps(resultado['cuadros'])
            self._ejecutar_javascript(f'window.scalaris?.geometria?.registrar("{identificador}", {cuadros});')

    def _montar_figura(self, figura, resultado: dict, escena: str):
        if not self.contenedor_figura:
            return
        self.contenedor_figura.clear()
        descripcion = (resultado.get('conjunto_solucion') or {}).get('descripcion') or f'Visualización geométrica: {escena}'
        with self.contenedor_figura:
            self._montar_contenedor_figura(figura, descripcion)
        self._registrar_cuadros(resultado)

    def _montar_contenedor_figura(self, figura, descripcion: str):
        with ui.element('div').classes('geometria-figura w-full').props('role=img') as contenedor:
            contenedor.props.update({'id': f'geometria-figura-{id(self)}', 'aria-label': descripcion})
            self._elemento_plotly = ui.plotly(figura).classes('w-full h-full')
            self._elemento_plotly.on('plotly_afterplot', js_handler='() => window.scalaris.sincronizarTemaPlotly()')

    async def _construir_figura(self, resultado: dict, escena: str) -> bool:
        from ._actualizacion_geometria import ERROR_RENDERIZADO
        try:
            figura = await self._obtener_solo_figura(resultado, escena)
            if figura is None:
                self._renderizar_error(ERROR_RENDERIZADO)
                return False
            self._montar_figura(figura, resultado, escena)
            return True
        except ImportError:
            self._renderizar_error({'mensaje': 'No se pudo cargar el módulo de gráficos. Recarga la página e inténtalo de nuevo.'})
            return False
        except Exception:
            registro.exception('No se pudo construir la figura geométrica')
            self._renderizar_error(ERROR_RENDERIZADO)
            return False

    def _renderizar_resumen(self, resultado: dict, escena: str):
        renderizar_resumen(self, resultado, escena)
