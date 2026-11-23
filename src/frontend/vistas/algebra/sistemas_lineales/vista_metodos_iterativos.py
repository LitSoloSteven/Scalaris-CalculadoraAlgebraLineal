"""Página de captura, resolución y procedimiento de métodos iterativos."""
import logging

from nicegui import ui

from src.ai.contexto.contexto import ContextoIA, EstadoContexto
from src.frontend.componentes.aplicacion.base.sonido import emitir_sonido
from src.frontend.componentes.aplicacion.controles.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.glosa.panel.panel_ia import PanelIA
from src.frontend.componentes.resultados.acciones.avisos_resultado import MENSAJE_ERROR_INESPERADO
from src.frontend.controladores.algebra.sistemas_lineales.resolucion.controlador_iterativos import resolver_iterativo
from src.frontend.controladores.compartido.sesion.calculo_vigente import ejecutar_calculo_vigente
from src.frontend.controladores.compartido.sesion.sesion_matricial import actualizar_contexto, invalidar_resultado
from src.frontend.navegacion import ruta_de
from src.frontend.nucleo.textos.textos_metodos_iterativos import ESTADO_CALCULO, ESTADO_EDICION, ESTADO_INICIAL
from .captura.captura_iterativa import CapturaIterativa
from .resultados.resultado_iterativo import mostrar_resultado_iterativo

_REGISTRO = logging.getLogger(__name__)
_SONIDOS_RESULTADO = {
    'SOLUCION_EXACTA': 'exito', 'TOLERANCIA_ALCANZADA': 'exito', 'MAXIMO_ITERACIONES': 'aviso',
    'LIMITE_ARITMETICO': 'aviso', 'DIAGONAL_NULA': 'error', 'ENTRADA_INVALIDA': 'error',
}


class VistaMetodosIterativos:
    """Orquesta la sesión de Jacobi y retira resultados obsoletos al editar."""

    def __init__(self) -> None:
        self.captura = CapturaIterativa(self.editar)
        self.reproductor_pasos = None
        self.ultimo_resultado = None
        self._identificador_calculo = 0
        self._huella_resultado = None
        self.panel_ia = PanelIA(self)

    def construir(self) -> None:
        """Monta la navegación, los controles de captura y la región de resultados."""
        crear_estructura_aplicacion(self, ruta_activa=ruta_de('metodos_iterativos'))
        ui.context.client.on_delete(self._cerrar)
        with ui.column().classes('vista-raiz iterativos-raiz w-full max-w-7xl mx-auto mt-4'):
            ui.label('Métodos iterativos').classes('text-2xl font-bold texto-principal').props('role=heading aria-level=1')
            with ui.tabs(value='jacobi').classes('pestanas-controles pestanas-metodo').props('dense no-caps'):
                ui.tab('jacobi', label='Jacobi')
            with ui.element('div').classes('disposicion-dividida'):
                with ui.column().classes('disposicion-panel panel-tarjeta iterativos-panel'):
                    self.captura.construir()
                    self._construir_acciones()
                with ui.column().classes('disposicion-panel panel-tarjeta iterativos-panel'):
                    ui.label('Resultado').classes('text-xl font-semibold texto-principal')
                    self.estado = ui.label(ESTADO_INICIAL).classes('texto-secundario').props('role=status aria-live=polite')
                    self.contenedor_resultados = ui.column().classes('w-full min-w-0')
        self.panel_ia.construir()

    def _construir_acciones(self) -> None:
        with ui.row().classes('w-full items-center flex-wrap'):
            ui.button('Cargar ejemplo', on_click=lambda: self.captura.restablecer(True), color=None).classes(
                'boton-discreto').props('ripple=false')
            ui.button('Limpiar', on_click=lambda: self.captura.restablecer(), color=None).classes(
                'boton-discreto').props('ripple=false')
            self.boton_resolver = ui.button('Resolver', on_click=self.resolver, color=None).classes(
                'boton-principal').props('ripple=false aria-label=Resolver')

    def editar(self) -> None:
        """Invalida el cálculo anterior y devuelve el control para resolver de nuevo."""
        self._retirar_resultado()
        self.boton_resolver.props('loading=false')
        self.estado.set_text(ESTADO_EDICION)
        actualizar_contexto(self)

    async def resolver(self) -> None:
        """Calcula la captura en segundo plano y publica únicamente la solicitud vigente."""
        self._retirar_resultado()
        solicitud = self._identificador_calculo
        self.captura.marcar_diagnostico(None)
        self.estado.set_text(ESTADO_CALCULO)
        self.boton_resolver.props('loading=true')
        actualizar_contexto(self)
        try:
            respuesta = await ejecutar_calculo_vigente(self, self.captura.obtener, resolver_iterativo)
            if respuesta is not None:
                self._publicar(*respuesta)
        except Exception as error:
            _REGISTRO.error('Error en métodos iterativos: %s', type(error).__name__)
            if self._identificador_calculo == solicitud and not self.estado.is_deleted:
                self._retirar_resultado()
                self.estado.set_text(MENSAJE_ERROR_INESPERADO)
                self.boton_resolver.props('loading=false')
                emitir_sonido('error')
        finally:
            if self._identificador_calculo == solicitud and not self.boton_resolver.is_deleted:
                self.boton_resolver.props('loading=false')

    def _publicar(self, resultado: dict, huella: str) -> None:
        self.estado.set_text('')
        self.captura.marcar_diagnostico(resultado.get('diagnostico'))
        with self.contenedor_resultados:
            self.reproductor_pasos = mostrar_resultado_iterativo(resultado)
        self.ultimo_resultado = resultado
        self._huella_resultado = huella
        emitir_sonido(_SONIDOS_RESULTADO[resultado['codigo']])
        actualizar_contexto(self)

    def _retirar_resultado(self) -> None:
        invalidar_resultado(self)
        self.panel_ia.foco_explicacion = None
        self.contenedor_resultados.clear()

    def _cerrar(self) -> None:
        invalidar_resultado(self)
        self.panel_ia.foco_explicacion = None

    def obtener_contexto_ia(self) -> ContextoIA:
        """Entrega a Glosa la captura activa y un resumen del resultado si sigue vigente."""
        captura = self.captura.obtener()
        ecuaciones = captura['modo'] == 'ecuaciones'
        entrada = {'ecuaciones': captura['ecuaciones']} if ecuaciones else {
            'matriz_a': captura['matriz_a'], 'vector_b': captura['vector_b'], 'variables': captura['variables'],
        }
        entrada.update({clave: captura[clave] for clave in ('vector_inicial', 'tolerancia', 'maximo_iteraciones')})
        respuesta = self.ultimo_resultado
        resumen = {clave: respuesta.get(clave) for clave in ('codigo', 'aproximacion', 'norma_residuo')} if respuesta else None
        vacio = not captura['ecuaciones'].strip() if ecuaciones else captura['matriz_vacia']
        return ContextoIA('jacobi', 'Métodos iterativos', 'Jacobi', entrada, EstadoContexto(resultado=resumen, vacio=vacio))
