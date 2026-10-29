"""Controles y lectura de entradas para las escenas geométricas."""
from __future__ import annotations

from nicegui import ui
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from src.frontend.textos import LIMPIEZA_VISUALIZAR
from src.backend.geometria.transferencia import LIMITES_VECTORES_ESCENA
from src.frontend.componentes.cuadricula_ecuaciones import CuadriculaEcuaciones
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
                with ui.row().classes('w-full gap-4 mt-6'):
                    crear_boton_limpieza(self, lambda: not self.contenedor_controles.is_deleted,
                                          lambda: [self.contenedor_controles])
                    ui.button(LIMPIEZA_VISUALIZAR, on_click=self._visualizar_captura, color=None).classes(
                        'boton-principal flex-[2] py-3'
                    ).props('ripple=false')

    def _construir_controles_rectas(self):
        self.cuadricula = CuadriculaEcuaciones(filas_iniciales=2, columnas_iniciales=2)
        self.cuadricula.inyectar_recursos_cliente()
        self.cuadricula.al_cambiar_datos = self._notificar_cambio_datos
        self.cuadricula.construir_contenedor_cuadricula()

    def _construir_panel_vectores(self, panel):
        panel.inyectar_recursos_cliente()
        contenedor = ui.column().classes('geometria-contenedor')
        panel.construir(contenedor)
        while len(panel.vectores) < panel.minimo_vectores:
            panel.agregar_vector()
        panel.al_cambiar_datos = self._notificar_cambio_datos

    def _construir_controles_vectores(self):
        minimo, maximo = LIMITES_VECTORES_ESCENA['vectores']
        self.panel_vectores = PanelVectoresGeometria(
            identificador_panel='geometria_vectores',
            opciones={'minimo_vectores': minimo, 'maximo_vectores': maximo},
        )
        self._construir_panel_vectores(self.panel_vectores)

    def _construir_controles_combinacion(self):
        minimo, maximo = LIMITES_VECTORES_ESCENA['combinacion']
        self.panel_combinacion = PanelVectoresGeometria(
            identificador_panel='geometria_combinacion',
            opciones={'minimo_vectores': minimo, 'maximo_vectores': maximo,
                      'permitir_orientacion': False, 'etiqueta_primer_vector': 'b'},
        )
        self._construir_panel_vectores(self.panel_combinacion)

    def _extraer_carga_controles(self) -> dict | None:
        if self.escena == 'rectas-planos':
            if not self.cuadricula:
                return None
            matriz, vector = self.cuadricula.obtener_datos_matriz()
            return construir_carga_sistema(matriz, vector, self.cuadricula.esta_completamente_vacio())
        panel = self.panel_vectores if self.escena == 'vectores' else self.panel_combinacion
        if not panel:
            return None
        caches = [datos.get('celdas', {}) for datos in panel.vectores.values()]
        return construir_carga_vectores(self.escena, panel.dimension, caches)

    def _construir_deslizador(self, resultado: dict, escena: str):
        if not self.contenedor_deslizador:
            return
        self.contenedor_deslizador.clear()
        cuadros = resultado.get('cuadros', [])
        if escena == 'vectores' and cuadros:
            with self.contenedor_deslizador:
                self._mostrar_deslizador(resultado, cuadros)

    def _mostrar_deslizador(self, resultado: dict, cuadros: list):
        indice = resultado['cuadro_predeterminado']
        etiqueta = cuadros[indice].get('escalar_exacto', '1')
        identificador = f'geometria-figura-{id(self)}'
        with ui.row().classes('geometria-deslizador-fila w-full items-center gap-4 mt-2'):
            ui.label('k =').classes('font-bold text-sm texto-principal geometria-accion')
            ui.label(etiqueta).classes('font-bold text-sm texto-principal geometria-deslizador-valor')
            entrada = ui.element('input').classes('geometria-deslizador-entrada').props(
                f'type="range" min="0" max="{len(cuadros) - 1}" step="1" value="{indice}" '
                f'data-geometria-deslizador="{identificador}" aria-label="Valor del parámetro k"'
            )
            entrada.props['aria-valuetext'] = etiqueta
        aviso = ui.label('').classes('geometria-aviso text-sm texto-secundario').props('role=alert')
        aviso.props['id'] = f'geometria-error-cuadro-{identificador}'
