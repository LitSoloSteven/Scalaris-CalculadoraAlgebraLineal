"""Resumen exacto, aproximación legible y tabla navegable de los barridos."""
from decimal import Decimal, localcontext
from functools import partial

from nicegui import ui

from src.frontend.nucleo.textos.textos_metodos_iterativos import CAUSAS_PARADA
from .pasos_iterativos import crear_reproductor_iterativo


def mostrar_resultado_iterativo(resultado: dict):
    """Renderiza el resultado y devuelve su reproductor si se confirmaron barridos."""
    codigo = resultado['codigo']
    ui.label(CAUSAS_PARADA[codigo]).classes('text-lg font-semibold texto-principal').props('role=status')
    diagnostico = resultado.get('diagnostico')
    if diagnostico:
        ui.label(diagnostico['mensaje']).classes('iterativos-numero texto-secundario').props('role=alert')
    if resultado['aproximacion'] is not None:
        _mostrar_resumen(resultado)
    dominancia = resultado.get('dominancia_estricta')
    if dominancia is not None:
        ui.label(f'Dominancia diagonal estricta: {"sí" if dominancia else "no"}.').classes('text-sm texto-secundario')
    if not resultado['pasos']:
        return None
    reproductor = crear_reproductor_iterativo(resultado)
    _mostrar_tabla(resultado, reproductor.ir_a)
    reproductor.construir()
    return reproductor


def _mostrar_resumen(resultado: dict) -> None:
    barridos = len(resultado['pasos'])
    ui.label(f'Barridos completos: {barridos}').classes('texto-secundario')
    for variable, valor in zip(resultado['variables'], resultado['aproximacion']):
        ui.label(_presentar_escalar(variable, valor)).classes('iterativos-numero texto-principal select-text')
    ui.label(f'r = b − Ax = ({", ".join(resultado["residuo"])})').classes('iterativos-numero texto-principal select-text')
    ui.label(_presentar_escalar('‖r‖∞', resultado['norma_residuo'])).classes('iterativos-numero select-text')
    ui.label(_presentar_escalar('Tolerancia', resultado['entrada_canonica']['tolerancia'])).classes('iterativos-numero select-text')
    if not barridos and resultado['codigo'] in {'SOLUCION_EXACTA', 'TOLERANCIA_ALCANZADA'}:
        ui.label('El vector inicial ya satisfacía el criterio de parada.').classes('texto-secundario')


def _presentar_escalar(etiqueta: str, exacto: str) -> str:
    numerador, _, denominador = exacto.partition('/')
    numerador_decimal = Decimal(numerador)
    denominador_decimal = Decimal(denominador or '1')
    with localcontext() as contexto:
        contexto.prec = 9
        decimal = numerador_decimal / denominador_decimal
    numerador_redondeado, denominador_redondeado = decimal.as_integer_ratio()
    if numerador_redondeado * int(denominador_decimal) == denominador_redondeado * int(numerador_decimal):
        return f'{etiqueta} = {decimal}'
    return f'{etiqueta} ≈ {decimal} (exacto: {exacto})'


def _mostrar_tabla(resultado: dict, ir_a) -> None:
    ui.label('Tabla de iteraciones').classes('text-base font-semibold texto-principal')
    with ui.element('div').classes('iterativos-desplazamiento').props('tabindex=0 aria-label="Tabla de iteraciones"'):
        with ui.element('table').classes('iterativos-tabla'):
            with ui.element('thead'), ui.element('tr'):
                for etiqueta in ('Barrido', *resultado['variables'], '‖r‖∞', '‖Δx‖∞'):
                    with ui.element('th').props('scope=col'):
                        ui.label(etiqueta)
            with ui.element('tbody'):
                for paso in resultado['pasos']:
                    _mostrar_fila(paso, ir_a)


def _mostrar_fila(paso: dict, ir_a) -> None:
    indice = paso['indice']
    with ui.element('tr'):
        with ui.element('th').props('scope=row'):
            ui.button(str(indice), on_click=partial(ir_a, indice - 1), color=None).classes(
                'boton-discreto').props(f'ripple=false aria-label="Ver barrido {indice}"')
        for valor in (*paso['vector_nuevo'], paso['norma_residuo'], paso['norma_cambio']):
            with ui.element('td'):
                ui.label(valor).classes('iterativos-numero select-text')
