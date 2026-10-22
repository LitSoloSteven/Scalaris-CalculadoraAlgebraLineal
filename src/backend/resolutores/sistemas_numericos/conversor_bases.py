"""Conversor y trazador didáctico de cambios de base numérica posicional."""

from typing import Any

from src.backend.constantes import ERROR, EXITO
from src.backend.utilidades.reglas_dominio import BASES_NUMERICAS, capturar_entrada_base


class ConversorBases:
    """Convierte números entre bases 2, 8, 10 y 16 con desglose de pasos."""

    def decimal_a_todo(self, valor_texto: Any, base_destino: str = "todas") -> dict:
        """Convierte desde base decimal a las demás bases."""
        return self._procesar(valor_texto, 10, base_destino)

    def binario_a_todo(self, valor_texto: Any, base_destino: str = "todas") -> dict:
        """Convierte desde base binaria a las demás bases."""
        return self._procesar(valor_texto, 2, base_destino)

    def octal_a_todo(self, valor_texto: Any, base_destino: str = "todas") -> dict:
        """Convierte desde base octal a las demás bases."""
        return self._procesar(valor_texto, 8, base_destino)

    def hexadecimal_a_todo(self, valor_texto: Any, base_destino: str = "todas") -> dict:
        """Convierte desde base hexadecimal a las demás bases."""
        return self._procesar(valor_texto, 16, base_destino)

    def _procesar(self, valor_texto: Any, base_origen: int, base_destino: str) -> dict:
        """Parsea la entrada, calcula representaciones y genera el paso a paso."""
        try:
            es_negativo, limpio, magnitud = capturar_entrada_base(valor_texto, base_origen)
        except ValueError as error:
            return {"estado": ERROR, "mensaje": str(error)}
        try:
            numero = -magnitud if es_negativo else magnitud
            resultado = self._formatear_salida(numero)
            resultado["estado"] = EXITO
            resultado["pasos"] = self._generar_pasos(limpio, magnitud, base_origen, base_destino, es_negativo)
            return resultado
        except ValueError:
            return {"estado": ERROR, "mensaje": f"Valor inválido para la base {base_origen}."}

    @staticmethod
    def _formatear_salida(numero: int) -> dict:
        """Devuelve las cadenas formateadas en decimal, binario, octal y hexadecimal."""
        signo = "-" if numero < 0 else ""
        magnitud = abs(numero)
        return {
            "decimal": f"{signo}{magnitud}",
            "binario": f"{signo}{format(magnitud, 'b')}",
            "octal": f"{signo}{format(magnitud, 'o')}",
            "hexadecimal": f"{signo}{format(magnitud, 'X')}",
        }

    def _generar_pasos(
        self,
        limpio: str,
        magnitud: int,
        base_origen: int,
        base_destino_texto: str,
        es_negativo: bool,
    ) -> list[dict]:
        """Genera expansiones polinomiales y divisiones sucesivas según origen y destino."""
        pasos = []
        if base_origen != 10:
            pasos.append(self._generar_expansion_posicional(limpio, base_origen, magnitud, es_negativo))

        destinos = []
        if base_destino_texto == "todas":
            destinos = [base for base in [2, 8, 10, 16] if base != base_origen and base != 10]
        else:
            base_destino = BASES_NUMERICAS.get(base_destino_texto)
            if base_destino and base_destino != 10 and base_destino != base_origen:
                destinos.append(base_destino)

        for destino in destinos:
            pasos.append(self._generar_divisiones_sucesivas(magnitud, destino, es_negativo))
        return pasos

    @staticmethod
    def _generar_expansion_posicional(
        limpio: str, base_origen: int, magnitud: int, es_negativo: bool
    ) -> dict:
        """Genera el desglose posicional en potencias de la base de origen."""
        terminos = []
        longitud = len(limpio)
        for i, digito in enumerate(limpio):
            potencia = longitud - 1 - i
            valor = int(digito, base_origen)
            peso = base_origen ** potencia
            producto = valor * peso
            terminos.append({
                "digito": digito,
                "valor": valor,
                "potencia": potencia,
                "peso": peso,
                "producto": producto,
            })
        return {
            "tipo": "expansion_posicional",
            "base_origen": base_origen,
            "terminos": terminos,
            "total": f"-{magnitud}" if es_negativo else str(magnitud),
            "es_negativo": es_negativo,
        }

    @staticmethod
    def _generar_divisiones_sucesivas(magnitud: int, base_destino: int, es_negativo: bool) -> dict:
        """Genera el algoritmo de divisiones sucesivas hacia la base de destino."""
        filas = []
        dividendo = magnitud
        if dividendo == 0:
            filas.append({"dividendo": 0, "divisor": base_destino, "cociente": 0, "residuo": 0})
            resultado = "0"
        else:
            while dividendo > 0:
                cociente = dividendo // base_destino
                residuo = dividendo % base_destino
                filas.append({"dividendo": dividendo, "divisor": base_destino, "cociente": cociente, "residuo": residuo})
                dividendo = cociente
            digitos_disponibles = "0123456789ABCDEF"
            resultado_abs = "".join(digitos_disponibles[paso_division["residuo"]] for paso_division in reversed(filas))
            resultado = f"-{resultado_abs}" if es_negativo else resultado_abs

        return {
            "tipo": "division_sucesiva",
            "base_destino": base_destino,
            "filas": filas,
            "lectura": "Se lee de abajo hacia arriba",
            "resultado": resultado,
        }
