"""Adaptación exacta entre matriz aumentada y ecuaciones de un sistema iterativo."""
from dataclasses import dataclass

from src.backend.utilidades.validacion.validadores import ValidadorMatriz
from .captura import preparar_captura_ecuaciones


@dataclass(frozen=True)
class SistemaCapturado:
    """Conserva las filas de A, los términos independientes y el orden de columnas."""

    matriz: list[list[str]]
    independientes: list[str]
    variables: list[str]


def interpretar_ecuaciones(texto: str) -> SistemaCapturado:
    """Interpreta texto con el analizador compartido; avisa con ValueError si falla la conversión."""
    captura = preparar_captura_ecuaciones([texto])
    if captura['estado'] != 'EXITO':
        raise ValueError(captura['mensaje'])
    matriz, variables = captura['matriz_a'], captura['variables']
    if len(matriz) != len(variables):
        raise ValueError(f'Escribe un sistema cuadrado. Hay {len(matriz)} ecuaciones y {len(variables)} incógnitas.')
    return SistemaCapturado(matriz, captura['vector_b'], variables)


def ajustar_variables(variables: list[str], dimension: int) -> list[str]:
    """Conserva el tramo común y añade nombres que siguen el orden del analizador."""
    actuales = variables[:dimension]
    while len(actuales) < dimension:
        indice = len(actuales) + 1
        anterior = actuales[-1] if actuales else None
        nombre = f'x{indice}' if anterior in (None, f'x{indice - 1}') else f'{anterior}_1'
        actuales.append(nombre)
    return actuales


def redactar_ecuaciones(sistema: SistemaCapturado) -> str:
    """Convierte los datos exactos a ecuaciones; una celda inválida produce ValueError."""
    return '\n'.join(
        _redactar_fila(fila, independiente, sistema.variables, numero)
        for numero, (fila, independiente) in enumerate(zip(sistema.matriz, sistema.independientes), 1)
    )


def _redactar_fila(fila: list[str], independiente: str, variables: list[str], numero: int) -> str:
    terminos = []
    for columna, (coeficiente, variable) in enumerate(zip(fila, variables), 1):
        valor = _normalizar_celda(coeficiente, f'coeficiente ({numero}, {columna})')
        if valor != '0' or numero == 1:
            termino = f'{valor.removeprefix("-")}*{variable}'
            signo = '-' if valor.startswith('-') else '+'
            terminos.append(f'{signo} {termino}' if terminos else f'{signo.removeprefix("+")}{termino}')
    izquierda = ' '.join(terminos) or f'0*{variables[0]}'
    return f'{izquierda} = {_normalizar_celda(independiente, f"término independiente {numero}")}'


def _normalizar_celda(texto: str, ubicacion: str) -> str:
    valida, valor, mensaje = ValidadorMatriz.parsear_numero_exacto(texto)
    if not valida:
        raise ValueError(f'Revisa {ubicacion}. {mensaje}')
    return str(valor)
