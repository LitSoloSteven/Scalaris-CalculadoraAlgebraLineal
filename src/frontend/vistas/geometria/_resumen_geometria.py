"""Resúmenes textuales y fórmulas escapadas de las escenas geométricas."""
from __future__ import annotations

from html import escape
import json
from nicegui import ui


def _mostrar_formula(vista, formula: str, nombre: str):
    identificador = f'geometria-formula-{id(vista)}-{nombre}'
    contenido = escape(formula)
    with ui.element('div').classes('geometria-formula matematicas-desplazamiento').props('role=img') as contenedor:
        contenedor.props['aria-label'] = nombre
        ui.html(f'<div id="{identificador}" class="matematicas-etiqueta text-sm">$$ {contenido} $$</div>')
    vista._ejecutar_javascript(f'window.scalaris?.renderizarMathJax({json.dumps([identificador])});')


def _mostrar_aviso(mensaje: str):
    ui.label(mensaje).classes('geometria-aviso text-sm texto-secundario mt-2')


def _mostrar_estado(mensaje: str, clase: str):
    ui.label(mensaje).classes(f'geometria-resumen {clase} px-4 py-2 mt-2')


def _resumir_soluciones_infinitas(vista, conjunto: dict, dimension: int):
    if conjunto.get('espacio_completo'):
        espacio = 'R²' if dimension == 2 else 'R³'
        _mostrar_estado(f'Todos los puntos de {espacio} son solución', 'distintivo-exito')
        return
    _mostrar_estado(f'Solución paramétrica (d={conjunto.get("dimension", 0)})', 'distintivo-advertencia')
    if conjunto.get('descripcion'):
        _mostrar_aviso(conjunto['descripcion'])
    if conjunto.get('parametros_latex'):
        _mostrar_formula(vista, conjunto['parametros_latex'], 'solucion')
    if conjunto.get('variables_libres'):
        _mostrar_aviso(f'Variables libres: {", ".join(conjunto["variables_libres"])}')


def _resumir_estado_rectas(vista, resultado: dict):
    estado = resultado.get('estado_solucion', '')
    conjunto = resultado.get('conjunto_solucion')
    dimension = resultado.get('numero_variables', 2)
    if estado == 'SOLUCION_UNICA' and conjunto and conjunto.get('punto_exacto'):
        punto = ', '.join(conjunto['punto_exacto'])
        _mostrar_estado(f'Única solución en ({punto})', 'distintivo-exito')
        if conjunto.get('punto_latex'):
            _mostrar_formula(vista, f'\\mathbf{{x}} = {conjunto["punto_latex"]}', 'solucion')
    elif estado == 'SIN_SOLUCION':
        paralelas = 'paralelas' in resultado.get('banderas', []) and dimension == 2
        mensaje = 'Las rectas son paralelas y no se intersectan' if paralelas else 'El sistema no tiene solución'
        _mostrar_estado(mensaje, 'distintivo-error')
    elif estado == 'SOLUCIONES_INFINITAS' and conjunto:
        _resumir_soluciones_infinitas(vista, conjunto, dimension)


def _resumir_rectas(vista, resultado: dict):
    for indice, ecuacion in enumerate(resultado.get('ecuaciones', [])):
        _mostrar_formula(vista, ecuacion.get('latex', ''), f'ecuacion-{indice}')
    if resultado.get('parametro_pendiente') and resultado.get('conjunto_solucion') is None:
        _mostrar_aviso('No pudimos dibujar el conjunto solución. Las ecuaciones sí se grafican.')
    else:
        _resumir_estado_rectas(vista, resultado)


def _resumir_vectores(vista, resultado: dict):
    coordenadas_u = ', '.join(resultado.get('vector_u', {}).get('exacta', []))
    coordenadas_v = ', '.join(resultado.get('vector_v', {}).get('exacta', []))
    formula = f'\\mathbf{{u}} = ({coordenadas_u}), \\quad \\mathbf{{v}} = ({coordenadas_v})'
    _mostrar_formula(vista, formula, 'vectores')


def _resumir_combinacion(vista, resultado: dict):
    coordenadas = ', '.join(resultado.get('objetivo', {}).get('exacta', []))
    partes = [f'\\mathbf{{v}}_{indice + 1} = ({", ".join(vector.get("exacta", []))})'
              for indice, vector in enumerate(resultado.get('vectores', []))]
    vectores = ', \\quad '.join(partes)
    _mostrar_formula(vista, f'\\mathbf{{b}} = ({coordenadas}), \\quad {vectores}', 'combinacion')
    estado = resultado.get('estado_solucion', '')
    cadena = resultado.get('cadena', [])
    if estado == 'UNICA' and cadena:
        punto = ', '.join(cadena[-1].get('exacta', []))
        _mostrar_estado(f'b se alcanza en ({punto})', 'texto-principal font-bold text-sm')
    elif estado == 'INFINITA':
        _mostrar_aviso('b es combinación lineal de los vectores, pero la representación no es única.')
    elif estado == 'SIN_SOLUCION':
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
    if resultado.get('fuera_de_rango'):
        _mostrar_aviso('Algunos elementos quedan fuera del rango visible')
    if (resultado.get('conjunto_solucion') or {}).get('segmento_visible') is False:
        _mostrar_aviso('La recta solución queda fuera del rango visible')
