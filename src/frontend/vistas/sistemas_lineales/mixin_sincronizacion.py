"""Coordinacion de los controles de captura de sistemas lineales."""
from nicegui import ui
from functools import partial
from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS, DIMENSION_MINIMA
from src.frontend.componentes.cuadricula_base import ejecutar_transicion_cuadricula, selectores_cambio_dimension, actualizar_estados_botones_dimension
from src.frontend.controladores.sesion_matricial import actualizar_contexto, notificar_edicion
from src.frontend.controladores.sistemas_lineales.estado_captura import cambiar_numero_ecuaciones, matriz_vacia, ecuaciones_vacias
from src.frontend.controladores.sistemas_lineales.captura import preparar_captura_ecuaciones


class MixinSincronizacionSistemasLineales:
    """Maneja la lista de ecuaciones, su sincronización con la matriz y verificación de estado vacío."""

    def agregar_ecuacion(self):
        """Solicita agregar una ecuacion dentro de los limites del dominio."""
        cambiar_numero_ecuaciones(self, 1)

    def eliminar_ecuacion(self):
        """Solicita quitar la ultima ecuacion sin vaciar la lista."""
        cambiar_numero_ecuaciones(self, -1)

    async def _cambiar_ecuaciones_animadas(self, incremento: int):
        indice = self.num_ecuaciones if incremento > 0 else self.num_ecuaciones - 1
        selector = f"#{self.contenedor_ecuaciones_lista.html_id} input[data-ecuaciones-indice='{indice}']"
        await ejecutar_transicion_cuadricula(
            vars(self), selectores_cambio_dimension(selector, incremento),
            partial(cambiar_numero_ecuaciones, self, incremento),
            (self.boton_quitar_ecuacion, self.boton_agregar_ecuacion), self._actualizar_botones_ecuaciones,
        )

    def _actualizar_botones_ecuaciones(self):
        actualizar_estados_botones_dimension(getattr(self, 'boton_quitar_ecuacion', None), getattr(self, 'boton_agregar_ecuacion', None),
                                            self.num_ecuaciones, DIMENSION_MINIMA, DIMENSION_MAXIMA_SISTEMAS)

    def _al_cambiar_ecuaciones(self, evento=None):
        """Actualiza el estado de captura y contexto al editar una ecuacion."""
        notificar_edicion(self)
        self.actualizar_botones_sincronizacion()
        self._programar_vista_previa()
        actualizar_contexto(self)

    def renderizar_ecuaciones(self):
        """Reconstruye las ecuaciones editables conservando sus valores."""
        valores_guardados = [entrada.value for entrada in self.entradas_ecuaciones]
        self._reconstruir_ecuaciones(valores_guardados)
        if getattr(self, 'contenedor_vista_previa', None):
            self._programar_vista_previa()

    def sincronizar_desde_matriz(self):
        """Convierte la matriz capturada en ecuaciones y actualiza la captura."""
        ecuaciones = self.cuadricula.exportar_a_ecuaciones(conservar_forma=True)
        self.num_ecuaciones = max(len(ecuaciones), 1)

        self._reconstruir_ecuaciones(ecuaciones)

        self.actualizar_botones_sincronizacion()
        if getattr(self, 'contenedor_vista_previa', None):
            self._programar_vista_previa()
        ui.notify('Sincronizado desde Matriz', type='positive', position='top')

    def _reconstruir_ecuaciones(self, valores):
        """Reconstruye las entradas de ecuaciones conservando sus valores y eventos."""
        if not self.contenedor_ecuaciones_lista:
            return
        self.contenedor_ecuaciones_lista.clear()
        self.entradas_ecuaciones.clear()
        with self.contenedor_ecuaciones_lista:
            for i in range(self.num_ecuaciones):
                valor = valores[i] if i < len(valores) else ''
                self._crear_entrada_ecuacion(i, valor)
        self._actualizar_botones_ecuaciones()

    def _crear_entrada_ecuacion(self, i, valor):
        """Crea una ecuación numerada y registra el control para sincronizarla."""
        with ui.row().classes('w-full items-center gap-3 no-wrap mb-3'):
            ui.label(f'{i+1}.').classes('font-bold texto-secundario w-6 text-right shrink-0')
            entrada = ui.input(
                value=valor,
                placeholder=f'Ej. 2x + 3y = {i*2 + 4}',
                on_change=self._al_cambiar_ecuaciones
            ).classes('matriz-entrada flex-1 min-w-0').props(f'borderless autocomplete="new-password" name="eq{i}" data-ecuaciones-indice="{i}"')
            self.entradas_ecuaciones.append(entrada)

    def sincronizar_desde_ecuaciones(self):
        """Analiza las ecuaciones y carga la matriz, o informa del error de entrada."""
        lineas = [entrada.value or "" for entrada in self.entradas_ecuaciones]
        resultado = preparar_captura_ecuaciones(lineas)
        if resultado["estado"] == "ERROR":
            ui.notify(f'Error al sincronizar: {resultado["mensaje"]}', type='negative', position='top')
            return

        self.cuadricula.cargar_datos(resultado["matriz_a"], resultado["vector_b"])
        ui.notify('Sincronizado desde Ecuaciones', type='positive', position='top')

    def esta_matriz_vacia(self):
        """Consulta al controlador si la matriz contiene valores significativos."""
        return matriz_vacia(self)

    def estan_ecuaciones_vacias(self):
        """Consulta al controlador si las ecuaciones contienen texto significativo."""
        return ecuaciones_vacias(self)

    def esta_vacio(self):
        """Devuelve si la captura activa carece de valores distintos de cero."""
        if self.pestanas_modo.value == 'Matriz':
            return self.esta_matriz_vacia()
        else:
            return self.estan_ecuaciones_vacias()

    def esta_completamente_vacio(self):
        """Consulta si la captura activa carece de texto incluso de ceros escritos."""
        if self.pestanas_modo.value == 'Matriz':
            return self.cuadricula.esta_completamente_vacio()
        return ecuaciones_vacias(self, False)

    def actualizar_botones_sincronizacion(self, _=None):
        """Muestra los botones de sincronización según los datos capturados."""
        if hasattr(self, 'boton_desde_ecuaciones') and self.boton_desde_ecuaciones:
            self.boton_desde_ecuaciones.set_visibility(not self.estan_ecuaciones_vacias())
        if hasattr(self, 'boton_desde_matriz') and self.boton_desde_matriz:
            self.boton_desde_matriz.set_visibility(not self.esta_matriz_vacia())

    def _al_cambiar_cuadricula(self):
        """Actualiza el estado de captura y contexto al editar una celda."""
        casilla = getattr(self, "casilla_homogeneo", None)
        if casilla is not None and casilla.value != self.cuadricula.modo_homogeneo:
            casilla.set_value(self.cuadricula.modo_homogeneo)
        notificar_edicion(self)
        self._programar_vista_previa()
        self.actualizar_botones_sincronizacion()
        actualizar_contexto(self)
