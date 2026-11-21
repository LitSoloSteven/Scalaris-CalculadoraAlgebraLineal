"""Controles compartidos de limpieza, historial y ciclo de vida matricial."""
import logging

from nicegui import ui
from src.frontend.componentes.avisos_resultado import mostrar_error_inesperado
from src.frontend.componentes.limpieza_captura import LimpiezaCaptura

from src.frontend.controladores.sesion_matricial import (
    actualizar_contexto, cancelar_vista_previa, describir_registro,
    invalidar_resultado, programar_vista_previa, registrar_calculo,
)

registro = logging.getLogger(__name__)


class MixinSesionMatricial:
    """Orquesta los controles comunes usando el estado explicito de cada vista."""

    def _programar_vista_previa(self) -> None:
        """Programa la vista previa cancelable de la captura actual."""
        programar_vista_previa(self)

    def _renderizar_columna_herramientas(self) -> None:
        """Compone teclado, vista previa e historial con los controles de la sesion."""
        with ui.column().classes('disposicion-panel sesion-panel-herramientas'):
            with ui.tabs().classes('pestanas-controles w-full').props('dense no-caps') as self.pestanas_herramientas:
                ui.tab('teclado', label='Teclado')
                ui.tab('vista_previa', label='Vista previa')
                ui.tab('historial', label='Historial')
            self.pestanas_herramientas.on_value_change(
                lambda evento: self._programar_vista_previa() if evento.value == 'vista_previa' else None
            )
            with ui.tab_panels(self.pestanas_herramientas, value='teclado').classes('w-full p-0 bg-transparent'):
                with ui.tab_panel('teclado').classes('p-0 mt-4'):
                    self.calculadora.construir(getattr(self, 'pestanas_modo', None))
                with ui.tab_panel('vista_previa').classes('p-6 panel-tarjeta mt-4 min-h-[300px] items-center'):
                    ui.label('Vista Previa en Vivo').classes('font-bold texto-principal mb-4')
                    self.contenedor_vista_previa = ui.column().classes('w-full items-center justify-center')
                with ui.tab_panel('historial').classes('p-6 panel-tarjeta mt-4 min-h-[300px]'):
                    ui.label('Últimos cálculos de esta sesión').classes('font-bold texto-principal mb-4')
                    self.contenedor_historial = ui.column().classes('w-full')
        self._programar_vista_previa()
        self._renderizar_historial()

    def _registrar_desmontaje(self) -> None:
        """Retira tareas y reproductor al borrar el cliente de la pagina."""
        ui.add_head_html('<link rel="stylesheet" href="/assets/css/vistas_sesion_matricial.css">')
        ui.context.client.on_delete(self._desmontar_sesion)

    def _desmontar_sesion(self) -> None:
        """Cancela recursos de esta vista al desmontar su cliente."""
        cancelar_vista_previa(self)
        invalidar_resultado(self)
        recomendacion = getattr(self, 'recomendacion', None)
        if recomendacion is not None:
            recomendacion.cancelar()

    def _activar_carga(self, emisor, solicitud: int) -> None:
        """Asocia la carga del boton con la solicitud que la inicio."""
        emisor._solicitud_calculo = solicitud
        emisor.props('loading=true')

    def _puede_actualizar_resultados(self, emisor) -> bool:
        """Consulta si el boton y su contenedor siguen montados."""
        return not emisor.is_deleted and not self.contenedor_resultados.is_deleted

    def _finalizar_carga(self, emisor, solicitud: int) -> None:
        """Retira la carga solo si el boton aun pertenece a esta solicitud."""
        if not emisor.is_deleted and getattr(emisor, '_solicitud_calculo', None) == solicitud:
            emisor.props('loading=false')

    async def confirmar_limpieza(self) -> None:
        """Delega la confirmación en el control común de captura."""
        await self._obtener_limpieza().confirmar()

    async def ejecutar_animacion_limpieza(self, dialogo) -> None:
        """Delega el vaciado tolerante a fallos de JavaScript."""
        await self._obtener_limpieza().ejecutar(dialogo)

    def _obtener_limpieza(self) -> LimpiezaCaptura:
        if not hasattr(self, 'control_limpieza'):
            self.control_limpieza = LimpiezaCaptura(
                self, lambda: not self.contenedor_resultados.is_deleted, getattr(self, '_campos_visuales_limpieza', None),
            )
        return self.control_limpieza

    def _construir_boton_limpieza(self) -> None:
        self._obtener_limpieza().construir()

    def _mostrar_error_inesperado(self, error: Exception) -> None:
        """Presenta un error orientativo sin publicar detalles internos ni entradas."""
        registro.error('Error inesperado en la herramienta matricial: %s', type(error).__name__)
        if self.contenedor_resultados.is_deleted:
            return
        invalidar_resultado(self)
        mostrar_error_inesperado(self.contenedor_resultados)
        actualizar_contexto(self)

    def _agregar_a_historial(self, datos: dict) -> None:
        """Registra los datos del calculo y actualiza sus tarjetas."""
        registrar_calculo(self.historial, datos)
        self._renderizar_historial()

    def _renderizar_historial(self) -> None:
        """Dibuja los registros de sesion o la orientacion del historial vacio."""
        contenedor = self.contenedor_historial
        if contenedor is None or contenedor.is_deleted:
            return
        contenedor.clear()
        with contenedor:
            if not self.historial:
                ui.label('No hay cálculos en esta sesión.').classes('texto-secundario italic text-sm mt-4 text-center')
            for datos in self.historial:
                self._renderizar_tarjeta_historial(datos)

    def _renderizar_tarjeta_historial(self, datos: dict) -> None:
        """Compone una tarjeta de historial con sus datos de presentacion."""
        etiquetas = describir_registro(datos)
        with ui.column().classes('panel-tarjeta p-4 w-full mb-3 gap-2 sesion-historial'):
            with ui.row().classes('w-full justify-between items-center'):
                ui.badge(etiquetas['dimensiones'], color=None).classes('distintivo-exito font-mono')
                ui.label(datos['hora']).classes('text-xs texto-secundario')
            ui.label(etiquetas['estado']).classes(f"text-xs font-bold {etiquetas['clase']}")
            if etiquetas['detalle']:
                ui.label(etiquetas['detalle']).classes('text-sm texto-principal sesion-numero')
            ui.button('Restaurar', on_click=lambda evento, elemento=datos: self._restaurar_historial(elemento), color=None).classes('boton-discreto text-xs w-full mt-2').props('ripple=false')
