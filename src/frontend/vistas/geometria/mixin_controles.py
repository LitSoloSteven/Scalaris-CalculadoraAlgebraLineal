"""Controles y lectura de entradas para las escenas geométricas."""
from __future__ import annotations

from nicegui import ui
from src.backend.geometria.transferencia import LIMITES_VECTORES_ESCENA
from src.frontend.componentes.equation_grid import EquationGrid
from src.frontend.controladores.geometria.captura import construir_carga_sistema, construir_carga_vectores
from ._panel_vectores import PanelVectoresGeometria


class MixinControlesGeometria:
    """Compone entradas reutilizables y delega la preparación de las cargas."""

    def _construir_controles(self, escena: str):
        if not self.contenedor_controles:
            return
        self.contenedor_controles.clear()
        constructores = {
            'rectas-planos': self._construir_controles_rectas,
            'vectores': self._construir_controles_vectores,
            'combinacion': self._construir_controles_combinacion,
        }
        constructor = constructores.get(escena)
        if constructor:
            with self.contenedor_controles:
                constructor()

    def _construir_controles_rectas(self):
        self.cuadricula = EquationGrid(default_m=2, default_n=2)
        self.cuadricula.inject_scripts()
        self.cuadricula.on_data_change = self._notificar_cambio_datos
        self.cuadricula.build_grid_container()

    def _construir_panel_vectores(self, panel):
        panel.inject_scripts()
        contenedor = ui.column().classes('geometria-contenedor')
        panel.build(contenedor)
        while len(panel.vectors) < panel.min_vectors:
            panel.add_vector()
        panel.on_data_change = self._notificar_cambio_datos

    def _construir_controles_vectores(self):
        minimo, maximo = LIMITES_VECTORES_ESCENA['vectores']
        self.panel_vectores = PanelVectoresGeometria(panel_id='geometria_vectores', min_vectors=minimo, max_vectors=maximo)
        self._construir_panel_vectores(self.panel_vectores)

    def _construir_controles_combinacion(self):
        minimo, maximo = LIMITES_VECTORES_ESCENA['combinacion']
        self.panel_combinacion = PanelVectoresGeometria(
            panel_id='geometria_combinacion', min_vectors=minimo, max_vectors=maximo,
            allow_orientation_toggle=False, first_vector_fixed_label='b',
        )
        self._construir_panel_vectores(self.panel_combinacion)

    def _extraer_carga_controles(self) -> dict | None:
        if self.escena == 'rectas-planos':
            if not self.cuadricula:
                return None
            matriz, vector = self.cuadricula.obtener_datos_matriz()
            return construir_carga_sistema(matriz, vector, self.cuadricula.is_strictly_empty())
        panel = self.panel_vectores if self.escena == 'vectores' else self.panel_combinacion
        if not panel:
            return None
        caches = [datos.get('cache', {}) for datos in panel.vectors.values()]
        return construir_carga_vectores(self.escena, panel.dim, caches)

    def _construir_deslizador(self, resultado: dict, escena: str):
        if not self.contenedor_deslizador:
            return
        self.contenedor_deslizador.clear()
        cuadros = resultado.get('frames', [])
        if escena == 'vectores' and cuadros:
            with self.contenedor_deslizador:
                self._mostrar_deslizador(resultado, cuadros)

    def _mostrar_deslizador(self, resultado: dict, cuadros: list):
        indice = resultado.get('default_frame', 16)
        etiqueta = cuadros[indice].get('k_exact', '1')
        identificador = f'geometria-figura-{id(self)}'
        with ui.row().classes('geometria-deslizador-fila w-full items-center gap-4 mt-2'):
            ui.label('k =').classes('font-bold text-sm text-main geometria-accion')
            ui.label(etiqueta).classes('font-bold text-sm text-main geometria-deslizador-valor')
            entrada = ui.element('input').classes('geometria-deslizador-entrada').props(
                f'type="range" min="0" max="{len(cuadros) - 1}" step="1" value="{indice}" '
                f'data-geometria-deslizador="{identificador}" aria-label="Valor del parámetro k"'
            )
            entrada.props['aria-valuetext'] = etiqueta
        aviso = ui.label('').classes('geometria-aviso text-sm text-sec').props('role=alert')
        aviso.props['id'] = f'geometria-error-cuadro-{identificador}'
