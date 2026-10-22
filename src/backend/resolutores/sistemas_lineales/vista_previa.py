"""Preparación matemática exacta de vistas previas de sistemas."""

from dataclasses import dataclass
from fractions import Fraction
import re

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.formateadores import (
    matriz_aumentada_gauss_a_latex,
    formatear_expresion_lineal,
)
from src.backend.utilidades.formateadores import formatear_variable_para_latex, numero_a_latex
from src.backend.utilidades.analizadores import AnalizadorSistema
from src.backend.utilidades.validadores import ValidadorMatriz
from src.backend.resolutores.sistemas_lineales.captura_ecuaciones import contar_ecuaciones

from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS, MAXIMO_CARACTERES_ECUACIONES, MAXIMO_CELDAS_SISTEMA
_PATRON_LINEA = re.compile(r"^Línea (\d+):(.*)$")


@dataclass(frozen=True)
class ResultadoVistaPrevia:
    """Agrupa el estado inmutable de una matriz o sistema para previsualizar."""

    estado: str
    matriz: tuple[tuple[Fraction | None, ...], ...] | None
    variables: tuple[str, ...]
    mensaje: str


def analizar_ecuaciones(lineas: list[str]) -> ResultadoVistaPrevia:
    """Analiza ecuaciones y conserva el número original de cada línea."""
    if _excede_longitud_ecuaciones(lineas):
        mensaje = f"Reduce el texto a {MAXIMO_CARACTERES_ECUACIONES} caracteres para ver la vista previa."
        return ResultadoVistaPrevia("error", None, (), mensaje)
    escritas = [(indice, linea.strip()) for indice, linea in enumerate(lineas, 1) if linea.strip()]
    if not escritas:
        return ResultadoVistaPrevia("vacio", None, (), "")
    if contar_ecuaciones(lineas) > DIMENSION_MAXIMA_SISTEMAS:
        mensaje = f"La vista previa admite hasta {DIMENSION_MAXIMA_SISTEMAS} ecuaciones."
        return ResultadoVistaPrevia("error", None, (), mensaje)
    texto = "\n".join(linea for _, linea in escritas)
    correcto, matriz, variables, mensaje = AnalizadorSistema.parsear_sistema(texto)
    if correcto:
        if _excede_dimensiones(matriz, variables):
            mensaje = f"La vista previa admite hasta {DIMENSION_MAXIMA_SISTEMAS} variables."
            return ResultadoVistaPrevia("error", None, (), mensaje)
        filas = tuple(tuple(fila) for fila in matriz.datos)
        return ResultadoVistaPrevia("ok", filas, tuple(variables), "")
    return ResultadoVistaPrevia("error", None, (), _mensaje_ecuacion_original(mensaje, escritas))


def _excede_dimensiones(matriz: Matriz, variables: list[str]) -> bool:
    """Comprueba ambas dimensiones del resultado analizado con el límite canónico."""
    return len(variables) > DIMENSION_MAXIMA_SISTEMAS or matriz.filas > DIMENSION_MAXIMA_SISTEMAS


def _excede_longitud_ecuaciones(lineas):
    """Detiene el conteo al superar el límite de texto de la vista previa."""
    longitud = 0
    for linea in lineas:
        longitud += len(linea)
        if longitud > MAXIMO_CARACTERES_ECUACIONES:
            return True
    return False


def _mensaje_ecuacion_original(mensaje, escritas):
    """Relaciona el error del analizador con la línea escrita antes de quitar vacíos."""
    mensaje = mensaje.replace(chr(0x2014), "-")
    coincidencia = _PATRON_LINEA.match(mensaje)
    if coincidencia:
        indice = int(coincidencia.group(1)) - 1
        if 0 <= indice < len(escritas):
            mensaje = f"Ecuación {escritas[indice][0]}:{coincidencia.group(2)}"
    return mensaje


def latex_matriz_aumentada(
    matriz: tuple[tuple[Fraction | None, ...], ...], numero_variables: int
) -> str:
    """Devuelve la representación LaTeX de una matriz aumentada."""
    if not matriz:
        return ""
    celdas_invalidas = {
        (fila, columna)
        for fila, valores in enumerate(matriz)
        for columna, valor in enumerate(valores)
        if valor is None
    }
    datos = [[valor if valor is not None else 0 for valor in fila] for fila in matriz]
    matriz_backend = Matriz(len(datos), len(datos[0]), datos)
    latex = matriz_aumentada_gauss_a_latex(matriz_backend, numero_variables)
    filas = latex.split(r" \\ ")
    if len(filas) != len(matriz):
        return latex
    for fila, valores_invalidos in enumerate(_invalidas_por_fila(len(matriz), celdas_invalidas)):
        filas[fila] = _marcar_celdas_invalidas(filas[fila], valores_invalidos)
    return r" \\ ".join(filas)


def _marcar_celdas_invalidas(fila_latex, columnas):
    """Sustituye solo las celdas inválidas por un interrogante en la fila LaTeX."""
    celdas = fila_latex.split(" & ")
    for columna in columnas:
        if columna < len(celdas):
            celdas[columna] = r"\color{gray}{?}"
    return " & ".join(celdas)


def latex_sistema(
    matriz: tuple[tuple[Fraction | None, ...], ...], variables: tuple[str, ...]
) -> str:
    """Devuelve las ecuaciones de una matriz aumentada dentro de cases."""
    ecuaciones = []
    variables_latex = [formatear_variable_para_latex(variable) for variable in variables]
    for fila in matriz:
        coeficientes = [fila[columna] for columna in range(len(variables))]
        expresion = formatear_expresion_lineal(coeficientes, variables_latex)
        termino = numero_a_latex(fila[len(variables)])
        ecuaciones.append(f"{expresion} = {termino}")
    return r"\begin{cases} " + r" \\ ".join(ecuaciones) + r" \end{cases}"


def matriz_desde_celdas(
    matriz_a: list[list[str]], vector_b: list[str]
) -> ResultadoVistaPrevia:
    """Convierte las celdas editables en una matriz aumentada exacta."""
    if not matriz_a or not matriz_a[0]:
        return ResultadoVistaPrevia("vacio", None, (), "")
    datos: list[tuple[Fraction | None, ...]] = []
    errores = False
    columnas = len(matriz_a[0])
    for indice_fila, fila in enumerate(matriz_a):
        valor_b = vector_b[indice_fila] if indice_fila < len(vector_b) else "0"
        datos_fila = _parsear_fila_aumentada(fila, valor_b)
        errores = errores or None in datos_fila
        datos.append(datos_fila)
    variables = tuple(f"x{indice + 1}" for indice in range(columnas))
    estado = "error" if errores else "ok"
    mensaje = "Corrige los valores inválidos para ver las ecuaciones." if errores else ""
    return ResultadoVistaPrevia(estado, tuple(datos), variables, mensaje)


def _parsear_fila_aumentada(fila, termino):
    """Convierte una fila y su término a fracciones, marcando entradas inválidas."""
    datos_fila = []
    for valor in [*fila, termino]:
        parseado, numero, _ = ValidadorMatriz.parsear_numero_exacto(valor or "0")
        datos_fila.append(numero if parseado else None)
    return tuple(datos_fila)


def _invalidas_por_fila(
    cantidad_filas: int, invalidas: set[tuple[int, int]]
) -> list[set[int]]:
    """Identifica valores de marcado especial en filas de la matriz."""
    filas = [set() for _ in range(cantidad_filas)]
    for fila, columna in invalidas:
        filas[fila].add(columna)
    return filas


def preparar_vista_previa(captura: dict) -> dict:
    """Entrega estado y bloques LaTeX serializables, aplicando los límites de dominio."""
    if "ecuaciones" in captura:
        resultado = analizar_ecuaciones(captura["ecuaciones"])
    else:
        resultado = matriz_desde_celdas(captura["matriz_a"], captura["vector_b"])
    salida = {"estado": resultado.estado, "mensaje": resultado.mensaje,
              "matriz_latex": None, "sistema_latex": None}
    if resultado.matriz is None:
        return salida
    cantidad_variables = len(resultado.variables)
    salida["matriz_latex"] = latex_matriz_aumentada(resultado.matriz, cantidad_variables)
    if len(resultado.matriz) * cantidad_variables > MAXIMO_CELDAS_SISTEMA:
        salida["mensaje_sistema"] = "Sistema demasiado grande para vista previa en ecuaciones."
    elif resultado.estado == "ok":
        salida["sistema_latex"] = latex_sistema(resultado.matriz, resultado.variables)
    return salida
