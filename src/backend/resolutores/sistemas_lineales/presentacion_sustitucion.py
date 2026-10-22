"""Etiquetas y pasos de sustitucion a partir de soluciones ya calculadas."""
from src.backend.resolutores.sistemas_lineales.modelo_solucion import ParametrosSolucion
from src.backend.utilidades.formateadores import formatear_expresion_parametrica, formatear_variable_para_latex

NOMBRES_PARAMETROS = ("t", "s", "r", "u", "v")


def _etiqueta_variable(indice: int, nombres: list[str] | None) -> str:
    if nombres and indice < len(nombres):
        return formatear_variable_para_latex(nombres[indice])
    return f"x_{{{indice + 1}}}"


def presentar_sustitucion(parametros: ParametrosSolucion, pivotes: list[int], nombres: list[str] | None) -> tuple:
    """Devuelve textos, solucion exacta opcional y pasos usando parametros, pivotes y etiquetas recibidos."""
    libres = parametros["columnas_libres"]
    etiquetas = [NOMBRES_PARAMETROS[indice] if indice < len(NOMBRES_PARAMETROS) else f"t_{indice + 1}"
                 for indice in range(len(libres))]
    parametros = {**parametros, "nombres_parametros": etiquetas}
    solucion = []
    for indice, constante in enumerate(parametros["particular"]):
        terminos = {nombre: direccion[indice] for nombre, direccion in zip(etiquetas, parametros["direcciones"])
                    if direccion[indice] != 0}
        solucion.append(formatear_expresion_parametrica(constante, terminos))
    pasos = []
    if libres:
        partes = [f"{_etiqueta_variable(columna, nombres)} = {nombre}" for columna, nombre in zip(libres, etiquetas)]
        pasos.append(rf"\text{{Variables libres identificadas: }} {', '.join(partes)}")
    pasos.extend(f"{_etiqueta_variable(columna, nombres)} = {solucion[columna]}" for columna in reversed(pivotes))
    exacta = None if libres else list(parametros["particular"])
    return solucion, exacta, pasos, libres, parametros
