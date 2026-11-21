"""Reducción acotada de la notación de cálculo a operaciones reales ordinarias."""

import ast
from itertools import islice

from .compartido.errores_numericos import ErrorCapacidadNumerica
from .funcion_real.sintaxis.nodos_derivada import constante, llamada, proteger_derivada
from .funcion_real.sintaxis.nodos_integral import NOMBRE_INTEGRAL, construir_integral
from .funcion_real.sintaxis.notacion_calculo import (
    AGREGADOS, ANGULARES_RADIANES, DERIVADAS, GRADOS_POR_MEDIA_VUELTA, GUARDIA_DERIVADA, POSTFIJOS,
    TRIGONOMETRICAS_DIRECTAS, TRIGONOMETRICAS_INVERSAS, UNIDADES_POR_MIL, entero_literal,
)
from .reglas_derivacion import derivar_nodo

_SUMATORIA = AGREGADOS["∑"]
_PRODUCTORIA = AGREGADOS["∏"]
_GRADOS = POSTFIJOS["°"]
_POR_MIL = POSTFIJOS["‰"]
_ANGULARES = (*TRIGONOMETRICAS_DIRECTAS, *TRIGONOMETRICAS_INVERSAS)
_MENSAJE_PRESUPUESTO = "La expresión contiene demasiadas operaciones al desarrollar los símbolos de cálculo."


def desarrollar_calculo(arbol: ast.Expression, maximo: int, unidad: str) -> ast.Expression:
    """Devuelve el AST desarrollado; lanza ValueError si el cálculo excede el presupuesto."""
    return ast.Expression(body=_Expansion(maximo, unidad)._expandir(arbol.body, {}))


class _Expansion:
    def __init__(self, maximo: int, unidad: str) -> None:
        self._maximo = self._restante = maximo
        self._unidad = unidad

    def _expandir(self, nodo: ast.AST, indices: dict[str, int], en_derivada: bool = False) -> ast.AST:
        self._consumir()
        if isinstance(nodo, ast.Name) and nodo.id in indices:
            return constante(indices[nodo.id])
        if isinstance(nodo, ast.BinOp):
            return ast.BinOp(
                left=self._expandir(nodo.left, indices, en_derivada), op=nodo.op,
                right=self._expandir(nodo.right, indices, en_derivada),
            )
        if isinstance(nodo, ast.UnaryOp):
            return ast.UnaryOp(op=nodo.op, operand=self._expandir(nodo.operand, indices, en_derivada))
        if isinstance(nodo, ast.Call):
            return self._expandir_llamada(nodo, indices, en_derivada)
        return nodo

    def _expandir_llamada(self, nodo: ast.Call, indices: dict[str, int], en_derivada: bool) -> ast.AST:
        nombre = nodo.func.id
        if nombre in (_SUMATORIA, _PRODUCTORIA):
            return self._expandir_agregado(nodo, indices, en_derivada)
        if nombre == NOMBRE_INTEGRAL:
            return self._expandir_integral(nodo, indices, en_derivada)
        argumento = self._expandir(nodo.args[0], indices, en_derivada or nombre in DERIVADAS)
        if nombre == GUARDIA_DERIVADA:
            return proteger_derivada(argumento, self._expandir(nodo.args[1], indices, en_derivada))
        if nombre in DERIVADAS:
            return self._expandir_derivada(argumento, DERIVADAS[nombre])
        if nombre == _GRADOS:
            return _escalar_grados(argumento)
        if nombre == _POR_MIL:
            return ast.BinOp(left=argumento, op=ast.Div(), right=constante(UNIDADES_POR_MIL))
        return self._expandir_angular(nombre, nodo.args[0], argumento, en_derivada)

    def _expandir_agregado(self, nodo: ast.Call, indices: dict[str, int], en_derivada: bool) -> ast.AST:
        indice, inferior, superior, expresion = nodo.args
        operador = ast.Add if nodo.func.id == _SUMATORIA else ast.Mult
        terminos = (
            self._expandir(expresion, {**indices, indice.id: valor}, en_derivada)
            for valor in range(entero_literal(inferior), entero_literal(superior) + 1)
        )
        resultado = next(terminos)
        for termino in terminos:
            self._consumir()
            resultado = ast.BinOp(left=resultado, op=operador(), right=termino)
        return resultado

    def _expandir_integral(self, nodo: ast.Call, indices: dict[str, int], en_derivada: bool) -> ast.Call:
        cuerpo, variable, inferior, superior = nodo.args
        indices_cuerpo = {nombre: valor for nombre, valor in indices.items() if nombre != variable.id}
        return construir_integral(
            self._expandir(cuerpo, indices_cuerpo, en_derivada), variable,
            self._expandir(inferior, indices, en_derivada), self._expandir(superior, indices, en_derivada),
        )

    def _expandir_derivada(self, argumento: ast.AST, orden: int) -> ast.AST:
        resultado = argumento
        for _ in range(orden):
            try:
                argumento = derivar_nodo(argumento)
            except OverflowError as error:
                raise ErrorCapacidadNumerica("La derivada excede la capacidad numérica.") from error
            resultado = proteger_derivada(resultado, argumento)
            cantidad = sum(1 for _ in islice(ast.walk(resultado), self._maximo + 1))
            self._consumir(cantidad)
        return resultado

    def _expandir_angular(self, nombre: str, original: ast.AST, argumento: ast.AST, en_derivada: bool) -> ast.AST:
        if nombre in TRIGONOMETRICAS_DIRECTAS and _tiene_grados_explicitos(original):
            return llamada(ANGULARES_RADIANES[nombre], argumento)
        if not en_derivada or self._unidad != "grados":
            return llamada(nombre, argumento)
        if nombre in TRIGONOMETRICAS_DIRECTAS:
            return llamada(ANGULARES_RADIANES[nombre], _escalar_grados(argumento))
        if nombre in TRIGONOMETRICAS_INVERSAS:
            escala = ast.BinOp(left=constante(GRADOS_POR_MEDIA_VUELTA), op=ast.Div(), right=ast.Name(id="pi", ctx=ast.Load()))
            return ast.BinOp(left=llamada(ANGULARES_RADIANES[nombre], argumento), op=ast.Mult(), right=escala)
        return llamada(nombre, argumento)

    def _consumir(self, cantidad: int = 1) -> None:
        self._restante -= cantidad
        if self._restante < 0:
            raise ValueError(_MENSAJE_PRESUPUESTO)


def _escalar_grados(argumento: ast.AST) -> ast.BinOp:
    escala = ast.BinOp(left=ast.Name(id="pi", ctx=ast.Load()), op=ast.Div(), right=constante(GRADOS_POR_MEDIA_VUELTA))
    return ast.BinOp(left=argumento, op=ast.Mult(), right=escala)


def _tiene_grados_explicitos(nodo: ast.AST) -> bool:
    if isinstance(nodo, ast.Call):
        nombre = nodo.func.id
        if nombre == _GRADOS:
            return True
        if nombre == GUARDIA_DERIVADA:
            return _tiene_grados_explicitos(nodo.args[1])
        if nombre in _ANGULARES or nombre in ANGULARES_RADIANES.values() or nombre in DERIVADAS:
            return False
        if nombre == NOMBRE_INTEGRAL:
            return _tiene_grados_explicitos(nodo.args[0])
        return any(_tiene_grados_explicitos(argumento) for argumento in nodo.args)
    return any(_tiene_grados_explicitos(hijo) for hijo in ast.iter_child_nodes(nodo))
