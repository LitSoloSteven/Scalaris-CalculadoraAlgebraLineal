"""Vista de captura, sesión y resultados de factorización LU."""
from nicegui import ui

from src.frontend import textos
from src.frontend.componentes.calculadora import PanelCalculadora
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.panel_matriz_rectangular import PanelMatrizRectangular
from src.frontend.controladores.operaciones_matrices.vista_previa_factorizacion_lu import preparar_presentacion_factorizacion_lu
from src.frontend.controladores.sesion_matricial import invalidar_resultado, actualizar_contexto
from src.frontend.navegacion import ruta_de
from src.frontend.vistas.mixin_sesion_matricial import MixinSesionMatricial
from src.frontend.vistas.vista_previa_matricial import actualizar_vista_previa
from ._estados_modelos import mostrar_estado
from .mixin_ejemplos_factorizacion_lu import MixinEjemplosFactorizacionLU
from .resultados_factorizacion_lu import ResultadosFactorizacionLU


class VistaFactorizacionLU(ResultadosFactorizacionLU, MixinEjemplosFactorizacionLU, MixinSesionMatricial):
    """Compone una sesión matricial independiente para factorización PA = LU."""

    def __init__(self) -> None:
        self.panel_matriz = PanelMatrizRectangular()
        self.calculadora = PanelCalculadora()
        self.ultimo_resultado = self.reproductor_pasos = self._huella_resultado = None
        self._identificador_calculo = self._revision_captura = 0
        self.contenedor_vista_previa = self.contenedor_historial = self.tarea_vista_previa = None
        self.historial = []

    def construir(self) -> None:
        """Monta captura, herramientas, resultados y el panel de Glosa."""
        self._registrar_desmontaje()
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("factorizacion_lu"))
        ui.page_title(f"{textos.LU_TITULO} | Scalaris")
        self.panel_matriz.inyectar_recursos_cliente()
        self.calculadora.inyectar_recursos_cliente()
        ui.add_head_html('<link rel="stylesheet" href="/assets/css/vistas_factorizacion_lu.css">')
        with (ui.element('div').classes('factorizacion-lu-marco w-full'),
              ui.column().classes('vista-raiz sesion-vista factorizacion-lu-vista w-full max-w-7xl mx-auto p-6 gap-4')):
            ui.label(textos.LU_TITULO).classes('text-2xl font-bold texto-principal')
            ui.label(textos.LU_DESCRIPCION).classes('texto-secundario')
            with ui.element('div').classes('disposicion-dividida'):
                self._construir_captura()
                self._renderizar_columna_herramientas()
            self.contenedor_resultados = ui.column().classes('panel-tarjeta p-6 w-full min-w-0')
            self.panel_matriz.al_cambiar_datos = self._al_cambiar_matriz
        self.panel_ia = PanelIA(self)
        self.panel_ia.construir()
        self._al_cambiar_matriz()

    def _construir_captura(self) -> None:
        with ui.column().classes('disposicion-panel min-w-0'):
            self._construir_ejemplos()
            ui.label(textos.LU_CONVENCION).classes('texto-secundario factorizacion-lu-convencion')
            self.panel_matriz.construir_contenedor()
            with ui.row().classes('w-full gap-4'):
                crear_boton_limpieza(self, lambda: not self.contenedor_resultados.is_deleted,
                                      lambda: [self.panel_matriz.contenedor_cuadricula])
                ui.button(textos.LU_CALCULAR, on_click=self.calcular, color=None).classes(
                    'boton-principal flex-[2] py-3').props('ripple=false')

    def _al_cambiar_matriz(self) -> None:
        invalidar_resultado(self)
        if hasattr(self, 'panel_ia'):
            self.panel_ia.limpiar_foco_explicacion()
        actualizar_contexto(self)
        self._programar_vista_previa()
        self._restablecer_resultados()

    def _restablecer_resultados(self) -> None:
        mostrar_estado(self.contenedor_resultados, textos.LU_ORIENTACION)

    async def _actualizar_vista_previa(self) -> None:
        await actualizar_vista_previa(self, self.panel_matriz, preparar_presentacion_factorizacion_lu)

    def _restaurar_historial(self, elemento: dict) -> None:
        self.panel_matriz.cargar_matriz(elemento['datos'])

    def _capturar(self) -> dict:
        return {'matriz_a': self.panel_matriz.obtener_datos_matriz()}

    def esta_completamente_vacio(self) -> bool:
        """Indica si no hay texto capturado en la matriz."""
        return self.panel_matriz.esta_vacio()

    def limpiar_todo(self) -> None:
        """Vacía la captura e invalida el resultado mediante su observador."""
        self.panel_matriz.limpiar()

    def obtener_contexto_ia(self):
        """Indica que el contexto específico aún no está disponible."""
        return None
