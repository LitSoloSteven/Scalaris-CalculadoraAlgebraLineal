"""Vista para capturar matrices y analizar transformaciones lineales."""

from nicegui import ui
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from .limpieza_modelos import MixinLimpiezaModelos

from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.navegacion import ruta_de
from src.frontend.componentes.captura_matrices import PanelCapturaMatrices


from .mixin_calculo_transformaciones import MixinCalculoTransformaciones


from .mixin_captura_transformaciones import MixinCapturaTransformaciones
from .mixin_ejemplos_transformaciones import MixinEjemplosTransformaciones


class VistaTransformaciones(MixinLimpiezaModelos, MixinCalculoTransformaciones, MixinCapturaTransformaciones, MixinEjemplosTransformaciones):
    """Vista completa de Transformaciones Lineales."""

    def __init__(self):
        self.filas = 2
        self.columnas = 2
        self.entradas_coeficientes: list[list] = []
        self.entradas_variables: list = []
        self.contenedor_coeficientes = None
        self.contenedor_variables = None
        self.contenedor_resultados = None
        self.ultimo_resultado = None


    def construir(self):
        """Construye los controles y contenedores de la vista."""
        PanelCapturaMatrices.inyectar_recursos_cliente()
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("transformaciones"))

        with ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 vista-raiz"):

            with ui.row().classes("w-full items-center gap-3 mb-6"):
                ui.icon("transform", size="2rem").classes("texto-acento")
                with ui.column().classes("gap-0"):
                    ui.label("Transformaciones Lineales").classes("text-2xl font-bold texto-principal")
                    ui.label("T: R^n -> R^m · Nucleo · Imagen · Rango · Nulidad").classes("text-sm texto-secundario")

            with ui.element("div").classes("disposicion-dividida mb-8"):
                with ui.column().classes("disposicion-panel"):
                    self._construir_ejemplos()
                    self._construir_selector_tamano()
                    self._construir_panel_a()
                    self._construir_panel_variables()

                    self._crear_accion_principal()

                with ui.column().classes("disposicion-panel"):
                    self.contenedor_resultados = ui.column().classes(
                        "w-full panel-tarjeta p-6 items-center justify-center min-h-[400px]"
                    ).props('id="resultados-transformaciones"')
                    self._restablecer_resultados()

    def _crear_accion_principal(self):
        """Construye crear accion principal conservando el orden de los elementos."""
        with ui.row().classes("w-full mt-6 gap-4"):
            crear_boton_limpieza(self, lambda: not self.contenedor_resultados.is_deleted)
            ui.button(
                "Analizar", icon="analytics",
                on_click=lambda evento: self._analizar(evento.sender),
                color=None,
            ).classes("boton-principal flex-[2] py-3").props("ripple=false")

    def _campos_captura(self):
        return [entrada for fila in self.entradas_coeficientes for entrada in fila] + self.entradas_variables


    def obtener_contexto_ia(self):
        """Devuelve None porque esta vista todavía no proporciona contexto al asistente."""
        return None

    def obtener_senales_ia(self):
        """Devuelve None porque esta vista todavía no proporciona señales al asistente."""
        return None
