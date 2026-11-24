"""Resumen exacto, aproximación legible y tabla navegable de los barridos."""
from functools import partial

from nicegui import ui

from src.frontend.componentes.exportacion_pdf.montaje.integracion import region_pdf
from src.frontend.controladores.algebra.sistemas_lineales.resolucion.presentacion_iterativa import (
    DECIMALES_INICIALES, presentar_numero_iterativo, presentar_vector_iterativo,
)
from src.frontend.nucleo.textos.textos_metodos_iterativos import (
    CAUSAS_PARADA, NOMBRES_METODOS, PDF_ESTADOS_ITERATIVOS,
)
from .pasos_iterativos import crear_reproductor_iterativo


def _mostrar_bloque_resumen(resultado: dict, decimales: int | None) -> None:
    codigo = resultado['codigo']
    ui.label(CAUSAS_PARADA[codigo]).classes('text-lg font-semibold texto-principal').props('role=status')
    metodo = resultado.get('metodo')
    if metodo in NOMBRES_METODOS:
        ui.label(f'Método: {NOMBRES_METODOS[metodo]}').classes('text-sm font-semibold texto-secundario')
    diagnostico = resultado.get('diagnostico')
    if diagnostico:
        ui.label(diagnostico['mensaje']).classes('iterativos-numero texto-secundario').props('role=alert')
    if resultado.get('aproximacion') is not None:
        _mostrar_resumen(resultado, decimales)
    dominancia = resultado.get('dominancia_estricta')
    if dominancia is not None:
        ui.label(f'Dominancia diagonal estricta: {"sí" if dominancia else "no"}.').classes('text-sm texto-secundario')


def mostrar_resultado_iterativo(
    resultado: dict, *, decimales: int | None = DECIMALES_INICIALES, panel_ia=None, sigue_vigente=None,
):
    """Renderiza el resultado, las regiones PDF y el reproductor si hubo barridos."""
    exportable = resultado.get('codigo') in PDF_ESTADOS_ITERATIVOS
    if exportable:
        with region_pdf('metodos_iterativos-resumen'):
            _mostrar_bloque_resumen(resultado, decimales)
    else:
        _mostrar_bloque_resumen(resultado, decimales)
    if panel_ia is not None:
        panel_ia.renderizar_sugerencias_en_linea()
    if not resultado['pasos']:
        return None
    reproductor = crear_reproductor_iterativo(
        resultado, decimales=decimales, panel_ia=panel_ia, sigue_vigente=sigue_vigente,
    )
    if exportable:
        with region_pdf('metodos_iterativos-tabla'):
            _mostrar_tabla(resultado, reproductor.ir_a, decimales)
    else:
        _mostrar_tabla(resultado, reproductor.ir_a, decimales)
    reproductor.construir()
    return reproductor


def _mostrar_resumen(resultado: dict, decimales: int | None) -> None:
    barridos = len(resultado['pasos'])
    ui.label(f'Barridos completos: {barridos}').classes('texto-secundario')
    for variable, valor in zip(resultado['variables'], resultado['aproximacion']):
        ui.label(_presentar_escalar(variable, valor, decimales)).classes('iterativos-numero texto-principal select-text')
    simbolo = '=' if decimales is None else '≈'
    residuo = presentar_vector_iterativo(resultado['residuo'], decimales)
    ui.label(f'r = b − Ax {simbolo} {residuo}').classes('iterativos-numero texto-principal select-text')
    for etiqueta, valor in (('‖r‖∞', resultado['norma_residuo']), ('Tolerancia', resultado['entrada_canonica']['tolerancia'])):
        ui.label(_presentar_escalar(etiqueta, valor, decimales)).classes('iterativos-numero select-text')
    if not barridos and resultado['codigo'] in {'SOLUCION_EXACTA', 'TOLERANCIA_ALCANZADA'}:
        ui.label('El vector inicial ya satisfacía el criterio de parada.').classes('texto-secundario')


def _presentar_escalar(etiqueta: str, exacto: str, decimales: int | None = None) -> str:
    if decimales is None:
        return f'{etiqueta} (exacto: {exacto})'
    return f'{etiqueta} ≈ {presentar_numero_iterativo(exacto, decimales)}'


def _mostrar_tabla(resultado: dict, ir_a, decimales: int | None) -> None:
    ui.label('Tabla de iteraciones').classes('text-base font-semibold texto-principal')
    if decimales is not None:
        unidad = 'decimal' if decimales == 1 else 'decimales'
        ui.label(f'Valores redondeados ({decimales} {unidad})').classes('text-sm texto-secundario')
    with (
        ui.element('div').classes('iterativos-desplazamiento').props('tabindex=0 aria-label="Tabla de iteraciones"'),
        ui.element('table').classes('iterativos-tabla'),
    ):
        _mostrar_encabezado(resultado['variables'])
        with ui.element('tbody'):
            for paso in resultado['pasos']:
                _mostrar_fila(paso, ir_a, decimales)


def _mostrar_encabezado(variables: list[str]) -> None:
    with ui.element('thead'), ui.element('tr'):
        for etiqueta in ('Barrido', *variables, '‖r‖∞', '‖Δx‖∞'):
            with ui.element('th').props('scope=col'):
                ui.label(etiqueta)


def _mostrar_fila(paso: dict, ir_a, decimales: int | None) -> None:
    indice = paso['indice']
    with ui.element('tr'):
        with ui.element('th').props('scope=row'):
            ui.button(str(indice), on_click=partial(ir_a, indice - 1), color=None).classes(
                'boton-discreto').props(f'ripple=false aria-label="Ver barrido {indice}"')
        for valor in (*paso['vector_nuevo'], paso['norma_residuo'], paso['norma_cambio']):
            with ui.element('td'):
                ui.label(presentar_numero_iterativo(valor, decimales)).classes('iterativos-numero select-text')
