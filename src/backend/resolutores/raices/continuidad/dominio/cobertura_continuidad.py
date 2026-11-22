"""Reconocimiento conservador de expresiones polinómicas en el AST validado."""
import ast


def cubre_intervalo_cerrado(arbol: ast.Expression) -> bool:
    """Determina si las operaciones del AST validado son polinómicas sobre todos los reales."""
    return _es_polinomio(arbol.body)


def _es_polinomio(nodo: ast.AST) -> bool:
    if isinstance(nodo, (ast.Constant, ast.Name)):
        return True
    if isinstance(nodo, ast.UnaryOp):
        return _es_polinomio(nodo.operand)
    if not isinstance(nodo, ast.BinOp):
        return False
    if isinstance(nodo.op, ast.Pow):
        return _exponente_natural(nodo.right) and _es_polinomio(nodo.left)
    return (isinstance(nodo.op, (ast.Add, ast.Sub, ast.Mult))
            and _es_polinomio(nodo.left) and _es_polinomio(nodo.right))


def _exponente_natural(nodo: ast.AST) -> bool:
    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.UAdd):
        nodo = nodo.operand
    return isinstance(nodo, ast.Constant) and type(nodo.value) is int and nodo.value >= 0
