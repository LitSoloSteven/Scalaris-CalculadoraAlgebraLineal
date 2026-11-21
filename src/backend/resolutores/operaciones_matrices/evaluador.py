"""Evaluador de expresiones algebraicas matriciales complejas paso a paso."""

from fractions import Fraction
from operator import add, mul, sub, truediv

from src.backend.constantes import ERROR, EXITO
from src.backend.modelos.escalares.entrada_numerica import fraccion_desde_texto
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.analizador_expresiones import (
    OPERADORES_BINARIOS,
    convertir_a_rpn,
    es_nombre_matriz,
    es_numero,
    exponente_de,
    tokenizar_expresion,
)
from src.backend.resolutores.operaciones_matrices.formateadores import (
    matriz_a_latex,
    multiplicar_matriz_a_latex,
    sumar_restar_matriz_a_latex,
)
from src.backend.resolutores.operaciones_matrices.operaciones import (
    ResolutorOperacionesMatrices,
    elevar_matriz,
    producto_kronecker,
    sumar_directa,
)
from src.backend.resolutores.operaciones_matrices.presupuesto_expresiones import (
    PresupuestoExpresion,
    validar_longitud_expresion,
    validar_magnitud,
    validar_presupuesto_operaciones,
)
from src.backend.utilidades.formato.formateadores import numero_a_latex

_Operandos = tuple[str, Fraction | Matriz]
_Resultado = tuple[Matriz, list, str, str]
_BLOQUES = {"⊕": (sumar_directa, r"\oplus", "Suma directa"),
            "⊗": (producto_kronecker, r"\otimes", "Producto de Kronecker")}
_OPERACIONES_ESCALARES = {"+": add, "-": sub, "*": mul, "/": truediv}
_ERROR_DIVISION_CERO = "No se puede dividir entre cero."


def _apilar_escalar(pila: list[_Operandos], valor: Fraction, literal: str | None = None) -> None:
    validar_magnitud(valor)
    pila.append((literal or numero_a_latex(valor), valor))


def _operar_escalares(token: str, izquierda: Fraction, derecha: Fraction) -> Fraction:
    if token in _BLOQUES:
        raise ValueError(f"El operador {token} requiere dos matrices.")
    if token == "/" and derecha == 0:
        raise ValueError(_ERROR_DIVISION_CERO)
    return _OPERACIONES_ESCALARES[token](izquierda, derecha)


def _forma_binaria(token: str, izquierda: Matriz, derecha: Matriz) -> tuple[int, int]:
    if token == "⊕":
        return izquierda.filas + derecha.filas, izquierda.columnas + derecha.columnas
    if token == "⊗":
        return izquierda.filas * derecha.filas, izquierda.columnas * derecha.columnas
    if token == "*":
        return izquierda.filas, derecha.columnas
    return izquierda.filas, izquierda.columnas


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
    """Evalúa expresiones matriciales y registra un segmento por operación matricial."""

    def __init__(self) -> None:
        """Inicializa el evaluador con el resolutor de operaciones base."""
        self.resolutor_operaciones_matrices = ResolutorOperacionesMatrices()
        self.pasos_globales: list[dict] = []
        self._presupuesto = PresupuestoExpresion()

    def _tokenizar(self, expresion: str) -> list[str]:
        """Convierte la cadena en tokens e inserta multiplicaciones implicitas."""
        return tokenizar_expresion(expresion)

    def _registrar_segmento(
        self, pila: list[_Operandos], contador: int, operandos: tuple[str, str | None],
        resultado: _Resultado, muestra: str,
    ) -> int:
        matriz, pasos, latex, tipo = resultado
        validar_magnitud(matriz)
        nombre_temporal = f"T_{{{contador}}}"
        paso = _crear_paso_segmento(
            (nombre_temporal, f"{nombre_temporal} = {muestra}", tipo),
            operandos, latex, matriz, pasos,
        )
        self.pasos_globales.append(paso)
        pila.append((nombre_temporal, matriz))
        return contador + 1

    def _operar_unaria_matriz(self, token: str, nombre: str, valor: Matriz) -> _Resultado:
        operaciones = self.resolutor_operaciones_matrices
        exponente = exponente_de(token)
        self._presupuesto.reservar(valor.filas, valor.columnas, max(1, abs(exponente or 0)))
        if exponente is not None:
            tipo = "Inversión" if exponente == -1 else "Potencia matricial"
            return elevar_matriz(valor, exponente), [], f"{{{nombre}}}^{{{exponente}}}", tipo
        if token == "ᵀ":
            return operaciones.transponer(valor), [], f"{nombre}^T", "Transposición"
        resultado = operaciones.multiplicar_escalar(Fraction(-1), valor)
        return resultado["matriz_resultado"], [], f"-{nombre}", "Negación"

    def _procesar_unaria(self, token: str, pila: list[_Operandos], contador: int) -> int:
        nombre, valor = pila.pop()
        if isinstance(valor, Matriz):
            resultado = self._operar_unaria_matriz(token, nombre, valor)
            return self._registrar_segmento(pila, contador, (nombre, None), resultado, resultado[2])
        exponente = exponente_de(token)
        if exponente is not None:
            if valor == 0 and exponente < 0:
                raise ValueError(_ERROR_DIVISION_CERO)
            validar_magnitud(valor, abs(exponente))
            valor = valor ** exponente
        _apilar_escalar(pila, -valor if token == "¬" else valor)
        return contador

    def _ejecutar_binaria_matrices(
        self, token: str, izquierda: Matriz, derecha: Matriz
    ) -> _Resultado:
        if token == "/":
            raise ValueError("El divisor debe ser un escalar.")
        self._presupuesto.reservar(*_forma_binaria(token, izquierda, derecha))
        if token in _BLOQUES:
            calcular, simbolo, tipo = _BLOQUES[token]
            formula = f"{matriz_a_latex(izquierda)} {simbolo} {matriz_a_latex(derecha)}"
            return calcular(izquierda, derecha), [], formula, tipo

        operaciones = self.resolutor_operaciones_matrices
        calcular = {"*": operaciones.multiplicar, "+": operaciones.sumar, "-": operaciones.restar}[token]
        resultado = calcular(izquierda, derecha)
        if resultado["estado"] == ERROR:
            raise ValueError(resultado["mensaje"])
        if token == "*":
            formula = multiplicar_matriz_a_latex(izquierda, derecha)
            tipo = "Multiplicación de Matrices"
        else:
            formula = sumar_restar_matriz_a_latex(izquierda, derecha, token)
            tipo = "Suma" if token == "+" else "Resta"
        return resultado["matriz_resultado"], resultado["pasos"], formula, tipo

    def _ejecutar_binaria_mixta(
        self, token: str, izquierda: _Operandos, derecha: _Operandos
    ) -> _Resultado:
        nombre_izquierda, valor_izquierda = izquierda
        nombre_derecha, valor_derecha = derecha
        matriz, escalar = (valor_izquierda, valor_derecha) if isinstance(valor_izquierda, Matriz) else (
            valor_derecha, valor_izquierda
        )
        if token == "/":
            if isinstance(valor_derecha, Matriz):
                raise ValueError("El divisor debe ser un escalar.")
            escalar = _operar_escalares("/", Fraction(1), escalar)
            formula, tipo = rf"\frac{{{nombre_izquierda}}}{{{nombre_derecha}}}", "División escalar"
        elif token == "*":
            formula, tipo = rf"{nombre_izquierda} \cdot {nombre_derecha}", "Multiplicación Escalar"
        elif token in _BLOQUES:
            raise ValueError(f"El operador {token} requiere dos matrices.")
        else:
            accion = "sumar" if token == "+" else "restar"
            raise ValueError(f"No se puede {accion} un escalar y una matriz.")

        self._presupuesto.reservar(matriz.filas, matriz.columnas)
        resultado = self.resolutor_operaciones_matrices.multiplicar_escalar(escalar, matriz)
        if resultado["estado"] == ERROR:
            raise ValueError(resultado["mensaje"])
        return resultado["matriz_resultado"], resultado["pasos"] if token == "/" else [], formula, tipo

    def _procesar_binaria(self, token: str, pila: list[_Operandos], contador: int) -> int:
        derecha = pila.pop()
        izquierda = pila.pop()
        nombre_izquierda, valor_izquierda = izquierda
        nombre_derecha, valor_derecha = derecha
        matriz_izquierda = isinstance(valor_izquierda, Matriz)
        matriz_derecha = isinstance(valor_derecha, Matriz)
        if not (matriz_izquierda or matriz_derecha):
            _apilar_escalar(pila, _operar_escalares(token, valor_izquierda, valor_derecha))
            return contador

        if matriz_izquierda and matriz_derecha:
            try:
                resultado = self._ejecutar_binaria_matrices(token, valor_izquierda, valor_derecha)
            except ValueError as error:
                raise ValueError(f"Error ({nombre_izquierda} {token} {nombre_derecha}): {error}") from error
        else:
            resultado = self._ejecutar_binaria_mixta(token, izquierda, derecha)
        simbolo = _BLOQUES[token][1] if token in _BLOQUES else token
        muestra = resultado[2] if token == "/" else f"{nombre_izquierda} {simbolo} {nombre_derecha}"
        return self._registrar_segmento(pila, contador, (nombre_izquierda, nombre_derecha), resultado, muestra)

    def _consumir_token_rpn(
        self,
        token: str,
        pila: list[_Operandos],
        diccionario_matrices: dict[str, Matriz],
        contador: int,
    ) -> int:
        """Procesa un token individual en el recorrido RPN y actualiza la pila."""
        if es_numero(token):
            literal = token if token[-1].isdecimal() else None
            _apilar_escalar(pila, fraccion_desde_texto(token), literal)
            return contador
        if es_nombre_matriz(token):
            if token not in diccionario_matrices:
                raise ValueError(f"La matriz '{token}' no ha sido definida.")
            matriz = diccionario_matrices[token]
            validar_magnitud(matriz)
            pila.append((token, matriz))
            return contador
        if token in OPERADORES_BINARIOS:
            return self._procesar_binaria(token, pila, contador)
        return self._procesar_unaria(token, pila, contador)

    def evaluar(self, expresion: str, diccionario_matrices: dict[str, Matriz]) -> dict:
        """Devuelve el resultado matricial y sus pasos o un error de sintaxis, cálculo o presupuesto."""
        self.pasos_globales = []
        self._presupuesto = PresupuestoExpresion()
        try:
            validar_longitud_expresion(expresion)
            tokens = self._tokenizar(expresion)
            validar_presupuesto_operaciones(tokens, diccionario_matrices)
            rpn = convertir_a_rpn(tokens)
            pila: list[_Operandos] = []
            contador = 1
            for token in rpn:
                contador = self._consumir_token_rpn(token, pila, diccionario_matrices, contador)

            if len(pila) != 1:
                return _empaquetar_error_evaluador("La expresión no pudo ser evaluada completamente.")
            nombre_final, valor_final = pila.pop()
            if not isinstance(valor_final, Matriz):
                return _empaquetar_error_evaluador("El resultado final es un escalar, no una matriz.")
        except ValueError as error:
            return _empaquetar_error_evaluador(str(error))

        return _empaquetar_exito_evaluador(expresion, nombre_final, valor_final, self.pasos_globales)
