"""Analizadores sintácticos para sistemas de ecuaciones lineales."""

from fractions import Fraction
import re

from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.validadores import ValidadorMatriz


def _clave_orden_natural(cadena: str) -> list[int | str]:
    """Genera una clave de ordenamiento natural para variables alfanuméricas."""
    return [
        int(fragmento) if fragmento.isdigit() else fragmento.lower()
        for fragmento in re.split(r"(\d+)", cadena)
    ]


class AnalizadorSistema:
    """Parsea ecuaciones lineales de texto a matrices aumentadas de coeficientes."""

    EXPRESION_REGULAR_TERMINO = re.compile(
        r"([+-]?)\s*(?:(?:([\d\.\/]+)\s*\*?\s*)?([a-zA-Z][a-zA-Z0-9_]*)|([\d\.\/]+))"
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

    @classmethod
    def _procesar_termino(
        cls,
        coincidencia: re.Match,
    ) -> tuple[bool, str | None, Fraction, str]:
        """Extrae el signo, valor y variable o constante de un término sintáctico."""
        signo_texto, coeficiente_texto, nombre_variable, constante_texto = coincidencia.groups()
        signo = -1 if signo_texto == "-" else 1

        if nombre_variable:
            if not coeficiente_texto:
                valor = Fraction(1)
            else:
                exito, valor_analizado, _ = ValidadorMatriz.parsear_numero_exacto(coeficiente_texto)
                if not exito:
                    return False, None, Fraction(0), f"Coeficiente inválido '{coeficiente_texto}' en la variable '{nombre_variable}'."
                valor = valor_analizado
            return True, nombre_variable, signo * valor, ""

        if constante_texto:
            exito, valor_analizado, _ = ValidadorMatriz.parsear_numero_exacto(constante_texto)
            if not exito:
                return False, None, Fraction(0), f"Término independiente inválido '{constante_texto}'."
            return True, None, signo * valor_analizado, ""

        return True, None, Fraction(0), ""

    @classmethod
    def _parsear_lado_izquierdo(
        cls,
        cadena_izquierda: str,
    ) -> tuple[dict[str, Fraction], Fraction, str | None]:
        """Extrae los coeficientes de variables y constantes del lado izquierdo."""
        coeficientes: dict[str, Fraction] = {}
        suma_constantes = Fraction(0)
        cadena_limpia = cadena_izquierda.replace(" ", "")

        coincidencias = list(cls.EXPRESION_REGULAR_TERMINO.finditer(cadena_izquierda))
        reconstruido = "".join(coincidencia.group(0).replace(" ", "") for coincidencia in coincidencias)
        if len(reconstruido) != len(cadena_limpia):
            return {}, Fraction(0), f"Contiene operadores o sintaxis no válida en '{cadena_izquierda}'."

        for coincidencia_termino in coincidencias:
            correcto, variable, valor, error = cls._procesar_termino(coincidencia_termino)
            if not correcto:
                return {}, Fraction(0), error
            if variable:
                coeficientes[variable] = coeficientes.get(variable, Fraction(0)) + valor
            else:
                suma_constantes += valor

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

        variables_ordenadas = sorted(list(todas_variables), key=_clave_orden_natural)

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
