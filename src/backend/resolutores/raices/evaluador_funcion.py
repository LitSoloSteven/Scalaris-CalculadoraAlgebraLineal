"""Evaluación segura de expresiones reales mediante una gramática AST acotada."""
import ast
from collections.abc import Callable
from math import inf

from .gramatica_funcion import analizar_expresion, FUNCIONES_REALES, CONSTANTES_REALES
from .integracion_real import integrar_real, PresupuestoIntegral
from .nodos_integral import NOMBRE_INTEGRAL, signo_infinito
from .notacion_calculo import GUARDIA_DERIVADA
from .operaciones_reales import aplicar_funcion, aplicar_operador, comprobar_real, ejecutar_operacion
from .unidades_angulares import validar_unidad_angular

FUNCIONES_PERMITIDAS = {**FUNCIONES_REALES, **CONSTANTES_REALES}


def compilar(expresion: str, *, unidad_angular: str = "radianes") -> Callable[[float], float]:
    """Valida una expresión y devuelve f(x); lanza ValueError o ErrorNoFinito si es inválida."""
    unidad = validar_unidad_angular(unidad_angular)
    arbol = analizar_expresion(expresion, unidad_angular=unidad)

    def funcion(valor: float) -> float:
        """Evalúa la expresión con argumento finito y errores de dominio controlados."""
        return _Evaluacion(unidad).nodo(arbol.body, {"x": comprobar_real(valor)})

    return funcion


def evaluar_constante_real(expresion: str) -> float:
    """Evalúa una expresión real cerrada en radianes; lanza ValueError si es inválida."""
    arbol = analizar_expresion(expresion, solo_constantes=True)
    return _Evaluacion("radianes").nodo(arbol.body, {})


def evaluar(funcion: Callable[[float], float], valor: float) -> float:
    """Devuelve f(valor) finito; lanza ErrorDominio o ErrorNoFinito para fallos numéricos."""
    argumento = comprobar_real(valor)
    return ejecutar_operacion(lambda: funcion(argumento))


class _Evaluacion:
    def __init__(self, unidad: str) -> None:
        self._unidad = unidad
        self._presupuesto: PresupuestoIntegral | None = None

    def nodo(self, nodo: ast.AST, valores: dict[str, float], en_cola: bool = False) -> float:
        """Evalúa un nodo validado en su alcance y unidad angular."""
        if isinstance(nodo, ast.Constant):
            return comprobar_real(nodo.value)
        if isinstance(nodo, ast.Name):
            return valores[nodo.id] if nodo.id in valores else CONSTANTES_REALES[nodo.id]
        if isinstance(nodo, ast.UnaryOp):
            operando = self.nodo(nodo.operand, valores, en_cola)
            return -operando if isinstance(nodo.op, ast.USub) else operando
        if isinstance(nodo, ast.BinOp):
            izquierda = self.nodo(nodo.left, valores, en_cola)
            derecha = self.nodo(nodo.right, valores, en_cola)
            return aplicar_operador(nodo.op, izquierda, derecha, admitir_subdesbordamiento=en_cola)
        if isinstance(nodo, ast.Call):
            return self._llamada(nodo, valores, en_cola)
        raise ValueError("La expresión contiene un nodo no evaluable.")

    def _llamada(self, nodo: ast.Call, valores: dict[str, float], en_cola: bool) -> float:
        nombre = nodo.func.id
        if nombre == NOMBRE_INTEGRAL:
            return self._integral(nodo, valores, en_cola)
        argumento = self.nodo(nodo.args[0], valores, en_cola)
        if nombre == GUARDIA_DERIVADA:
            return self.nodo(nodo.args[1], valores, en_cola)
        return aplicar_funcion(nombre, argumento, unidad_angular=self._unidad, admitir_subdesbordamiento=en_cola)

    def _integral(self, nodo: ast.Call, valores: dict[str, float], en_cola: bool) -> float:
        cuerpo, variable, inferior, superior = nodo.args
        signos = signo_infinito(inferior), signo_infinito(superior)
        inicio, fin = (
            signo * inf if signo else self.nodo(limite, valores, en_cola)
            for signo, limite in zip(signos, (inferior, superior))
        )
        if self._presupuesto is None:
            self._presupuesto = PresupuestoIntegral()
        presupuesto = self._presupuesto
        permitir_subdesbordamiento = en_cola or any(signos)

        def integrando(muestra: float) -> float:
            presupuesto.consumir()
            return self.nodo(cuerpo, {**valores, variable.id: muestra}, permitir_subdesbordamiento)

        return integrar_real(integrando, inicio, fin)
