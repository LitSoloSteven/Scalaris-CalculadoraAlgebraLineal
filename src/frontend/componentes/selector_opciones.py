"""Selector exclusivo adaptable con valor enlazable a otros controles NiceGUI."""
from collections.abc import Sequence
from functools import partial

from nicegui import ui
from nicegui.elements.mixins.value_element import ValueElement
from nicegui.events import Handler, ValueChangeEventArguments

OpcionSelector = tuple[str, str, str]
COLUMNAS_COMPACTAS = 2


class SelectorOpciones(ValueElement):
    """Muestra todas las opciones y notifica sus valores sin conocer al consumidor."""

    def __init__(self, opciones: Sequence[OpcionSelector], valor_inicial: str,
                 al_cambiar: Handler, nombre_grupo: str):
        """Recibe valor, etiqueta y nombre accesible; rechaza opciones ambiguas."""
        valores = [opcion[0] for opcion in opciones]
        if not valores or len(set(valores)) != len(valores) or valor_inicial not in valores:
            raise ValueError('El selector necesita valores únicos y una opción inicial válida.')
        self._valores = valores
        self.botones = {}
        ui.add_head_html('<link rel="stylesheet" href="/assets/css/selector_opciones.css">')
        ui.add_head_html('<script src="/assets/js/selector_opciones.js"></script>')
        with ui.element('div').classes('selector-opciones-contenedor'):
            super().__init__(tag='div', value=valor_inicial)
        self.classes('pestanas-controles pestanas-metodo selector-opciones')
        self.props.update({'role': 'radiogroup', 'aria-label': nombre_grupo})
        self._columnas_compactas = min(COLUMNAS_COMPACTAS, len(valores))
        self._indice_seleccionado = valores.index(valor_inicial)
        filas = (len(valores) + self._columnas_compactas - 1) // self._columnas_compactas
        self.props['data-selector-columnas'] = str(self._columnas_compactas)
        self.style(f'--selector-cantidad: {len(valores)}; --selector-columnas-compactas: {self._columnas_compactas}; '
                   f'--selector-filas-compactas: {filas}; '
                   f'--selector-cuadricula-compacta: repeat({self._columnas_compactas}, minmax(0, 1fr));')
        with self:
            ui.element('span').classes('selector-opciones-indicador').props('aria-hidden=true')
            for opcion in opciones:
                self._construir_opcion(opcion)
        self.on_value_change(self._sincronizar_seleccion)
        self._aplicar_seleccion(valor_inicial)
        self.on_value_change(al_cambiar)

    def _construir_opcion(self, opcion: OpcionSelector) -> None:
        valor, etiqueta, nombre_accesible = opcion
        boton = ui.button(etiqueta, on_click=partial(self.set_value, valor), color=None).classes(
            'selector-opciones-opcion'
        ).props('no-caps unelevated ripple=false role=radio')
        boton.props['aria-label'] = nombre_accesible
        boton.on('keydown', js_handler='evento => window.scalaris.selectorOpciones.teclado(evento)')
        boton.on('click', js_handler='evento => window.scalaris.selectorOpciones.activar(evento)')
        self.botones[valor] = boton

    def _sincronizar_seleccion(self, evento: ValueChangeEventArguments) -> None:
        self._aplicar_seleccion(evento.value)

    def _aplicar_seleccion(self, valor: str) -> None:
        indice = self._valores.index(valor)
        self.style(f'--selector-indice-anterior: {self._indice_seleccionado}; '
                   f'--selector-columna-anterior: {self._indice_seleccionado % self._columnas_compactas}; '
                   f'--selector-fila-anterior: {self._indice_seleccionado // self._columnas_compactas}; '
                   f'--selector-indice: {indice}; --selector-columna-compacta: {indice % self._columnas_compactas}; '
                   f'--selector-fila-compacta: {indice // self._columnas_compactas};')
        self._indice_seleccionado = indice
        for nombre, boton in self.botones.items():
            activo = nombre == valor
            boton.props.update({'aria-checked': str(activo).lower(), 'tabindex': '0' if activo else '-1'})

    def asociar_contenido(self, valor: str, contenedor: ui.element) -> ui.element:
        """Enlaza una región nombrada con su opción sin reconstruir su contenido."""
        boton = self.botones[valor]
        contenedor.props.update({'role': 'region', 'aria-labelledby': boton.html_id})
        boton.props['aria-controls'] = contenedor.html_id
        return contenedor.bind_visibility_from(self, 'value', backward=lambda actual: actual == valor)
