"""Captura y composición de la vista del modelo insumo-producto de Leontief."""

from nicegui import ui
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from .limpieza_modelos import MixinLimpiezaModelos
from ._estados_modelos import mostrar_estado

from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.iconos import icono_svg
from src.frontend.navegacion import ruta_de
from src.frontend.componentes.captura_matrices import PanelCapturaMatrices
from .mixin_calculo_leontief import MixinCalculoLeontief


from .mixin_captura_leontief import MixinCapturaLeontief
from .mixin_ejemplos_leontief import MixinEjemplosLeontief


class VistaLeontief(MixinLimpiezaModelos, MixinCalculoLeontief, MixinCapturaLeontief, MixinEjemplosLeontief):
    """Vista completa del Modelo de Leontief."""

    def __init__(self):
        self.numero_sectores = 2
        self.entradas_coeficientes: list[list] = []
        self.entradas_demanda: list = []
        self.entradas_sectores: list = []
        self.contenedor_coeficientes = None
        self.contenedor_resultados = None
        self.ultimo_resultado = None

    def construir(self):
        """Monta captura, ejemplos y resultados del modelo económico."""
        PanelCapturaMatrices.inyectar_recursos_cliente()
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("leontief"))

        with ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 vista-raiz"):
            with ui.row().classes("w-full items-center gap-3 mb-6"):
                ui.html(icono_svg("matriz_inversa")).classes("w-8 h-8 texto-acento")
                with ui.column().classes("gap-0"):
                    ui.label("Modelo de Leontief").classes("text-2xl font-bold texto-principal")
                    ui.label("Insumo-Producto · x = (I - C)^(-1) d").classes("text-sm texto-secundario")

            with ui.element("div").classes("disposicion-dividida mb-8"):
                with ui.column().classes("disposicion-panel"):
                    self._construir_ejemplos()
                    self._construir_selector_tamano()
                    self._construir_panel_c()
                    self._construir_panel_d()
                    self._construir_panel_sectores()

                    self._crear_accion_principal()

                with ui.column().classes("disposicion-panel"):
                    self.contenedor_resultados = ui.column().classes(
                        "w-full panel-tarjeta p-6 items-center justify-center min-h-[400px]"
                    ).props('id="resultados-leontief"')
                    self._restablecer_resultados()

    def _crear_accion_principal(self):
        """Construye crear accion principal conservando el orden de los elementos."""
        with ui.row().classes("w-full mt-6 gap-4"):
            crear_boton_limpieza(self, lambda: not self.contenedor_resultados.is_deleted, self._campos_captura)
            ui.button(
                "Calcular", icon="calculate",
                on_click=lambda evento: self._calcular(evento.sender),
                color=None
            ).classes("boton-principal flex-[2] py-3").props("ripple=false")

    def _campos_captura(self):
        return [entrada for fila in self.entradas_coeficientes for entrada in fila] + self.entradas_demanda + self.entradas_sectores

    def _restablecer_resultados(self):
        self.ultimo_resultado = None
        mostrar_estado(self.contenedor_resultados, "Ingresa la matriz C y el vector d, luego presiona Calcular.")

    def obtener_contexto_ia(self):
        """Indica que esta vista no publica contexto del asistente."""
        return None

    def obtener_senales_ia(self):
        """Indica que esta vista no solicita sugerencias automáticas."""
        return None
