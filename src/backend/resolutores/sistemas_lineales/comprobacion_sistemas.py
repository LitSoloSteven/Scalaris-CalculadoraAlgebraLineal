"""Sustitucion simbolica exacta de una familia afin en cada ecuacion original."""
from fractions import Fraction

from src.backend.utilidades.formateadores import numero_a_latex, formatear_variable_para_latex


def comprobar_familia(coeficientes: list, independientes: list, parametros: dict, variables: list | None = None) -> dict:
    """Comprueba Ax=b para cualquier parametro real; devuelve filas exactas y desarrollo LaTeX."""
    _validar_dimensiones(coeficientes, independientes, parametros, variables)
    particular = parametros["particular"]
    direcciones = parametros["direcciones"]
    nombres = [formatear_variable_para_latex(nombre) for nombre in parametros["nombres_parametros"]]
    componentes = [_componente(particular[indice], [vector[indice] for vector in direcciones], nombres)
                   for indice in range(len(particular))]
    etiquetas = [formatear_variable_para_latex(nombre) for nombre in variables] if variables else [f"x_{{{indice+1}}}" for indice in range(len(particular))]
    filas = [_comprobar_fila(fila, independiente, (particular, direcciones), (componentes, nombres, etiquetas))
             for fila, independiente in zip(coeficientes, independientes)]
    coincide = all(fila["coincide"] for fila in filas)
    return {"coincide": coincide, "filas": filas, "pasos_latex": [fila["detalle_latex"] for fila in filas]}


def _validar_dimensiones(coeficientes: list, independientes: list, parametros: dict, variables: list | None) -> None:
    columnas = len(parametros["particular"])
    if not coeficientes or len(coeficientes) != len(independientes):
        raise ValueError("La comprobacion requiere una ecuacion por termino independiente.")
    vectores = coeficientes + parametros["direcciones"]
    if columnas == 0 or any(len(vector) != columnas for vector in vectores):
        raise ValueError("Las dimensiones de las ecuaciones y de la familia deben coincidir.")
    if len(parametros["direcciones"]) != len(parametros["nombres_parametros"]):
        raise ValueError("Cada direccion requiere un nombre de parametro.")
    if variables is not None and len(variables) != columnas:
        raise ValueError("Cada variable requiere una etiqueta.")


def _componente(constante: Fraction, pesos: list, nombres: list) -> str:
    terminos = [numero_a_latex(constante)]
    terminos.extend(rf"({numero_a_latex(peso)}){nombre}" for peso, nombre in zip(pesos, nombres))
    return "+".join(terminos)


def _comprobar_fila(fila: list, independiente: Fraction, vectores: tuple, presentacion: tuple) -> dict:
    particular, direcciones = vectores
    componentes, nombres, etiquetas = presentacion
    constante = sum((valor * peso for valor, peso in zip(fila, particular)), Fraction(0))
    pesos = [sum((valor * peso for valor, peso in zip(fila, vector)), Fraction(0)) for vector in direcciones]
    coincide = constante == independiente and not any(pesos)
    identidad = "+".join(rf"({numero_a_latex(valor)}){etiqueta}" for valor, etiqueta in zip(fila, etiquetas))
    sustitucion = "+".join(rf"({numero_a_latex(valor)})\left({componente}\right)"
                           for valor, componente in zip(fila, componentes))
    desarrollo = _componente(constante, pesos, nombres)
    comparacion = "=" if coincide else r"\not\equiv"
    conclusion = "Se cumple para todos los parametros reales" if coincide else "No se cumple para todos los parametros"
    detalle = (rf"{identidad}={numero_a_latex(independiente)}:\quad {sustitucion}={desarrollo}"
               rf"{comparacion}{numero_a_latex(independiente)}\quad\text{{{conclusion}}}")
    return {"constante": constante, "coeficientes_parametros": pesos, "coincide": coincide, "detalle_latex": detalle}
