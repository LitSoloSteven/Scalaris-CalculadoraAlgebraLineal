"""Presentacion de resultados y estados de sistemas lineales."""

from nicegui import ui
from src.frontend.controladores.sistemas_lineales.presentacion_solucion import formatear_elemento_solucion
from src.frontend.controladores.sesion_matricial import invalidar_resultado, actualizar_contexto, calculo_sigue_vigente

from src.frontend.controladores.sistemas_lineales.captura import preparar_captura_ecuaciones
from src.frontend.controladores.sistemas_lineales.estado_captura import modo_homogeneo_activo
from src.frontend.componentes.presentacion_analisis import mostrar_resumen_analisis
from .mixin_resolucion import MixinResolucionSistemas



class MixinResultadosSistemasLineales(MixinResolucionSistemas):
    """Resuelve sistemas lineales y presenta sus resultados y procedimientos."""

    def limpiar_todo(self) -> None:
        """Limpia la captura y retira el resultado y su contexto anterior."""
        invalidar_resultado(self)
        self.cuadricula.limpiar()
        for entrada in self.entradas_ecuaciones:
            entrada.value = ''
        self.restablecer_resultados()
        actualizar_contexto(self)

    def restablecer_resultados(self):
        """Limpia el resultado anterior y presenta el estado inicial de la herramienta."""
        invalidar_resultado(self)
        if getattr(self, "panel_ia", None):
            self.panel_ia.limpiar_foco_explicacion()
        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(remove='items-start justify-start', add='items-center justify-center')
        with self.contenedor_resultados:
            ui.icon('calculate', size='4rem').classes('texto-marcador mb-4')
            ui.label('Listo para resolver').classes('text-xl font-bold texto-principal')
            ui.label('Ingresa las ecuaciones o la matriz y presiona Resolver').classes('text-sm texto-secundario mt-2 text-center')

    async def resolver_sistema(self, emisor):
        """Gestiona la carga, el resultado y los errores del sistema capturado."""
        if self.esta_completamente_vacio():
            self.restablecer_resultados()
            with self.contenedor_resultados:
                self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
                with ui.row().classes('items-center gap-2 px-4 py-2 distintivo-advertencia mb-4 w-fit'):
                    ui.icon('warning_amber', size='sm')
                    ui.label('Ingresa al menos un valor antes de resolver').classes('font-bold')
            return

        boton = emisor
        solicitud = getattr(self, '_identificador_calculo', 0) + 1
        self._activar_carga(boton, solicitud)
        try:
            await self._resolver_nucleo()
        except Exception as evento:
            if calculo_sigue_vigente(self, solicitud):
                self._mostrar_error_inesperado(evento)
        finally:
            self._finalizar_carga(boton, solicitud)

    def _obtener_carga(self) -> tuple[dict, list, list, list] | None:
        """Extrae y valida los datos de entrada según el modo activo."""
        variables = None
        if self.pestanas_modo.value == 'Matriz':
            valores_coeficientes, valores_independientes = self.cuadricula.obtener_datos_matriz()
            if valores_coeficientes and len(valores_coeficientes) > 0:
                variables = [f"x{j+1}" for j in range(len(valores_coeficientes[0]))]
            else:
                variables = []
        else:
            datos_ecuaciones = self._extraer_ecuaciones_carga()
            if datos_ecuaciones is None:
                return None
            valores_coeficientes, valores_independientes, variables = datos_ecuaciones

        carga = {"matriz_a": valores_coeficientes, "vector_b": valores_independientes, "variables": variables}
        if modo_homogeneo_activo(self):
            carga["homogeneo"] = True
        return carga, valores_coeficientes, valores_independientes, variables

    def _extraer_ecuaciones_carga(self):
        """Analiza ecuaciones escritas y muestra el error del analizador si falla."""
        lineas = [entrada.value or "" for entrada in self.entradas_ecuaciones]
        resultado = preparar_captura_ecuaciones(lineas)
        if resultado["estado"] == "ERROR":
            with self.contenedor_resultados:
                self.contenedor_resultados.classes(remove='items-center justify-center', add='items-start justify-start')
                with ui.row().classes('items-center gap-2 px-4 py-2 distintivo-error mb-4 w-fit'):
                    ui.icon('close', size='sm')
                    ui.label(resultado["mensaje"]).classes('font-bold')
            return None

        return resultado["matriz_a"], resultado["vector_b"], resultado["variables"]

    def _renderizar_elementos_solucion(self, solucion: list, variables: list | None, es_unica: bool) -> None:
        """Presenta las etiquetas y los valores preparados por el controlador."""
        for indice, valor in enumerate(solucion):
            variable = variables[indice] if variables and indice < len(variables) else f"x{indice+1}"
            variable_html, variable_latex, texto_valor = formatear_elemento_solucion(variable, valor)
            if es_unica:
                ui.html(f'{variable_html} = {texto_valor}').classes(
                    'sesion-numero px-4 py-2 panel-tarjeta font-bold matematicas-etiqueta texto-principal min-w-0 max-w-full'
                )
            else:
                ui.html(f'<div class="matematicas-desplazamiento sesion-numero px-4 py-2 panel-tarjeta matematicas-etiqueta texto-principal min-w-0 max-w-full">$$ {variable_latex} = {texto_valor} $$</div>')

    def _renderizar_encabezado_y_solucion(self, respuesta: dict, variables: list | None):
        """Renderiza las insignias de estado y las fichas de solución."""
        estado = respuesta.get("estado")
        if respuesta.get("homogeneo"):
            mostrar_resumen_analisis(respuesta["homogeneo"])
        mensaje_clasificacion = respuesta.get("clasificacion") or respuesta.get("mensaje", "")

        if str(estado).upper() == "ERROR":
            with ui.row().classes('items-center gap-2 px-4 py-2 distintivo-error mb-4 w-fit'):
                ui.icon('close', size='sm')
                ui.label(mensaje_clasificacion).classes('font-bold')
            return

        if estado == "SIN_SOLUCION":
            with ui.row().classes('items-center gap-2 px-4 py-2 distintivo-error mb-4 w-fit'):
                ui.icon('close', size='sm')
                ui.label("Sin solución").classes('font-bold')
            return

        es_unica = (estado == "SOLUCION_UNICA")
        clase_distintivo = 'distintivo-exito' if es_unica else 'distintivo-advertencia'
        nombre_icono = 'check' if es_unica else 'warning_amber'
        texto_corto = "Solución única" if es_unica else "Infinitas soluciones"

        with ui.row().classes('w-full items-center gap-3 mb-4 flex-wrap'):
            with ui.row().classes(f'items-center gap-2 px-4 py-2 {clase_distintivo}'):
                ui.icon(nombre_icono, size='sm')
                ui.label(texto_corto).classes('matematicas-etiqueta')

            if respuesta.get("solucion"):
                self._renderizar_elementos_solucion(respuesta["solucion"], variables, es_unica)

        if getattr(self, 'panel_ia', None):
            self.panel_ia.renderizar_sugerencias_en_linea()

    def cambiar_metodo(self, evento=None) -> None:
        """Invalida el resultado del metodo anterior sin alterar la captura activa."""
        self.restablecer_resultados()
        actualizar_contexto(self)
        ui.run_javascript('window.scalaris.animarCambioMetodo();')
