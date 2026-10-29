"""Coordinacion del calculo y estados de la matriz inversa."""
from __future__ import annotations

import json
from nicegui import run, ui
from src.frontend.controladores.sesion_matricial import invalidar_resultado, actualizar_contexto, notificar_edicion, captura_sigue_vigente, calculo_sigue_vigente

from src.frontend.controladores.operaciones_inversas import (
    ControladorOperacionesInversas,
)
from src.frontend.controladores.operaciones_inversas.presentacion import preparar_opciones_inversa
from src.ai.huellas import calcular_huella
from src.frontend.vistas.operaciones_inversas._tarjeta_inversa import (
    renderizar_resultado_inversa,
)
from ._vista_previa_inversa import actualizar_vista_previa



class MixinResultadosOperacionesInversas:
    """Maneja el vista previa en vivo, resolución y presentación de la matriz inversa y verificaciones."""

    async def _actualizar_vista_previa(self):
        """Genera y renderiza la vista previa de la matriz en MathJax."""
        await actualizar_vista_previa(self)

    def restablecer_resultados(self):
        """Restaura el estado inicial y estado vacio de la tarjeta de resultados."""
        if not self.contenedor_resultados:
            return
        invalidar_resultado(self)
        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(remove='sesion-obsoleta')
        self.contenedor_resultados.classes(
            remove='items-start justify-start',
            add='items-center justify-center',
        )
        with self.contenedor_resultados:
            ui.icon('flip', size='4rem').classes('texto-marcador mb-4')
            ui.label('Listo para invertir').classes('text-xl font-bold texto-principal')
            ui.label(
                'Ingresa una matriz cuadrada y presiona Calcular inversa'
            ).classes('text-sm texto-secundario mt-2 text-center')

    def _al_cambiar_matriz(self):
        """Actualiza la vista previa y el contexto al editar o redimensionar la matriz."""
        notificar_edicion(self)
        self._programar_vista_previa()
        if self.ultimo_resultado is not None and self.contenedor_resultados:
            self.contenedor_resultados.classes(add='sesion-obsoleta')
            aviso = getattr(self, '_aviso_resultado_obsoleto', None)
            if aviso is None or aviso.is_deleted:
                with self.contenedor_resultados:
                    self._aviso_resultado_obsoleto = ui.label(
                        'Resultado anterior. Los datos cambiaron; pulsa Calcular inversa para actualizarlo.'
                    ).classes('texto-advertencia text-sm').props('role="status"')
        actualizar_contexto(self)

    def limpiar_todo(self) -> None:
        """Limpia la matriz, invalida resultado y huella, y actualiza el contexto."""
        invalidar_resultado(self)
        self.panel_matriz_cuadrada.limpiar()
        self.restablecer_resultados()
        if getattr(self, 'panel_ia', None):
            self.panel_ia.limpiar_foco_explicacion()
        actualizar_contexto(self)

    def _mostrar_aviso_matriz_vacia(self) -> None:
        """Notifica que la matriz está vacía antes de calcular."""
        self.contenedor_resultados.clear()
        self.contenedor_resultados.style('opacity: 1;')
        self.contenedor_resultados.classes(
            remove='items-center justify-center', add='items-start justify-start'
        )
        with (
            self.contenedor_resultados,
            ui.row().classes('items-center gap-2 px-4 py-2 distintivo-advertencia mb-4 w-fit'),
        ):
            ui.icon('warning', size='sm')
            ui.label('Ingresa al menos un valor antes de calcular.').classes('font-bold')

    async def _confirmar_calculo_grande(self, dimension: int) -> bool:
        """Muestra diálogo de confirmación si la dimensión es grande."""
        with ui.dialog().props(':transition-duration="window.scalaris.movimiento.duracion(\'--dur-view\')"') as dialogo, ui.card().classes('panel-tarjeta no-shadow p-6 sesion-dialogo'):
            ui.label('Confirmar cálculo').classes('text-xl font-bold mb-3')
            ui.label(
                f'Una dimensión n={dimension} ({dimension}×{dimension}) puede tardar unos segundos y consumir bastante memoria. '
                f'¿Deseas continuar?'
            ).classes('text-sm texto-secundario mb-6')
            with ui.row().classes('w-full justify-end gap-3'):
                ui.button('Cancelar', on_click=lambda: dialogo.submit(False), color=None).classes('boton-discreto px-4').props('ripple=false')
                ui.button('Continuar', on_click=lambda: dialogo.submit(True), color=None).classes('boton-principal px-4').props('ripple=false')
        return bool(await dialogo)

    def _mostrar_carga_calculo(self, dimension: int) -> None:
        """Renderiza el estado de carga y mensaje explicativo según n."""
        self.contenedor_resultados.clear()
        self.contenedor_resultados.style('opacity: 1;')
        self.contenedor_resultados.classes(
            remove='items-start justify-start', add='items-center justify-center'
        )
        with self.contenedor_resultados:
            ui.spinner(size='3rem').classes('texto-acento mb-4')
            mensaje_calculo = 'Calculando inversa...'
            if preparar_opciones_inversa(dimension)['confirmar']:
                mensaje_calculo += ' (matrices grandes pueden tardar)'
            ui.label(mensaje_calculo).classes('texto-secundario font-semibold')

    def _finalizar_exito_calculo(self, resultado: dict, dimension: int) -> None:
        """Actualiza historial, scripts cliente y contexto IA tras cálculo exitoso."""
        if resultado.get("estado") in ("EXITO", "SINGULAR"):
            self._agregar_a_historial({
                'datos': self.panel_matriz_cuadrada.obtener_datos_matriz(),
                'dimension': dimension, 'estado': resultado["estado"],
                'determinante': resultado.get("determinante_texto"),
            })

        ui.run_javascript('if(window.scalaris && window.scalaris.renderizarMathJax) window.scalaris.renderizarMathJax();')
        actualizar_contexto(self)

    async def calcular(self, emisor):
        """Calcula una captura estable y descarta respuestas tras edicion o desmontaje."""
        if self.panel_matriz_cuadrada.esta_vacio():
            self._mostrar_aviso_matriz_vacia()
            return
        dimension = self.panel_matriz_cuadrada.dimension
        if preparar_opciones_inversa(dimension)['confirmar'] and not await self._confirmar_calculo_grande(dimension):
            return
        if not self._puede_actualizar_resultados(emisor):
            return
        invalidar_resultado(self)
        solicitud = self._identificador_calculo
        self._activar_carga(emisor, solicitud)
        dimension = self.panel_matriz_cuadrada.dimension
        self._mostrar_carga_calculo(dimension)
        datos = self.panel_matriz_cuadrada.obtener_datos_matriz()
        huella = calcular_huella({'datos': datos})
        revision = self._revision_captura
        try:
            carga = json.dumps({'dimension': dimension, 'datos': datos})
            resultado = await run.io_bound(ControladorOperacionesInversas.procesar_inversa, carga)
            if self.contenedor_resultados.is_deleted:
                return
            if not calculo_sigue_vigente(self, solicitud):
                return
            if not captura_sigue_vigente(self, revision, huella, {'datos': self.panel_matriz_cuadrada.obtener_datos_matriz()}):
                self.contenedor_resultados.clear()
                with self.contenedor_resultados:
                    ui.label('Los datos cambiaron. Presiona Calcular inversa de nuevo.').classes('texto-secundario')
                return
            self.ultimo_resultado = resultado
            self._huella_resultado = huella
            self.contenedor_resultados.classes(remove='sesion-obsoleta')
            renderizar_resultado_inversa(self, resultado)
            self._finalizar_exito_calculo(resultado, dimension)
        except Exception as error:
            if calculo_sigue_vigente(self, solicitud):
                self._mostrar_error_inesperado(error)
        finally:
            self._finalizar_carga(emisor, solicitud)
