"""Reglas simbólicas sobre nodos de funciones reales previamente validados."""
import ast
from functools import partial

from ..sintaxis.nodos_derivada import (
    constante as _constante, depende_de_x as _depende_de_x, llamada as _llamada, valor_constante as _valor_constante,
    proteger_derivada,
)
from ..sintaxis.nodos_integral import NOMBRE_INTEGRAL, construir_integral, sustituir_variable
from ..sintaxis.notacion_calculo import ANGULARES_RADIANES, GUARDIA_DERIVADA, TRIGONOMETRICAS_INVERSAS

_MENSAJE_POTENCIA_VARIABLE = (
    "La derivada de una potencia con base y exponente variables no está disponible "
    "en esta versión."
)


class ErrorDerivadaNoDisponible(ValueError):
    """Indica que la regla de derivación requerida no está soportada en esta versión."""


def derivar_nodo(nodo: ast.AST) -> ast.AST:
    """Deriva un nodo validado respecto de x; puede lanzar ErrorDerivadaNoDisponible."""
    if isinstance(nodo, ast.Call) and nodo.func.id == GUARDIA_DERIVADA:
        original, derivada = nodo.args
        return proteger_derivada(original, derivar_nodo(derivada))
    if not _depende_de_x(nodo):
        return _constante(0)
    if isinstance(nodo, ast.Name):
        return _constante(1)
    if isinstance(nodo, ast.UnaryOp):
        return _derivar_unario(nodo)
    if isinstance(nodo, ast.BinOp):
        return _derivar_binario(nodo)
    if isinstance(nodo, ast.Call):
        return _derivar_llamada(nodo)
    raise ErrorDerivadaNoDisponible("La expresión contiene un nodo que no se puede derivar.")


def _derivar_unario(nodo: ast.UnaryOp) -> ast.AST:
    derivada = derivar_nodo(nodo.operand)
    return _negar(derivada) if isinstance(nodo.op, ast.USub) else derivada


def _derivar_binario(nodo: ast.BinOp) -> ast.AST:
    if isinstance(nodo.op, ast.Pow):
        return _derivar_potencia(nodo)
    izquierda = derivar_nodo(nodo.left)
    derecha = derivar_nodo(nodo.right)
    if isinstance(nodo.op, ast.Add):
        return _suma(izquierda, derecha)
    if isinstance(nodo.op, ast.Sub):
        return _resta(izquierda, derecha)
    if isinstance(nodo.op, ast.Mult):
        return _producto_regla(nodo.left, derecha, izquierda, nodo.right)
    if isinstance(nodo.op, ast.Div):
        numerador = _resta(_producto(izquierda, nodo.right), _producto(nodo.left, derecha))
        return _cociente(numerador, _potencia(nodo.right, _constante(2)))
    raise ErrorDerivadaNoDisponible("La expresión contiene un operador que no se puede derivar.")


def _producto_regla(
    base_izquierda: ast.AST,
    derivada_derecha: ast.AST,
    derivada_izquierda: ast.AST,
    base_derecha: ast.AST,
) -> ast.AST:
    return _suma(
        _producto(derivada_izquierda, base_derecha),
        _producto(base_izquierda, derivada_derecha),
    )


def _derivar_potencia(nodo: ast.BinOp) -> ast.AST:
    exponente_depende = _depende_de_x(nodo.right)
    base_depende = _depende_de_x(nodo.left)
    if exponente_depende and base_depende:
        raise ErrorDerivadaNoDisponible(_MENSAJE_POTENCIA_VARIABLE)
    if not exponente_depende:
        derivada_base = derivar_nodo(nodo.left)
        factor = _producto(nodo.right, _potencia(nodo.left, _resta(nodo.right, _constante(1))))
        return _producto(factor, derivada_base)
    derivada_exponente = derivar_nodo(nodo.right)
    factor = _producto(
        _potencia(nodo.left, nodo.right),
        _llamada("ln", nodo.left),
    )
    return _producto(factor, derivada_exponente)


def _derivar_llamada(nodo: ast.Call) -> ast.AST:
    nombre = nodo.func.id
    if nombre == NOMBRE_INTEGRAL:
        return _derivar_integral(nodo)
    regla = _REGLAS_LLAMADA.get(nombre)
    if regla is None:
        raise ErrorDerivadaNoDisponible(f"La función {nombre} no tiene regla de derivación disponible.")
    argumento = nodo.args[0]
    return regla(argumento, derivar_nodo(argumento))


def _derivar_integral(nodo: ast.Call) -> ast.AST:
    cuerpo, variable, inferior, superior = nodo.args
    extremos = _resta(
        _derivar_extremo(cuerpo, variable, superior),
        _derivar_extremo(cuerpo, variable, inferior),
    )
    parcial = derivar_nodo(cuerpo)
    return extremos if _es_cero(parcial) else _suma(extremos, construir_integral(parcial, variable, inferior, superior))


def _derivar_extremo(cuerpo: ast.AST, variable: ast.Name, limite: ast.AST) -> ast.AST:
    cambio = derivar_nodo(limite)
    if _es_cero(cambio):
        return cambio
    return _producto(sustituir_variable(cuerpo, variable, limite), cambio)


def _regla_seno(argumento: ast.AST, derivada: ast.AST, *, coseno: str = "cos") -> ast.AST:
    return _producto(_llamada(coseno, argumento), derivada)


def _regla_coseno(argumento: ast.AST, derivada: ast.AST, *, seno: str = "sin") -> ast.AST:
    return _negar(_producto(_llamada(seno, argumento), derivada))


def _regla_tangente(argumento: ast.AST, derivada: ast.AST, *, tangente: str = "tan") -> ast.AST:
    return _producto(_suma(_constante(1), _potencia(_llamada(tangente, argumento), _constante(2))), derivada)


def _regla_arco_seno(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    raiz = _llamada("sqrt", _resta(_constante(1), _potencia(argumento, _constante(2))))
    return _cociente(derivada, raiz)


def _regla_arco_coseno(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    return _negar(_regla_arco_seno(argumento, derivada))


def _regla_arco_tangente(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    return _cociente(derivada, _suma(_constante(1), _potencia(argumento, _constante(2))))


def _regla_seno_hiperbolico(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    return _producto(_llamada("cosh", argumento), derivada)


def _regla_coseno_hiperbolico(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    return _producto(_llamada("sinh", argumento), derivada)


def _regla_tangente_hiperbolica(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    return _producto(_resta(_constante(1), _potencia(_llamada("tanh", argumento), _constante(2))), derivada)


def _regla_exponencial(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    return _producto(_llamada("exp", argumento), derivada)


def _regla_logaritmo(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    return _cociente(derivada, argumento)


def _regla_logaritmo_decimal(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    return _cociente(derivada, _producto(argumento, _llamada("ln", _constante(10))))


def _regla_logaritmo_binario(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    return _cociente(derivada, _producto(argumento, _llamada("ln", _constante(2))))


def _regla_raiz_cuadrada(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    return _cociente(derivada, _producto(_constante(2), _llamada("sqrt", argumento)))


def _regla_raiz_cubica(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    cuadrado = _potencia(_llamada("cbrt", argumento), _constante(2))
    return _cociente(derivada, _producto(_constante(3), cuadrado))


def _regla_raiz_cuarta(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    cubo = _potencia(_llamada("raiz4", argumento), _constante(3))
    return _cociente(derivada, _producto(_constante(4), cubo))


def _regla_valor_absoluto(argumento: ast.AST, derivada: ast.AST) -> ast.AST:
    return _cociente(_producto(argumento, derivada), _llamada("abs", argumento))


_REGLAS_LLAMADA = {
    "sin": _regla_seno,
    "cos": _regla_coseno,
    "tan": _regla_tangente,
    "asin": _regla_arco_seno,
    "acos": _regla_arco_coseno,
    "atan": _regla_arco_tangente,
    "sinh": _regla_seno_hiperbolico,
    "cosh": _regla_coseno_hiperbolico,
    "tanh": _regla_tangente_hiperbolica,
    "exp": _regla_exponencial,
    "ln": _regla_logaritmo,
    "log": _regla_logaritmo,
    "log10": _regla_logaritmo_decimal,
    "log2": _regla_logaritmo_binario,
    "sqrt": _regla_raiz_cuadrada,
    "cbrt": _regla_raiz_cubica,
    "raiz4": _regla_raiz_cuarta,
    "abs": _regla_valor_absoluto,
}
_REGLAS_LLAMADA.update({
    ANGULARES_RADIANES["sin"]: partial(_regla_seno, coseno=ANGULARES_RADIANES["cos"]),
    ANGULARES_RADIANES["cos"]: partial(_regla_coseno, seno=ANGULARES_RADIANES["sin"]),
    ANGULARES_RADIANES["tan"]: partial(_regla_tangente, tangente=ANGULARES_RADIANES["tan"]),
    **{ANGULARES_RADIANES[nombre]: _REGLAS_LLAMADA[nombre] for nombre in TRIGONOMETRICAS_INVERSAS},
})


def _es_cero(nodo: ast.AST) -> bool:
    valor = _valor_constante(nodo)
    return valor is not None and valor == 0


def _es_uno(nodo: ast.AST) -> bool:
    valor = _valor_constante(nodo)
    return valor is not None and valor == 1


def _es_menos_uno(nodo: ast.AST) -> bool:
    valor = _valor_constante(nodo)
    return valor is not None and valor == -1


def _negar(nodo: ast.AST) -> ast.AST:
    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.USub):
        return nodo.operand
    valor = _valor_constante(nodo)
    if valor is not None:
        return _constante(-valor)
    return ast.UnaryOp(op=ast.USub(), operand=nodo)


def _suma(izquierda: ast.AST, derecha: ast.AST) -> ast.AST:
    if _es_cero(izquierda):
        return derecha
    if _es_cero(derecha):
        return izquierda
    valor_izquierda = _valor_constante(izquierda)
    valor_derecha = _valor_constante(derecha)
    if valor_izquierda is not None and valor_derecha is not None:
        return _constante(valor_izquierda + valor_derecha)
    return ast.BinOp(left=izquierda, op=ast.Add(), right=derecha)


def _resta(izquierda: ast.AST, derecha: ast.AST) -> ast.AST:
    if _es_cero(derecha):
        return izquierda
    if _es_cero(izquierda):
        return _negar(derecha)
    valor_izquierda = _valor_constante(izquierda)
    valor_derecha = _valor_constante(derecha)
    if valor_izquierda is not None and valor_derecha is not None:
        return _constante(valor_izquierda - valor_derecha)
    return ast.BinOp(left=izquierda, op=ast.Sub(), right=derecha)


def _producto(izquierda: ast.AST, derecha: ast.AST) -> ast.AST:
    if _es_cero(izquierda) or _es_cero(derecha):
        return _constante(0)
    if _es_uno(izquierda):
        return derecha
    if _es_uno(derecha):
        return izquierda
    if _es_menos_uno(izquierda):
        return _negar(derecha)
    if _es_menos_uno(derecha):
        return _negar(izquierda)
    valor_izquierda = _valor_constante(izquierda)
    valor_derecha = _valor_constante(derecha)
    if valor_izquierda is not None and valor_derecha is not None:
        return _constante(valor_izquierda * valor_derecha)
    return ast.BinOp(left=izquierda, op=ast.Mult(), right=derecha)


def _cociente(numerador: ast.AST, denominador: ast.AST) -> ast.AST:
    if _es_uno(denominador):
        return numerador
    valor_numerador = _valor_constante(numerador)
    valor_denominador = _valor_constante(denominador)
    if valor_denominador not in (None, 0) and valor_numerador is not None:
        return _constante(valor_numerador / valor_denominador)
    return ast.BinOp(left=numerador, op=ast.Div(), right=denominador)


def _potencia(base: ast.AST, exponente: ast.AST) -> ast.AST:
    if _es_cero(exponente):
        return _constante(1)
    if _es_uno(exponente):
        return base
    return ast.BinOp(left=base, op=ast.Pow(), right=exponente)
