"""Captura exacta, validación y conversión Matriz/Ecuaciones para restricciones."""
from __future__ import annotations

from dataclasses import dataclass
import re

from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS, DIMENSION_MINIMA
from src.backend.modelos.escalares.conversion_fracciones import texto_fraccion_exacta
from src.backend.resolutores.operaciones_vectores.subespacios.contrato_subespacios import (
    ErrorCapturaSubespacio,
)
from src.backend.resolutores.sistemas_lineales.captura.exportacion_ecuaciones import (
    exportar_ecuaciones_desde_datos,
)
from src.backend.utilidades.validacion.validadores import ValidadorMatriz
from src.frontend.controladores.algebra.sistemas_lineales.nucleo.captura import (
    preparar_captura_ecuaciones,
)
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    EJEMPLO_RESTRICCIONES,
    MENSAJE_ECUACIONES_VACIAS,
    MENSAJE_SOLO_CONSTANTES,
)

_PATRON_CANONICO = re.compile(r"^[xX]_?(\d+)$")
_PATRON_MATRIZ = re.compile(r"^matriz_a\[(\d+)\]\[(\d+)\]$")
_PATRON_VECTOR_B = re.compile(r"^vector_b\[(\d+)\]$")
_ALIAS_INDICES = {"x": 0, "y": 1, "z": 2}


@dataclass(frozen=True)
class RestriccionesCapturadas:
    """Instantánea serializable de restricciones lineales Ax = b en ℝⁿ."""

    dimension_ambiente: int
    matriz_a: list[list[str]]
    vector_b: list[str]


class ErrorCapturaRestricciones(ValueError):
    """Error de validación localizado para entradas de restricciones."""

    def __init__(self, mensaje: str, diagnostico: dict | None = None) -> None:
        super().__init__(mensaje)
        self.diagnostico = diagnostico or _crear_diagnostico(mensaje)


def _crear_diagnostico(
    mensaje: str,
    *,
    ubicacion: str | None = None,
    campo: str | None = None,
    fila: int | None = None,
    columna: int | None = None,
) -> dict:
    return {
        "mensaje": " ".join(str(mensaje).split()),
        "ubicacion": ubicacion,
        "campo": campo,
        "fila": fila,
        "columna": columna,
        "etiqueta": None,
        "componente": None,
    }


def ejemplo_restricciones() -> RestriccionesCapturadas:
    """Devuelve una copia del ejemplo afín oficial en ℝ³."""
    return RestriccionesCapturadas(
        dimension_ambiente=int(EJEMPLO_RESTRICCIONES["dimension_ambiente"]),
        matriz_a=[list(fila) for fila in EJEMPLO_RESTRICCIONES["matriz_a"]],
        vector_b=list(EJEMPLO_RESTRICCIONES["vector_b"]),
    )


def ayuda_variables_restricciones(dimension_ambiente: int) -> str:
    """Describe los nombres canónicos y alias admitidos para la dimensión activa."""
    base = f"Variables admitidas: x1 a x{dimension_ambiente}."
    if dimension_ambiente == 2:
        return f"{base} También puedes usar alias x, y."
    if dimension_ambiente == 3:
        return f"{base} También puedes usar alias x, y, z."
    return f"{base} En ℝ^{dimension_ambiente} no hay alias x, y, z."


def _validar_dimension(dimension_ambiente: int) -> int:
    if type(dimension_ambiente) is not int or not (
        DIMENSION_MINIMA <= dimension_ambiente <= DIMENSION_MAXIMA_SISTEMAS
    ):
        raise ErrorCapturaRestricciones(
            f"La dimensión ambiente debe estar entre {DIMENSION_MINIMA} y {DIMENSION_MAXIMA_SISTEMAS}.",
            _crear_diagnostico(
                f"La dimensión ambiente debe estar entre {DIMENSION_MINIMA} y {DIMENSION_MAXIMA_SISTEMAS}.",
                ubicacion="dimension_ambiente",
                campo="dimension_ambiente",
            ),
        )
    return dimension_ambiente


def _resolver_indice_variable(nombre: str, dimension_ambiente: int) -> int:
    coincidencia = _PATRON_CANONICO.fullmatch(nombre)
    if coincidencia:
        indice = int(coincidencia.group(1))
        if 1 <= indice <= dimension_ambiente:
            return indice - 1
        mensaje = (
            f"La coordenada {nombre} excede la dimensión ambiente ℝ^{dimension_ambiente}; "
            f"usa variables entre x1 y x{dimension_ambiente}."
        )
        raise ErrorCapturaRestricciones(mensaje, _crear_diagnostico(mensaje, ubicacion="ecuaciones", campo="ecuaciones"))
    return _resolver_alias(nombre, dimension_ambiente)


def _resolver_alias(nombre: str, dimension_ambiente: int) -> int:
    clave = nombre.lower()
    if clave not in _ALIAS_INDICES:
        mensaje = f"Variable '{nombre}' no válida. {ayuda_variables_restricciones(dimension_ambiente)}"
        raise ErrorCapturaRestricciones(mensaje, _crear_diagnostico(mensaje, ubicacion="ecuaciones", campo="ecuaciones"))
    indice = _ALIAS_INDICES[clave]
    if dimension_ambiente in (2, 3) and indice < dimension_ambiente:
        return indice
    mensaje = (
        f"El alias '{nombre}' no está disponible en ℝ^{dimension_ambiente}. "
        f"{ayuda_variables_restricciones(dimension_ambiente)}"
    )
    raise ErrorCapturaRestricciones(mensaje, _crear_diagnostico(mensaje, ubicacion="ecuaciones", campo="ecuaciones"))


def _mapear_columnas(variables: list[str], dimension_ambiente: int) -> list[int]:
    columnas: list[int] = []
    usadas: dict[int, str] = {}
    for nombre in variables:
        columna = _resolver_indice_variable(nombre, dimension_ambiente)
        if columna in usadas:
            mensaje = (
                f"Colisión de variables: '{usadas[columna]}' y '{nombre}' "
                f"corresponden ambas a la coordenada x{columna + 1}."
            )
            raise ErrorCapturaRestricciones(
                mensaje,
                _crear_diagnostico(mensaje, ubicacion="ecuaciones", campo="ecuaciones"),
            )
        usadas[columna] = nombre
        columnas.append(columna)
    return columnas


def _error_analisis_ecuaciones(mensaje_bruto: str) -> ErrorCapturaRestricciones:
    limpio = " ".join(str(mensaje_bruto or "").split())
    if "no se detectaron variables" in limpio.lower():
        return ErrorCapturaRestricciones(
            MENSAJE_SOLO_CONSTANTES,
            _crear_diagnostico(MENSAJE_SOLO_CONSTANTES, ubicacion="ecuaciones", campo="ecuaciones"),
        )
    return ErrorCapturaRestricciones(
        limpio,
        _crear_diagnostico(limpio, ubicacion="ecuaciones", campo="ecuaciones"),
    )


def interpretar_ecuaciones_restricciones(
    texto: str, dimension_ambiente: int
) -> RestriccionesCapturadas:
    """Convierte ecuaciones de texto a [A | b] conservando la dimensión ambiente."""
    dimension = _validar_dimension(dimension_ambiente)
    if not isinstance(texto, str) or not texto.strip():
        raise ErrorCapturaRestricciones(
            MENSAJE_ECUACIONES_VACIAS,
            _crear_diagnostico(MENSAJE_ECUACIONES_VACIAS, ubicacion="ecuaciones", campo="ecuaciones"),
        )
    captura = preparar_captura_ecuaciones([texto])
    if captura["estado"] != "EXITO":
        raise _error_analisis_ecuaciones(captura["mensaje"])
    columnas = _mapear_columnas(captura["variables"], dimension)
    matriz_a: list[list[str]] = []
    for fila_origen in captura["matriz_a"]:
        fila = ["0"] * dimension
        for columna, valor in zip(columnas, fila_origen):
            fila[columna] = str(valor)
        matriz_a.append(fila)
    vector_b = [str(valor) for valor in captura["vector_b"]]
    return RestriccionesCapturadas(dimension, matriz_a, vector_b)


def _normalizar_celda(
    celda: object, campo: str, fila: int, columna: int | None
) -> str:
    texto = str(celda).strip() if celda is not None else ""
    valida, valor, error = ValidadorMatriz.parsear_numero_exacto(texto)
    if not valida:
        ubicacion = (
            f"matriz_a[{fila}][{columna}]" if columna is not None else f"vector_b[{fila}]"
        )
        etiqueta = f"fila {fila + 1}, columna x{columna + 1}" if columna is not None else f"fila {fila + 1}, término b"
        mensaje = f"Revisa {etiqueta}. {error}"
        raise ErrorCapturaRestricciones(
            mensaje,
            _crear_diagnostico(
                mensaje,
                ubicacion=ubicacion,
                campo=campo,
                fila=fila + 1,
                columna=(columna + 1) if columna is not None else None,
            ),
        )
    return texto_fraccion_exacta(valor)


def redactar_ecuaciones_restricciones(
    matriz_a: list[list[str]], vector_b: list[str]
) -> str:
    """Convierte [A | b] a ecuaciones con variables x1..xn y término explícito en filas nulas."""
    if not matriz_a or len(matriz_a) != len(vector_b):
        raise ErrorCapturaRestricciones(
            "La matriz A y el vector b deben tener la misma cantidad de filas.",
            _crear_diagnostico("La matriz A y el vector b deben tener la misma cantidad de filas.", campo="matriz_a"),
        )
    matriz_normalizada = [
        [_normalizar_celda(celda, "matriz_a", fila, columna) for columna, celda in enumerate(valores)]
        for fila, valores in enumerate(matriz_a)
    ]
    vector_normalizado = [
        _normalizar_celda(celda, "vector_b", fila, None)
        for fila, celda in enumerate(vector_b)
    ]
    return "\n".join(
        exportar_ecuaciones_desde_datos(matriz_normalizada, vector_normalizado, True)
    )


def diagnostico_restricciones_desde_error(
    error: ErrorCapturaSubespacio, formato: str = "matriz"
) -> dict:
    """Traduce un ErrorCapturaSubespacio de restricciones a coordenadas 1-based de la vista."""
    ubicacion = error.ubicacion
    base = str(error).split(" Ubicacion:", 1)[0].strip()
    if ubicacion:
        coincidencia_a = _PATRON_MATRIZ.fullmatch(ubicacion)
        if coincidencia_a:
            return _diagnostico_matriz(int(coincidencia_a.group(1)), int(coincidencia_a.group(2)), base, ubicacion, formato)
        coincidencia_b = _PATRON_VECTOR_B.fullmatch(ubicacion)
        if coincidencia_b:
            return _diagnostico_vector_b(int(coincidencia_b.group(1)), base, ubicacion, formato)
    campo = "ecuaciones" if formato == "ecuaciones" else ubicacion
    return _crear_diagnostico(base, ubicacion=ubicacion, campo=campo)


def _diagnostico_matriz(fila: int, columna: int, base: str, ubicacion: str, formato: str) -> dict:
    if formato == "ecuaciones":
        mensaje = f"Ecuación {fila + 1}, coordenada x{columna + 1}: {base}"
        return _crear_diagnostico(mensaje, ubicacion=ubicacion, campo="ecuaciones", fila=fila + 1, columna=columna + 1)
    mensaje = f"Fila {fila + 1}, columna x{columna + 1}: {base}"
    return _crear_diagnostico(mensaje, ubicacion=ubicacion, campo="matriz_a", fila=fila + 1, columna=columna + 1)


def _diagnostico_vector_b(fila: int, base: str, ubicacion: str, formato: str) -> dict:
    if formato == "ecuaciones":
        mensaje = f"Ecuación {fila + 1}, término independiente: {base}"
        return _crear_diagnostico(mensaje, ubicacion=ubicacion, campo="ecuaciones", fila=fila + 1)
    mensaje = f"Fila {fila + 1}, término b: {base}"
    return _crear_diagnostico(mensaje, ubicacion=ubicacion, campo="vector_b", fila=fila + 1)
