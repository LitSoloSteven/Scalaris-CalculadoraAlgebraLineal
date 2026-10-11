"""Resúmenes textuales y fórmulas escapadas de las escenas geométricas."""
from __future__ import annotations

from html import escape
import json
from nicegui import ui


def _mostrar_formula(vista, formula: str, nombre: str):
    identificador = f'geometria-formula-{id(vista)}-{nombre}'
    contenido = escape(formula)
    with ui.element('div').classes('geometria-formula math-scroll-container').props('role=img') as contenedor:
        contenedor.props['aria-label'] = nombre
        ui.html(f'<div id="{identificador}" class="math-label text-sm">$$ {contenido} $$</div>')
    vista._ejecutar_js(f'window.scalaris?.renderizarMathJax({json.dumps([identificador])});')


def _mostrar_aviso(mensaje: str):
    ui.label(mensaje).classes('geometria-aviso text-sm text-sec mt-2')


def _mostrar_estado(mensaje: str, clase: str):
    ui.label(mensaje).classes(f'geometria-resumen {clase} px-4 py-2 mt-2')


def _resumir_soluciones_infinitas(vista, conjunto: dict, dimension: int):
    if conjunto.get('whole_space'):
        espacio = 'R²' if dimension == 2 else 'R³'
        _mostrar_estado(f'Todos los puntos de {espacio} son solución', 'badge-success')
        return
    _mostrar_estado(f'Solución paramétrica (d={conjunto.get("dimension", 0)})', 'badge-warning')
    if conjunto.get('description'):
        _mostrar_aviso(conjunto['description'])
    if conjunto.get('param_latex'):
        _mostrar_formula(vista, conjunto['param_latex'], 'solucion')
    if conjunto.get('free_vars'):
        _mostrar_aviso(f'Variables libres: {", ".join(conjunto["free_vars"])}')


def _resumir_estado_rectas(vista, resultado: dict):
    estado = resultado.get('solution_status', '')
    conjunto = resultado.get('set')
    dimension = resultado.get('n', 2)
    if estado == 'UNIQUE_SOLUTION' and conjunto and conjunto.get('point_exact'):
        punto = ', '.join(conjunto['point_exact'])
        _mostrar_estado(f'Única solución en ({punto})', 'badge-success')
        if conjunto.get('point_latex'):
            _mostrar_formula(vista, f'\\mathbf{{x}} = {conjunto["point_latex"]}', 'solucion')
    elif estado == 'NO_SOLUTION':
        paralelas = 'parallel' in resultado.get('flags', []) and dimension == 2
        mensaje = 'Las rectas son paralelas y no se intersectan' if paralelas else 'El sistema no tiene solución'
        _mostrar_estado(mensaje, 'badge-error')
    elif estado == 'INFINITE_SOLUTIONS' and conjunto:
        _resumir_soluciones_infinitas(vista, conjunto, dimension)


def _resumir_rectas(vista, resultado: dict):
    for indice, ecuacion in enumerate(resultado.get('equations', [])):
        _mostrar_formula(vista, ecuacion.get('latex', ''), f'ecuacion-{indice}')
    if resultado.get('pending_param') and resultado.get('set') is None:
        _mostrar_aviso('No pudimos dibujar el conjunto solución. Las ecuaciones sí se grafican.')
    else:
        _resumir_estado_rectas(vista, resultado)


def _resumir_vectores(vista, resultado: dict):
    coordenadas_u = ', '.join(resultado.get('u', {}).get('exact', []))
    coordenadas_v = ', '.join(resultado.get('v', {}).get('exact', []))
    formula = f'\\mathbf{{u}} = ({coordenadas_u}), \\quad \\mathbf{{v}} = ({coordenadas_v})'
    _mostrar_formula(vista, formula, 'vectores')


def _resumir_combinacion(vista, resultado: dict):
    coordenadas = ', '.join(resultado.get('b', {}).get('exact', []))
    partes = [f'\\mathbf{{v}}_{indice + 1} = ({", ".join(vector.get("exact", []))})'
              for indice, vector in enumerate(resultado.get('vectors', []))]
    vectores = ', \\quad '.join(partes)
    _mostrar_formula(vista, f'\\mathbf{{b}} = ({coordenadas}), \\quad {vectores}', 'combinacion')
    estado = resultado.get('solution_status', '')
    cadena = resultado.get('chain', [])
    if estado == 'UNIQUE' and cadena:
        punto = ', '.join(cadena[-1].get('exact', []))
        _mostrar_estado(f'b se alcanza en ({punto})', 'text-main font-bold text-sm')
    elif estado == 'INFINITE':
        _mostrar_aviso('b es combinación lineal de los vectores, pero la representación no es única.')
    elif estado == 'NO_SOLUTION':
        _mostrar_aviso('b no pertenece al espacio generado por los vectores dados.')


def renderizar_resumen(vista, resultado: dict, escena: str) -> None:
    """Presenta el resultado de una escena sin calcular ni interpretar sus datos."""
    if not vista.contenedor_resumen:
        return
    vista.contenedor_resumen.clear()
    if vista.contenedor_estado:
        vista.contenedor_estado.clear()
    presentadores = {'rectas-planos': _resumir_rectas, 'vectores': _resumir_vectores, 'combinacion': _resumir_combinacion}
    presentador = presentadores.get(escena)
    if presentador:
        with vista.contenedor_resumen:
            presentador(vista, resultado)
            _mostrar_avisos_rango(resultado)


def _mostrar_avisos_rango(resultado: dict):
    if resultado.get('out_of_range'):
        _mostrar_aviso('Algunos elementos quedan fuera del rango visible')
    if (resultado.get('set') or {}).get('segment_visible') is False:
        _mostrar_aviso('La recta solución queda fuera del rango visible')
