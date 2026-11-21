"""Reducción acotada de la notación de cálculo a operaciones reales ordinarias."""

import ast
from itertools import islice

from .nodos_derivada import constante, llamada
from .notacion_calculo import (
    AGREGADOS, ANGULARES_RADIANES, DERIVADAS, GRADOS_POR_MEDIA_VUELTA, POSTFIJOS,
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
    return ast.Expression(body=_Expansion(maximo, unidad).expandir(arbol.body, {}))


class _Expansion:
    def __init__(self, maximo: int, unidad: str) -> None:
        self._maximo = self._restante = maximo
        self._unidad = unidad

    def expandir(self, nodo: ast.AST, indices: dict[str, int], en_derivada: bool = False) -> ast.AST:
        self._consumir()
        if isinstance(nodo, ast.Name) and nodo.id in indices:
            return constante(indices[nodo.id])
        if isinstance(nodo, ast.BinOp):
            return ast.BinOp(
                left=self.expandir(nodo.left, indices, en_derivada), op=nodo.op,
                right=self.expandir(nodo.right, indices, en_derivada),
            )
        if isinstance(nodo, ast.UnaryOp):
            return ast.UnaryOp(op=nodo.op, operand=self.expandir(nodo.operand, indices, en_derivada))
        if isinstance(nodo, ast.Call):
            return self._expandir_llamada(nodo, indices, en_derivada)
        return nodo

    def _expandir_llamada(self, nodo: ast.Call, indices: dict[str, int], en_derivada: bool) -> ast.AST:
        nombre = nodo.func.id
        if nombre in (_SUMATORIA, _PRODUCTORIA):
            return self._expandir_agregado(nodo, indices, en_derivada)
        argumento = self.expandir(nodo.args[0], indices, en_derivada or nombre in DERIVADAS)
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
            self.expandir(expresion, {**indices, indice.id: valor}, en_derivada)
            for valor in range(entero_literal(inferior), entero_literal(superior) + 1)
        )
        resultado = next(terminos)
        for termino in terminos:
            self._consumir()
            resultado = ast.BinOp(left=resultado, op=operador(), right=termino)
        return resultado

    def _expandir_derivada(self, argumento: ast.AST, orden: int) -> ast.AST:
        for _ in range(orden):
            argumento = derivar_nodo(argumento)
            cantidad = sum(1 for _ in islice(ast.walk(argumento), self._maximo + 1))
            self._consumir(cantidad)
        return argumento

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
        if nombre in _ANGULARES or nombre in ANGULARES_RADIANES.values() or nombre in DERIVADAS:
            return False
        return any(_tiene_grados_explicitos(argumento) for argumento in nodo.args)
    return any(_tiene_grados_explicitos(hijo) for hijo in ast.iter_child_nodes(nodo))
