"""Resolucion de sistemas mediante el motor comun de eliminacion exacta."""
from dataclasses import replace

from src.backend.constantes import CERO_EPSILON, SIN_SOLUCION
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.analisis_rouche import analizar_sistema_rouche
from src.backend.resolutores.sistemas_lineales.clasificacion_sistema import clasificar_sistema
from src.backend.resolutores.sistemas_lineales.configuracion_reduccion import ConfiguracionReduccion
from src.backend.resolutores.sistemas_lineales.pasos_reduccion import RegistroPasosSistema
from src.backend.resolutores.sistemas_lineales.reduccion import ReductorFilas
from src.backend.resolutores.sistemas_lineales.sustitucion import ejecutar_sustitucion_hacia_atras
from src.backend.modelos.aritmetica import es_cero


class ResolutorGauss:
    """Orquesta reduccion, clasificacion y solucion parametrica sin duplicar eliminacion."""

    REDUCCION_COMPLETA: bool = False

    def __init__(self, matriz_aumentada: Matriz, tolerancia_cero: float = CERO_EPSILON,
                 nombres_variables: list[str] | None = None, numero_terminos_independientes: int = 1,
                 configuracion: ConfiguracionReduccion | None = None) -> None:
        """Recibe matriz, tolerancia, nombres y opciones; rechaza bloques independientes invalidos con ValueError."""
        if type(numero_terminos_independientes) is not int or numero_terminos_independientes < 1:
            raise ValueError("numero_terminos_independientes debe ser un entero >= 1.")
        if numero_terminos_independientes >= matriz_aumentada.columnas:
            raise ValueError("numero_terminos_independientes debe ser menor que las columnas de la matriz.")
        opciones = configuracion or ConfiguracionReduccion(tolerancia_cero=tolerancia_cero)
        self._configuracion = replace(opciones, reduccion_completa=self.REDUCCION_COMPLETA)
        self.matriz_inicial = matriz_aumentada.clonar()
        self.matriz = matriz_aumentada.clonar()
        self.tolerancia_cero = self._configuracion.tolerancia_cero
        self.nombres_variables = nombres_variables
        self.numero_terminos_independientes = numero_terminos_independientes
        self.pasos: list[dict] = []
        self.intercambios = 0
        self.multiplicadores: list[dict] = []
        self.pivote_bloqueado: tuple[int, int] | None = None

    def _numero_variables(self) -> int:
        return self.matriz.columnas - self.numero_terminos_independientes

    def _eliminar(self) -> tuple[int, list[int]]:
        registro = RegistroPasosSistema(self.REDUCCION_COMPLETA)
        reduccion = ReductorFilas(self.matriz_inicial, self._numero_variables(),
                                 self._configuracion, registro.registrar).reducir()
        self.matriz = reduccion["matriz_reducida"]
        self.pasos = registro.pasos
        self.intercambios = reduccion["intercambios"]
        self.multiplicadores = reduccion["multiplicadores"]
        self.pivote_bloqueado = reduccion["pivote_bloqueado"]
        return reduccion["rango"], reduccion["columnas_pivote"]

    def resolver_reduccion(self) -> dict:
        """Devuelve matriz reducida, rango, columnas pivote y pasos para uno o varios bloques independientes."""
        rango, columnas_pivote = self._eliminar()
        return {"matriz_reducida": self.matriz, "rango": rango,
                "columnas_pivote": columnas_pivote, "pasos": self.pasos}

    def resolver(self) -> dict:
        """Devuelve solucion, clasificacion y pasos; ValueError si hay varios terminos o pivote bloqueado."""
        if self.numero_terminos_independientes != 1:
            raise ValueError(
                f"resolver() requiere numero_terminos_independientes=1 (recibido {self.numero_terminos_independientes}). "
                "Usa resolver_reduccion() para multiples terminos independientes."
            )
        rango, columnas_pivote = self._eliminar()
        if self.pivote_bloqueado is not None:
            raise ValueError("El sistema requiere intercambiar filas; selecciona pivoteo parcial.")
        numero_variables = self._numero_variables()
        estado, mensaje = clasificar_sistema(self.matriz, numero_variables, rango, self.tolerancia_cero)
        es_homogeneo = all(es_cero(fila[numero_variables], self.tolerancia_cero)
                           for fila in self.matriz_inicial.datos)
        analisis = analizar_sistema_rouche(estado, rango, numero_variables, es_homogeneo, columnas_pivote)
        if estado == SIN_SOLUCION:
            return _respuesta_sin_solucion(self.matriz, mensaje, analisis, self.pasos)
        solucion = ejecutar_sustitucion_hacia_atras(
            self.matriz, columnas_pivote, numero_variables, self.nombres_variables,
        )
        return _respuesta_con_solucion((self.matriz, estado, mensaje), analisis, self.pasos, solucion)


def _respuesta_sin_solucion(matriz: Matriz, mensaje: str, analisis: dict, pasos: list[dict]) -> dict:
    return {
        "estado": SIN_SOLUCION, "mensaje": mensaje, "clasificacion": mensaje,
        "matriz_escalonada": matriz, "solucion": None, "solucion_exacta": None,
        "columnas_libres": [], "parametros_solucion": None,
        "analisis_sistema": analisis, "pasos": pasos, "pasos_sustitucion_regresiva": [],
    }


def _respuesta_con_solucion(info_sistema: tuple[Matriz, str, str], analisis: dict,
                           pasos: list[dict], datos_solucion: tuple) -> dict:
    matriz, estado, mensaje = info_sistema
    solucion, solucion_exacta, pasos_sustitucion, libres, parametros = datos_solucion
    return {
        "estado": estado, "mensaje": mensaje, "clasificacion": mensaje,
        "matriz_escalonada": matriz, "solucion": solucion, "solucion_exacta": solucion_exacta,
        "columnas_libres": libres, "parametros_solucion": parametros,
        "analisis_sistema": analisis, "pasos": pasos,
        "pasos_sustitucion_regresiva": pasos_sustitucion,
    }
