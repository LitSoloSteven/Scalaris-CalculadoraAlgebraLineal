"""Eliminacion comun con eventos numericos independientes de su presentacion."""
from collections.abc import Callable
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.modelos.conversion_fracciones import convertir_fraccion, convertir_fila_fracciones
from src.backend.modelos.operaciones_filas import sumar_fila_multiplicada
from src.backend.resolutores.sistemas_lineales.configuracion_reduccion import ConfiguracionReduccion
from src.backend.modelos.aritmetica import es_cero


class ReductorFilas:
    """Reduce una copia de la matriz y publica operaciones, sin textos ni LaTeX."""

    def __init__(self, matriz: Matriz, numero_variables: int,
                 configuracion: ConfiguracionReduccion, registrar: Callable | None = None) -> None:
        """Recibe matriz, columnas activas, opciones y observador; lanza ValueError si son invalidos."""
        if type(numero_variables) is not int or not 1 <= numero_variables <= matriz.columnas:
            raise ValueError("El numero de variables debe pertenecer a las columnas de la matriz.")
        self.matriz = matriz.clonar()
        self.numero_variables = numero_variables
        self.configuracion = configuracion
        self._registrar = registrar
        self.columnas_pivote: list[int] = []
        self.intercambios = 0
        self.multiplicadores: list[dict] = []
        self.pivote_bloqueado: tuple[int, int] | None = None

    def _emitir(self, tipo: str, **datos) -> None:
        if self._registrar is not None:
            self._registrar(tipo, self.matriz, datos)

    def _seleccionar_pivote(self, fila: int, columna: int) -> int | None:
        estrategia = self.configuracion.estrategia_pivote
        if estrategia == "sin_intercambios":
            return fila if not es_cero(self.matriz.obtener(fila, columna), self.configuracion.tolerancia_cero) else None
        candidatas = [indice for indice in range(fila, self.matriz.filas)
                      if not es_cero(self.matriz.obtener(indice, columna), self.configuracion.tolerancia_cero)]
        if not candidatas:
            return None
        if estrategia == "primer_no_nulo":
            return candidatas[0]
        return max(candidatas, key=lambda indice: abs(self.matriz.obtener(indice, columna)))

    def _columna_bloqueada(self, fila: int, columna: int) -> bool:
        necesita_intercambio = any(not es_cero(self.matriz.obtener(indice, columna), self.configuracion.tolerancia_cero)
                                  for indice in range(fila + 1, self.matriz.filas))
        if necesita_intercambio:
            self.pivote_bloqueado = (fila, columna)
        return necesita_intercambio

    def _intercambiar(self, fila: int, seleccionada: int) -> None:
        if seleccionada != fila:
            self.matriz.intercambiar_filas(fila, seleccionada)
            self.intercambios += 1
            self._emitir("intercambio", fila=fila, seleccionada=seleccionada)

    def _eliminar_destino(self, destino: int, fila_pivote: int, columna: int) -> None:
        valor = self.matriz.obtener(destino, columna)
        if es_cero(valor, self.configuracion.tolerancia_cero):
            return
        factor = convertir_fraccion(valor) / convertir_fraccion(self.matriz.obtener(fila_pivote, columna))
        origen = convertir_fila_fracciones(self.matriz.datos[fila_pivote])
        fila_destino = convertir_fila_fracciones(self.matriz.datos[destino])
        self.matriz.datos[destino] = sumar_fila_multiplicada(fila_destino, origen, -factor)
        if self.configuracion.capturar_multiplicadores:
            self.multiplicadores.append({"fila": destino, "columna": fila_pivote, "valor": factor})
        self._emitir("eliminacion", fila=destino, fila_pivote=fila_pivote, columna=columna, factor=factor)

    def _eliminar_columna(self, fila: int, columna: int) -> None:
        self._emitir("pivote", fila=fila, columna=columna, valor=self.matriz.obtener(fila, columna))
        destinos = range(self.matriz.filas) if self.configuracion.reduccion_completa else range(fila + 1, self.matriz.filas)
        for destino in destinos:
            if destino != fila:
                self._eliminar_destino(destino, fila, columna)

    def _normalizar(self) -> None:
        if not self.configuracion.normalizar_pivotes:
            return
        for fila, columna in enumerate(self.columnas_pivote):
            valor = self.matriz.obtener(fila, columna)
            if not es_cero(valor - 1, self.configuracion.tolerancia_cero):
                self.matriz.datos[fila] = [componente / Fraction(valor) for componente in self.matriz.datos[fila]]
                self._emitir("normalizacion", fila=fila, valor=valor)

    def reducir(self) -> dict:
        """Devuelve matriz reducida, rango, pivotes, factores e intercambios sin mutar la entrada."""
        self._emitir("inicial")
        for columna in range(self.numero_variables):
            fila = len(self.columnas_pivote)
            if fila >= self.matriz.filas:
                break
            seleccionada = self._seleccionar_pivote(fila, columna)
            if seleccionada is None:
                if self.configuracion.estrategia_pivote == "sin_intercambios" and self._columna_bloqueada(fila, columna):
                    break
                continue
            self._intercambiar(fila, seleccionada)
            self._eliminar_columna(fila, columna)
            self.columnas_pivote.append(columna)
        self._normalizar()
        return {
            "matriz_reducida": self.matriz, "rango": len(self.columnas_pivote),
            "columnas_pivote": list(self.columnas_pivote), "intercambios": self.intercambios,
            "multiplicadores": list(self.multiplicadores), "pivote_bloqueado": self.pivote_bloqueado,
        }
