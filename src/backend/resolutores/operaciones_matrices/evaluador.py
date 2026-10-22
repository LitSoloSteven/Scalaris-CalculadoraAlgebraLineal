"""Evaluador de expresiones algebraicas matriciales complejas paso a paso."""

from fractions import Fraction
import re
from typing import Any

from src.backend.constantes import ERROR, EXITO
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.analizador_expresiones import (
    convertir_a_rpn,
    tokenizar_expresion,
)
from src.backend.resolutores.operaciones_matrices.formateadores import (
    matriz_a_latex,
    multiplicar_matriz_a_latex,
    sumar_restar_matriz_a_latex,
)
from src.backend.resolutores.operaciones_matrices.operaciones import (
    ResolutorOperacionesMatrices,
)
from src.backend.resolutores.operaciones_matrices.presupuesto_expresiones import (
    validar_longitud_expresion, validar_presupuesto_operaciones,
)


def _es_escalar(valor: object) -> bool:
    """Indica si el valor es un escalar numerico en vez de una Matriz."""
    return not isinstance(valor, Matriz)


def _crear_paso_segmento(
    datos_operacion: tuple[str, str, str],
    operandos: tuple[str, str | None],
    latex: str,
    resultado_matriz: Matriz,
    pasos: list,
) -> dict:
    """Construye un paso intermedio con claves canónicas en español."""
    nombre_temporal, muestra, tipo = datos_operacion
    nombre_a, nombre_b = operandos
    resultado_latex = matriz_a_latex(resultado_matriz)
    return {
        "variable_temporal": nombre_temporal,
        "representacion_operacion": muestra,
        "tipo_operacion": tipo,
        "nombre_operando_a": nombre_a,
        "nombre_operando_b": nombre_b,
        "matriz_simbolica_latex": latex,
        "matriz_resultado_latex": resultado_latex,
        "matriz_resultado": resultado_matriz,
        "pasos_celda_a_celda": pasos,
    }


def _empaquetar_error_evaluador(mensaje: str) -> dict:
    """Construye la respuesta de error para el evaluador de expresiones."""
    return {
        "estado": ERROR,
        "mensaje": mensaje,
        "matriz_resultado": None,
        "pasos_segmento": [],
    }


def _empaquetar_exito_evaluador(
    expresion: str, nombre_final: str, valor_final: Matriz, pasos: list
) -> dict:
    """Construye la respuesta exitosa con claves canónicas para el evaluador."""
    resultado_latex = matriz_a_latex(valor_final)
    mensaje_resultado = f"Expresión '{expresion}' resuelta con éxito."
    return {
        "estado": EXITO,
        "mensaje": mensaje_resultado,
        "variable_final": nombre_final,
        "matriz_resultado": valor_final,
        "matriz_resultado_latex": resultado_latex,
        "pasos_segmento": pasos,
    }


class EvaluadorExpresionesMatriciales:
    """Parsea y evalua expresiones matriciales (ej. 2A - B(C - D^T)) en pasos atómicos."""

    def __init__(self) -> None:
        """Inicializa el evaluador con el resolutor de operaciones base."""
        self.resolutor_operaciones_matrices = ResolutorOperacionesMatrices()
        self.pasos_globales: list[dict] = []

    def _tokenizar(self, expresion: str) -> list[str]:
        """Convierte la cadena en tokens e inserta multiplicaciones implicitas."""
        return tokenizar_expresion(expresion)

    def _a_rpn(self, tokens: list[str]) -> list[str]:
        """Aplica Shunting-Yard para convertir tokens a Notacion Polaca Inversa."""
        return convertir_a_rpn(tokens)

    def _procesar_transpuesta(self, pila: list, contador: int) -> int:
        """Aplica la transpuesta sobre el operando superior de la pila."""
        if not pila:
            raise ValueError("Operación de transpuesta sin operando.")
        nombre, valor = pila.pop()
        if _es_escalar(valor):
            pila.append((f"{nombre}ᵀ", valor))
            return contador

        nombre_temporal = f"T_{{{contador}}}"
        resultado_matriz = self.resolutor_operaciones_matrices.transponer(valor)
        paso = _crear_paso_segmento(
            (nombre_temporal, f"{nombre_temporal} = {nombre}^T", "Transposición"),
            (nombre, None),
            f"{nombre}^T",
            resultado_matriz,
            [],
        )
        self.pasos_globales.append(paso)
        pila.append((nombre_temporal, resultado_matriz))
        return contador + 1

    def _procesar_negacion(self, pila: list, contador: int) -> int:
        """Aplica la negacion unaria sobre el operando superior de la pila."""
        if not pila:
            raise ValueError("Operación de negación sin operando.")
        nombre, valor = pila.pop()
        if _es_escalar(valor):
            pila.append((f"-{nombre}", -valor))
            return contador

        nombre_temporal = f"T_{{{contador}}}"
        resultado_operacion = self.resolutor_operaciones_matrices.multiplicar_escalar(Fraction(-1), valor)
        resultado_matriz = resultado_operacion["matriz_resultado"]
        paso = _crear_paso_segmento(
            (nombre_temporal, f"{nombre_temporal} = -{nombre}", "Negación"),
            (nombre, None),
            f"-{nombre}",
            resultado_matriz,
            [],
        )
        self.pasos_globales.append(paso)
        pila.append((nombre_temporal, resultado_matriz))
        return contador + 1

    def _ejecutar_binaria_matrices(
        self, token: str, nombre_a: str, valor_a: Matriz, nombre_b: str, valor_b: Matriz
    ) -> tuple[Matriz, list, str, str]:
        """Aplica suma, resta o producto entre dos matrices."""
        if token == "*":
            resultado = self.resolutor_operaciones_matrices.multiplicar(valor_a, valor_b)
            if resultado["estado"] == ERROR:
                raise ValueError(f"Error ({nombre_a} * {nombre_b}): {resultado['mensaje']}")
            return resultado["matriz_resultado"], resultado["pasos"], multiplicar_matriz_a_latex(valor_a, valor_b), "Multiplicación de Matrices"
        if token == "+":
            resultado = self.resolutor_operaciones_matrices.sumar(valor_a, valor_b)
            if resultado["estado"] == ERROR:
                raise ValueError(f"Error ({nombre_a} + {nombre_b}): {resultado['mensaje']}")
            return resultado["matriz_resultado"], resultado["pasos"], sumar_restar_matriz_a_latex(valor_a, valor_b, "+"), "Suma"
        resultado = self.resolutor_operaciones_matrices.restar(valor_a, valor_b)
        if resultado["estado"] == ERROR:
            raise ValueError(f"Error ({nombre_a} - {nombre_b}): {resultado['mensaje']}")
        return resultado["matriz_resultado"], resultado["pasos"], sumar_restar_matriz_a_latex(valor_a, valor_b, "-"), "Resta"

    def _resolver_producto_escalar_matriz(
        self, izquierda_nombre: str, izquierda_valor: Any, derecha_nombre: str, derecha_valor: Any
    ) -> tuple[Matriz, list, str, str]:
        """Calcula el producto entre un escalar y una matriz."""
        escalar = izquierda_valor if _es_escalar(izquierda_valor) else derecha_valor
        matriz = derecha_valor if _es_escalar(izquierda_valor) else izquierda_valor
        resultado_operacion = self.resolutor_operaciones_matrices.multiplicar_escalar(escalar, matriz)
        return (
            resultado_operacion["matriz_resultado"],
            [],
            f"{izquierda_nombre} \\cdot {derecha_nombre}",
            "Multiplicación Escalar",
        )

    def _despachar_binaria(
        self,
        token: str,
        izquierda: tuple[str, Any],
        derecha: tuple[str, Any],
    ) -> tuple[Matriz, list, str, str]:
        """Determina y ejecuta la operación binaria entre operandos mixtos o matriciales."""
        izquierda_nombre, izquierda_valor = izquierda
        derecha_nombre, derecha_valor = derecha
        hay_escalar = _es_escalar(izquierda_valor) or _es_escalar(derecha_valor)
        if token == "*" and hay_escalar:
            return self._resolver_producto_escalar_matriz(izquierda_nombre, izquierda_valor, derecha_nombre, derecha_valor)
        if token in ("+", "-") and hay_escalar:
            accion = "sumar" if token == "+" else "restar"
            raise ValueError(f"No se puede {accion} un escalar y una matriz.")
        return self._ejecutar_binaria_matrices(token, izquierda_nombre, izquierda_valor, derecha_nombre, derecha_valor)

    def _procesar_binaria(self, token: str, pila: list, contador: int) -> int:
        """Resuelve una operacion binaria (+, -, *) entre operandos de la pila."""
        if len(pila) < 2:
            raise ValueError("Expresión matemática mal formada.")
        derecha = pila.pop()
        izquierda = pila.pop()

        if token == "*" and _es_escalar(izquierda[1]) and _es_escalar(derecha[1]):
            pila.append((f"{izquierda[1] * derecha[1]}", izquierda[1] * derecha[1]))
            return contador

        nombre_temporal = f"T_{{{contador}}}"
        resultado_matriz, pasos, latex, operacion_palabra = self._despachar_binaria(token, izquierda, derecha)
        paso = _crear_paso_segmento(
            (nombre_temporal, f"{nombre_temporal} = {izquierda[0]} {token} {derecha[0]}", operacion_palabra),
            (izquierda[0], derecha[0]),
            latex,
            resultado_matriz,
            pasos,
        )
        self.pasos_globales.append(paso)
        pila.append((nombre_temporal, resultado_matriz))
        return contador + 1

    def _consumir_token_rpn(
        self,
        token: str,
        pila: list,
        diccionario_matrices: dict[str, Matriz],
        contador: int,
    ) -> int:
        """Procesa un token individual en el recorrido RPN y actualiza la pila."""
        if re.match(r"^\d+(\.\d+)?$", token):
            pila.append((token, Fraction(token)))
            return contador
        if re.match(r"^[A-Za-z][A-Za-z0-9_]*$", token):
            if token not in diccionario_matrices:
                raise ValueError(f"La matriz '{token}' no ha sido definida.")
            pila.append((token, diccionario_matrices[token]))
            return contador
        if token == "ᵀ":
            return self._procesar_transpuesta(pila, contador)
        if token == "¬":
            return self._procesar_negacion(pila, contador)
        if token in ("+", "-", "*"):
            return self._procesar_binaria(token, pila, contador)
        return contador

    def evaluar(self, expresion: str, diccionario_matrices: dict[str, Matriz]) -> dict:
        """Evalua la expresion algebraica completa sobre el catalogo de matrices."""
        self.pasos_globales = []
        try:
            validar_longitud_expresion(expresion)
            tokens = self._tokenizar(expresion)
            validar_presupuesto_operaciones(tokens, diccionario_matrices)
            rpn = self._a_rpn(tokens)
            pila: list = []
            contador = 1
            for token in rpn:
                contador = self._consumir_token_rpn(token, pila, diccionario_matrices, contador)

            if len(pila) != 1:
                return _empaquetar_error_evaluador("La expresión no pudo ser evaluada completamente.")
            nombre_final, valor_final = pila.pop()
            if _es_escalar(valor_final):
                return _empaquetar_error_evaluador("El resultado final es un escalar, no una matriz.")
        except ValueError as error:
            return _empaquetar_error_evaluador(str(error))

        return _empaquetar_exito_evaluador(expresion, nombre_final, valor_final, self.pasos_globales)
