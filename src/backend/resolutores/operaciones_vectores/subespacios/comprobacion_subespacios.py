"""Comprobaciones exactas y testigos del analisis de subespacios."""
from collections.abc import Iterable
from fractions import Fraction
from itertools import chain

from src.backend.modelos.escalares.conversion_fracciones import convertir_fraccion, texto_fraccion_exacta
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.solucion.comprobacion_sistemas import (
    comprobar_familia,
)
from src.backend.resolutores.sistemas_lineales.reduccion.configuracion_reduccion import ConfiguracionReduccion
from src.backend.resolutores.sistemas_lineales.solucion.modelo_solucion import ParametrosSolucion
from src.backend.resolutores.sistemas_lineales.reduccion.reduccion import ReductorFilas
from .contrato_subespacios import (
    ErrorVerificacionSubespacio,
    TestigoSubespacio,
)

CONFIGURACION_EXACTA = ConfiguracionReduccion(reduccion_completa=True, tolerancia_cero=0)
# 2048 bits caben en el límite decimal mínimo configurable de CPython.
MAXIMO_BITS_DESARROLLO = 2048


def verificar_base_generadores(
    generadores: tuple[Matriz, ...],
    base: tuple[tuple[Fraction, ...], ...],
    indices: tuple[int, ...],
    matriz_reducida: Matriz | None = None,
) -> tuple[dict, ...]:
    """Verifica las columnas originales y su independencia con los pivotes si se aporta la reducción."""
    if len(indices) != len(base) or len(set(indices)) != len(indices):
        raise ErrorVerificacionSubespacio(
            "Los indices de la base no son unicos ni corresponden uno a uno con sus vectores."
        )
    if any(not 0 <= indice < len(generadores) for indice in indices):
        raise ErrorVerificacionSubespacio(
            "La base referencia una columna de generador fuera de rango."
        )
    comprobaciones = []
    for indice, vector in zip(indices, base):
        columna = tuple(Fraction(generadores[indice].obtener(fila, 0))
                        for fila in range(generadores[indice].filas))
        if columna != vector:
            raise ErrorVerificacionSubespacio(
                f"La columna {indice} no coincide con el vector base seleccionado."
            )
        comprobaciones.append({
            "tipo": "columna_original",
            "indice": indice,
            "coincide": True,
            "detalle": f"La base usa la columna original {indice}.",
        })
    comprobaciones.append(_comprobacion_independencia(base, indices, matriz_reducida))
    return tuple(comprobaciones)


def comprobar_familia_exacta(
    matriz_a: Matriz,
    vector_b: tuple[Fraction, ...],
    parametros: ParametrosSolucion,
    columnas_libres: tuple[int, ...] | None = None,
) -> tuple[dict, ...]:
    """Verifica A·p=b y A·d=0, y comprueba la base si se indican las columnas libres."""
    if columnas_libres is not None:
        _validar_base_nucleo(parametros, columnas_libres, matriz_a.columnas)
    direcciones = parametros["direcciones"]
    filas = [*matriz_a.datos, vector_b, parametros["particular"], *direcciones]
    detallar = not _requiere_resumen(chain.from_iterable(filas))
    parametros_con_nombres = {
        **parametros,
        "nombres_parametros": [
            f"t_{indice + 1}" for indice in range(len(direcciones))
        ],
    }
    verificacion = comprobar_familia(
        matriz_a.datos, list(vector_b), parametros_con_nombres, None, detallar
    )
    if not verificacion["coincide"]:
        raise ErrorVerificacionSubespacio(
            "La familia propuesta no satisface todas las ecuaciones originales."
        )
    return tuple({
        "tipo": "familia",
        "fila": indice + 1,
        "coincide": fila["coincide"],
        "detalle_latex": fila["detalle_latex"] if detallar else (
            rf"\text{{Fila {indice + 1} verificada exactamente. Desarrollo omitido por tamaño.}}"
        ),
    } for indice, fila in enumerate(verificacion["filas"]))


def _validar_base_nucleo(
    parametros: ParametrosSolucion, columnas_libres: tuple[int, ...], dimension: int
) -> None:
    particular = parametros["particular"]
    direcciones = parametros["direcciones"]
    if (
        len(particular) != dimension
        or len(direcciones) != len(columnas_libres)
        or any(len(direccion) != dimension for direccion in direcciones)
    ):
        raise ErrorVerificacionSubespacio(
            "La familia propuesta no tiene la dimensión ni la cantidad de direcciones esperadas."
        )
    if any(
        direccion[columna] != (indice == posicion)
        for indice, direccion in enumerate(direcciones)
        for posicion, columna in enumerate(columnas_libres)
    ):
        raise ErrorVerificacionSubespacio(
            "Las direcciones no forman la base canónica sobre las variables libres."
        )


def _requiere_resumen(valores: Iterable[Fraction]) -> bool:
    for valor in valores:
        fraccion = convertir_fraccion(valor)
        if max(fraccion.numerator.bit_length(), fraccion.denominator.bit_length()) > MAXIMO_BITS_DESARROLLO:
            return True
    return False


def construir_testigo_contradictorio(
    matriz_reducida: Matriz, numero_variables: int
) -> TestigoSubespacio:
    """Devuelve la primera fila reducida 0=c con c distinto de cero; error si no existe."""
    for indice, fila in enumerate(matriz_reducida.datos):
        coeficientes = tuple(Fraction(valor) for valor in fila[:numero_variables])
        termino = Fraction(fila[numero_variables])
        if all(valor == 0 for valor in coeficientes) and termino != 0:
            return {
                "tipo": "fila_contradictoria",
                "indice_fila": indice,
                "coeficientes": coeficientes,
                "termino_independiente": termino,
                "valor_izquierdo": Fraction(0),
                "descripcion": _descripcion_testigo(f"La fila {indice + 1} reducida queda", termino),
            }
    raise ErrorVerificacionSubespacio(
        "El sistema se clasifico como incompatible sin fila contradictoria."
    )


def construir_testigo_origen(
    matriz_a: Matriz, vector_b: tuple[Fraction, ...]
) -> TestigoSubespacio:
    """Devuelve una ecuacion original con b distinto de cero que el origen no satisface."""
    for indice, (fila, termino) in enumerate(zip(matriz_a.datos, vector_b)):
        if termino != 0:
            coeficientes = tuple(Fraction(valor) for valor in fila)
            return {
                "tipo": "origen_no_pertenece",
                "indice_fila": indice,
                "coeficientes": coeficientes,
                "termino_independiente": Fraction(termino),
                "valor_izquierdo": Fraction(0),
                "descripcion": _descripcion_testigo(f"En el origen, la ecuacion {indice + 1} da", termino),
            }
    raise ErrorVerificacionSubespacio(
        "El conjunto afin no contiene al origen pero el vector b es nulo."
    )


def _descripcion_testigo(prefijo: str, termino: Fraction) -> str:
    if _requiere_resumen((termino,)):
        return f"{prefijo} 0 = c, con c distinto de cero. El testigo conserva su valor exacto."
    return f"{prefijo} 0 = {texto_fraccion_exacta(termino)}."


def _comprobacion_independencia(
    base: tuple[tuple[Fraction, ...], ...], indices: tuple[int, ...],
    matriz_reducida: Matriz | None,
) -> dict:
    if not base:
        return {
            "tipo": "independencia_base",
            "coincide": True,
            "detalle": "La base vacia describe el subespacio cero.",
        }
    if matriz_reducida is None:
        matriz = Matriz(len(base[0]), len(base), [list(fila) for fila in zip(*base, strict=True)])
        reduccion = ReductorFilas(matriz, matriz.columnas, CONFIGURACION_EXACTA).reducir()
        independiente = reduccion["rango"] == len(base)
    else:
        independiente = _pivotes_canonicos(matriz_reducida, indices)
    if not independiente:
        raise ErrorVerificacionSubespacio(
            "La base seleccionada no es linealmente independiente."
        )
    return {
        "tipo": "independencia_base",
        "coincide": True,
        "detalle": "Los vectores son linealmente independientes.",
    }


def _pivotes_canonicos(matriz: Matriz, indices: tuple[int, ...]) -> bool:
    return len(indices) <= matriz.filas and all(
        columna < matriz.columnas and all(
            matriz.obtener(fila, columna) == (fila == posicion) for fila in range(matriz.filas)
        )
        for posicion, columna in enumerate(indices)
    )
