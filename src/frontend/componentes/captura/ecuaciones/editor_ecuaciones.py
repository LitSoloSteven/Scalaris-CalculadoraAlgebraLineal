"""Captura de ecuaciones por filas con intercambio de texto multilínea."""
from collections.abc import Callable
from functools import partial

from nicegui import ui

from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS, DIMENSION_MINIMA, MAXIMO_CARACTERES_ECUACIONES
from src.backend.utilidades.captura.estado_captura import ajustar_numero_ecuaciones
from src.frontend.componentes.aplicacion.base.sonido import notificar
from src.frontend.componentes.captura.ecuaciones.filas_ecuaciones import (
    crear_cabecera_ecuaciones, montar_filas_ecuaciones,
)
from src.frontend.componentes.captura.nucleo.cuadricula_base import (
    actualizar_estados_botones_dimension, ejecutar_transicion_cuadricula, selectores_cambio_dimension,
)

_PEGADO_MULTILINEA = r'''evento => {
    const texto = evento.clipboardData?.getData('text/plain') ?? '';
    if (/[\r\n]/.test(texto)) { evento.preventDefault(); emit(texto); }
}'''


class EditorEcuaciones:
    """Monta filas numeradas y permite convertir el borrador a texto para el analizador."""

    def __init__(self, cantidad_inicial: int, al_editar: Callable[[], None]) -> None:
        self._al_editar = al_editar
        self._estado_transicion = {}
        with ui.column().classes('w-full min-w-0') as self.contenedor:
            self._botones = crear_cabecera_ecuaciones(self.cambiar_cantidad)
            self._lista = ui.column().classes('w-full min-w-0')
        self._actualizar_filas([''] * cantidad_inicial)

    @property
    def value(self) -> str:
        """Devuelve el borrador como texto, con un salto de línea entre campos."""
        valores = self._valores()
        return '\n'.join(valores) if any(valores) else ''

    def set_value(self, texto: str) -> None:
        """Reemplaza las filas con un sistema válido en tamaño o vacía las que ya existen."""
        valores = texto.splitlines() if texto else [''] * len(self.entradas)
        if len(valores) > DIMENSION_MAXIMA_SISTEMAS:
            raise ValueError(f'Usa hasta {DIMENSION_MAXIMA_SISTEMAS} ecuaciones.')
        if valores != self._valores():
            self._actualizar_filas(valores)
            self._al_editar()

    async def cambiar_cantidad(self, incremento: int) -> None:
        """Añade un campo vacío o retira el último dentro de los límites de captura."""
        entradas = self.entradas
        cantidad = ajustar_numero_ecuaciones(len(entradas), incremento)
        if cantidad == len(entradas):
            return
        indice = max(cantidad, len(entradas)) - 1
        selector = f"#{self._lista.html_id} input[data-ecuaciones-indice='{indice}']"
        await ejecutar_transicion_cuadricula(
            self._estado_transicion, selectores_cambio_dimension(selector, incremento),
            partial(self._aplicar_cantidad, cantidad, entradas), self._botones, self._actualizar_botones,
        )

    def _aplicar_cantidad(self, cantidad: int, entradas: list[ui.input]) -> None:
        if self.entradas is not entradas or not self.contenedor.visible or self.contenedor.is_deleted:
            return
        valores = self._valores()
        self._actualizar_filas((valores + [''])[:cantidad])
        self._al_editar()

    def _actualizar_filas(self, valores: list[str]) -> None:
        self.entradas = montar_filas_ecuaciones(self._lista, valores, self._al_editar)
        for indice, entrada in enumerate(self.entradas):
            entrada.on('paste', partial(self._pegar_filas, indice), js_handler=_PEGADO_MULTILINEA)
        self._actualizar_botones()

    def _pegar_filas(self, indice: int, evento) -> None:
        if not isinstance(evento.args, str) or not evento.args or evento.sender.is_deleted:
            return
        if len(evento.args) > MAXIMO_CARACTERES_ECUACIONES:
            notificar(f'Usa hasta {MAXIMO_CARACTERES_ECUACIONES} caracteres.', type='warning')
            return
        lineas = evento.args.splitlines()
        fin = indice + len(lineas)
        if fin > DIMENSION_MAXIMA_SISTEMAS:
            notificar(f'Usa hasta {DIMENSION_MAXIMA_SISTEMAS} ecuaciones.', type='warning')
            return
        valores = self._valores()
        valores[indice:fin] = lineas
        self._actualizar_filas(valores)
        self._al_editar()
        self.entradas[fin - 1].run_method('focus')

    def localizar_fila_escrita(self, fila: int | None) -> tuple[int, ui.input] | None:
        """Ubica una fila del sistema analizado entre los campos visibles, incluidos los vacíos."""
        escritas = [(indice, entrada) for indice, entrada in enumerate(self.entradas, 1)
                    if (entrada.value or '').strip()]
        return escritas[fila - 1] if fila is not None and 1 <= fila <= len(escritas) else None

    def _actualizar_botones(self) -> None:
        actualizar_estados_botones_dimension(*self._botones, len(self.entradas), DIMENSION_MINIMA, DIMENSION_MAXIMA_SISTEMAS)

    def _valores(self) -> list[str]:
        return [entrada.value or '' for entrada in self.entradas]
