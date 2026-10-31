"""Diálogo accesible y efímero de datos para la portada del PDF."""
import json
from collections.abc import Callable
from html import escape

from nicegui import ui
from src.frontend import constantes as limites, textos
from src.frontend.controladores.exportacion_pdf.portada import validar_portada

_MAXIMOS = {'nombre': limites.PDF_MAXIMO_NOMBRE, 'docente': limites.PDF_MAXIMO_DOCENTE,
            'grupo': limites.PDF_MAXIMO_GRUPO}


class DialogoPortada:
    """Gestiona campos y errores en memoria hasta cerrar; nunca usa almacenamiento."""

    def __init__(self, generar: Callable, activador: ui.button):
        self.campos = {}
        self.errores = {}
        self.generar = generar
        self.activador = activador
        self.ocupado = False
        with ui.dialog().props('transition-show=none transition-hide=none') as self.dialogo:
            with ui.card().classes('panel-tarjeta pdf-portada'):
                ui.label(textos.PDF_PORTADA_TITULO).classes('text-xl font-bold texto-principal').props('id=pdf-portada-titulo')
                self.dialogo.props('aria-labelledby=pdf-portada-titulo')
                self._crear_campos()
                self.estado = ui.label('').classes('texto-secundario pdf-mensaje').props('role=status aria-live=polite')
                self._crear_acciones()
        self.dialogo.on('hide', self._al_cerrar)

    def _crear_campos(self) -> None:
        for clave, etiqueta in textos.PDF_CAMPOS.items():
            identificador = f'pdf-campo-{clave}'
            error_id = f'pdf-error-{clave}'
            ui.html(f'<label for="{identificador}">{escape(etiqueta)}</label>')
            campo = ui.input(value='').classes('w-full min-w-0').props(
                f'outlined dense autocomplete=off for={identificador} aria-describedby={error_id}')
            campo.props(f'maxlength={_MAXIMOS[clave]}' if clave in _MAXIMOS else 'type=date')
            if clave == 'nombre':
                campo.props('autofocus')
            self.campos[clave] = campo
            self.errores[clave] = ui.label('').classes('pdf-error pdf-mensaje').props(f'id={error_id} role=alert')

    def _crear_acciones(self) -> None:
        with ui.row().classes('w-full justify-end gap-3 flex-wrap'):
            self.cancelar = ui.button(textos.PDF_CANCELAR, on_click=self.dialogo.close, color=None).classes(
                'boton-discreto pdf-control').props('ripple=false')
            self.confirmar = ui.button(textos.PDF_GENERAR, on_click=self.generar, color=None).classes(
                'boton-principal pdf-control').props('ripple=false')

    def abrir(self) -> None:
        """Abre el diálogo vacío y coloca el foco en el primer campo mediante autofocus."""
        self.estado.set_text('')
        self.dialogo.open()

    def validar(self) -> dict | None:
        """Muestra errores debajo de los campos y devuelve datos válidos normalizados."""
        portada, errores = validar_portada({clave: campo.value for clave, campo in self.campos.items()})
        for clave, campo in self.campos.items():
            self.errores[clave].set_text(errores.get(clave, ''))
            campo.props(f'aria-invalid={str(clave in errores).lower()}')
        if errores:
            self._enfocar(f'pdf-campo-{next(iter(errores))}')
            return None
        return portada

    def cargar(self, ocupado: bool) -> None:
        """Bloquea generación duplicada mientras mantiene Escape disponible para cancelar."""
        self.ocupado = ocupado
        self.confirmar.props('loading' if ocupado else 'loading=false')
        self.confirmar.set_enabled(not ocupado)
        for campo in self.campos.values():
            campo.set_enabled(not ocupado)
        if ocupado:
            self.estado.set_text(textos.PDF_CARGANDO)

    def _al_cerrar(self) -> None:
        for campo in self.campos.values():
            campo.set_value('')
        for error in self.errores.values():
            error.set_text('')
        if not self.activador.is_deleted and self.activador.visible:
            self._enfocar(self.activador.html_id)

    def _enfocar(self, identificador: str) -> None:
        ui.run_javascript(f'window.scalaris.capturaPdf.enfocar({json.dumps(identificador)});')
