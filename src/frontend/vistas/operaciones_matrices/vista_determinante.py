"""Captura y herramientas de sesión del determinante exacto."""
from nicegui import ui

from src.backend.utilidades.estado_captura import captura_vacia
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from src.frontend.componentes.calculadora import PanelCalculadora
from src.frontend.componentes.selector_opciones import SelectorOpciones
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.panel_matriz_cuadrada import PanelMatrizCuadrada
from src.frontend.controladores.operaciones_matrices.contexto_determinante import obtener_contexto_determinante
from src.frontend.controladores.operaciones_matrices.vista_previa_determinante import preparar_presentacion_determinante
from src.frontend.controladores.sesion_matricial import invalidar_resultado, actualizar_contexto
from src.frontend.navegacion import ruta_de
from src.frontend.vistas.mixin_sesion_matricial import MixinSesionMatricial
from src.frontend.vistas.vista_previa_matricial import actualizar_vista_previa
from src.frontend import textos
from .recomendacion_determinante import RecomendacionDeterminante
from .resultados_determinante import ResultadosDeterminante


class VistaDeterminante(ResultadosDeterminante, MixinSesionMatricial):
    """Compone captura, recomendación y herramientas matriciales compartidas."""

    def __init__(self):
        """Prepara captura y estado explícito de la sesión del cliente."""
        self.panel_matriz = PanelMatrizCuadrada()
        self.calculadora = PanelCalculadora()
        self.recomendacion = RecomendacionDeterminante(self)
        self.ultimo_resultado = None
        self.reproductor_pasos = None
        self._huella_resultado = None
        self._identificador_calculo = 0
        self._revision_captura = 0
        self.contenedor_vista_previa = None
        self.contenedor_historial = None
        self.tarea_vista_previa = None
        self.historial = []

    def construir(self) -> None:
        """Monta captura y pestañas de teclado, vista previa e historial."""
        self._registrar_desmontaje()
        crear_estructura_aplicacion(self, ruta_activa=ruta_de('determinantes'))
        ui.page_title(f'{textos.DETERMINANTES_TITULO} | Scalaris')
        self.panel_matriz.inyectar_recursos_cliente()
        self.calculadora.inyectar_recursos_cliente()
        ui.add_head_html('<link rel="stylesheet" href="/assets/css/vistas_determinantes.css">')
        with (ui.element('div').classes('determinantes-marco w-full'),
              ui.column().classes('vista-raiz sesion-vista sesion-paneles-compartidos determinantes-vista w-full max-w-7xl mx-auto p-6 gap-4')):
            ui.label(textos.DETERMINANTES_TITULO).classes('determinantes-titulo text-2xl font-bold texto-principal')
            ui.label(textos.DETERMINANTES_DESCRIPCION).classes('texto-secundario')
            with ui.element('div').classes('disposicion-dividida'):
                self._construir_captura()
                self._renderizar_columna_herramientas()
            self.contenedor_resultados = ui.column().classes('panel-tarjeta p-6 w-full min-w-0')
            self.resultados = self.contenedor_resultados
            self.panel_matriz.al_cambiar_datos = self._al_cambiar_matriz
        self.panel_ia = PanelIA(self)
        self.panel_ia.construir()
        self._al_cambiar_matriz()

    def _construir_captura(self) -> None:
        with ui.column().classes('disposicion-panel'):
            self.recomendacion.construir()
            self.metodos_determinante = SelectorOpciones(
                textos.OPCIONES_METODOS_DETERMINANTES, 'lu', self._al_cambiar_metodo,
                textos.NOMBRE_SELECTOR_DETERMINANTES)
            self.panel_matriz.construir_contenedor()
            with ui.row().classes('w-full gap-4'):
                crear_boton_limpieza(self, lambda: not self.contenedor_resultados.is_deleted,
                                      lambda: [self.panel_matriz.contenedor_cuadricula])
                ui.button(textos.DETERMINANTES_CALCULAR, on_click=self.calcular, color=None).classes(
                    'boton-principal flex-[2] py-3').props('ripple=false')

    def _al_cambiar_matriz(self) -> None:
        self._invalidar_resultado()
        self._programar_vista_previa()
        self.recomendacion.programar()

    def _al_cambiar_metodo(self) -> None:
        self._invalidar_resultado()
        self.recomendacion.actualizar_eleccion()

    def _invalidar_resultado(self) -> None:
        invalidar_resultado(self)
        if hasattr(self, 'panel_ia'):
            self.panel_ia.limpiar_foco_explicacion()
        actualizar_contexto(self)
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.label(textos.DETERMINANTES_ORIENTACION).props('role=status')

    async def _actualizar_vista_previa(self) -> None:
        """Dibuja la captura en notación de determinante dentro del límite."""
        await actualizar_vista_previa(self, self.panel_matriz, preparar_presentacion_determinante)

    def _restaurar_historial(self, elemento: dict) -> None:
        """Repone matriz y método, retirando el resultado sin calcular otra vez."""
        self.panel_matriz.cargar_matriz(elemento['datos'])
        self.metodos_determinante.set_value(elemento['metodo'])
        self._invalidar_resultado()

    def esta_completamente_vacio(self) -> bool:
        """Consulta texto significativo en la captura cuadrada."""
        return captura_vacia(self.panel_matriz.cache.values(), considerar_cero=False)

    def limpiar_todo(self) -> None:
        """Vacía la matriz, la recomendación y cualquier cálculo vigente."""
        self.panel_matriz.limpiar()

    def _capturar(self) -> dict:
        return {'dimension': self.panel_matriz.dimension, 'datos': self.panel_matriz.obtener_datos_matriz(),
                'metodo': self.metodos_determinante.value}

    def obtener_contexto_ia(self):
        """Devuelve el ejercicio vigente y el método para el asistente contextual."""
        return obtener_contexto_determinante(self)
