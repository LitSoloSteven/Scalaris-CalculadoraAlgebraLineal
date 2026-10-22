"""Modelo matricial con aritmética exacta basada en Fraction."""

from fractions import Fraction
from typing import Union

from src.backend.constantes import (
    CERO_EPSILON,
    LIMITE_RECONSTRUCCION_FRACCION,
)
from src.backend.excepciones import ErrorDatosMatriz
from src.backend.modelos.operaciones_filas import sumar_fila_multiplicada
from src.backend.modelos.aritmetica import numeros_iguales
from src.backend.modelos.entrada_numerica import motivo_cadena_no_soportada
from src.backend.modelos.copia_normalizada import copiar_datos_normalizados

Numerico = Union[float, Fraction, int]
NumericoSimilar = Union[Numerico, str]


class Matriz:
    """Estructura de datos matricial con soporte de operaciones elementales."""

    def __init__(
        self,
        filas: int,
        columnas: int,
        datos: list[list[Numerico]] | None = None,
    ):
        """Crea filas por columnas desde datos o ceros; lanza ErrorDatosMatriz ante forma o valores invalidos."""
        self._validar_dimensiones_modelo(filas, columnas)
        self.filas = filas
        self.columnas = columnas
        if datos is not None:
            self._validar_forma_datos(datos, filas, columnas)
            copia = (copiar_datos_normalizados(datos)
                     if type(self) is Matriz and self._normalizar_valor is _NORMALIZADOR_CANONICO else None)
            self.datos = (copia if copia is not None
                          else [[self._normalizar_valor(valor) for valor in fila] for fila in datos])
        else:
            self.datos = [[Fraction(0) for _ in range(columnas)] for _ in range(filas)]

    @staticmethod
    def _validar_dimensiones_modelo(filas: int, columnas: int) -> None:
        if not isinstance(filas, int) or not isinstance(columnas, int):
            raise ErrorDatosMatriz(
                f"Las dimensiones deben ser enteros (filas={filas!r}, columnas={columnas!r})."
            )
        if filas <= 0 or columnas <= 0:
            raise ErrorDatosMatriz(
                f"Las dimensiones deben ser positivas (recibido {filas}×{columnas})."
            )

    @staticmethod
    def _validar_forma_datos(datos: list, filas: int, columnas: int) -> None:
        if len(datos) != filas:
            raise ErrorDatosMatriz(
                f"Se esperaban {filas} filas; datos trae {len(datos)}."
            )
        for i, fila in enumerate(datos):
            if len(fila) != columnas:
                raise ErrorDatosMatriz(
                    f"Fila {i + 1} tiene {len(fila)} columnas; se esperaban {columnas}."
                )

    @staticmethod
    def _normalizar_cadena(valor: str) -> Numerico:
        """Convierte una cadena a fraccion aplicando los limites de entrada comunes."""
        valor_limpio = valor.strip()
        if not valor_limpio:
            return Fraction(0)
        rechazo = motivo_cadena_no_soportada(valor_limpio)
        if rechazo is not None:
            raise ErrorDatosMatriz(rechazo)
        try:
            return Fraction(valor_limpio)
        except (ValueError, ZeroDivisionError):
            raise ErrorDatosMatriz(f"Valor no parseable como número: '{valor}'.")

    @staticmethod
    def _normalizar_valor(valor: NumericoSimilar) -> Numerico:
        """Normaliza cadenas, flotantes y enteros a fracciones exactas."""
        if isinstance(valor, (Fraction, int)):
            return valor
        if isinstance(valor, str):
            return Matriz._normalizar_cadena(valor)
        if isinstance(valor, float):
            try:
                fraccion = Fraction(valor).limit_denominator(LIMITE_RECONSTRUCCION_FRACCION)
                if abs(float(fraccion) - valor) < CERO_EPSILON:
                    return fraccion
            except (ValueError, OverflowError):
                pass
            return valor
        raise ErrorDatosMatriz(f"Tipo no soportado en celda: {type(valor).__name__}.")

    def _verificar_limites(self, fila: int, columna: int) -> None:
        """Verifica que las coordenadas pertenezcan al rango de la matriz."""
        if not (0 <= fila < self.filas and 0 <= columna < self.columnas):
            raise IndexError(
                f"Índice [{fila},{columna}] fuera de rango para matriz {self.filas}×{self.columnas}."
            )

    def obtener(self, fila: int, columna: int) -> Numerico:
        """Devuelve el numero en fila y columna; lanza IndexError si la coordenada no pertenece a la matriz."""
        self._verificar_limites(fila, columna)
        return self.datos[fila][columna]

    def establecer(self, fila: int, columna: int, valor: Numerico) -> None:
        """Asigna valor en fila y columna; lanza IndexError por coordenadas y ErrorDatosMatriz por valores invalidos."""
        self._verificar_limites(fila, columna)
        self.datos[fila][columna] = self._normalizar_valor(valor)

    def clonar(self) -> 'Matriz':
        """Devuelve una copia profunda de la matriz actual."""
        nuevos_datos = [fila[:] for fila in self.datos]
        return Matriz(self.filas, self.columnas, nuevos_datos)

    def intercambiar_filas(self, fila1: int, fila2: int) -> None:
        """Intercambia fila1 y fila2 sin retorno; lanza IndexError si alguna fila no pertenece a la matriz."""
        self._verificar_limites(fila1, 0)
        self._verificar_limites(fila2, 0)
        if fila1 != fila2:
            self.datos[fila1], self.datos[fila2] = self.datos[fila2], self.datos[fila1]

    def sumar_fila_escalada(
        self,
        fila_destino: int,
        fila_origen: int,
        escalar: Numerico,
    ) -> None:
        """Suma escalar por fila_origen a fila_destino; lanza IndexError por filas y ErrorDatosMatriz por escalar invalido."""
        self._verificar_limites(fila_destino, 0)
        self._verificar_limites(fila_origen, 0)
        escalar_normalizado = self._normalizar_valor(escalar)
        nueva_fila = sumar_fila_multiplicada(self.datos[fila_destino], self.datos[fila_origen], escalar_normalizado)
        self.datos[fila_destino] = [self._normalizar_valor(valor) for valor in nueva_fila]

    def __eq__(self, otro: object) -> bool:
        """Compara otro por dimensiones y valores exactos; aplica tolerancia solo si intervienen flotantes."""
        if not isinstance(otro, Matriz):
            return NotImplemented
        if self.filas != otro.filas or self.columnas != otro.columnas:
            return False
        return all(
            numeros_iguales(self.datos[r][c], otro.datos[r][c])
            for r in range(self.filas)
            for c in range(self.columnas)
        )

    def __str__(self) -> str:
        """Genera una representación en texto con números formateados."""
        from src.backend.utilidades.formateadores import formatear_fraccion_texto

        filas_texto = []
        for fila in self.datos:
            fila_formateada = [f"{formatear_fraccion_texto(valor):>8}" for valor in fila]
            filas_texto.append("[ " + " ".join(fila_formateada) + " ]")
        return "\n".join(filas_texto)


_NORMALIZADOR_CANONICO = Matriz._normalizar_valor
