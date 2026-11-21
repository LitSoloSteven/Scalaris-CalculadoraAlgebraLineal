"""Analizadores sintácticos para sistemas de ecuaciones lineales."""

from fractions import Fraction
import re

from src.backend.modelos.entrada_numerica import (
    DIVISIONES_TIPOGRAFICAS, FRACCIONES_TIPOGRAFICAS, SIGNO_MENOS_TIPOGRAFICO, SIMBOLO_POR_MIL,
)
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.validadores import ValidadorMatriz

_LETRAS_VARIABLE = "a-zA-ZΑ-Ωα-ω"
_DIGITOS_SUBINDICE = "₀₁₂₃₄₅₆₇₈₉"
_NORMALIZACION_SUBINDICES = str.maketrans(_DIGITOS_SUBINDICE, "0123456789")
_PRODUCTOS = "*×·⋅∙"
_DIVISIONES = "/" + DIVISIONES_TIPOGRAFICAS
_ATOMO_NUMERICO = rf"(?:\d+(?:\.\d*)?|\.\d+|[{FRACCIONES_TIPOGRAFICAS}])"
_RAZON_NUMERICA = rf"{_ATOMO_NUMERICO}(?:\s*[{_DIVISIONES}]\s*\d+)?{SIMBOLO_POR_MIL}?"


def _clave_orden_natural(cadena: str) -> list[int | str]:
    """Genera una clave de ordenamiento natural para variables alfanuméricas."""
    return [
        int(fragmento) if fragmento.isdigit() else fragmento.lower()
        for fragmento in re.split(r"(\d+)", cadena)
    ]


class AnalizadorSistema:
    """Parsea ecuaciones lineales de texto a matrices aumentadas de coeficientes."""

    EXPRESION_REGULAR_TERMINO = re.compile(
        rf"\s*(?P<signo>[+{SIGNO_MENOS_TIPOGRAFICO}-]?)\s*"
        rf"(?:(?:(?P<coeficiente>{_RAZON_NUMERICA})(?:\s*[{_PRODUCTOS}])?\s*)?"
        rf"(?P<variable>[{_LETRAS_VARIABLE}][{_LETRAS_VARIABLE}0-9_{_DIGITOS_SUBINDICE}]*)"
        rf"(?:\s*(?P<operador>[{_PRODUCTOS}{_DIVISIONES}])\s*"
        rf"(?P<escalar>{_ATOMO_NUMERICO}{SIMBOLO_POR_MIL}?))?"
        rf"|(?P<constante>{_RAZON_NUMERICA}))"
    )

    @classmethod
    def _parsear_renglon(
        cls,
        indice: int,
        linea: str,
    ) -> tuple[bool, dict[str, Fraction], Fraction, str]:
        """Parsea una ecuación individual separando término independiente y variables."""
        if "=" not in linea:
            return False, {}, Fraction(0), f"Línea {indice}: Falta el signo '=' en la ecuación '{linea}'."

        partes = linea.split("=")
        if len(partes) != 2:
            return False, {}, Fraction(0), f"Línea {indice}: Debe contener un único '=' ('{linea}')."

        cadena_izquierda, cadena_derecha = partes[0].strip(), partes[1].strip()
        exito_derecha, valor_derecha, error_derecha = ValidadorMatriz.parsear_numero_exacto(cadena_derecha)
        if not exito_derecha:
            return False, {}, Fraction(0), f"Línea {indice}: Término independiente inválido '{cadena_derecha}': {error_derecha}"

        coeficientes_izquierda, constante_izquierda, error_izquierda = cls._parsear_lado_izquierdo(cadena_izquierda)
        if error_izquierda:
            return False, {}, Fraction(0), f"Línea {indice}: {error_izquierda}"

        valor_derecha -= constante_izquierda
        return True, coeficientes_izquierda, valor_derecha, ""

    @staticmethod
    def _procesar_termino(coincidencia: re.Match[str]) -> tuple[str | None, Fraction, str]:
        """Extrae el signo, valor y variable o constante de un término sintáctico."""
        signo, coeficiente, variable, operador, escalar, constante = coincidencia.groups()
        literal = coeficiente or constante or "1"
        valido, valor, error = ValidadorMatriz.parsear_numero_exacto(literal)
        if not valido:
            return None, Fraction(0), f"Valor inválido '{literal}': {error}"
        if operador:
            valor, error = _aplicar_escalar(valor, operador, escalar)
        if signo in ("-", SIGNO_MENOS_TIPOGRAFICO):
            valor = -valor
        if variable:
            variable = variable.translate(_NORMALIZACION_SUBINDICES)
        return variable, valor, error

    @classmethod
    def _parsear_lado_izquierdo(
        cls,
        cadena_izquierda: str,
    ) -> tuple[dict[str, Fraction], Fraction, str | None]:
        """Extrae los coeficientes de variables y constantes del lado izquierdo."""
        coeficientes: dict[str, Fraction] = {}
        suma_constantes = Fraction(0)
        posicion = 0
        if not cadena_izquierda:
            return {}, Fraction(0), "Escribe un término a la izquierda de '='."
        while posicion < len(cadena_izquierda):
            coincidencia = cls.EXPRESION_REGULAR_TERMINO.match(cadena_izquierda, posicion)
            if coincidencia is None or (posicion and not coincidencia["signo"]):
                return {}, Fraction(0), f"Contiene operadores o sintaxis no válida en '{cadena_izquierda}'."
            variable, valor, error = cls._procesar_termino(coincidencia)
            if error:
                return {}, Fraction(0), error
            if variable:
                coeficientes[variable] = coeficientes.get(variable, Fraction(0)) + valor
            else:
                suma_constantes += valor
            posicion = coincidencia.end()

        return coeficientes, suma_constantes, None

    @classmethod
    def parsear_sistema(
        cls,
        texto_crudo: str,
        variables_estrictas: bool = False,
    ) -> tuple[bool, Matriz | None, list[str], str]:
        """Procesa el texto ingresado construyendo una matriz aumentada."""
        lineas = [linea.strip() for linea in texto_crudo.strip().splitlines() if linea.strip()]
        if not lineas:
            return False, None, [], "El texto ingresado está vacío."

        ecuaciones_analizadas = []
        todas_variables = set()

        for indice, linea in enumerate(lineas, 1):
            correcto, coeficientes, valor_derecha, error = cls._parsear_renglon(indice, linea)
            if not correcto:
                return False, None, [], error
            ecuaciones_analizadas.append((coeficientes, valor_derecha))
            todas_variables.update(coeficientes.keys())

        if not todas_variables:
            return False, None, [], "No se detectaron variables válidas en el sistema."

        variables_ordenadas = sorted(todas_variables, key=lambda variable: (_clave_orden_natural(variable), variable))

        coherente, error_coherencia = _validar_coherencia(ecuaciones_analizadas, variables_estrictas)
        if not coherente:
            return False, None, [], error_coherencia

        filas = len(ecuaciones_analizadas)
        columnas = len(variables_ordenadas) + 1
        datos_matriz = []

        for coeficientes, valor_derecha in ecuaciones_analizadas:
            fila = [coeficientes.get(nombre_variable, Fraction(0)) for nombre_variable in variables_ordenadas]
            fila.append(valor_derecha)
            datos_matriz.append(fila)

        return True, Matriz(filas, columnas, datos_matriz), variables_ordenadas, "Sistema procesado correctamente."


def _validar_coherencia(ecuaciones: list, variables_estrictas: bool) -> tuple[bool, str]:
    """Comprueba la relación entre variables solo cuando la captura la exige."""
    if variables_estrictas:
        return ValidadorMatriz.validar_coherencia_variables(ecuaciones)
    return True, ""


def _aplicar_escalar(valor: Fraction, operador: str, literal: str) -> tuple[Fraction, str]:
    valido, escalar, error = ValidadorMatriz.parsear_numero_exacto(literal)
    if not valido:
        return Fraction(0), f"Escalar inválido '{literal}': {error}"
    if operador in _PRODUCTOS:
        return valor * escalar, ""
    if not escalar:
        return Fraction(0), "No puedes dividir una variable entre cero."
    return valor / escalar, ""
