"""Resolución delegada y acciones sobre el resultado de un sistema lineal."""
import json

from nicegui import run, ui

from src.ai.huellas import calcular_huella
from src.frontend.controladores.sistemas_lineales.flujo_vista import entrada_actual, procesar_carga_sistema
from src.frontend.controladores.sistemas_lineales.estado_captura import opciones_transferencia
from src.frontend.controladores.sesion_matricial import actualizar_contexto, invalidar_resultado, captura_sigue_vigente, calculo_sigue_vigente
from src.frontend.componentes.transferencia import guardar_matriz, guardar_sistema, url_transferencia
from src.frontend.navegacion import ruta_de


class MixinResolucionSistemas:
    """Coordina cálculo y transferencias a partir de datos capturados por la vista."""

    async def _resolver_nucleo(self):
        """Delega el calculo a un trabajador y publica solo una captura vigente."""
        invalidar_resultado(self)
        solicitud = self._identificador_calculo
        self.contenedor_resultados.clear()
        datos_entrada = self._obtener_carga()
        if datos_entrada is None:
            return
        carga, coeficientes, independientes, variables = datos_entrada
        entrada = entrada_actual(self)
        huella = calcular_huella(entrada)
        revision = self._revision_captura
        respuesta = json.loads(await run.io_bound(procesar_carga_sistema, json.dumps(carga), entrada['metodo']))
        if self.contenedor_resultados.is_deleted:
            return
        if not calculo_sigue_vigente(self, solicitud):
            return
        if not captura_sigue_vigente(self, revision, huella, entrada_actual(self)):
            self.contenedor_resultados.clear()
            with self.contenedor_resultados:
                ui.label('Los datos cambiaron. Presiona Resolver de nuevo.').classes('texto-secundario')
            return
        self.ultimo_resultado = respuesta
        self._huella_resultado = huella
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
            self._renderizar_encabezado_y_solucion(respuesta, variables)
            self._renderizar_seccion_pasos(respuesta)
            self._renderizar_botones_accion(respuesta, coeficientes, independientes)
        ui.run_javascript('window.scalaris.renderizarMathJax();')
        actualizar_contexto(self)

    def _renderizar_botones_accion(self, respuesta: dict, coeficientes: list, independientes: list):
        estado = respuesta.get("estado")
        if str(estado).upper() == "ERROR":
            return
        numero_variables = len(coeficientes[0]) if coeficientes else 0
        self._agregar_a_historial({'matriz_a': coeficientes, 'vector_b': independientes, 'filas': len(coeficientes), 'columnas': numero_variables, 'estado': estado, 'metodo': self.pestanas_metodo.value})
        with ui.row().classes('gap-2 mt-4 flex-wrap'):
            if opciones_transferencia(coeficientes)['inversa']:
                ui.button('Ver A⁻¹ en Matriz inversa', icon='arrow_forward', color=None,
                          on_click=lambda: ui.navigate.to(url_transferencia(ruta_de('inversa'), guardar_matriz('sistemas', coeficientes)))
                          ).classes('boton-discreto').props('ripple=false').tooltip('Misma eliminación de filas, ahora sobre [A | I]')
            if opciones_transferencia(coeficientes)['visualizador']:
                ui.button('Ver en el Visualizador', icon='insights', color=None,
                          on_click=lambda: ui.navigate.to(url_transferencia(ruta_de('visualizador'), guardar_sistema('sistemas', coeficientes, independientes)))
                          ).classes('boton-discreto').props('ripple=false').tooltip('Visualiza el sistema en R² o R³')
