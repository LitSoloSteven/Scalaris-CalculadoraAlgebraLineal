"""Vista interactiva para evaluación de expresiones matriciales en Scalaris."""

from __future__ import annotations

from nicegui import ui

from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.captura_matrices import PanelCapturaMatrices
from src.frontend.navegacion import ruta_de
from src.frontend.controladores.operaciones_matrices import ControladorOperacionesMatrices
from src.frontend.controladores.sesion_matricial import actualizar_contexto
from src.frontend.vistas.operaciones_matrices.mixin_resultados import MixinResultadosOperacionesMatrices

from .mixin_contexto_matrices import MixinContextoMatrices


class VistaOperacionesMatrices(MixinResultadosOperacionesMatrices, MixinContextoMatrices):
    """Controlador de vista modular para el cálculo y paso a paso de matrices."""

    def __init__(self):
        self.panel_captura_matrices = PanelCapturaMatrices()
        self.contenedor_resultados = None
        self.entrada_expresion = None
        self.reproductor_pasos = None
        self._version_solicitud = 0

    def restablecer_resultados(self):
        """Limpia los resultados y detiene cualquier reproducción activa."""
        self.ultimo_resultado = None
        self._version_solicitud += 1
        if getattr(self, 'reproductor_pasos', None) is not None:
            self.reproductor_pasos.detener()
            self.reproductor_pasos = None

        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.icon('data_object', size='4rem').classes('texto-marcador mb-4')
            ui.label('Sin resultados').classes('text-xl font-bold texto-principal')
            ui.label(
                'Añade matrices y escribe una expresión matemática para empezar'
            ).classes('text-sm texto-secundario mt-2 text-center')

    def _al_cambiar_matriz(self):
        """Notifica al panel de Glosa cuando cambian los datos de las matrices."""
        actualizar_contexto(self)

    def _navegar_a_inversa(self, nombre: str) -> None:
        """Valida y redirige a la vista de matriz inversa mediante handoff."""
        matriz = self.panel_captura_matrices.matrices.get(nombre)
        if matriz is None:
            return
        datos = []
        for indice_fila in range(matriz['filas']):
            fila = [str(matriz['cache'].get((indice_fila, c), '0')).strip() or '0' for c in range(matriz['columnas'])]
            datos.append(fila)

        transferencia = ControladorOperacionesMatrices.preparar_inversa(
            nombre, {"filas": matriz['filas'], "columnas": matriz['columnas'], "datos": datos}
        )
        if transferencia.get("mensaje"):
            ui.notify(transferencia["mensaje"], type='warning')
            return

        from src.frontend.componentes.transferencia import url_transferencia, guardar_matriz
        from src.frontend.navegacion import ruta_de
        token = guardar_matriz('matrices', transferencia["datos"])
        ui.navigate.to(url_transferencia(ruta_de('inversa'), token))

    def _renderizar_panel_expresion(self) -> None:
        """Renderiza el entrada de la expresión matemática y el botón Evaluar."""
        with ui.column().classes('w-full panel-tarjeta p-6 mt-4'):
            ui.label('Expresión Matemática').classes('text-lg font-bold texto-principal mb-2')
            self.entrada_expresion = ui.input(
                placeholder='Ej. A + B * C'
            ).classes('matriz-entrada w-full text-xl py-2').props(
                'borderless autocomplete="new-password"'
            )
            self.entrada_expresion.on_value_change(lambda _: self._al_cambiar_matriz())

            ui.button(
                'Evaluar',
                icon='calculate',
                on_click=lambda evento: self.evaluar_expresion(evento.sender),
                color=None,
            ).classes('boton-principal w-full py-3 mt-4').props('ripple=false')

    def construir(self):
        """Construye los paneles de captura, expresión y resultados."""
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de('matrices'))
        self.panel_captura_matrices.inyectar_recursos_cliente()
        self.panel_captura_matrices.al_cambiar_datos = self._al_cambiar_matriz

        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4 vista-raiz'):
            with ui.row().classes('w-full justify-between items-center mb-8 gap-4 flex-wrap'):
                ui.label('Matrices').classes('text-2xl font-bold texto-principal')

            with ui.element('div').classes('disposicion-dividida mb-8'):
                with ui.column().classes('disposicion-panel'):
                    self.panel_captura_matrices.al_invertir = self._navegar_a_inversa
                    self.panel_captura_matrices.construir(ui.column().classes('w-full'))
                    self._renderizar_panel_expresion()

                with ui.column().classes('disposicion-panel'):
                    self.contenedor_resultados = ui.column().classes(
                        'w-full panel-tarjeta p-6 items-center justify-center min-h-[400px]'
                    ).props('id="resultados-matrices"')
                    self.restablecer_resultados()

        self.panel_ia.construir()
