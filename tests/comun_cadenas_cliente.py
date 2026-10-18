"""Resolución estática de cadenas cliente con ámbitos y detección de ciclos."""
import ast
import itertools

DECLARACIONES_AMBITO = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


class ResolutorCadenasCliente:
    """Reconstruye alternativas literales sin ejecutar Python ni evaluar entradas."""

    def __init__(self, arbol, padres):
        self._arbol = arbol
        self._padres = padres
        self._enlaces = {}
        self._registrar_asignaciones()
        self._registrar_argumentos()

    def variantes(self, nodo, visitados=frozenset()):
        """Devuelve cadenas conocidas; valores dinámicos quedan sin resolver."""
        if isinstance(nodo, ast.Constant):
            return [nodo.value] if isinstance(nodo.value, str) else []
        if isinstance(nodo, ast.Name):
            return self._resolver_nombre(nodo, visitados)
        if isinstance(nodo, ast.IfExp):
            return self.variantes(nodo.body, visitados) + self.variantes(nodo.orelse, visitados)
        if isinstance(nodo, ast.JoinedStr):
            return self._interpolar(nodo, visitados)
        if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Add):
            return self._concatenar(nodo, visitados)
        return []

    def _concatenar(self, nodo, visitados):
        izquierda = self.variantes(nodo.left, visitados) or ["__interpolacion__"]
        derecha = self.variantes(nodo.right, visitados) or ["__interpolacion__"]
        return [a + b for a, b in itertools.product(izquierda, derecha)]

    def _interpolar(self, nodo, visitados):
        opciones = []
        for parte in nodo.values:
            valor = parte.value if isinstance(parte, ast.FormattedValue) else parte
            opciones.append(self.variantes(valor, visitados) or ["__interpolacion__"])
        return ["".join(variante) for variante in itertools.product(*opciones)]

    def _ambito(self, nodo):
        actual = self._padres.get(nodo)
        while actual is not None and not isinstance(actual, DECLARACIONES_AMBITO):
            actual = self._padres.get(actual)
        return actual or self._arbol

    def _registrar_asignaciones(self):
        for nodo in ast.walk(self._arbol):
            destinos, valor = _asignacion(nodo)
            for destino in destinos:
                if isinstance(destino, ast.Name):
                    clave = (self._ambito(nodo), destino.id)
                    self._enlaces.setdefault(clave, []).append(valor)

    def _registrar_argumentos(self):
        funciones = {(self._ambito(nodo), nodo.name): nodo for nodo in ast.walk(self._arbol)
                     if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for nodo in ast.walk(self._arbol):
            if not isinstance(nodo, ast.Call) or not isinstance(nodo.func, ast.Name):
                continue
            funcion = self._buscar_funcion(nodo, funciones)
            if funcion is not None:
                self._registrar_parametros(funcion, nodo)

    def _buscar_funcion(self, nodo, funciones):
        ambito = self._ambito(nodo)
        while ambito is not None:
            funcion = funciones.get((ambito, nodo.func.id))
            if funcion is not None or ambito is self._arbol:
                return funcion
            ambito = self._ambito(ambito)
        return None

    def _registrar_parametros(self, funcion, llamada):
        parametros = funcion.args.posonlyargs + funcion.args.args
        for parametro, argumento in zip(parametros, llamada.args):
            if isinstance(argumento, ast.Constant) and isinstance(argumento.value, str):
                self._enlaces.setdefault((funcion, parametro.arg), []).append(argumento)

    def _resolver_nombre(self, nodo, visitados):
        ambito = self._ambito(nodo)
        while ambito is not None:
            clave = (ambito, nodo.id)
            if clave in self._enlaces:
                return self._resolver_enlace(clave, visitados)
            if ambito is self._arbol:
                return []
            ambito = self._ambito(ambito)
        return []

    def _resolver_enlace(self, clave, visitados):
        if clave in visitados:
            return []
        siguientes = visitados | {clave}
        return [cadena for valor in self._enlaces[clave]
                for cadena in self.variantes(valor, siguientes)]


def _asignacion(nodo):
    if isinstance(nodo, ast.Assign):
        return nodo.targets, nodo.value
    if isinstance(nodo, ast.AnnAssign) and nodo.value is not None:
        return [nodo.target], nodo.value
    return [], None
