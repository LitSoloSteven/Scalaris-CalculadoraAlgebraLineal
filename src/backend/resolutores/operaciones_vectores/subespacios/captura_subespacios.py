"""Captura exacta y acotada de generadores y restricciones de subespacios."""
from collections.abc import Mapping
from fractions import Fraction

from src.backend.constantes import (
    DIMENSION_MAXIMA_SISTEMAS,
    DIMENSION_MAXIMA_VECTORES,
    DIMENSION_MINIMA,
    LONGITUD_MAXIMA_CADENA_NUMERO,
    MENSAJE_NUMERO_DEMASIADO_LARGO,
)
from src.backend.modelos.escalares.entrada_numerica import convertir_numero_exacto
from src.backend.modelos.matriz import Matriz
from .contrato_subespacios import (
    MODO_GENERADORES,
    MODO_RESTRICCIONES,
    EntradaGeneradores,
    EntradaRestricciones,
    ErrorCapturaSubespacio,
    validar_dimension_ambiente,
    validar_etiqueta,
)

ORIENTACION_COLUMNA = "columna"
MOSTRAR_CLAVES_AJENAS = 5
CLAVES_GENERADORES = frozenset({"modo", "dimension_ambiente", "vectores"})
CLAVES_RESTRICCIONES = frozenset({"modo", "dimension_ambiente", "matriz_a", "vector_b"})
CLAVES_VECTOR = frozenset({"datos", "orientacion"})


def capturar_generadores(captura: object) -> EntradaGeneradores:
    """Convierte generadores columna exactos; lanza error con ubicacion ante forma o celda invalida."""
    datos = _validar_mapa(captura, CLAVES_GENERADORES, "captura")
    _validar_modo(datos, MODO_GENERADORES)
    dimension = validar_dimension_ambiente(datos["dimension_ambiente"])
    vectores = datos["vectores"]
    if not isinstance(vectores, Mapping):
        raise ErrorCapturaSubespacio(
            "VECTORES_INVALIDOS", "Los generadores deben ser un objeto de vectores.", "vectores"
        )
    if not DIMENSION_MINIMA <= len(vectores) <= DIMENSION_MAXIMA_VECTORES:
        raise ErrorCapturaSubespacio(
            "CANTIDAD_INVALIDA",
            f"Introduce entre {DIMENSION_MINIMA} y {DIMENSION_MAXIMA_VECTORES} generadores.",
            "vectores",
        )
    generadores = []
    etiquetas = []
    for etiqueta, vector in vectores.items():
        validar_etiqueta(etiqueta, "vectores")
        componentes = _componentes_vector(vector, etiqueta, dimension)
        generadores.append(Matriz(dimension, 1, [[valor] for valor in componentes]))
        etiquetas.append(etiqueta)
    return {
        "modo": MODO_GENERADORES,
        "dimension_ambiente": dimension,
        "generadores": tuple(generadores),
        "etiquetas": tuple(etiquetas),
    }


def capturar_restricciones(captura: object) -> EntradaRestricciones:
    """Convierte A y b exactos; lanza error con ubicacion ante forma, tipo o limite invalido."""
    datos = _validar_mapa(captura, CLAVES_RESTRICCIONES, "captura")
    _validar_modo(datos, MODO_RESTRICCIONES)
    dimension = validar_dimension_ambiente(
        datos["dimension_ambiente"], DIMENSION_MAXIMA_SISTEMAS
    )
    filas = _filas_exactas(datos["matriz_a"], dimension)
    vector_b = _vector_exacto(datos["vector_b"], len(filas))
    return {
        "modo": MODO_RESTRICCIONES,
        "dimension_ambiente": dimension,
        "matriz_a": Matriz(len(filas), dimension, filas),
        "vector_b": vector_b,
    }


def _validar_mapa(captura: object, claves: frozenset[str], ubicacion: str) -> Mapping:
    if not isinstance(captura, Mapping):
        raise ErrorCapturaSubespacio(
            "CAPTURA_INVALIDA", "La captura debe ser un objeto de datos.", ubicacion
        )
    ajenas = _campos_ajenos(captura, claves)
    if ajenas is not None:
        raise ErrorCapturaSubespacio(
            "CAMPOS_AJENOS",
            f"La captura contiene campos no admitidos: {ajenas}.",
            ubicacion,
        )
    faltantes = claves - set(captura)
    if faltantes:
        raise ErrorCapturaSubespacio(
            "CAMPOS_FALTANTES",
            f"Faltan campos obligatorios: {', '.join(sorted(faltantes))}.",
            ubicacion,
        )
    return captura


def _campos_ajenos(datos: Mapping, claves: frozenset[str]) -> str | None:
    """Describe hasta cinco campos no admitidos y resume el resto sin copiar el mapa."""
    ajenas = []
    total = 0
    for clave in datos:
        if clave not in claves:
            total += 1
            if len(ajenas) < MOSTRAR_CLAVES_AJENAS:
                ajenas.append(str(clave))
    if not total:
        return None
    detalle = ", ".join(sorted(ajenas))
    if total > len(ajenas):
        detalle += f" y {total - len(ajenas)} mas"
    return detalle


def _validar_modo(datos: Mapping, esperado: str) -> None:
    if datos.get("modo") != esperado:
        raise ErrorCapturaSubespacio(
            "MODO_INVALIDO", f"La captura debe declarar el modo {esperado}.", "modo"
        )


def _componentes_vector(vector: object, etiqueta: str, dimension: int) -> list[Fraction]:
    ubicacion = f"vectores.{etiqueta}"
    if not isinstance(vector, Mapping):
        raise ErrorCapturaSubespacio(
            "VECTOR_INVALIDO",
            "Cada generador debe ser un objeto con datos y orientacion.",
            ubicacion,
        )
    ajenas = _campos_ajenos(vector, CLAVES_VECTOR)
    if ajenas is not None:
        raise ErrorCapturaSubespacio(
            "CAMPOS_AJENOS",
            f"El generador contiene campos no admitidos: {ajenas}.",
            ubicacion,
        )
    orientacion = vector.get("orientacion", ORIENTACION_COLUMNA)
    if orientacion != ORIENTACION_COLUMNA:
        raise ErrorCapturaSubespacio(
            "ORIENTACION_INVALIDA",
            "Los generadores deben ser vectores columna.",
            f"{ubicacion}.orientacion",
        )
    datos = vector.get("datos")
    if not isinstance(datos, (list, tuple)) or len(datos) != dimension:
        raise ErrorCapturaSubespacio(
            "LONGITUD_INVALIDA",
            f"El generador debe tener {dimension} componentes.",
            f"{ubicacion}.datos",
        )
    return [
        _convertir_celda(celda, f"{ubicacion}.datos[{indice}]")
        for indice, celda in enumerate(datos)
    ]


def _filas_exactas(matriz_a: object, dimension: int) -> list[list[Fraction]]:
    if not isinstance(matriz_a, (list, tuple)) or not DIMENSION_MINIMA <= len(matriz_a) <= DIMENSION_MAXIMA_SISTEMAS:
        raise ErrorCapturaSubespacio(
            "FILAS_INVALIDAS",
            f"La matriz A debe tener entre {DIMENSION_MINIMA} y {DIMENSION_MAXIMA_SISTEMAS} filas.",
            "matriz_a",
        )
    filas = []
    for indice, fila in enumerate(matriz_a):
        if not isinstance(fila, (list, tuple)) or len(fila) != dimension:
            raise ErrorCapturaSubespacio(
                "FILA_INVALIDA",
                f"La fila {indice + 1} debe tener {dimension} coeficientes.",
                f"matriz_a[{indice}]",
            )
        filas.append([
            _convertir_celda(celda, f"matriz_a[{indice}][{columna}]")
            for columna, celda in enumerate(fila)
        ])
    return filas


def _vector_exacto(vector_b: object, cantidad: int) -> tuple[Fraction, ...]:
    if not isinstance(vector_b, (list, tuple)) or len(vector_b) != cantidad:
        raise ErrorCapturaSubespacio(
            "TERMINOS_INVALIDOS",
            f"El vector b debe tener {cantidad} terminos independientes.",
            "vector_b",
        )
    return tuple(
        _convertir_celda(celda, f"vector_b[{indice}]")
        for indice, celda in enumerate(vector_b)
    )


def _convertir_celda(celda: object, ubicacion: str) -> Fraction:
    if type(celda) is bool:
        raise ErrorCapturaSubespacio(
            "VALOR_BOOLEANO", "Los valores deben ser numericos exactos.", ubicacion
        )
    if isinstance(celda, float):
        raise ErrorCapturaSubespacio(
            "VALOR_NO_EXACTO",
            "Los valores no admiten flotantes; usa enteros o fracciones exactas.",
            ubicacion,
        )
    if isinstance(celda, str) and len(celda) > LONGITUD_MAXIMA_CADENA_NUMERO:
        raise ErrorCapturaSubespacio("VALOR_INVALIDO", MENSAJE_NUMERO_DEMASIADO_LARGO, ubicacion)
    if isinstance(celda, str) and not celda.strip():
        return Fraction(0)
    exito, fraccion, mensaje = convertir_numero_exacto(celda)
    if not exito:
        raise ErrorCapturaSubespacio("VALOR_INVALIDO", mensaje, ubicacion)
    return fraccion
