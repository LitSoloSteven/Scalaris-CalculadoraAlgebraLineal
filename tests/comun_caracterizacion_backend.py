"""Materialización y serialización exacta de casos literales de caracterización."""

from dataclasses import asdict, is_dataclass
from fractions import Fraction
from importlib import import_module

from src.backend.modelos.matriz import Matriz

MODULOS = {
    "gauss": ("sistemas_lineales.gauss", "ResolutorGauss"),
    "gauss_jordan": ("sistemas_lineales.gauss_jordan", "ResolutorGaussJordan"),
    "operaciones": ("operaciones_matrices.operaciones", "ResolutorOperacionesMatrices"),
    "determinante": ("operaciones_matrices.determinante", "ResolutorDeterminante"),
    "inversa": ("operaciones_matrices.inversa", "ResolutorInversa"),
    "evaluador": ("operaciones_matrices.evaluador", "EvaluadorExpresionesMatriciales"),
    "leontief": ("operaciones_matrices.leontief", "ResolutorModeloLeontief"),
    "transformaciones": ("operaciones_matrices.transformaciones", "ResolutorTransformacionesLineales"),
    "vectores": ("operaciones_vectores.operaciones", "ResolutorOperacionesVectores"),
    "combinacion": ("operaciones_vectores.combinacion_lineal", "ResolutorCombinacionLineal"),
    "romanos": ("sistemas_numericos.calculadora_romana", "CalculadoraRomana"),
    "bases": ("sistemas_numericos.conversor_bases", "ConversorBases"),
}


def normalizar_contrato(valor):
    """Serializa objetos y fracciones conservando claves, textos y tipos numéricos."""
    if isinstance(valor, Fraction):
        return {"fraccion": [valor.numerator, valor.denominator]}
    if isinstance(valor, Matriz):
        return {"tipo": "Matriz", "datos": normalizar_contrato(valor.datos)}
    if is_dataclass(valor):
        return normalizar_contrato(asdict(valor))
    if isinstance(valor, (list, tuple)):
        return [normalizar_contrato(elemento) for elemento in valor]
    if isinstance(valor, dict):
        return {clave: normalizar_contrato(contenido) for clave, contenido in valor.items()}
    return valor


def construir_argumento(valor):
    """Materializa matrices y fracciones descritas por datos literales."""
    if isinstance(valor, dict):
        return _construir_diccionario(valor)
    if isinstance(valor, list):
        return [construir_argumento(elemento) for elemento in valor]
    return valor


def _construir_diccionario(valor):
    """Convierte un descriptor matricial o recorre un catálogo de operandos."""
    if "matriz" in valor:
        datos = [[Fraction(celda) for celda in fila] for fila in valor["matriz"]]
        return Matriz(len(datos), len(datos[0]), datos)
    if "identidad" in valor:
        orden = valor["identidad"]
        datos = [[Fraction(i == j) for j in range(orden)] for i in range(orden)]
        return Matriz(orden, orden, datos)
    return {clave: construir_argumento(elemento) for clave, elemento in valor.items()}


def ejecutar_caso(caso):
    """Ejecuta un contrato completo, incluyendo tipo y mensaje de sus excepciones."""
    modulo, clase = MODULOS[caso["familia"]]
    resolutor = getattr(import_module(f"src.backend.resolutores.{modulo}"), clase)
    argumentos = [construir_argumento(valor) for valor in caso["argumentos"]]
    opciones = caso.get("opciones", {})
    metodo = caso["metodo"]
    try:
        if caso["familia"] in ("gauss", "gauss_jordan"):
            resultado = getattr(resolutor(*argumentos, **opciones), metodo)()
        else:
            resultado = getattr(resolutor(), metodo)(*argumentos, **opciones)
        return normalizar_contrato(resultado)
    except ValueError as error:
        return {"excepcion": type(error).__name__, "mensaje": str(error),
                "atributos": normalizar_contrato(vars(error))}
