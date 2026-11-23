"""Controles de matriz, ecuaciones y parámetros de métodos iterativos."""
from collections.abc import Callable

from nicegui import ui

from src.backend.constantes import MAXIMO_CARACTERES_ECUACIONES
from src.backend.resolutores.sistemas_lineales.iterativos.limites_iterativos import MAXIMO_ITERACIONES_ITERATIVO
from src.frontend.componentes.aplicacion.base.sonido import emitir_sonido
from src.frontend.componentes.captura.ecuaciones.cuadricula_ecuaciones import CuadriculaEcuaciones
from src.frontend.componentes.captura.vectores.captura_vectores import PanelCapturaVectores
from src.frontend.controladores.algebra.sistemas_lineales.nucleo.captura_iterativa import (
    SistemaCapturado, ajustar_variables, interpretar_ecuaciones, redactar_ecuaciones,
)
from src.frontend.controladores.algebra.sistemas_lineales.resolucion.controlador_iterativos import (
    MAXIMO_INICIAL, TOLERANCIA_INICIAL, ejemplo_iterativo,
)
from src.frontend.nucleo.textos.textos_metodos_iterativos import EJEMPLO_CARGADO

_NOMBRE_INICIO = 'x_0'
_OPCIONES_INICIO = {
    'minimo_vectores': 1, 'maximo_vectores': 1, 'permitir_orientacion': False,
    'etiqueta_primer_vector': _NOMBRE_INICIO,
}


def _asignar_inicio(anteriores: list[str], nuevas: list[str], valores: dict[int, str]) -> dict[int, str]:
    if not set(anteriores).intersection(nuevas):
        return {indice: valores.get(indice, '0') for indice in range(len(nuevas))}
    por_variable = {nombre: valores.get(indice, '0') for indice, nombre in enumerate(anteriores)}
    return {indice: por_variable.get(nombre, '0') for indice, nombre in enumerate(nuevas)}


def _localizar_celda_matriz(cuadricula: CuadriculaEcuaciones, campo: str, fila: int | None, columna: int | None):
    if not fila:
        return None
    if campo == 'vector_b':
        return cuadricula.entradas_independientes[fila - 1]
    return cuadricula.entradas_coeficientes[fila - 1][columna - 1] if columna else None


class CapturaIterativa:
    """Monta la captura y sincroniza las dos representaciones sin perder borradores inválidos."""

    def __init__(self, al_editar: Callable[[], None]) -> None:
        self.al_editar = al_editar
        self.cuadricula = CuadriculaEcuaciones(cuadrada=True)
        self.vector = PanelCapturaVectores('iterativos', _OPCIONES_INICIO)
        self.variables = ajustar_variables([], self.cuadricula.columnas)
        self._variables_matriz = self.variables
        self.modo = 'matriz'
        self._sincronizando = False
        self._campo_marcado = None
        self._matriz_sincronizada = None

    def construir(self) -> None:
        """Monta los controles y los vincula a la revisión de la captura."""
        self.cuadricula.inyectar_recursos_cliente()
        self.vector.inyectar_recursos_cliente()
        with ui.tabs(value='matriz').classes('pestanas-controles sistemas-pestanas-modo').props('dense no-caps') as self.selector:
            ui.tab('matriz', label='Matriz', icon='grid_4x4')
            ui.tab('ecuaciones', label='Ecuaciones', icon='functions')
        with ui.column().classes('w-full min-w-0') as self.panel_matriz:
            self.etiqueta_variables = ui.label().classes('iterativos-numero texto-secundario text-sm')
            self.cuadricula.construir_contenedor_cuadricula()
        self.ecuaciones = ui.textarea('Ecuaciones, una por línea', on_change=self._editar_ecuaciones).classes(
            'w-full min-w-0').props(f'outlined maxlength={MAXIMO_CARACTERES_ECUACIONES}')
        self.ecuaciones.set_visibility(False)
        self.aviso = ui.label().classes('iterativos-numero texto-secundario').props('role=status aria-live=polite')
        self.ejemplo = ui.label(EJEMPLO_CARGADO).classes('text-sm texto-secundario').props('role=status')
        self.ejemplo.set_visibility(False)
        self._construir_parametros()
        self.cuadricula.al_cambiar_dimension = self._cambiar_dimension
        self.cuadricula.al_cambiar_datos = self._editar
        self.vector.al_cambiar_datos = self._editar
        self.selector.on_value_change(lambda evento: self.cambiar_modo(evento.value))

    def _construir_parametros(self) -> None:
        with ui.row().classes('iterativos-parametros w-full items-start'):
            with ui.column().classes('gap-1 min-w-0'):
                ui.label('Vector inicial x⁽⁰⁾').classes('font-semibold texto-principal')
                self.vector.construir(ui.column().classes('min-w-0'))
                self.vector.contenedor_cabecera.set_visibility(False)
                self._ajustar_inicio(self.variables, reiniciar=True)
            with ui.column().classes('gap-2 min-w-0 flex-1'):
                self.tolerancia = ui.input('Tolerancia', value=TOLERANCIA_INICIAL, on_change=lambda: self._editar()).classes('w-full').props(
                    'outlined data-solo-numerico=true')
                self.maximo = ui.input('Máximo de iteraciones', value=MAXIMO_INICIAL, on_change=lambda: self._editar()).classes('w-full').props(
                    f'outlined inputmode=numeric hint="De 1 a {MAXIMO_ITERACIONES_ITERATIVO}"')

    def cambiar_modo(self, destino: str) -> None:
        """Convierte la fuente solo si es válida y devuelve el foco lógico al modo anterior si falla."""
        if self._sincronizando or destino == self.modo:
            return
        self._sincronizando = True
        try:
            self._sincronizar_destino(destino)
        except ValueError as error:
            self.selector.set_value(self.modo)
            self.aviso.set_text(str(error))
            emitir_sonido('aviso')
            return
        finally:
            self._sincronizando = False
        self.modo = destino
        self.panel_matriz.set_visibility(destino == 'matriz')
        self.ecuaciones.set_visibility(destino == 'ecuaciones')
        self._editar(conservar_ejemplo=True)

    def _sincronizar_destino(self, destino: str) -> None:
        if destino == 'ecuaciones':
            if self.cuadricula.esta_completamente_vacio():
                return
            sistema = self._obtener_matriz()
            if sistema != self._matriz_sincronizada:
                texto = redactar_ecuaciones(sistema)
                interpretar_ecuaciones(texto)
                self.ecuaciones.set_value(texto)
                self._matriz_sincronizada = sistema
        elif self.ecuaciones.value.strip():
            sistema = interpretar_ecuaciones(self.ecuaciones.value)
            self._cargar_matriz(sistema)
            self._matriz_sincronizada = sistema
        else:
            self._ajustar_inicio(self._variables_matriz)

    def _obtener_matriz(self) -> SistemaCapturado:
        matriz, independientes = self.cuadricula.obtener_datos_matriz()
        return SistemaCapturado(matriz, independientes, self._variables_matriz)

    def _cargar_matriz(self, sistema: SistemaCapturado) -> None:
        self.cuadricula.cargar_datos(sistema.matriz, sistema.independientes)
        self._variables_matriz = sistema.variables
        self._ajustar_inicio(sistema.variables)
        nombres = ', '.join(sistema.variables)
        self.etiqueta_variables.set_text(f'Incógnitas por columna: {nombres}')

    def _cambiar_dimension(self, _filas: int, columnas: int) -> None:
        if not self._sincronizando:
            self._variables_matriz = ajustar_variables(self.variables, columnas)
            self._ajustar_inicio(self._variables_matriz)
            self.etiqueta_variables.set_text(f'Incógnitas por columna: {", ".join(self.variables)}')

    def _editar_ecuaciones(self) -> None:
        if self._sincronizando:
            return
        self._editar()
        try:
            sistema = interpretar_ecuaciones(self.ecuaciones.value)
        except ValueError as error:
            if self.ecuaciones.value.strip():
                self.aviso.set_text(str(error))
            return
        self._ajustar_inicio(sistema.variables)

    def _ajustar_inicio(self, variables: list[str], *, reiniciar: bool = False) -> None:
        if variables == self.variables and not reiniciar:
            return
        vector = self.vector.vectores[_NOMBRE_INICIO]
        valores = vector['celdas'] if not reiniciar else {}
        vector['celdas'] = _asignar_inicio(self.variables, variables, valores)
        self.variables = variables
        self.vector.dimension = len(variables)
        self.vector.renderizar_cuadricula_vector(_NOMBRE_INICIO)
        for campo, variable in zip(self._campos_vector(), variables):
            campo.props(f'aria-label="Valor inicial de {variable}"')

    def _campos_vector(self) -> list[ui.input]:
        contenedor = self.vector.vectores[_NOMBRE_INICIO]['contenedor']
        return [campo for campo in contenedor.descendants() if isinstance(campo, ui.input)]

    def _editar(self, *, conservar_ejemplo: bool = False) -> None:
        if self._sincronizando:
            return
        self.marcar_diagnostico(None)
        self.aviso.set_text('')
        if not conservar_ejemplo:
            self.ejemplo.set_visibility(False)
        self.al_editar()

    def restablecer(self, con_ejemplo: bool = False) -> None:
        """Limpia ambos borradores o carga el ejemplo y restablece los parámetros."""
        self._sincronizando = True
        try:
            if con_ejemplo:
                sistema = ejemplo_iterativo()
                self._cargar_matriz(sistema)
                self.ecuaciones.set_value(redactar_ecuaciones(sistema))
                self._matriz_sincronizada = sistema
            else:
                if self.cuadricula.columnas != len(self.variables):
                    dimension = len(self.variables)
                    self._cargar_matriz(SistemaCapturado([[''] * dimension for _ in self.variables], [''] * dimension, self.variables))
                self.cuadricula.limpiar()
                self.ecuaciones.set_value('')
                self._matriz_sincronizada = None
                self._variables_matriz = self.variables
                self.etiqueta_variables.set_text(f'Incógnitas por columna: {", ".join(self.variables)}')
            self._ajustar_inicio(self.variables, reiniciar=True)
            self.tolerancia.set_value(TOLERANCIA_INICIAL)
            self.maximo.set_value(MAXIMO_INICIAL)
        finally:
            self._sincronizando = False
        self._editar()
        self.ejemplo.set_visibility(con_ejemplo)

    def obtener(self) -> dict:
        """Devuelve los valores crudos vigentes, incluido cualquier parámetro vacío."""
        sistema = self._obtener_matriz()
        celdas = self.vector.vectores[_NOMBRE_INICIO]['celdas']
        return {
            'modo': self.modo, 'matriz_a': sistema.matriz, 'vector_b': sistema.independientes,
            'variables': sistema.variables, 'matriz_vacia': self.cuadricula.esta_completamente_vacio(),
            'ecuaciones': self.ecuaciones.value, 'tolerancia': self.tolerancia.value,
            'maximo_iteraciones': self.maximo.value,
            'vector_inicial': [celdas.get(indice, '') for indice in range(len(self.variables))],
        }

    def marcar_diagnostico(self, diagnostico: dict | None) -> None:
        """Señala el control afectado y mantiene los datos disponibles para editarlos."""
        if self._campo_marcado is not None and not self._campo_marcado.is_deleted:
            self._campo_marcado.props(remove='error aria-invalid')
        self._campo_marcado = self._localizar_campo(diagnostico) if diagnostico else None
        if self._campo_marcado is not None:
            self._campo_marcado.props('error aria-invalid=true')

    def _localizar_campo(self, diagnostico: dict):
        campo = diagnostico['campo']
        fila, columna = diagnostico['fila'], diagnostico['columna']
        if campo in ('ecuaciones', 'matriz_a', 'vector_b') and self.modo == 'ecuaciones':
            if fila and columna:
                self.aviso.set_text(f'Ecuación {fila}, incógnita {self.variables[columna - 1]}.')
            return self.ecuaciones
        if campo in ('matriz_a', 'vector_b'):
            return _localizar_celda_matriz(self.cuadricula, campo, fila, columna)
        if campo == 'vector_inicial' and fila:
            return self._campos_vector()[fila - 1]
        return {'tolerancia': self.tolerancia, 'maximo_iteraciones': self.maximo}.get(campo)
