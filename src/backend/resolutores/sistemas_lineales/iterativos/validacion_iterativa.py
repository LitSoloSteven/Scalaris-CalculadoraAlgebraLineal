"""Validación exacta compartida por los métodos iterativos de sistemas lineales."""
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import islice

from src.backend.constantes import (
    DIMENSION_MAXIMA_SISTEMAS, LONGITUD_MAXIMA_CADENA_NUMERO,
    MENSAJE_NUMERO_DEMASIADO_LARGO,
)
from src.backend.modelos.escalares.entrada_numerica import convertir_numero_exacto

from .contrato_iterativo import (
    CampoIterativo, CodigoIterativo, DiagnosticoIterativo, EntradaIterativa,
)
from .limites_iterativos import fraccion_admitida


@dataclass(frozen=True, kw_only=True)
class ParametrosValidacion:
    """Reúne el nombre visible, los topes y la fábrica de diagnósticos del método."""

    nombre_metodo: str
    maximo_iteraciones: int
    maximo_bits_entrada: int
    crear_diagnostico: Callable[..., DiagnosticoIterativo]


@dataclass(frozen=True, kw_only=True)
class EntradaPreparada:
    """Instantánea inmutable de A, b, el inicio y los parámetros ya validados."""

    matriz: tuple[tuple[Fraction, ...], ...]
    vector_b: tuple[Fraction, ...]
    vector_inicial: tuple[Fraction, ...]
    tolerancia: Fraction
    maximo_iteraciones: int
    dominancia_estricta: bool


@dataclass(frozen=True, kw_only=True)
class FalloValidacion:
    """Fallo de entrada con su código, diagnóstico y dominancia si pudo evaluarse."""

    codigo: CodigoIterativo
    diagnostico: DiagnosticoIterativo
    dominancia_estricta: bool | None = None


@dataclass(frozen=True, kw_only=True)
class DatosValidacion:
    """Agrupa los campos crudos que se validan antes de construir la instantánea."""

    matriz: object
    vector_b: object
    vector_inicial: object
    tolerancia: object
    maximo_iteraciones: object


def preparar_entrada(
    entrada: object, parametros: ParametrosValidacion,
) -> EntradaPreparada | FalloValidacion:
    """Valida la entrada tipada y devuelve una instantánea o el fallo ubicado."""
    if not isinstance(entrada, EntradaIterativa):
        return _fallo(
            parametros,
            "entrada",
            f"La entrada debe cumplir el contrato del método de {parametros.nombre_metodo}.",
        )
    return _preparar_sistema(
        DatosValidacion(
            matriz=entrada.matriz_a,
            vector_b=entrada.vector_b,
            vector_inicial=entrada.vector_inicial,
            tolerancia=entrada.tolerancia,
            maximo_iteraciones=entrada.maximo_iteraciones,
        ),
        parametros,
    )


def preparar_captura(
    captura: object, parametros: ParametrosValidacion,
) -> EntradaPreparada | FalloValidacion:
    """Valida las celdas crudas de A y usa un inicio cero cuando se omite el campo."""
    if not isinstance(captura, Mapping):
        return _fallo(
            parametros,
            "entrada",
            f"La captura de {parametros.nombre_metodo} debe contener campos con nombre.",
        )
    matriz = _preparar_cuadricula(captura.get("matriz_a"), parametros)
    if isinstance(matriz, FalloValidacion):
        return matriz
    return _preparar_sistema(
        DatosValidacion(
            matriz=matriz,
            vector_b=captura.get("vector_b"),
            vector_inicial=captura.get("vector_inicial", (0,) * len(matriz)),
            tolerancia=captura.get("tolerancia"),
            maximo_iteraciones=captura.get("maximo_iteraciones"),
        ),
        parametros,
    )


def _preparar_sistema(
    datos: DatosValidacion, parametros: ParametrosValidacion,
) -> EntradaPreparada | FalloValidacion:
    if isinstance(datos.matriz, FalloValidacion):
        return datos.matriz
    dominancia = _es_estrictamente_dominante(datos.matriz)
    dimension = len(datos.matriz)
    vector_b = _validar_vector(datos.vector_b, "vector_b", dimension, parametros)
    if isinstance(vector_b, FalloValidacion):
        return replace(vector_b, dominancia_estricta=dominancia)
    vector_inicial = _validar_vector(
        datos.vector_inicial, "vector_inicial", dimension, parametros,
    )
    if isinstance(vector_inicial, FalloValidacion):
        return replace(vector_inicial, dominancia_estricta=dominancia)
    tolerancia = _validar_tolerancia(datos.tolerancia, parametros)
    if isinstance(tolerancia, FalloValidacion):
        return replace(tolerancia, dominancia_estricta=dominancia)
    maximo = _validar_maximo(datos.maximo_iteraciones, parametros)
    if isinstance(maximo, FalloValidacion):
        return replace(maximo, dominancia_estricta=dominancia)
    diagonal_nula = _buscar_diagonal_nula(datos.matriz)
    if diagonal_nula is not None:
        return _fallo_diagonal(diagonal_nula, dominancia, parametros)
    return EntradaPreparada(
        matriz=datos.matriz,
        vector_b=vector_b,
        vector_inicial=vector_inicial,
        tolerancia=tolerancia,
        maximo_iteraciones=maximo,
        dominancia_estricta=dominancia,
    )


def _preparar_cuadricula(
    datos: object, parametros: ParametrosValidacion,
) -> tuple[tuple[Fraction, ...], ...] | FalloValidacion:
    if not isinstance(datos, (list, tuple)):
        return _fallo_cuadricula(
            parametros,
            "La matriz A debe ser una lista o tupla de filas con los coeficientes originales.",
        )
    filas = tuple(islice(datos, DIMENSION_MAXIMA_SISTEMAS + 1))
    dimension = len(filas)
    if dimension == 0:
        return _fallo_cuadricula(parametros, "La matriz A no puede estar vacía.")
    if dimension > DIMENSION_MAXIMA_SISTEMAS:
        return _fallo_cuadricula(
            parametros,
            f"El orden de A debe estar entre 1 y {DIMENSION_MAXIMA_SISTEMAS}.",
        )
    copia = tuple(
        tuple(islice(fila, dimension + 1)) if isinstance(fila, (list, tuple)) else fila
        for fila in filas
    )
    return _convertir_matriz(copia, dimension, parametros)


def _convertir_matriz(
    datos: tuple, columnas: int, parametros: ParametrosValidacion,
) -> tuple[tuple[Fraction, ...], ...] | FalloValidacion:
    """Convierte la instantánea de A y ubica las filas inválidas."""
    filas_convertidas = []
    for indice_fila, fila in enumerate(datos, 1):
        if not isinstance(fila, (list, tuple)):
            return _fallo_cuadricula(
                parametros,
                f"La fila {indice_fila} de A no es una secuencia válida.",
                indice_fila,
            )
        if len(fila) != columnas:
            unidad = "columna" if columnas == 1 else "columnas"
            mensaje = f"La fila {indice_fila} de A debe tener exactamente {columnas} {unidad}."
            return _fallo_cuadricula(parametros, mensaje, indice_fila)
        fila_convertida = _convertir_secuencia(
            fila, "matriz_a", parametros, indice_fila,
        )
        if isinstance(fila_convertida, FalloValidacion):
            return fila_convertida
        filas_convertidas.append(fila_convertida)
    return tuple(filas_convertidas)


def _convertir_secuencia(
    valores: tuple | list,
    campo: CampoIterativo,
    parametros: ParametrosValidacion,
    fila: int | None = None,
) -> tuple[Fraction, ...] | FalloValidacion:
    """Convierte una secuencia y devuelve la primera celda inválida con su ubicación."""
    convertidas = []
    for indice, valor in enumerate(valores, 1):
        ubicacion_fila = fila if fila is not None else indice
        ubicacion_columna = indice if fila is not None else None
        fraccion = _convertir_escalar(
            valor, campo, parametros, ubicacion_fila, ubicacion_columna,
        )
        if isinstance(fraccion, FalloValidacion):
            return fraccion
        convertidas.append(fraccion)
    return tuple(convertidas)


def _convertir_escalar(
    valor: object,
    campo: CampoIterativo,
    parametros: ParametrosValidacion,
    fila: int | None = None,
    columna: int | None = None,
) -> Fraction | FalloValidacion:
    """Convierte un valor exacto y rechaza booleanos, flotantes o tamaños excesivos."""
    if isinstance(valor, bool):
        return _fallo(parametros, campo, "No se admiten valores booleanos.", fila, columna)
    if not isinstance(valor, (int, str, Fraction)):
        return _fallo(parametros, campo, "El valor debe ser un número exacto.", fila, columna)
    if isinstance(valor, str) and len(valor) > LONGITUD_MAXIMA_CADENA_NUMERO:
        return _fallo(parametros, campo, MENSAJE_NUMERO_DEMASIADO_LARGO, fila, columna)
    valido, fraccion, mensaje = convertir_numero_exacto(valor)
    if not valido:
        return _fallo(parametros, campo, mensaje, fila, columna)
    if not fraccion_admitida(fraccion, parametros.maximo_bits_entrada):
        return _fallo(
            parametros,
            campo,
            f"El número excede el tamaño máximo de {parametros.maximo_bits_entrada} bits "
            "en numerador o denominador.",
            fila,
            columna,
        )
    return fraccion


def _validar_vector(
    valor: object,
    campo: CampoIterativo,
    dimension: int,
    parametros: ParametrosValidacion,
) -> tuple[Fraction, ...] | FalloValidacion:
    """Copia el vector y comprueba su longitud antes de leer sus celdas."""
    if not isinstance(valor, (tuple, list)):
        return _fallo(
            parametros, campo, f"El vector debe ser una tupla o lista de {dimension} valores.",
        )
    copia = tuple(islice(iter(valor), dimension + 1))
    if len(copia) != dimension:
        return _fallo(
            parametros, campo, f"El vector no tiene exactamente {dimension} valores.",
        )
    return _convertir_secuencia(copia, campo, parametros)


def _validar_tolerancia(
    valor: object, parametros: ParametrosValidacion,
) -> Fraction | FalloValidacion:
    """Exige una tolerancia racional estrictamente positiva y de tamaño admitido."""
    fraccion = _convertir_escalar(valor, "tolerancia", parametros)
    if isinstance(fraccion, FalloValidacion):
        return fraccion
    if fraccion <= 0:
        return _fallo(
            parametros, "tolerancia", "La tolerancia debe ser estrictamente positiva.",
        )
    return fraccion


def _validar_maximo(
    valor: object, parametros: ParametrosValidacion,
) -> int | FalloValidacion:
    """Exige un entero positivo dentro del tope documentado de iteraciones."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        return _fallo(
            parametros, "maximo_iteraciones",
            "El máximo de iteraciones debe ser un entero.",
        )
    if not 1 <= valor <= parametros.maximo_iteraciones:
        return _fallo(
            parametros,
            "maximo_iteraciones",
            f"El máximo de iteraciones debe estar entre 1 y {parametros.maximo_iteraciones}.",
        )
    return valor


def _buscar_diagonal_nula(matriz: tuple[tuple[Fraction, ...], ...]) -> int | None:
    """Devuelve el índice de la primera ecuación con diagonal cero, si existe."""
    for indice, fila in enumerate(matriz):
        if fila[indice] == 0:
            return indice
    return None


def _es_estrictamente_dominante(matriz: tuple[tuple[Fraction, ...], ...]) -> bool:
    """Comprueba |a_ii| > suma de |a_ij| fuera de la diagonal en cada fila."""
    for indice, fila in enumerate(matriz):
        suma_fuera = sum(
            abs(valor) for posicion, valor in enumerate(fila) if posicion != indice
        )
        if abs(fila[indice]) <= suma_fuera:
            return False
    return True


def _fallo_diagonal(
    indice: int, dominancia: bool, parametros: ParametrosValidacion,
) -> FalloValidacion:
    """Construye el diagnóstico de una diagonal nula con su fila y columna."""
    posicion = indice + 1
    return FalloValidacion(
        codigo="DIAGONAL_NULA",
        diagnostico=parametros.crear_diagnostico(
            mensaje=(
                f"El coeficiente diagonal A[{posicion},{posicion}] debe ser distinto de cero."
            ),
            campo="matriz_a",
            fila=posicion,
            columna=posicion,
        ),
        dominancia_estricta=dominancia,
    )


def _fallo(
    parametros: ParametrosValidacion,
    campo: CampoIterativo,
    mensaje: str,
    fila: int | None = None,
    columna: int | None = None,
) -> FalloValidacion:
    """Construye un fallo de entrada con el campo y las coordenadas conocidas."""
    return FalloValidacion(
        codigo="ENTRADA_INVALIDA",
        diagnostico=parametros.crear_diagnostico(
            mensaje=mensaje, campo=campo, fila=fila, columna=columna,
        ),
    )


def _fallo_cuadricula(
    parametros: ParametrosValidacion, mensaje: str, fila: int | None = None,
) -> FalloValidacion:
    """Construye un fallo de forma de A con el diagnóstico propio del método."""
    return FalloValidacion(
        codigo="ENTRADA_INVALIDA",
        diagnostico=parametros.crear_diagnostico(
            mensaje=mensaje, campo="matriz_a", fila=fila,
        ),
    )
