"""Adaptación de los barridos de cada método al reproductor compartido."""
from functools import partial

from nicegui import ui

from src.ai.contexto.contexto import compactar_numero
from src.frontend.componentes.glosa.interaccion.glosa_foco import crear_accion_explicacion
from src.frontend.componentes.reproductor_pasos.formato.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.interfaz.reproductor import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.nucleo.modelo import GrupoReproductor, PasoReproductor
from src.frontend.controladores.algebra.sistemas_lineales.resolucion.presentacion_iterativa import (
    DECIMALES_INICIALES, presentar_numero_iterativo, presentar_vector_iterativo,
)
from src.frontend.nucleo.textos.textos_metodos_iterativos import AYUDA_METODOS, METODO_SECUENCIAL, NOMBRES_METODOS


def crear_reproductor_iterativo(
    resultado: dict, *, decimales: int | None = DECIMALES_INICIALES, panel_ia=None, sigue_vigente=None,
) -> ReproductorPasos:
    """Construye el reproductor con un paso exacto por barrido confirmado."""
    entrada = resultado['entrada_canonica']
    metodo = resultado['metodo']
    total_pasos = len(resultado['pasos'])
    pasos = tuple(_crear_paso(paso, entrada, resultado, indice_total=total_pasos) for paso in resultado['pasos'])
    grupo = GrupoReproductor(
        f'Barridos de {NOMBRES_METODOS[metodo]}',
        f'{len(pasos)} barridos',
        'iteracion',
        tuple(range(len(pasos))),
    )
    opciones: dict = {'sin_movimiento': True}
    if panel_ia is not None:
        opciones['al_explicar'] = crear_accion_explicacion(panel_ia, pasos, sigue_vigente=sigue_vigente)
        opciones['esta_ocupado'] = lambda: bool(getattr(panel_ia, '_esta_enviando', False))
    renderizar = partial(_renderizar_paso, decimales=decimales)
    return ReproductorPasos(pasos, (grupo,), renderizar, 'metodos-iterativos', opciones)


def _compactar_vector(valores: tuple | list) -> list[str]:
    return [compactar_numero(str(valor), 48) for valor in valores]


def _crear_paso(
    paso: dict, entrada: dict, resultado: dict, *, indice_total: int,
) -> PasoReproductor:
    indice = paso['indice']
    metodo = resultado['metodo']
    variables = resultado['variables']
    detalle = {
        'metodo': NOMBRES_METODOS[metodo],
        'actualizacion': 'secuencial' if metodo == METODO_SECUENCIAL else 'simultanea',
        'barrido': indice,
        'variables': list(variables),
        'vector_anterior': _compactar_vector(paso['vector_anterior']),
        'vector_nuevo': _compactar_vector(paso['vector_nuevo']),
        'norma_residuo': compactar_numero(str(paso['norma_residuo']), 48),
        'norma_cambio': compactar_numero(str(paso['norma_cambio']), 48),
        'tolerancia': compactar_numero(str(entrada['tolerancia']), 32),
        'causa_parada': resultado['codigo'],
    }
    metadatos = {
        'indice': indice,
        'total': indice_total,
        'tipo': 'iteracion',
        'operacion': f'Barrido {indice} ({NOMBRES_METODOS[metodo]})',
        'detalle': detalle,
    }
    return PasoReproductor(
        indice=indice - 1, tipo='iteracion', descripcion=f'Barrido {indice}',
        etiqueta_tipo='Iteración',
        explicacion=AYUDA_METODOS[metodo],
        cuerpo=(paso, entrada, variables, metodo),
        meta_explicar=metadatos,
    )


def _numero_latex(valor: str, decimales: int | None) -> str:
    texto = presentar_numero_iterativo(valor, decimales)
    numerador, separador, denominador = texto.partition('/')
    if separador:
        return rf'\frac{{{numerador}}}{{{denominador}}}'
    mantisa, separador, exponente = texto.partition('e')
    return rf'{mantisa}\times 10^{{{int(exponente)}}}' if separador else texto


def _operando(paso: dict, fila: int, columna: int, metodo: str, decimales: int | None) -> str:
    actualizado = metodo == METODO_SECUENCIAL and columna < fila
    clave = 'vector_nuevo' if actualizado else 'vector_anterior'
    valor = rf'\left({_numero_latex(paso[clave][columna], decimales)}\right)'
    if metodo != METODO_SECUENCIAL:
        return valor
    barrido = paso['indice'] if actualizado else paso['indice'] - 1
    return rf'\underbrace{{{valor}}}_{{x_{{{columna + 1}}}^{{({barrido})}}}}'


def _despeje(paso: dict, entrada: dict, indice: int, metodo: str, decimales: int | None = None) -> str:
    fila = entrada['matriz'][indice]
    terminos = [
        rf'\left({_numero_latex(coeficiente, decimales)}\right){_operando(paso, indice, columna, metodo, decimales)}'
        for columna, coeficiente in enumerate(fila) if columna != indice and coeficiente != '0'
    ]
    suma = ' + '.join(terminos) or '0'
    independiente = _numero_latex(entrada['vector_b'][indice], decimales)
    diagonal = _numero_latex(fila[indice], decimales)
    nuevo = _numero_latex(paso['vector_nuevo'][indice], decimales)
    simbolo = '=' if decimales is None else r'\approx'
    return (
        rf'x_{{{indice + 1}}}^{{({paso["indice"]})}} {simbolo} '
        rf'\frac{{{independiente} - \left({suma}\right)}}{{{diagonal}}} {simbolo} {nuevo}'
    )


def _renderizar_paso(paso: PasoReproductor, contenedor, *, decimales: int | None) -> None:
    barrido, entrada, variables, metodo = paso.cuerpo
    simbolo = '=' if decimales is None else '≈'
    with contenedor, ui.column().classes('w-full gap-2'):
        for titulo, clave in (('Vector anterior', 'vector_anterior'), ('Vector nuevo', 'vector_nuevo')):
            vector = presentar_vector_iterativo(barrido[clave], decimales)
            ui.label(f'{titulo} {simbolo} {vector}').classes('iterativos-numero')
        columnas = range(len(variables))
        if variables != [f'x{indice + 1}' for indice in columnas]:
            ui.label(f'Incógnitas en orden: {", ".join(variables)}').classes('iterativos-numero texto-secundario')
        despejes = r' \\ '.join(_despeje(barrido, entrada, indice, metodo, decimales) for indice in columnas)
        renderizar_latex(r'\begin{gathered}' + despejes + r'\end{gathered}', vigilar_region=True)
