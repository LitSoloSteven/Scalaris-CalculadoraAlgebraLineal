"""Sintaxis y alcance léxico de una integral en el AST de funciones reales."""

import ast
from collections.abc import Iterator

from .constantes_funcion import CONSTANTES_REALES

SIMBOLO_INTEGRAL, NOMBRE_INTEGRAL = "∫", "integral"
SIMBOLO_INFINITO, NOMBRE_INFINITO = "∞", "infinito"
_VARIABLES_LIGABLES = frozenset("abcdefghijklmnopqrstuvwxyz") - CONSTANTES_REALES.keys() - {"x"}


def variable_ligable(nodo: ast.AST) -> bool:
    """Indica si el nodo es una letra disponible como variable local."""
    return isinstance(nodo, ast.Name) and nodo.id in _VARIABLES_LIGABLES


def es_integral(nodo: ast.AST) -> bool:
    """Identifica la llamada a integral por su nombre reservado."""
    return isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name) and nodo.func.id == NOMBRE_INTEGRAL


def signo_infinito(nodo: ast.AST) -> int:
    """Devuelve el signo de un límite infinito literal o cero si es una expresión real."""
    signo = -1 if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.USub) else 1
    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.USub, ast.UAdd)):
        nodo = nodo.operand
    return signo if isinstance(nodo, ast.Name) and nodo.id == NOMBRE_INFINITO else 0


def construir_integral(cuerpo: ast.AST, variable: ast.Name, inferior: ast.AST, superior: ast.AST) -> ast.Call:
    """Construye una llamada a integral a partir de sus cuatro argumentos."""
    nombre = ast.Name(id=NOMBRE_INTEGRAL, ctx=ast.Load())
    return ast.Call(func=nombre, args=[cuerpo, variable, inferior, superior], keywords=[])


def nodos_exteriores(nodo: ast.AST) -> Iterator[ast.AST]:
    """Recorre la función de x sin entrar en integrandos evaluados sobre otros intervalos."""
    yield nodo
    hijos = nodo.args[2:] if es_integral(nodo) else ast.iter_child_nodes(nodo)
    for hijo in hijos:
        yield from nodos_exteriores(hijo)


def sustituir_variable(cuerpo: ast.AST, variable: ast.Name, limite: ast.AST) -> ast.AST:
    """Sustituye ocurrencias libres en el integrando sin capturar variables del límite."""
    ocupadas = _nombres(cuerpo) | _nombres(limite)
    return _Sustitucion(variable.id, limite, ocupadas).visitar(cuerpo)


def nombres_libres(nodo: ast.AST) -> set[str]:
    """Devuelve nombres que no están ligados por una integral dentro del subárbol."""
    if isinstance(nodo, ast.Name):
        return {nodo.id}
    if es_integral(nodo):
        cuerpo, variable, inferior, superior = nodo.args
        return (nombres_libres(cuerpo) - {variable.id}) | nombres_libres(inferior) | nombres_libres(superior)
    return {nombre for hijo in ast.iter_child_nodes(nodo) for nombre in nombres_libres(hijo)}


def _nombres(nodo: ast.AST) -> set[str]:
    return {hijo.id for hijo in ast.walk(nodo) if isinstance(hijo, ast.Name)}


class _Sustitucion:
    def __init__(self, variable: str, reemplazo: ast.AST, ocupadas: set[str]) -> None:
        self._variable = variable
        self._reemplazo = reemplazo
        self._ocupadas = ocupadas
        self._nombres_reemplazo = nombres_libres(reemplazo)

    def visitar(self, nodo: ast.AST) -> ast.AST:
        """Sustituye los nombres libres sin alterar el árbol original."""
        if isinstance(nodo, ast.Name):
            return self._reemplazo if nodo.id == self._variable else nodo
        if es_integral(nodo):
            return self._visitar_integral(nodo)
        campos = {nombre: self._visitar_campo(valor) for nombre, valor in ast.iter_fields(nodo)}
        return type(nodo)(**campos)

    def _visitar_campo(self, valor: object) -> object:
        if isinstance(valor, ast.AST):
            return self.visitar(valor)
        if isinstance(valor, list):
            return [self._visitar_campo(elemento) for elemento in valor]
        return valor

    def _visitar_integral(self, nodo: ast.Call) -> ast.AST:
        cuerpo, variable, inferior, superior = nodo.args
        if variable.id != self._variable:
            if variable.id in self._nombres_reemplazo:
                cuerpo, variable = self._renombrar(cuerpo, variable)
            cuerpo = self.visitar(cuerpo)
        return construir_integral(cuerpo, variable, self.visitar(inferior), self.visitar(superior))

    def _renombrar(self, cuerpo: ast.AST, variable: ast.Name) -> tuple[ast.AST, ast.Name]:
        libres = _VARIABLES_LIGABLES - self._ocupadas
        if not libres:
            raise ValueError("Simplifica las variables locales de las integrales para derivar la expresión.")
        nombre = min(libres)
        self._ocupadas.add(nombre)
        nueva = ast.Name(id=nombre, ctx=ast.Load())
        return _Sustitucion(variable.id, nueva, self._ocupadas).visitar(cuerpo), nueva
