"""Vista para capturar matrices y analizar transformaciones lineales."""

from nicegui import ui
from src.frontend import textos_transformaciones as textos
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from .limpieza_modelos import MixinLimpiezaModelos

from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.navegacion import ruta_de
from src.frontend.componentes.captura_matrices import PanelCapturaMatrices


from .mixin_calculo_transformaciones import MixinCalculoTransformaciones


from .mixin_captura_transformaciones import MixinCapturaTransformaciones
from .mixin_ejemplos_transformaciones import MixinEjemplosTransformaciones
from .glosa_modelos import MixinGlosaModelos
from .transferencia_modelos import recibir_matriz_modelo
from .captura_aplicacion_transformacion import MixinAplicacionTransformacion


class VistaTransformaciones(MixinAplicacionTransformacion, MixinGlosaModelos, MixinLimpiezaModelos, MixinCalculoTransformaciones, MixinCapturaTransformaciones, MixinEjemplosTransformaciones):
    """Vista completa de Transformaciones Lineales."""
    herramienta_modelo = "transformaciones"

    def __init__(self):
        self.filas = 2
        self.columnas = 2
        self.modo_transformacion = textos.MODO_ANALISIS
        self.tipo_objeto = "vector"
        self.entradas_vector_original: list = []
        self.contenedor_vector_original = None
        self.entradas_coeficientes: list[list] = []
        self.entradas_variables: list = []
        self.contenedor_coeficientes = None
        self.contenedor_variables = None
        self.contenedor_resultados = None
        self.ultimo_resultado = None


    def construir(self, token_transferencia: str = ''):
        """Construye los controles y contenedores de la vista."""
        PanelCapturaMatrices.inyectar_recursos_cliente()
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("transformaciones"))
        with ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 vista-raiz min-w-0"):
            self.contenedor_transferencia = ui.column().classes('w-full')
            ui.label(textos.TITULO).classes("text-2xl font-bold texto-principal")
            ui.label(textos.DESCRIPCION).classes("texto-secundario")
            ui.label(textos.AVISO_ACADEMICO).classes("texto-secundario text-sm")
            self._construir_selector_modo()
            with ui.element("div").classes("disposicion-dividida mb-8"):
                self._construir_captura()
                with ui.column().classes("disposicion-panel min-w-0"):
                    self.contenedor_resultados = ui.column().classes(
                        "w-full panel-tarjeta p-6 min-w-0 min-h-[400px]"
                    ).props('id="resultados-transformaciones"')
                    self._restablecer_resultados()
        self._conectar_modelo()
        recibir_matriz_modelo(self, token_transferencia)

    def _construir_captura(self) -> None:
        with ui.column().classes("disposicion-panel min-w-0"):
            self._construir_ejemplos()
            self._construir_selector_tamano()
            self._construir_panel_a()
            region = ui.column().classes("w-full min-w-0")
            with self.selector_modo.asociar_contenido(textos.MODO_ANALISIS, region):
                self._construir_panel_variables()
            self._construir_panel_aplicacion()
            self._crear_accion_principal()

    def _crear_accion_principal(self):
        """Construye crear accion principal conservando el orden de los elementos."""
        with ui.row().classes("w-full mt-6 gap-4"):
            crear_boton_limpieza(self, lambda: not self.contenedor_resultados.is_deleted, self._campos_captura)
            self.boton_calcular = ui.button(
                textos.ANALIZAR, icon="analytics",
                on_click=lambda evento: self._analizar(evento.sender),
                color=None,
            ).classes("boton-principal flex-[2] py-3").props(f'ripple=false aria-label="{textos.ANALIZAR}"')

    def _campos_captura(self):
        auxiliares = (self.entradas_vector_original if self.modo_transformacion == textos.MODO_APLICACION
                      else self.entradas_variables)
        return [entrada for fila in self.entradas_coeficientes for entrada in fila] + auxiliares
