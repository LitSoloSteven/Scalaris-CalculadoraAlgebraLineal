"""Presentación accesible de estados vacíos, carga y errores de geometría."""
from __future__ import annotations

import json
from nicegui import ui
from src.frontend.controladores.geometria import selector_celda_error

MENSAJES_ENTRADA = {
    'rectas-planos': 'Escribe al menos una ecuación o carga un sistema desde Sistemas de ecuaciones',
    'vectores': 'Ingresa dos vectores para visualizar la suma y el escalamiento',
    'combinacion': 'Ingresa b y los vectores columna para ver la combinación lineal',
}


def _limpiar_contenedores(vista) -> None:
    for contenedor in (vista.contenedor_figura, vista.contenedor_deslizador, vista.contenedor_resumen):
        if contenedor:
            contenedor.clear()


def mostrar_estado_vacio(vista) -> None:
    """Muestra la orientación inicial correspondiente a la escena activa."""
    vista._ejecutar_js('window.scalaris?.geometria?.marcarInvalido(null);')
    _limpiar_contenedores(vista)
    if vista.contenedor_estado:
        vista.contenedor_estado.clear()
    if vista.contenedor_figura:
        with vista.contenedor_figura:
            _construir_mensaje_vacio(vista.escena)


def _construir_mensaje_vacio(escena: str):
    with ui.column().classes('geometria-vacio justify-center items-center text-center py-12').props('role=status'):
        ui.icon('insights', size='4rem').classes('text-placeholder mb-4').props('aria-hidden=true')
        ui.label(MENSAJES_ENTRADA.get(escena, '')).classes('text-sm text-sec')


def aplicar_estado_carga(vista) -> None:
    """Expone un estado de carga sin reducir la legibilidad de la figura anterior."""
    if not vista.contenedor_figura:
        return
    if vista.contenedor_estado:
        vista.contenedor_estado.clear()
        with vista.contenedor_estado:
            ui.label('Actualizando la figura…').classes('text-sm text-sec').props('role=status aria-live=polite')
    if vista._primer_dibujo:
        vista.contenedor_figura.clear()
        with vista.contenedor_figura:
            ui.skeleton(animation='none').classes('w-full geometria-figura').props('aria-label="Cargando figura"')


def _mostrar_mensaje_error(resultado: dict) -> None:
    advertencia = resultado.get("code") in ("bad_dimension", "not_finite")
    clase = 'badge-warning' if advertencia else 'badge-error'
    with ui.row().classes(f'geometria-resumen items-center gap-2 px-4 py-2 {clase}').props('role=alert'):
        ui.icon('info' if advertencia else 'close', size='sm').props('aria-hidden=true')
        ui.label(resultado.get("message") or 'No se pudo dibujar la figura. Revisa los valores e inténtalo de nuevo.').classes('font-bold')


def _mostrar_accion_celda(vista, celda: dict | None) -> None:
    if not celda:
        return
    columnas = vista.cuadricula.n if vista.cuadricula else 2
    selector = selector_celda_error(celda, escena=vista.escena, n_cuadricula=columnas)
    if not selector:
        return
    valor = json.dumps(selector)
    vista._ejecutar_js(f'window.scalaris?.geometria?.marcarInvalido({valor});')
    ui.button('Ir a la celda', icon='gps_fixed', color=None,
              on_click=lambda: vista._ejecutar_js(f'window.scalaris?.geometria?.enfocarCelda({valor});')).classes(
                  'btn-ghost mt-2 geometria-accion').props('ripple=false')


def renderizar_error(vista, resultado: dict) -> None:
    """Muestra el mensaje y permite enfocar la celda inválida cuando se conoce."""
    vista._clave_figura = None
    vista._elemento_plotly = None
    _limpiar_contenedores(vista)
    if vista.contenedor_estado:
        vista.contenedor_estado.clear()
    if vista.contenedor_figura:
        with vista.contenedor_figura:
            _mostrar_mensaje_error(resultado)
            _mostrar_accion_celda(vista, resultado.get("error_cell"))
