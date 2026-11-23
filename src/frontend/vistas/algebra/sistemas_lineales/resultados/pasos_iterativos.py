"""Adaptación de los barridos de cada método al reproductor compartido."""
from nicegui import ui

from src.frontend.componentes.reproductor_pasos.formato.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.interfaz.reproductor import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.nucleo.modelo import GrupoReproductor, PasoReproductor
from src.frontend.nucleo.textos.textos_metodos_iterativos import AYUDA_METODOS, METODO_SECUENCIAL, NOMBRES_METODOS


def crear_reproductor_iterativo(resultado: dict) -> ReproductorPasos:
    """Construye el reproductor con un paso exacto por barrido confirmado."""
    entrada = resultado['entrada_canonica']
    metodo = resultado['metodo']
    pasos = tuple(_crear_paso(paso, entrada, resultado['variables'], metodo) for paso in resultado['pasos'])
    grupo = GrupoReproductor(f'Barridos de {NOMBRES_METODOS[metodo]}', f'{len(pasos)} barridos', 'iteracion', tuple(range(len(pasos))))
    return ReproductorPasos(pasos, (grupo,), _renderizar_paso, 'metodos-iterativos', {'sin_movimiento': True})


def _crear_paso(paso: dict, entrada: dict, variables: list[str], metodo: str) -> PasoReproductor:
    indice = paso['indice']
    return PasoReproductor(
        indice=indice - 1, tipo='iteracion', descripcion=f'Barrido {indice}',
        etiqueta_tipo='Iteración',
        explicacion=AYUDA_METODOS[metodo],
        cuerpo=(paso, entrada, variables, metodo),
    )


def _racional(valor: str) -> str:
    numerador, separador, denominador = valor.partition('/')
    if not separador:
        return numerador
    return rf'\frac{{{numerador}}}{{{denominador}}}'


def _operando(paso: dict, fila: int, columna: int, metodo: str) -> str:
    actualizado = metodo == METODO_SECUENCIAL and columna < fila
    clave = 'vector_nuevo' if actualizado else 'vector_anterior'
    valor = rf'\left({_racional(paso[clave][columna])}\right)'
    if metodo != METODO_SECUENCIAL:
        return valor
    barrido = paso['indice'] if actualizado else paso['indice'] - 1
    return rf'\underbrace{{{valor}}}_{{x_{{{columna + 1}}}^{{({barrido})}}}}'


def _despeje(paso: dict, entrada: dict, indice: int, metodo: str) -> str:
    fila = entrada['matriz'][indice]
    terminos = [
        rf'\left({_racional(coeficiente)}\right){_operando(paso, indice, columna, metodo)}'
        for columna, coeficiente in enumerate(fila) if columna != indice and coeficiente != '0'
    ]
    suma = ' + '.join(terminos) or '0'
    independiente = _racional(entrada['vector_b'][indice])
    diagonal = _racional(fila[indice])
    nuevo = _racional(paso['vector_nuevo'][indice])
    return rf'x_{{{indice + 1}}}^{{({paso["indice"]})}} = \frac{{{independiente} - \left({suma}\right)}}{{{diagonal}}} = {nuevo}'


def _renderizar_paso(paso: PasoReproductor, contenedor) -> None:
    barrido, entrada, variables, metodo = paso.cuerpo
    with contenedor, ui.column().classes('w-full gap-2'):
        for titulo, clave in (('Vector anterior', 'vector_anterior'), ('Vector nuevo', 'vector_nuevo')):
            ui.label(f'{titulo} = ({", ".join(barrido[clave])})').classes('iterativos-numero')
        columnas = range(len(variables))
        if variables != [f'x{indice + 1}' for indice in columnas]:
            ui.label(f'Incógnitas en orden: {", ".join(variables)}').classes('iterativos-numero texto-secundario')
        despejes = r' \\ '.join(_despeje(barrido, entrada, indice, metodo) for indice in columnas)
        renderizar_latex(r'\begin{gathered}' + despejes + r'\end{gathered}', vigilar_region=True)
