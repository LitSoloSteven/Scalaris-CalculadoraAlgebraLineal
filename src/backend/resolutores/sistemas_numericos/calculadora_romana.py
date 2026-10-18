"""Operaciones aritméticas con números romanos con trazabilidad paso a paso."""

from src.backend.constantes import ERROR

from dataclasses import dataclass, field
import re

ERROR_TIPO_INVALIDO = "TIPO_INVALIDO"
ERROR_ENTRADA_VACIA = "ENTRADA_VACIA"
ERROR_SINTAXIS_INVALIDA = "SINTAXIS_INVALIDA"
ERROR_NO_CANONICO = "NO_CANONICO"
ERROR_FUERA_DE_RANGO = "FUERA_DE_RANGO"
ERROR_CERO_NO_REPRESENTABLE = "CERO_NO_REPRESENTABLE"
ERROR_NEGATIVO_NO_REPRESENTABLE = "NEGATIVO_NO_REPRESENTABLE"
ERROR_OPERANDO_NO_UN_DIGITO = "OPERANDO_NO_UN_DIGITO"


class ErrorNumeroRomano(ValueError):
    """Excepción estructurada para errores de validación y cálculo en números romanos."""

    def __init__(self, mensaje: str, codigo: str, token_invalido: str | None = None) -> None:
        super().__init__(mensaje)
        self.codigo = codigo
        self.token_invalido = token_invalido

    def a_diccionario(self) -> dict:
        """Serializa el error a un diccionario para respuestas de API."""
        return {
            "estado": ERROR,
            "codigo_error": self.codigo,
            "mensaje": str(self),
            "token": self.token_invalido,
        }



PARES_DECIMAL_A_ROMANO: list[tuple[int, str]] = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]

PATRON_ROMANO = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")


def desglosar_pasos_canonicos(numero: int) -> list[dict]:
    """Devuelve sustracciones canónicas para un entero positivo representable."""
    entero_a_romano(numero)
    pasos, restante = [], numero
    for valor, simbolo in PARES_DECIMAL_A_ROMANO:
        while restante >= valor:
            anterior = restante
            restante -= valor
            pasos.append({"valor_restado": valor, "simbolo": simbolo,
                          "anterior": anterior, "restante": restante})
    return pasos


@dataclass
class ResultadoOperacionRomana:
    """Estructura del resultado de una operación aritmética romana."""

    operacion: str
    operando_a_romano: str
    operando_a_decimal: int
    operando_b_romano: str
    operando_b_decimal: int
    resultado_romano: str
    resultado_decimal: int
    pasos: list[str] = field(default_factory=list)


def entero_a_romano(numero: int) -> str:
    """Convierte un entero positivo (1 a 3999) a su representación en números romanos."""
    if not isinstance(numero, int):
        raise ErrorNumeroRomano(
            f"El valor debe ser un entero, se recibió: {type(numero).__name__}",
            codigo=ERROR_TIPO_INVALIDO,
            token_invalido=str(numero),
        )
    if numero < 1 or numero > 3999:
        raise ErrorNumeroRomano(
            f"El sistema romano tradicional solo admite números entre 1 y 3999. Recibido: {numero}",
            codigo=ERROR_FUERA_DE_RANGO,
            token_invalido=str(numero),
        )

    resultado = []
    valor = numero
    for valor_simbolo, simbolo in PARES_DECIMAL_A_ROMANO:
        while valor >= valor_simbolo:
            resultado.append(simbolo)
            valor -= valor_simbolo
    return "".join(resultado)


def _validar_formato_romano(romano: str) -> str:
    """Valida tipo no nulo, no vacío y sintaxis regex del número romano."""
    if not isinstance(romano, str):
        raise ErrorNumeroRomano(
            "La entrada debe ser una cadena de texto.",
            codigo=ERROR_TIPO_INVALIDO,
            token_invalido=str(romano),
        )
    limpio = romano.strip().upper()
    if not limpio:
        raise ErrorNumeroRomano(
            "La cadena del número romano no puede estar vacía.",
            codigo=ERROR_ENTRADA_VACIA,
            token_invalido=romano,
        )
    if not PATRON_ROMANO.match(limpio):
        raise ErrorNumeroRomano(
            f"'{romano}' no es un número romano con sintaxis válida.",
            codigo=ERROR_SINTAXIS_INVALIDA,
            token_invalido=romano,
        )
    return limpio


def romano_a_entero(romano: str) -> int:
    """Convierte una cadena de número romano a entero con validación estricta canónica."""
    limpio = _validar_formato_romano(romano)
    total, i, longitud = 0, 0, len(limpio)
    valores_car = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    while i < longitud:
        actual = valores_car[limpio[i]]
        if i + 1 < longitud and actual < valores_car[limpio[i + 1]]:
            total += valores_car[limpio[i + 1]] - actual
            i += 2
        else:
            total += actual
            i += 1

    canonico = entero_a_romano(total)
    if canonico != limpio:
        raise ErrorNumeroRomano(
            f"'{romano}' no es una forma canónica válida (se esperaba '{canonico}').",
            codigo=ERROR_NO_CANONICO,
            token_invalido=romano,
        )
    return total


class CalculadoraRomana:
    """Calculadora de operaciones aritméticas en números romanos con paso a paso."""

    @staticmethod
    def sumar(operando_a: str, operando_b: str) -> ResultadoOperacionRomana:
        """Realiza la suma A + B en números romanos."""
        valor_a, valor_b = romano_a_entero(operando_a), romano_a_entero(operando_b)
        romano_a, romano_b = entero_a_romano(valor_a), entero_a_romano(valor_b)
        total_decimal = valor_a + valor_b
        if total_decimal > 3999:
            raise ErrorNumeroRomano(
                f"El resultado de la suma ({total_decimal}) excede el límite máximo romano de 3999 (MMMCMXCIX).",
                codigo=ERROR_FUERA_DE_RANGO,
                token_invalido=str(total_decimal),
            )

        total_romano = entero_a_romano(total_decimal)
        pasos = [
            f"Paso 1: Convertir operando A a decimal -> {romano_a} = {valor_a}",
            f"Paso 2: Convertir operando B a decimal -> {romano_b} = {valor_b}",
            f"Paso 3: Realizar la adición decimal -> {valor_a} + {valor_b} = {total_decimal}",
            f"Paso 4: Convertir el total a número romano -> {total_decimal} = {total_romano}",
            f"Resultado final: {romano_a} + {romano_b} = {total_romano} ({total_decimal})",
        ]
        return ResultadoOperacionRomana("suma", romano_a, valor_a, romano_b, valor_b, total_romano, total_decimal, pasos)

    @staticmethod
    def restar(operando_a: str, operando_b: str) -> ResultadoOperacionRomana:
        """Realiza la resta A - B en números romanos."""
        valor_a, valor_b = romano_a_entero(operando_a), romano_a_entero(operando_b)
        romano_a, romano_b = entero_a_romano(valor_a), entero_a_romano(valor_b)
        if valor_a == valor_b:
            raise ErrorNumeroRomano(
                f"Resta inválida ({romano_a} - {romano_b} = 0): En el sistema de numeración romana tradicional no existe el número cero.",
                codigo=ERROR_CERO_NO_REPRESENTABLE,
            )
        if valor_a < valor_b:
            raise ErrorNumeroRomano(
                f"Resta inválida ({romano_a} - {romano_b} = {valor_a - valor_b}): En el sistema de numeración romana tradicional no existen los números negativos.",
                codigo=ERROR_NEGATIVO_NO_REPRESENTABLE,
            )

        total_decimal = valor_a - valor_b
        total_romano = entero_a_romano(total_decimal)
        pasos = [
            f"Paso 1: Convertir minuendo A a decimal -> {romano_a} = {valor_a}",
            f"Paso 2: Convertir sustraendo B a decimal -> {romano_b} = {valor_b}",
            f"Paso 3: Validar que A > B ({valor_a} > {valor_b}) para garantizar resultado positivo no nulo.",
            f"Paso 4: Realizar la sustracción decimal -> {valor_a} - {valor_b} = {total_decimal}",
            f"Paso 5: Convertir la diferencia a número romano -> {total_decimal} = {total_romano}",
            f"Resultado final: {romano_a} - {romano_b} = {total_romano} ({total_decimal})",
        ]
        return ResultadoOperacionRomana("resta", romano_a, valor_a, romano_b, valor_b, total_romano, total_decimal, pasos)

    @staticmethod
    def _calcular_sumas_multiplicacion(
        valor_a: int, valor_b: int, romano_a: str, pasos: list[str]
    ) -> tuple[int, str]:
        """Ejecuta el bucle de sumas sucesivas para la multiplicación de 1 dígito."""
        acumulador_decimal = 0
        sumas_romanas = []
        for i in range(1, valor_b + 1):
            acumulado_anterior = acumulador_decimal
            acumulador_decimal += valor_a
            sumas_romanas.append(romano_a)
            acumulado_romano = entero_a_romano(acumulador_decimal)
            if i == 1:
                pasos.append(f"   - Suma 1: Base inicial = {romano_a} ({valor_a})")
            else:
                acumulado_anterior_romano = entero_a_romano(acumulado_anterior)
                pasos.append(
                    f"   - Suma {i}: Acumulado anterior {acumulado_anterior_romano} ({acumulado_anterior}) + {romano_a} ({valor_a}) = {acumulado_romano} ({acumulador_decimal})"
                )
        return acumulador_decimal, " + ".join(sumas_romanas)

    @classmethod
    def multiplicar_un_digito(cls, operando_a: str, operando_b: str) -> ResultadoOperacionRomana:
        """Realiza la multiplicación A * B mediante sumas sucesivas repetidas."""
        valor_a, valor_b = romano_a_entero(operando_a), romano_a_entero(operando_b)
        romano_a, romano_b = entero_a_romano(valor_a), entero_a_romano(valor_b)
        if valor_a < 1 or valor_a > 9:
            raise ErrorNumeroRomano(
                f"El operando A '{romano_a}' ({valor_a}) no es de 1 dígito. Debe estar entre I (1) y IX (9).",
                codigo=ERROR_OPERANDO_NO_UN_DIGITO, token_invalido=operando_a,
            )
        if valor_b < 1 or valor_b > 9:
            raise ErrorNumeroRomano(
                f"El operando B '{romano_b}' ({valor_b}) no es de 1 dígito. Debe estar entre I (1) y IX (9).",
                codigo=ERROR_OPERANDO_NO_UN_DIGITO, token_invalido=operando_b,
            )

        pasos = [
            f"Paso 1: Convertir factores a decimal -> {romano_a} = {valor_a}, {romano_b} = {valor_b}",
            f"Paso 2: Validar restricción de 1 dígito: {valor_a} ∈ [1, 9] y {valor_b} ∈ [1, 9] (Válido).",
            f"Paso 3: Aplicar definición formal de multiplicación por sumas sucesivas:",
            f"         {romano_a} × {romano_b} = sumar '{romano_a}' ({valor_a}) un total de {valor_b} veces.",
        ]
        acumulador_decimal, exp_sumas = cls._calcular_sumas_multiplicacion(valor_a, valor_b, romano_a, pasos)
        total_romano = entero_a_romano(acumulador_decimal)
        pasos.append(f"Paso 4: Expresión expandida completa: {exp_sumas} = {total_romano} ({acumulador_decimal})")
        pasos.append(f"Resultado final: {romano_a} × {romano_b} = {total_romano} ({acumulador_decimal})")
        return ResultadoOperacionRomana("multiplicacion", romano_a, valor_a, romano_b, valor_b, total_romano, acumulador_decimal, pasos)
