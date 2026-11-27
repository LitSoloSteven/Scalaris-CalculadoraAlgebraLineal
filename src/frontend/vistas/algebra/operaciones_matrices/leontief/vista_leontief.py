"""Captura y composición de la vista del modelo insumo-producto de Leontief."""

from nicegui import ui
from src.frontend.componentes.captura.ecuaciones.limpieza_captura import crear_boton_limpieza
from src.frontend.vistas.algebra.operaciones_matrices.compartido.limpieza_modelos import MixinLimpiezaModelos
from src.frontend.vistas.algebra.operaciones_matrices.compartido._estados_modelos import mostrar_estado

from src.frontend.componentes.aplicacion.controles.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.aplicacion.base.iconos import icono_svg
from src.frontend.navegacion import herramienta_por_identificador
from src.frontend.componentes.captura.matrices.captura_matrices import PanelCapturaMatrices
from .mixin_calculo_leontief import MixinCalculoLeontief


from .mixin_captura_leontief import MixinCapturaLeontief
from .mixin_ejemplos_leontief import MixinEjemplosLeontief
from src.frontend.vistas.algebra.operaciones_matrices.compartido.herramientas.glosa_modelos import MixinGlosaModelos
from src.frontend.vistas.algebra.operaciones_matrices.compartido.herramientas.transferencia_modelos import recibir_matriz_modelo


class VistaLeontief(MixinGlosaModelos, MixinLimpiezaModelos, MixinCalculoLeontief, MixinCapturaLeontief, MixinEjemplosLeontief):
    """Vista completa del Modelo de Leontief."""
    herramienta_modelo = "leontief"

    def __init__(self):
        self.numero_sectores = 2
        self.entradas_coeficientes: list[list] = []
        self.entradas_demanda: list = []
        self.entradas_sectores: list = []
        self.contenedor_coeficientes = None
        self.contenedor_resultados = None
        self.ultimo_resultado = None

    def construir(self, token_transferencia: str = ''):
        """Monta captura, ejemplos y resultados del modelo económico."""
        PanelCapturaMatrices.inyectar_recursos_cliente()
        herramienta = herramienta_por_identificador(self.herramienta_modelo)
        crear_estructura_aplicacion(self, ruta_activa=herramienta.ruta)

        with ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 vista-raiz disposicion-herramienta"):
            self.contenedor_transferencia = ui.column().classes('w-full empty:hidden')
            with ui.row().classes("w-full items-center gap-3 mb-2"):
                ui.html(icono_svg(herramienta.icono)).classes("w-8 h-8 texto-acento")
                with ui.column().classes("gap-0"):
                    ui.label("Modelo de Leontief").classes("text-2xl font-bold texto-principal").props('role="heading" aria-level="1"')
                    ui.label("Insumo-Producto · x = (I - C)^(-1) d").classes("text-sm texto-secundario")

            with ui.element("div").classes("disposicion-captura-fila mb-2"):
                with ui.column().classes("disposicion-panel gap-4"):
                    self._construir_ejemplos()
                    self._construir_selector_tamano()
                    self._construir_panel_c()
                    self._crear_accion_principal()

                with ui.column().classes("disposicion-panel gap-4"):
                    self._construir_panel_d()
                    self._construir_panel_sectores()
                    self.contenedor_herramientas = ui.column().classes("w-full min-w-0 gap-3")

            self.contenedor_resultados = ui.column().classes(
                "disposicion-resultados panel-tarjeta p-6 items-center justify-center min-h-[280px]"
            ).props('id="resultados-leontief"')
            self._restablecer_resultados()
        self._conectar_modelo()
        recibir_matriz_modelo(self, token_transferencia)

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
        self._sincronizar_captura_modelo()
        mostrar_estado(self.contenedor_resultados, "Ingresa la matriz C y el vector d, luego presiona Calcular.")
