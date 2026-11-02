"""Representación estática y escapada de los datos introducidos en una herramienta."""
from html import escape

from nicegui import ui
from src.frontend import textos


def renderizar_entrada(entrada: dict, herramienta: str) -> None:
    """Muestra la captura del cálculo sin evaluar expresiones ni interpretar HTML."""
    ui.label(textos.PDF_ENTRADA[0]).classes('text-h6')
    for clave, dato in entrada.items():
        titulo = textos.PDF_ETIQUETAS_ENTRADA.get(clave, str(clave))
        if herramienta == 'romanos' and clave == 'b':
            titulo = textos.PDF_SEGUNDO_OPERANDO
        _renderizar_dato(titulo, dato)


def _renderizar_dato(titulo: str, dato) -> None:
    with ui.column().classes('w-full gap-2'):
        ui.label(titulo).classes('text-weight-bold')
        if isinstance(dato, dict):
            _renderizar_diccionario(dato)
        elif isinstance(dato, (list, tuple)):
            _renderizar_lista(dato)
        else:
            ui.label(_valor(dato)).classes('pdf-mensaje')


def _renderizar_diccionario(dato: dict) -> None:
    if dato and all(isinstance(clave, tuple) and len(clave) == 2 for clave in dato):
        filas = max(clave[0] for clave in dato) + 1
        columnas = max(clave[1] for clave in dato) + 1
        _renderizar_tabla([[dato.get((fila, columna), '') for columna in range(columnas)]
                           for fila in range(filas)])
        return
    for clave, valor in dato.items():
        _renderizar_dato(textos.PDF_ETIQUETAS_ENTRADA.get(clave, str(clave)), valor)


def _renderizar_lista(datos: list | tuple) -> None:
    if all(isinstance(fila, (list, tuple)) for fila in datos):
        _renderizar_tabla(datos)
    elif any(isinstance(valor, dict) for valor in datos):
        for numero, valor in enumerate(datos, 1):
            _renderizar_dato(str(numero), valor)
    else:
        _renderizar_tabla([datos])


def _valor(dato) -> str:
    if isinstance(dato, bool):
        return textos.PDF_BOOLEANOS[dato]
    return '' if dato is None else str(dato)


def _renderizar_tabla(filas: list | tuple) -> None:
    contenido = ''.join('<tr>' + ''.join(f'<td>{escape(_valor(valor))}</td>' for valor in fila)
                        + '</tr>' for fila in filas)
    ui.html(f'<div class="pdf-tabla-entrada"><table><tbody>{contenido}</tbody></table></div>')
