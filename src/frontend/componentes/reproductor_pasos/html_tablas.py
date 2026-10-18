"""Formateadores seguros de valores y tablas matemáticas de pasos."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import html
import re
from typing import Any, Sequence

from src.backend.modelos.matriz import Matriz
from src.backend.constantes import DECIMALES_VISUALIZACION
from src.frontend.componentes.reproductor_pasos.catalogo import DIMENSION_MAXIMA_FRACCIONES_APILADAS
from .opciones import OpcionesTablaAumentada


def _filas_matriz(matriz: Matriz) -> int:
    """Obtiene la cantidad de filas de una matriz."""
    return matriz.filas


def _columnas_matriz(matriz: Matriz) -> int:
    """Obtiene la cantidad de columnas de una matriz."""
    return matriz.columnas


def _obtener_celda_matriz(matriz: Matriz, fila: int, columna: int) -> Any:
    """Obtiene el valor de una celda mediante la API de Matriz."""
    return matriz.obtener(fila, columna)


@dataclass(frozen=True)
class _ResaltadosAumentados:
    """Agrupa las opciones de resaltado aplicadas a cada fila."""

    ancho_izquierdo: int
    filas_cambiadas: Sequence[int]
    filas_intercambio: Sequence[int]
    pivote: tuple[int, int] | None
    bloque_resultado: bool
    apilada: bool


def formatear_valor(valor: int | Fraction | float | str, *, apilada: bool = False) -> str:
    """Formatea un número o texto para una celda."""
    if isinstance(valor, int) or (isinstance(valor, Fraction) and valor.denominator == 1):
        return str(valor.numerator if isinstance(valor, Fraction) else valor)
    if isinstance(valor, Fraction):
        signo = "−" if valor < 0 else ""
        numerador, denominador = abs(valor.numerator), valor.denominator
        if apilada:
            return f'{signo}<span class="inversa-fraccion"><span>{numerador}</span><span>{denominador}</span></span>'
        return f"{signo}{numerador}/{denominador}"
    return html.escape(str(valor))


def formatear_decimal(valor: int | Fraction | float | str) -> str:
    """Devuelve una aproximación decimal sin ceros finales redundantes."""
    try:
        numero = float(valor)
        if abs(numero) < 1e-12:
            return "0"
        texto = f"{numero:.{DECIMALES_VISUALIZACION}f}".rstrip("0").rstrip(".")
        return "0" if texto == "-0" else texto
    except (OverflowError, ValueError):
        return html.escape(str(valor))


def etiqueta_variable_html(nombre: str) -> str:
    """Convierte un subíndice numérico o escapa el nombre recibido."""
    coincidencia = re.fullmatch(r"([A-Za-z]+)_?(\d+)", nombre)
    if coincidencia:
        return f"{coincidencia.group(1)}<sub>{coincidencia.group(2)}</sub>"
    return html.escape(nombre)


def html_tabla_matriz(matriz: Matriz, *, decimales: bool = False) -> str:
    """Genera una tabla de matriz con desplazamiento horizontal propio."""
    n_filas = _filas_matriz(matriz)
    total_columnas = _columnas_matriz(matriz)
    compacta = n_filas > DIMENSION_MAXIMA_FRACCIONES_APILADAS
    apilada = not compacta and not decimales
    encabezado = "<th class='fila-etiqueta'></th>" + "".join(
        f"<th>C{columna + 1}</th>" for columna in range(total_columnas)
    )
    filas = [_fila_matriz(matriz, indice, apilada, decimales) for indice in range(n_filas)]
    clase = "inversa-tabla compacta" if compacta else "inversa-tabla"
    return _html_tabla(clase, encabezado, filas)


def _fila_matriz(matriz: Matriz, indice: int, apilada: bool, decimales: bool) -> str:
    """Construye una fila de la tabla de matriz con etiquetas y valores."""
    total_columnas = _columnas_matriz(matriz)
    celdas = [f"<th class='fila-etiqueta'>F{indice + 1}</th>"]
    for columna in range(total_columnas):
        valor = _obtener_celda_matriz(matriz, indice, columna)
        contenido = formatear_decimal(valor) if decimales else formatear_valor(valor, apilada=apilada)
        if decimales:
            celdas.append(f"<td>{contenido}</td>")
            continue
        titulo = _titulo_aproximado(valor)
        celdas.append(f"<td{titulo}>{contenido}</td>")
    return f"<tr>{''.join(celdas)}</tr>"


def _titulo_aproximado(valor: int | Fraction | float) -> str:
    """Crea el atributo de aproximación para celdas no enteras."""
    es_entero = isinstance(valor, int) or (isinstance(valor, Fraction) and valor.denominator == 1)
    return "" if es_entero else f' title="≈ {formatear_decimal(valor)}"'


def html_tabla_aumentada(matriz: Matriz, columnas_izquierda: int, opciones: OpcionesTablaAumentada | None = None) -> str:
    """Genera una tabla aumentada con resaltados y etiquetas opcionales."""
    configuracion = opciones if opciones is not None else {}
    filas_cambiadas = configuracion.get('filas_cambiadas', ())
    pivote = configuracion.get('pivote', None)
    filas_intercambio = configuracion.get('filas_intercambio', ())
    bloque_resultado = configuracion.get('bloque_resultado', False)
    etiquetas_izquierda = configuracion.get('etiquetas_izquierda', None)
    etiquetas_derecha = configuracion.get('etiquetas_derecha', None)
    total_columnas = _columnas_matriz(matriz)
    n_filas = _filas_matriz(matriz)
    if columnas_izquierda < 0 or columnas_izquierda > total_columnas:
        raise ValueError("El ancho izquierdo debe caber en la matriz aumentada.")
    ancho_derecha = total_columnas - columnas_izquierda
    compacta = columnas_izquierda > DIMENSION_MAXIMA_FRACCIONES_APILADAS
    encabezado = _encabezados_aumentados(columnas_izquierda, ancho_derecha, etiquetas_izquierda, etiquetas_derecha)
    opciones = _ResaltadosAumentados(
        columnas_izquierda, filas_cambiadas, filas_intercambio, pivote,
        bloque_resultado, columnas_izquierda <= DIMENSION_MAXIMA_FRACCIONES_APILADAS,
    )
    filas = [_fila_aumentada(matriz, indice, opciones) for indice in range(n_filas)]
    clases = "inversa-tabla compacta" if compacta else "inversa-tabla"
    if bloque_resultado:
        clases += " es-resultado"
    return _html_tabla(clases, encabezado, filas)


def _encabezados_aumentados(
    columnas_izquierda: int,
    ancho_derecha: int,
    etiquetas_izquierda: Sequence[str] | None,
    etiquetas_derecha: Sequence[str] | None,
) -> str:
    """Construye los encabezados de bloques y valida las etiquetas recibidas."""
    izquierda = _validar_etiquetas(etiquetas_izquierda, columnas_izquierda)
    derecha = _validar_etiquetas(etiquetas_derecha, ancho_derecha)
    cabecera_izquierda = "".join(f"<th>{etiqueta}</th>" for etiqueta in izquierda)

    th_derecha = []
    for indice, etiqueta in enumerate(derecha):
        clase_th = "class='separador-izquierdo'" if indice == 0 else ""
        th_derecha.append(f"<th {clase_th}>{etiqueta}</th>" if clase_th else f"<th>{etiqueta}</th>")
    cabecera_derecha = "".join(th_derecha)

    return f"<th class='fila-etiqueta'></th>{cabecera_izquierda}{cabecera_derecha}"


def _validar_etiquetas(etiquetas: Sequence[str] | None, ancho: int) -> list[str]:
    """Genera las etiquetas numéricas por defecto o valida las explícitas."""
    if etiquetas is None:
        return [str(indice + 1) for indice in range(ancho)]
    if len(etiquetas) != ancho:
        raise ValueError("La cantidad de etiquetas debe coincidir con el ancho del bloque.")
    return [etiqueta_variable_html(etiqueta) for etiqueta in etiquetas]


def _fila_aumentada(matriz: Matriz, indice: int, opciones: _ResaltadosAumentados) -> str:
    """Construye una fila aumentada y aplica sus clases de resaltado."""
    clase_fila = "fila-intercambio" if indice in opciones.filas_intercambio else "fila-modificada" if indice in opciones.filas_cambiadas else ""
    atributo_fila = f' class="{clase_fila}"' if clase_fila else ""
    celdas = [f"<th class='fila-etiqueta'>F{indice + 1}</th>"]
    total_columnas = _columnas_matriz(matriz)
    for columna in range(total_columnas):
        valor = _obtener_celda_matriz(matriz, indice, columna)
        clases = _clases_celda(columna, indice, opciones)
        clase_celda = f' class="{" ".join(clases)}"' if clases else ""
        contenido = formatear_valor(valor, apilada=opciones.apilada)
        celdas.append(f"<td{clase_celda}{_titulo_aproximado(valor)}>{contenido}</td>")
    return f"<tr{atributo_fila}>{''.join(celdas)}</tr>"


def _clases_celda(columna: int, indice: int, opciones: _ResaltadosAumentados) -> list[str]:
    """Devuelve las clases visuales de una celda aumentada."""
    clases = []
    if columna == opciones.ancho_izquierdo:
        clases.append("separador-izquierdo")
    if opciones.pivote is not None and opciones.pivote == (indice, columna):
        clases.append("celda-pivote")
    if opciones.bloque_resultado and columna >= opciones.ancho_izquierdo:
        clases.append("bloque-resultado")
    return clases


def _html_tabla(clases: str, encabezado: str, filas: list[str]) -> str:
    """Envuelve el encabezado y las filas en la tabla con scroll propia."""
    return (
        f'<div class="inversa-desplazamiento"><table class="{clases}">'
        f"<thead><tr>{encabezado}</tr></thead><tbody>{''.join(filas)}</tbody></table></div>"
    )
