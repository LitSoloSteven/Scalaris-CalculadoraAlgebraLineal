"""Valida y normaliza la representación de captura y la entrada tipada."""
from collections.abc import Mapping
from fractions import Fraction
from itertools import chain
from typing import cast

from src.backend.constantes import LONGITUD_MAXIMA_CADENA_NUMERO
from src.backend.modelos.escalares.entrada_numerica import convertir_numero_exacto
from ..subespacios.captura_subespacios import capturar_generadores, capturar_restricciones
from ..subespacios.contrato_subespacios import (
    EntradaSubespacio, ErrorCapturaSubespacio, validar_entrada_subespacio,
)
from .contrato_espacio_vectorial import (
    CampoDiagnostico, CampoOperacion, DiagnosticoEspacioVectorial,
    EntradaEspacioVectorial, ErrorCapturaEspacioVectorial, OperacionPolinomica,
    TerminoPolinomico,
)
from .limites_espacio_vectorial import (
    MAXIMO_BITS_ENTRADA, MAXIMO_GRADO_ENTRADA, MAXIMO_TERMINOS_ENTRADA, racional_admitido,
)

_CLAVES_ENTRADA = frozenset({"conjunto", "suma", "producto_escalar"})
_CLAVES_TERMINO = frozenset({"coeficiente", "exponentes"})


def crear_diagnostico(
    mensaje: str, campo: CampoDiagnostico = "general",
    coordenada: int | None = None, termino: int | None = None,
) -> DiagnosticoEspacioVectorial:
    """Devuelve un diagnóstico seguro con la ubicación que conoce el dominio."""
    return {"campo": campo, "coordenada": coordenada, "termino": termino, "mensaje": mensaje}


def capturar_espacio_vectorial(captura: object) -> EntradaEspacioVectorial:
    """Convierte datos serializables o lanza ErrorCapturaEspacioVectorial con ubicación."""
    datos = _validar_claves_entrada(captura)
    return _preparar_entrada(datos, _capturar_conjunto(datos["conjunto"]), list)


def validar_entrada_espacio_vectorial(entrada: object) -> EntradaEspacioVectorial:
    """Revalida el contrato tipado y devuelve la entrada con operaciones normalizadas."""
    datos = _validar_claves_entrada(entrada)
    conjunto = datos["conjunto"]
    try:
        validar_entrada_subespacio(conjunto)
    except ErrorCapturaSubespacio as error:
        raise _error_conjunto() from error
    return _preparar_entrada(datos, cast(EntradaSubespacio, conjunto), tuple)


def _validar_claves_entrada(entrada: object) -> Mapping:
    if not isinstance(entrada, Mapping) or not _claves_exactas(entrada, _CLAVES_ENTRADA):
        raise ErrorCapturaEspacioVectorial(crear_diagnostico(
            "La entrada debe contener conjunto, suma y producto escalar."
        ))
    return entrada


def _claves_exactas(datos: Mapping, claves: frozenset[str]) -> bool:
    return len(datos) == len(claves) and all(clave in datos for clave in claves)


def _capturar_conjunto(datos: object) -> EntradaSubespacio:
    if not isinstance(datos, Mapping) or len(datos) > _MAXIMO_CAMPOS_CONJUNTO:
        raise _error_conjunto()
    try:
        if datos.get("modo") == "generadores":
            _acotar_mapas_vectores(datos.get("vectores"))
            return capturar_generadores(datos)
        return capturar_restricciones(datos)
    except ErrorCapturaSubespacio as error:
        raise _error_conjunto() from error


_MAXIMO_CAMPOS_CONJUNTO = 4
_MAXIMO_CAMPOS_VECTOR = 2


def _acotar_mapas_vectores(vectores: object) -> None:
    from src.backend.constantes import DIMENSION_MAXIMA_VECTORES

    if not isinstance(vectores, Mapping) or len(vectores) > DIMENSION_MAXIMA_VECTORES:
        raise _error_conjunto()
    for vector in vectores.values():
        if isinstance(vector, Mapping) and len(vector) > _MAXIMO_CAMPOS_VECTOR:
            raise _error_conjunto()


def _error_conjunto() -> ErrorCapturaEspacioVectorial:
    return ErrorCapturaEspacioVectorial(crear_diagnostico(
        "Revisa el modo, la dimensión y los datos del conjunto.", "conjunto"
    ))


def _preparar_entrada(
    datos: Mapping, conjunto: EntradaSubespacio, contenedor: type[list] | type[tuple],
) -> EntradaEspacioVectorial:
    if any(not racional_admitido(valor, MAXIMO_BITS_ENTRADA) for valor in _valores(conjunto)):
        raise ErrorCapturaEspacioVectorial(crear_diagnostico(
            "Un coeficiente del conjunto excede el tamaño admitido.", "conjunto"
        ))
    dimension = conjunto["dimension_ambiente"]
    return {
        "conjunto": conjunto,
        "suma": _operacion(datos["suma"], "suma", dimension, contenedor),
        "producto_escalar": _operacion(datos["producto_escalar"], "producto_escalar", dimension, contenedor),
    }


def _valores(conjunto: EntradaSubespacio):
    if conjunto["modo"] == "generadores":
        return (fila[0] for generador in conjunto["generadores"] for fila in generador.datos)
    return chain(chain.from_iterable(conjunto["matriz_a"].datos), conjunto["vector_b"])


def _operacion(
    datos: object, campo: CampoOperacion, dimension: int, contenedor: type[list] | type[tuple],
) -> OperacionPolinomica:
    if not isinstance(datos, contenedor) or len(datos) != dimension:
        raise ErrorCapturaEspacioVectorial(crear_diagnostico(
            f"La operación debe tener {dimension} coordenadas.", campo
        ))
    cantidad_variables = dimension * 2 if campo == "suma" else dimension + 1
    return tuple(
        _coordenada(valor, (campo, indice), cantidad_variables, contenedor)
        for indice, valor in enumerate(datos, 1)
    )


def _coordenada(
    datos: object, ubicacion: tuple[CampoOperacion, int],
    cantidad_variables: int, contenedor: type[list] | type[tuple],
) -> tuple[TerminoPolinomico, ...]:
    if not isinstance(datos, contenedor) or len(datos) > MAXIMO_TERMINOS_ENTRADA:
        raise ErrorCapturaEspacioVectorial(crear_diagnostico(
            f"Cada coordenada admite hasta {MAXIMO_TERMINOS_ENTRADA} términos.", *ubicacion
        ))
    return tuple(
        _termino(valor, (*ubicacion, indice), cantidad_variables, contenedor)
        for indice, valor in enumerate(datos, 1)
    )


def _termino(
    datos: object, ubicacion: tuple[CampoOperacion, int, int],
    cantidad_variables: int, contenedor: type[list] | type[tuple],
) -> TerminoPolinomico:
    if not isinstance(datos, Mapping) or not _claves_exactas(datos, _CLAVES_TERMINO):
        raise ErrorCapturaEspacioVectorial(crear_diagnostico(
            "Indica el coeficiente y los exponentes del término.", *ubicacion
        ))
    exponentes = datos["exponentes"]
    if not _exponentes_validos(exponentes, cantidad_variables, contenedor):
        raise ErrorCapturaEspacioVectorial(crear_diagnostico(
            f"Usa {cantidad_variables} exponentes enteros no negativos y grado máximo {MAXIMO_GRADO_ENTRADA}.",
            *ubicacion,
        ))
    coeficiente = _coeficiente(datos["coeficiente"], desde_texto=contenedor is list)
    if coeficiente is None:
        raise ErrorCapturaEspacioVectorial(crear_diagnostico(
            "Usa un coeficiente racional exacto dentro del tamaño admitido.", *ubicacion
        ))
    return {"coeficiente": coeficiente, "exponentes": tuple(exponentes)}


def _exponentes_validos(datos: object, cantidad: int, contenedor: type[list] | type[tuple]) -> bool:
    return (
        isinstance(datos, contenedor) and len(datos) == cantidad
        and all(type(valor) is int and 0 <= valor <= MAXIMO_GRADO_ENTRADA for valor in datos)
        and sum(datos) <= MAXIMO_GRADO_ENTRADA
    )


def _coeficiente(valor: object, *, desde_texto: bool) -> Fraction | None:
    if desde_texto:
        if not isinstance(valor, str) or len(valor) > LONGITUD_MAXIMA_CADENA_NUMERO:
            return None
        valido, valor, _ = convertir_numero_exacto(valor)
        if not valido:
            return None
    if isinstance(valor, Fraction) and racional_admitido(valor, MAXIMO_BITS_ENTRADA):
        return valor
    return None
