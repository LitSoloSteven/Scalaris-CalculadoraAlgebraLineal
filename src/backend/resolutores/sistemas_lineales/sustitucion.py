"""Algoritmo de sustitucion hacia atras con expresiones parametricas exactas."""

from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.modelo_solucion import (
    ParametrosSolucion,
    validar_invariantes_parametricos,
)
from src.backend.utilidades.formateadores import (
    formatear_expresion_parametrica,
    formatear_variable_para_latex,
)


def _obtener_etiqueta_variable(
    indice: int,
    nombres_variables: list[str] | None,
) -> str:
    """Devuelve la representacion en LaTeX de una variable del sistema."""
    if nombres_variables and indice < len(nombres_variables):
        return formatear_variable_para_latex(nombres_variables[indice])
    return f"x_{{{indice + 1}}}"


def _inicializar_variables_libres(
    columnas_libres: list[int],
    numero_variables: int,
    nombres_variables: list[str] | None,
) -> tuple[dict[int, str], list[dict[str, Fraction]], list[str]]:
    """Construye nombres y terminos iniciales para variables libres."""
    nombres_parametros = ["t", "s", "r", "u", "v"]
    mapa_libres: dict[int, str] = {}
    for indice, columna in enumerate(columnas_libres):
        nombre = nombres_parametros[indice] if indice < len(nombres_parametros) else f"t_{indice + 1}"
        mapa_libres[columna] = nombre

    terminos: list[dict[str, Fraction]] = [{} for _ in range(numero_variables)]
    pasos_libres: list[str] = []
    if columnas_libres:
        partes = [
            f"{_obtener_etiqueta_variable(c, nombres_variables)} = {mapa_libres[c]}"
            for c in columnas_libres
        ]
        pasos_libres.append(rf"\text{{Variables libres identificadas: }} {', '.join(partes)}")
        for c in columnas_libres:
            terminos[c] = {mapa_libres[c]: Fraction(1)}

    return mapa_libres, terminos, pasos_libres


def _despejar_fila(
    matriz: Matriz,
    fila_indice: int,
    columna_pivote: int,
    numero_variables: int,
    acumulados: tuple[list[Fraction], list[dict[str, Fraction]]],
) -> tuple[Fraction, dict[str, Fraction]]:
    """Despeja el valor constante y terminos parametricos de una fila pivote."""
    constantes, terminos = acumulados
    pivote_valor = Fraction(matriz.obtener(fila_indice, columna_pivote))
    termino_indep = Fraction(matriz.obtener(fila_indice, numero_variables))

    c_valor = termino_indep
    t_valor: dict[str, Fraction] = {}
    for j in range(columna_pivote + 1, numero_variables):
        coef = Fraction(matriz.obtener(fila_indice, j))
        if coef != 0:
            c_valor -= coef * constantes[j]
            for variable, v_coef in terminos[j].items():
                t_valor[variable] = t_valor.get(variable, Fraction(0)) - (coef * v_coef)

    c_valor /= pivote_valor
    t_valor = {nombre_variable: coeficiente / pivote_valor for nombre_variable, coeficiente in t_valor.items() if (coeficiente / pivote_valor) != 0}
    return c_valor, t_valor


def _construir_parametros_solucion(
    numero_variables: int,
    columnas_libres: list[int],
    mapa_libres: dict[int, str],
    expresion_constante: list[Fraction],
    expresion_terminos: list[dict[str, Fraction]],
) -> ParametrosSolucion:
    """Construye y valida defensivamente el diccionario de solucion parametrica."""
    nombres_ordenados = [mapa_libres[c] for c in columnas_libres]
    direcciones = [
        [expresion_terminos[i].get(nombre, Fraction(0)) for i in range(numero_variables)]
        for nombre in nombres_ordenados
    ]
    validar_invariantes_parametricos(direcciones, expresion_constante, columnas_libres)
    return {
        "numero_variables": numero_variables,
        "columnas_libres": list(columnas_libres),
        "nombres_parametros": nombres_ordenados,
        "particular": list(expresion_constante),
        "direcciones": direcciones,
    }


def ejecutar_sustitucion_hacia_atras(
    matriz: Matriz,
    columnas_pivote: list[int],
    numero_variables: int,
    nombres_variables: list[str] | None,
) -> tuple[list[str], list[Fraction] | None, list[str], list[int], ParametrosSolucion]:
    """Resuelve la sustitucion regresiva construyendo representacion parametrica."""
    columnas_libres = [c for c in range(numero_variables) if c not in columnas_pivote]
    mapa_libres, expresion_terminos, pasos = _inicializar_variables_libres(
        columnas_libres, numero_variables, nombres_variables
    )
    expresion_constante = [Fraction(0)] * numero_variables

    for i in range(len(columnas_pivote) - 1, -1, -1):
        p_columna = columnas_pivote[i]
        c_valor, t_valor = _despejar_fila(matriz, i, p_columna, numero_variables, (expresion_constante, expresion_terminos))
        expresion_constante[p_columna] = c_valor
        expresion_terminos[p_columna] = t_valor
        etiqueta = _obtener_etiqueta_variable(p_columna, nombres_variables)
        pasos.append(f"{etiqueta} = {formatear_expresion_parametrica(c_valor, t_valor)}")

    solucion = [
        formatear_expresion_parametrica(expresion_constante[i], expresion_terminos[i])
        for i in range(numero_variables)
    ]
    solucion_exacta = None if columnas_libres else list(expresion_constante)
    parametros_solucion = _construir_parametros_solucion(
        numero_variables, columnas_libres, mapa_libres, expresion_constante, expresion_terminos
    )
    return solucion, solucion_exacta, pasos, columnas_libres, parametros_solucion
