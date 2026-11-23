"""Adaptación de los barridos de Jacobi al reproductor compartido."""
from nicegui import ui

from src.frontend.componentes.reproductor_pasos.formato.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.interfaz.reproductor import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.nucleo.modelo import GrupoReproductor, PasoReproductor


def crear_reproductor_iterativo(resultado: dict) -> ReproductorPasos:
    """Construye el reproductor con un paso exacto por barrido confirmado."""
    entrada = resultado['entrada_canonica']
    pasos = tuple(_crear_paso(paso, entrada, resultado['variables']) for paso in resultado['pasos'])
    grupo = GrupoReproductor('Barridos de Jacobi', f'{len(pasos)} barridos', 'iteracion', tuple(range(len(pasos))))
    return ReproductorPasos(pasos, (grupo,), _renderizar_paso, 'metodos-iterativos')


def _crear_paso(paso: dict, entrada: dict, variables: list[str]) -> PasoReproductor:
    indice = paso['indice']
    return PasoReproductor(
        indice=indice - 1, tipo='iteracion', descripcion=f'Barrido {indice}',
        etiqueta_tipo='Iteración',
        explicacion='Sustituye en todas las ecuaciones los valores del vector anterior.',
        cuerpo=(paso, entrada, variables),
    )


def _racional(valor: str) -> str:
    numerador, separador, denominador = valor.partition('/')
    if not separador:
        return numerador
    return rf'\frac{{{numerador}}}{{{denominador}}}'


def _despeje(paso: dict, entrada: dict, indice: int) -> str:
    fila = entrada['matriz'][indice]
    terminos = [
        rf'\left({_racional(coeficiente)}\right)\left({_racional(paso["vector_anterior"][columna])}\right)'
        for columna, coeficiente in enumerate(fila) if columna != indice and coeficiente != '0'
    ]
    suma = ' + '.join(terminos) or '0'
    independiente = _racional(entrada['vector_b'][indice])
    diagonal = _racional(fila[indice])
    nuevo = _racional(paso['vector_nuevo'][indice])
    return rf'x_{{{indice + 1}}}^{{({paso["indice"]})}} = \frac{{{independiente} - \left({suma}\right)}}{{{diagonal}}} = {nuevo}'


def _renderizar_paso(paso: PasoReproductor, contenedor) -> None:
    barrido, entrada, variables = paso.cuerpo
    with contenedor, ui.column().classes('w-full gap-2'):
        for titulo, clave in (('Vector anterior', 'vector_anterior'), ('Vector nuevo', 'vector_nuevo')):
            ui.label(f'{titulo} = ({", ".join(barrido[clave])})').classes('iterativos-numero')
        for indice, variable in enumerate(variables):
            ui.label(f'Incógnita {variable}').classes('iterativos-numero texto-secundario')
            renderizar_latex(_despeje(barrido, entrada, indice), vigilar_region=True)
